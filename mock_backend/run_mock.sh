#!/usr/bin/env bash
# Bring up the mock backend and print a freshly-issued bearer token.
#
#   ./run_mock.sh [--port 8080] [--no-token]
#
# The token is printed to stdout. Capture it like:
#   TOKEN=$(./run_mock.sh --print-token-only)
# (in another terminal — the script blocks on uvicorn while serving)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${MOCK_BACKEND_PORT:-8080}"
HOST="${MOCK_BACKEND_HOST:-0.0.0.0}"
ISSUE_TOKEN=1
PRINT_TOKEN_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --no-token) ISSUE_TOKEN=0; shift ;;
    --print-token-only) PRINT_TOKEN_ONLY=1; shift ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

cd "$SCRIPT_DIR"

# Lazy install — keep deps off the agent's environment by using a venv next to this dir.
VENV="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
  echo "[mock_backend] creating venv at $VENV" >&2
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip >/dev/null
  "$VENV/bin/pip" install -r requirements.txt >/dev/null
fi

PYTHON="$VENV/bin/python"
UVICORN="$VENV/bin/uvicorn"

# Kick off uvicorn in the background so we can issue a token, then bring it
# to the foreground with `wait`.
LOG_FILE="$SCRIPT_DIR/data/mock-backend.log"
mkdir -p "$SCRIPT_DIR/data"
"$UVICORN" app:app --host "$HOST" --port "$PORT" --log-level info >"$LOG_FILE" 2>&1 &
UVICORN_PID=$!
trap 'kill "$UVICORN_PID" 2>/dev/null || true' EXIT INT TERM

# Wait for /health to come up.
for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then break; fi
  sleep 0.1
done
if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
  echo "[mock_backend] failed to start — see $LOG_FILE" >&2
  exit 1
fi

if [[ "$ISSUE_TOKEN" -eq 1 ]]; then
  TOKEN=$(curl -sf -X POST "http://127.0.0.1:${PORT}/admin/tokens" \
    -H 'content-type: application/json' -d '{"label":"agent"}' \
    | "$PYTHON" -c 'import json,sys;print(json.load(sys.stdin)["token"])')
  if [[ "$PRINT_TOKEN_ONLY" -eq 1 ]]; then
    # In token-only mode we exit immediately so the caller can eat stdout.
    echo "$TOKEN"
    kill "$UVICORN_PID" 2>/dev/null || true
    exit 0
  fi
  echo "==============================================================" >&2
  echo "[mock_backend] up at http://127.0.0.1:${PORT}" >&2
  echo "[mock_backend] token: $TOKEN" >&2
  echo "[mock_backend] export: DRD_CLOUD_API_TOKEN=$TOKEN" >&2
  echo "[mock_backend] export: DRD_CLOUD_API_HOST=http://127.0.0.1:${PORT}" >&2
  echo "==============================================================" >&2
fi

wait "$UVICORN_PID"
