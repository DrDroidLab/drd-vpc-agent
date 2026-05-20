---
description: Run the VPC-agent end-to-end test loop against the local FastAPI mock backend (Kind or direct-celery)
argument-hint: "[--kind | --code] [--scenarios path/to/file.json] [--timeout 180] [--manual]"
---

# Run the VPC-agent end-to-end test loop

You are running the test suite for the local VPC agent against the FastAPI mock backend at `mock_backend/`. The mock simulates DrDroid cloud — it issues a bearer token, records every inbound request as JSONL, and lets you seed connection-test + playbook-task scenarios.

User args (may be empty): `$ARGUMENTS`

## Step 0: pick the path

Two paths exist. Choose based on what the user is changing:

- **`--kind` (default when uncertain on a branch that touches Dockerfile, base image, requirements.txt, helm/, or deploy_local.sh):** runs the *real* agent Docker image inside Kind alongside a sibling mock pod. Use this for image migrations (e.g. Debian→Alpine), helm changes, dep upgrades that affect runtime.
- **`--code` (default for pure Python changes — connector logic, playbook tasks, business code):** runs celery directly on the host against a host-bound mock. Faster (~30s vs minutes for image build).

If the user passed `--manual`, skip both and print the three-terminal manual flow from `mock_backend/README.md`. Stop.

If neither flag is set, infer: `git diff main --name-only | grep -E '^(Dockerfile|requirements\.txt|helm/|deploy_local\.sh|mock_backend/Dockerfile)'` — any hit ⇒ default `--kind`, else default `--code`.

## Step 1: preflight

Path-specific. Run the relevant checks in parallel.

**For `--kind`:**
- `kind get clusters` — check the binary works; cluster will be created if missing.
- `kubectl version --client` — fail fast if missing.
- `docker info` — Docker Desktop must be running.
- `cat credentials/secrets.yaml | head -5` from the repo root — should be non-empty. Empty file means scenarios that reference real connectors will fail with "Connector not found". Warn but proceed.

**For `--code`:**
- `redis-cli ping` — must return `PONG`. If not, suggest `docker run -d --rm --name drd-redis -p 6379:6379 redis:alpine` and ask before running.
- `cat credentials/secrets.yaml | head -5` (same as above).
- `lsof -i :8080` — must be free. If taken, pass `MOCK_BACKEND_PORT=<free>` through.
- `python -c 'import django, celery'` from the repo root — agent Python deps importable. If not, ask the user about `pip install -r requirements.txt`.

## Step 2: run the loop

### `--kind`

```bash
cd /Users/dipeshmittal/drdroid/drd-vpc-agent
./mock_backend/deploy_kind.sh
```

Pass `--scenarios <path>` and `--timeout <n>` through. The script:
1. ensures Kind cluster `drd-local` + `drdroid` namespace
2. builds `mock_backend/Dockerfile` and `kind load`s it
3. applies `mock_backend/k8s/manifests.yaml` (Deployment + Service)
4. waits for readiness, port-forwards `:18080`
5. mints a token via `/admin/tokens`
6. shells out to `./deploy_local.sh <token>` with `DRD_CLOUD_API_HOST=http://drd-vpc-agent-mock.drdroid.svc.cluster.local:8080` so agent pods talk to the mock over cluster DNS
7. seeds scenarios + runs `e2e.py`

The user does NOT bring a token — the mock issues it. `--reset-only` tears down the agent helm release and mock manifest.

### `--code`

```bash
cd /Users/dipeshmittal/drdroid/drd-vpc-agent
./mock_backend/run_e2e.sh
```

Same shape (start mock → mint token → boot agent → seed → validate) but agent runs as celery host processes. Pass `SCENARIOS_FILE=<path>` and `E2E_TIMEOUT=<n>` through.

Both scripts stream to stderr. Let them run; don't wrap in another background subprocess.

## Step 3: report

On PASS: one or two lines.

On FAIL: open the relevant logs.

**For `--kind`:**
- `kubectl -n drdroid get pods` — check pod state.
- `kubectl -n drdroid logs deploy/drd-vpc-agent-mock --tail 100`
- `kubectl -n drdroid logs -l app=celery-worker --tail 100`
- `kubectl -n drdroid logs -l app=celery-beat --tail 100`
- `kubectl -n drdroid describe pod <crashed-pod>` if any pod is in CrashLoopBackOff.
- While `deploy_kind.sh` is running, the mock admin API is up at `:18080` — `curl -s http://127.0.0.1:18080/admin/recorded` for buckets, `curl -s http://127.0.0.1:18080/admin/recorded/<bucket>` for events.

**For `--code`:**
- `mock_backend/data/mock-backend.log`
- `mock_backend/data/agent-logs/{beat,worker,worker-exec}.log`
- `mock_backend/data/recorded/*.jsonl` — the actual wire traffic.

Common failure modes:
- Agent pod CrashLoopBackOff right after `deploy_local.sh`: usually `secrets.yaml` is empty/malformed, or the alpine image is missing a binary the agent runtime needs (this is exactly what we're testing for on `experiment/alpine-base` — surface the traceback; don't try to fix it).
- "agent did not poll X": worker isn't draining. Check broker connectivity (redis pod for kind; host redis for code path); check worker log for traceback.
- "playbook_tasks executed without errors: FAIL" with `Connector not found`: scenario's `connector_name` isn't in `credentials/secrets.yaml`. Tell the user; don't edit secrets yourself.
- 401 in mock log: token env didn't reach the agent. For kind, check `kubectl -n drdroid get secret drd-cloud-secret -o yaml | base64 -D` (token field). For code, check the env exported by `run_e2e.sh`.

Don't speculate beyond the logs. If genuinely ambiguous after reading them, ask the user.

## Notes

- The test harness lives at `mock_backend/`. Code is checked in; `mock_backend/data/` is gitignored.
- This skill exists because the agent talks to `DRD_CLOUD_API_HOST` for ping/registration/connection tests/asset metadata/playbook tasks, and exercising those without mocking means hitting production.
- If the user wants to add new scenarios, point them at `mock_backend/scenarios/default.json` (commented inline) or `mock_backend/README.md`.
