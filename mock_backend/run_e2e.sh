#!/usr/bin/env bash
# One-shot end-to-end loop:
#   1. start the FastAPI mock in the background
#   2. issue a token, export DRD_CLOUD_API_HOST/TOKEN
#   3. start celery beat + workers in the background
#   4. seed scenarios
#   5. wait for the agent to drain everything
#   6. validate via e2e.py
#   7. tear everything down (PASS/FAIL exit code)
#
# Requirements:
#   - redis available at $REDIS_URL (default redis://localhost:6379/0)
#   - VPC agent's Python deps importable from the current shell
#     (e.g. `pip install -r requirements.txt` from repo root, or activate venv)
#   - credentials/secrets.yaml populated with the connectors referenced
#     in your scenarios file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

PORT="${MOCK_BACKEND_PORT:-8080}"
SCENARIOS_FILE="${SCENARIOS_FILE:-$SCRIPT_DIR/scenarios/default.json}"
E2E_TIMEOUT="${E2E_TIMEOUT:-120}"

cd "$SCRIPT_DIR"

# 1. mock backend ---------------------------------------------------------

VENV="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
  echo "[e2e] creating mock-backend venv" >&2
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip >/dev/null
  "$VENV/bin/pip" install -r requirements.txt >/dev/null
fi

LOG_DIR="$SCRIPT_DIR/data/agent-logs"
MOCK_LOG="$SCRIPT_DIR/data/mock-backend.log"
mkdir -p "$LOG_DIR"
: > "$MOCK_LOG"

"$VENV/bin/uvicorn" app:app --host 0.0.0.0 --port "$PORT" --log-level warning >>"$MOCK_LOG" 2>&1 &
MOCK_PID=$!
trap 'echo "[e2e] tearing down" >&2; kill $MOCK_PID 2>/dev/null || true; pkill -P $$ 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 50); do
  curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null && break
  sleep 0.1
done
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || { echo "[e2e] mock did not start — see $MOCK_LOG" >&2; exit 1; }
echo "[e2e] mock up on :${PORT}" >&2

# 2. token + env ---------------------------------------------------------

TOKEN=$(curl -sf -X POST "http://127.0.0.1:${PORT}/admin/tokens" \
  -H 'content-type: application/json' -d '{"label":"e2e"}' \
  | "$VENV/bin/python" -c 'import json,sys;print(json.load(sys.stdin)["token"])')
echo "[e2e] issued token ${TOKEN:0:14}…" >&2

export DRD_CLOUD_API_TOKEN="$TOKEN"
export DRD_CLOUD_API_HOST="http://127.0.0.1:${PORT}"
export VPC_AGENT_COMMIT_HASH="${VPC_AGENT_COMMIT_HASH:-e2e-test}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

# 3. wipe prior recordings & start agent ---------------------------------

curl -sf -X POST "http://127.0.0.1:${PORT}/admin/reset?keep_tokens=true" >/dev/null

cd "$REPO_DIR"
echo "[e2e] migrating sqlite" >&2
python manage.py migrate >/dev/null

echo "[e2e] starting celery beat + workers" >&2
celery -A agent beat -l INFO --pidfile="$LOG_DIR/beat.pid" >"$LOG_DIR/beat.log" 2>&1 &
celery -A agent worker -l INFO -Q celery --concurrency=2 --pidfile="$LOG_DIR/worker.pid" >"$LOG_DIR/worker.log" 2>&1 &
celery -A agent worker -l INFO -Q exec    --concurrency=2 --pidfile="$LOG_DIR/worker-exec.pid" >"$LOG_DIR/worker-exec.log" 2>&1 &

# Give celery a moment to register beat/worker schedules.
sleep 4

# 4. seed scenarios ------------------------------------------------------

echo "[e2e] seeding $SCENARIOS_FILE" >&2
"$VENV/bin/python" "$SCRIPT_DIR/seed_scenarios.py" \
  --host "http://127.0.0.1:${PORT}" --file "$SCENARIOS_FILE"

# 5. validate ------------------------------------------------------------

set +e
"$VENV/bin/python" "$SCRIPT_DIR/e2e.py" \
  --host "http://127.0.0.1:${PORT}" \
  --file "$SCENARIOS_FILE" \
  --timeout "$E2E_TIMEOUT"
RC=$?
set -e

if [[ $RC -eq 0 ]]; then
  echo "[e2e] PASS" >&2
else
  echo "[e2e] FAIL — see $LOG_DIR/*.log and $MOCK_LOG" >&2
fi
exit $RC
