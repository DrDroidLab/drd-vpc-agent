#!/usr/bin/env bash
# Boot the VPC agent (celery beat + worker + exec-worker) pointed at the
# mock backend. Token + host are required — get them from run_mock.sh.
#
#   DRD_CLOUD_API_TOKEN=... DRD_CLOUD_API_HOST=http://127.0.0.1:8080 ./run_agent.sh
#
# This expects: redis on $REDIS_URL (default localhost:6379), the agent's
# Python deps installed in the active environment, and credentials/secrets.yaml
# populated with at least the connectors referenced in your scenarios.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

: "${DRD_CLOUD_API_TOKEN:?set DRD_CLOUD_API_TOKEN — get one from run_mock.sh}"
: "${DRD_CLOUD_API_HOST:=http://127.0.0.1:8080}"
: "${CELERY_BROKER_URL:=redis://localhost:6379/0}"
: "${CELERY_RESULT_BACKEND:=redis://localhost:6379/0}"
: "${REDIS_URL:=redis://localhost:6379/0}"
: "${VPC_AGENT_COMMIT_HASH:=mock-test}"

export DRD_CLOUD_API_TOKEN DRD_CLOUD_API_HOST CELERY_BROKER_URL CELERY_RESULT_BACKEND REDIS_URL VPC_AGENT_COMMIT_HASH

cd "$REPO_DIR"

LOG_DIR="$SCRIPT_DIR/data/agent-logs"
mkdir -p "$LOG_DIR"

echo "[run_agent] migrating sqlite…" >&2
python manage.py migrate >/dev/null

echo "[run_agent] starting celery beat" >&2
celery -A agent beat -l INFO --pidfile="$LOG_DIR/beat.pid" >"$LOG_DIR/beat.log" 2>&1 &
BEAT_PID=$!

echo "[run_agent] starting celery worker (default queue)" >&2
celery -A agent worker -l INFO -Q celery --concurrency=2 \
  --pidfile="$LOG_DIR/worker.pid" >"$LOG_DIR/worker.log" 2>&1 &
WORKER_PID=$!

echo "[run_agent] starting celery worker (exec queue)" >&2
CELERY_QUEUE=exec celery -A agent worker -l INFO -Q exec --concurrency=2 \
  --pidfile="$LOG_DIR/worker-exec.pid" >"$LOG_DIR/worker-exec.log" 2>&1 &
EXEC_PID=$!

trap 'kill $BEAT_PID $WORKER_PID $EXEC_PID 2>/dev/null || true' EXIT INT TERM

echo "==============================================================" >&2
echo "[run_agent] agent running. logs in $LOG_DIR" >&2
echo "[run_agent] beat=$BEAT_PID worker=$WORKER_PID exec=$EXEC_PID" >&2
echo "[run_agent] press Ctrl-C to stop" >&2
echo "==============================================================" >&2

wait
