#!/usr/bin/env bash
# Full Kind-based test loop: agent runs from its real Docker image, mock
# backend runs as a sibling pod in the same namespace.
#
# By default it reuses the agent image when it already exists locally —
# the alpine first-build is ~20min, but subsequent test iterations are
# ~30s. Pass --rebuild-agent (or --rebuild) when the agent code changed.
#
# Usage:
#   ./mock_backend/deploy_kind.sh                # build (or reuse) + deploy + seed + validate
#   ./mock_backend/deploy_kind.sh --reuse-image  # force-skip both rebuilds (fastest)
#   ./mock_backend/deploy_kind.sh --rebuild      # force a full rebuild of both images
#   ./mock_backend/deploy_kind.sh --rebuild-agent  # rebuild agent only (after code changes)
#   ./mock_backend/deploy_kind.sh --rebuild-mock   # rebuild mock only
#   ./mock_backend/deploy_kind.sh --no-validate  # skip e2e.py
#   ./mock_backend/deploy_kind.sh --reset-only   # tear down mock + agent, leave cluster
#
# Token + host are auto-wired — you don't bring them. The script prints
# everything you need (token, URLs, kubectl tail commands) on success.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

KIND_CLUSTER="${KIND_CLUSTER_NAME:-drd-local}"
NS="drdroid"
MOCK_IMAGE="drd-vpc-agent-mock:local-latest"
MOCK_SVC_HOST="http://drd-vpc-agent-mock.${NS}.svc.cluster.local:8080"
PORT_FWD_LOCAL_PORT="${MOCK_PORT_FORWARD:-18080}"

VALIDATE=1
RESET_ONLY=0
REUSE_AGENT_IMAGE=auto    # auto | always | never
REUSE_MOCK_IMAGE=auto
SCENARIOS_FILE="${SCENARIOS_FILE:-$SCRIPT_DIR/scenarios/default.json}"
E2E_TIMEOUT="${E2E_TIMEOUT:-180}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-validate) VALIDATE=0; shift ;;
    --reset-only) RESET_ONLY=1; shift ;;
    --reuse-image) REUSE_AGENT_IMAGE=always; REUSE_MOCK_IMAGE=always; shift ;;
    --rebuild) REUSE_AGENT_IMAGE=never; REUSE_MOCK_IMAGE=never; shift ;;
    --rebuild-agent) REUSE_AGENT_IMAGE=never; shift ;;
    --rebuild-mock) REUSE_MOCK_IMAGE=never; shift ;;
    --scenarios) SCENARIOS_FILE="$2"; shift 2 ;;
    --timeout) E2E_TIMEOUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

log() { echo "[deploy_kind] $*" >&2; }

# Reset path -------------------------------------------------------------
if [[ "$RESET_ONLY" -eq 1 ]]; then
  log "uninstalling agent helm release"
  helm status drd-vpc-agent -n "$NS" >/dev/null 2>&1 && helm uninstall drd-vpc-agent -n "$NS" || true
  log "deleting mock manifest"
  kubectl delete -f "$SCRIPT_DIR/k8s/manifests.yaml" --ignore-not-found
  log "done"
  exit 0
fi

# 1. cluster -------------------------------------------------------------
if ! kind get clusters 2>/dev/null | grep -q "^${KIND_CLUSTER}$"; then
  log "creating Kind cluster '${KIND_CLUSTER}'"
  kind create cluster --name "${KIND_CLUSTER}"
fi
kubectl config use-context "kind-${KIND_CLUSTER}" >/dev/null
kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# 2. build + load mock image --------------------------------------------
should_rebuild_mock=1
if [[ "$REUSE_MOCK_IMAGE" == "always" ]]; then
  should_rebuild_mock=0
elif [[ "$REUSE_MOCK_IMAGE" == "auto" ]] && docker image inspect "$MOCK_IMAGE" >/dev/null 2>&1; then
  # Auto-reuse only if no source files are newer than the image.
  IMAGE_TS=$(docker image inspect -f '{{.Created}}' "$MOCK_IMAGE" 2>/dev/null | xargs -I{} date -j -f '%Y-%m-%dT%H:%M:%S' "{}" +%s 2>/dev/null || echo 0)
  NEWEST_SRC=$(find "$SCRIPT_DIR" -maxdepth 2 \( -name '*.py' -o -name 'requirements.txt' -o -name 'Dockerfile' \) -not -path '*/.venv/*' -not -path '*/data/*' -print0 2>/dev/null | xargs -0 stat -f '%m' 2>/dev/null | sort -n | tail -1)
  if [[ -n "$IMAGE_TS" && -n "$NEWEST_SRC" && "$NEWEST_SRC" -le "$IMAGE_TS" ]]; then
    should_rebuild_mock=0
  fi
fi

if [[ "$should_rebuild_mock" -eq 1 ]]; then
  log "building mock image: $MOCK_IMAGE"
  docker build -t "$MOCK_IMAGE" "$SCRIPT_DIR" >/dev/null
else
  log "reusing existing mock image: $MOCK_IMAGE"
fi

log "kind load $MOCK_IMAGE (idempotent)"
kind load docker-image "$MOCK_IMAGE" --name "${KIND_CLUSTER}" >/dev/null 2>&1 || true

# 3. apply mock manifests ------------------------------------------------
log "applying mock manifests"
kubectl apply -f "$SCRIPT_DIR/k8s/manifests.yaml" >/dev/null

# Force a pod recycle so a new image is picked up on rebuild.
kubectl -n "$NS" rollout restart deployment/drd-vpc-agent-mock >/dev/null

# 4. wait for readiness --------------------------------------------------
log "waiting for mock pod to be ready"
kubectl -n "$NS" rollout status deployment/drd-vpc-agent-mock --timeout=120s >/dev/null

# 5. port-forward briefly + mint a token --------------------------------
log "minting token via port-forward on :${PORT_FWD_LOCAL_PORT}"
kubectl -n "$NS" port-forward svc/drd-vpc-agent-mock "${PORT_FWD_LOCAL_PORT}:8080" >/tmp/drd-mock-pf.log 2>&1 &
PF_PID=$!
trap 'kill "$PF_PID" 2>/dev/null || true' EXIT INT TERM

# Wait until the forward is live.
for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}/health" >/dev/null; then break; fi
  sleep 0.2
done
if ! curl -sf "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}/health" >/dev/null; then
  log "port-forward never came up — see /tmp/drd-mock-pf.log"
  exit 1
fi

# Wipe queues + recordings between runs but keep tokens (so a long-running
# agent in the cluster wouldn't lose its credential — defensive).
curl -sf -X POST "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}/admin/reset?keep_tokens=true" >/dev/null

TOKEN=$(curl -sf -X POST "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}/admin/tokens" \
  -H 'content-type: application/json' -d '{"label":"kind-agent"}' \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
log "token: ${TOKEN:0:20}…"

# 5b. ensure credentials-secret exists ----------------------------------
# The helm chart mounts `credentials-secret` into the celery pods, but
# its manifest at helm/credentials-secret.yaml is NOT under templates/
# so `helm install` never creates it. Without this secret kubelet hangs
# the pods in PodInitializing forever (FailedMount).
#
# Build it from credentials/secrets.yaml on the host. Empty file is fine
# — the helm chart just needs the volume to exist. Idempotent.
log "ensuring credentials-secret exists in $NS"
SECRETS_FILE="$REPO_DIR/credentials/secrets.yaml"
if [[ ! -f "$SECRETS_FILE" ]]; then
  # Create an empty file rather than failing — most local test setups
  # don't need any real connector creds since NATIVE_KUBERNETES_API_MODE
  # is on.
  log "  no credentials/secrets.yaml found; creating empty placeholder"
  : > "$SECRETS_FILE"
fi
kubectl -n "$NS" create secret generic credentials-secret \
  --from-file=secrets.yaml="$SECRETS_FILE" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# 6. build (or reuse) the agent image + deploy via helm -----------------
# Self-contained — does not depend on the user's local deploy_local.sh
# (which is gitignored and per-machine). Logic:
#   a. compute image tag from git commit
#   b. decide skip-build (auto: skip when image already exists; --rebuild-agent forces)
#   c. docker build + kind load (when not skipping)
#   d. helm uninstall any prior release
#   e. write helm/values.local.yaml with token + host + image tag
#   f. helm upgrade --install
COMMIT_HASH=$(cd "$REPO_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "local-dev")
AGENT_IMAGE_NAME="drd-vpc-agent"
AGENT_IMAGE_TAG="local-${COMMIT_HASH}"
AGENT_FULL_IMAGE="${AGENT_IMAGE_NAME}:${AGENT_IMAGE_TAG}"

SKIP_AGENT_BUILD=0
case "$REUSE_AGENT_IMAGE" in
  always) SKIP_AGENT_BUILD=1 ;;
  auto)
    if docker image inspect "$AGENT_FULL_IMAGE" >/dev/null 2>&1; then
      log "auto-reuse: $AGENT_FULL_IMAGE already exists; skipping agent build"
      log "  (pass --rebuild-agent to force rebuild after agent code changes)"
      SKIP_AGENT_BUILD=1
    fi ;;
  never) SKIP_AGENT_BUILD=0 ;;
esac

cd "$REPO_DIR"

if [[ "$SKIP_AGENT_BUILD" -eq 0 ]]; then
  log "building agent image: $AGENT_FULL_IMAGE (this can take ~20min on first alpine build)"
  docker build \
    --build-arg COMMIT_HASH="$COMMIT_HASH" \
    -t "$AGENT_FULL_IMAGE" \
    -t "${AGENT_IMAGE_NAME}:local-latest" \
    "$REPO_DIR"
  log "kind load $AGENT_FULL_IMAGE"
  kind load docker-image "$AGENT_FULL_IMAGE" --name "${KIND_CLUSTER}" >/dev/null
else
  # Image exists locally; ensure it's also loaded into kind (idempotent NOP if already there).
  kind load docker-image "$AGENT_FULL_IMAGE" --name "${KIND_CLUSTER}" >/dev/null 2>&1 || true
fi

# Uninstall any previous helm release so we get a clean roll.
if helm status drd-vpc-agent -n "$NS" >/dev/null 2>&1; then
  log "uninstalling previous helm release"
  helm uninstall drd-vpc-agent -n "$NS" >/dev/null
fi

# Write a values override file pointing helm at the mock + the local image.
VALUES_LOCAL="$REPO_DIR/helm/values.local.yaml"
{
  echo "global:"
  echo "  DRD_CLOUD_API_TOKEN: \"$TOKEN\""
  echo "  DRD_CLOUD_API_HOST: \"$MOCK_SVC_HOST\""
  cat <<EOF

celery-beat:
  image:
    repository: $AGENT_IMAGE_NAME
    tag: $AGENT_IMAGE_TAG
    pullPolicy: Never

celery-worker:
  image:
    repository: $AGENT_IMAGE_NAME
    tag: $AGENT_IMAGE_TAG
    pullPolicy: Never
EOF
} > "$VALUES_LOCAL"

# The chart's configmap.yaml is at helm/ root (not under templates/), so
# helm install doesn't apply it. Same with credentials-secret (already
# handled above).
log "applying helm/configmap.yaml"
kubectl apply -f "$REPO_DIR/helm/configmap.yaml" -n "$NS" >/dev/null

log "helm upgrade --install drd-vpc-agent"
helm upgrade --install drd-vpc-agent "$REPO_DIR/helm" \
  -n "$NS" \
  -f "$REPO_DIR/helm/values.yaml" \
  -f "$VALUES_LOCAL"

# Give the agent a few seconds to call /connectors/proxy/ping etc.
sleep 5

# 7. seed scenarios ------------------------------------------------------
log "seeding scenarios from $SCENARIOS_FILE"
# Use the venv created by run_mock.sh / run_e2e.sh if it exists, otherwise
# fall back to system python — both will work, only httpx is needed.
if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  PY="$SCRIPT_DIR/.venv/bin/python"
else
  PY="python3"
  "$PY" -c 'import httpx' 2>/dev/null || pip install --quiet httpx
fi
"$PY" "$SCRIPT_DIR/seed_scenarios.py" \
  --host "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}" \
  --file "$SCENARIOS_FILE"

echo
echo "=============================================================="
echo "Mock backend  : $MOCK_SVC_HOST  (in-cluster)"
echo "Mock admin    : http://127.0.0.1:${PORT_FWD_LOCAL_PORT}  (port-forward, while this script lives)"
echo "Token         : $TOKEN"
echo "Agent pods    : kubectl -n ${NS} get pods"
echo "Agent logs    : kubectl -n ${NS} logs -l app=celery-worker -f"
echo "Mock logs     : kubectl -n ${NS} logs deploy/drd-vpc-agent-mock -f"
echo "Inspect calls : curl -s http://127.0.0.1:${PORT_FWD_LOCAL_PORT}/admin/recorded | jq"
echo "=============================================================="
echo

if [[ "$VALIDATE" -eq 1 ]]; then
  log "running e2e validator (timeout ${E2E_TIMEOUT}s)"
  set +e
  "$PY" "$SCRIPT_DIR/e2e.py" \
    --host "http://127.0.0.1:${PORT_FWD_LOCAL_PORT}" \
    --file "$SCENARIOS_FILE" \
    --timeout "$E2E_TIMEOUT"
  RC=$?
  set -e
  if [[ $RC -eq 0 ]]; then
    log "PASS"
  else
    log "FAIL — see logs above. Pods + mock are still running for inspection."
  fi
  exit $RC
else
  log "skipping validation (--no-validate). Port-forward holds while this script runs; Ctrl-C to release."
  wait "$PF_PID"
fi
