# mock_backend — local stand-in for DrDroid cloud

A FastAPI service that speaks the exact wire protocol the VPC agent
expects. The agent has no idea it's not the real backend.

## What it does

| Surface | Purpose |
|---|---|
| `GET  /connectors/proxy/ping` | startup reachability check (agent app `ready()`) |
| `POST /connectors/proxy/ping` | periodic heartbeat with pod health (every 50s) |
| `POST /connectors/proxy/register` | connector registration |
| `POST /connectors/proxy/connector/connection/tests` | poll for connection-test requests (every 10s) |
| `POST /connectors/proxy/connector/connection/results` | result upload |
| `POST /connectors/proxy/connector/metadata/register` | asset-metadata batches from extractors |
| `POST /playbooks-engine/proxy/execution/tasks` | poll for tasks (every 1s) — incl. `ASSET_REFRESH` |
| `POST /playbooks-engine/proxy/execution/results` | task / asset_refresh result upload |

Auth is `Authorization: Bearer <token>`. Tokens are issued by the mock
itself — the agent only knows it via `DRD_CLOUD_API_TOKEN`.

Every inbound request (body + headers + query + the response we sent) is
recorded as a JSONL event under `data/recorded/<bucket>.jsonl`.

## Layout

```
mock_backend/
├── app.py                # FastAPI app: proxy + admin + catch-all
├── storage.py            # JSON persistence (tokens, recordings, queues)
├── seed_scenarios.py     # push a scenarios file into the admin API
├── e2e.py                # poll recordings + assert agent behaviour
├── scenarios/default.json  # default seeded scenarios
├── run_mock.sh           # foreground: mock + token
├── run_agent.sh          # foreground: celery beat/workers pointed at the mock
├── run_e2e.sh            # one-shot loop: mock → agent → seed → validate
└── data/                 # gitignored — recordings, queues, logs
```

## Three ways to run it

### 1. Test the actual Docker image in Kind (recommended for image migrations)

This is what you want when validating things like the Debian → Alpine
base swap. The agent runs from its real image inside Kind; the mock
runs as a sibling pod in the same `drdroid` namespace.

```bash
# from repo root
./mock_backend/deploy_kind.sh
```

**Build-time note:** the alpine agent image takes ~20 min to build on
first run because several deps (psycopg2-binary, pymongo, sqlalchemy,
cryptography, lxml) have no musllinux wheels and compile from source.
By default `deploy_kind.sh` **auto-reuses** an existing
`drd-vpc-agent:local-<commit>` image — subsequent iterations are ~30s.

| When | Flag |
|---|---|
| Agent code changed → must rebuild | `--rebuild-agent` (or `--rebuild`) |
| Only mock/scenarios changed → reuse agent | (default) |
| Force-skip everything (fastest) | `--reuse-image` |
| Mock backend code changed | (auto-detected — mock rebuilds when src is newer than image) |

What it does:
1. ensures the `drd-local` Kind cluster + `drdroid` namespace
2. builds `mock_backend/Dockerfile` → `drd-vpc-agent-mock:local-latest`
3. `kind load`s it and applies `mock_backend/k8s/manifests.yaml`
4. waits for readiness, opens a `kubectl port-forward` on `:18080`
5. mints a token via `POST /admin/tokens`
6. shells out to `./deploy_local.sh <token>` with
   `DRD_CLOUD_API_HOST=http://drd-vpc-agent-mock.drdroid.svc.cluster.local:8080`
   so the agent pods talk to the mock over cluster DNS
7. seeds `scenarios/default.json`
8. runs `e2e.py` and reports PASS/FAIL

You don't bring a token — the mock issues one. Reset everything between
runs with `./mock_backend/deploy_kind.sh --reset-only`.

### 2. Skip Kind, run agent directly via celery (fast feedback on code)

```bash
# Prereq: redis on :6379, repo Python deps importable
./mock_backend/run_e2e.sh
```

Exit 0 = PASS, 1 = FAIL. Logs in `mock_backend/data/`.

### 3. Manual three-terminal loop

```bash
# terminal 1 — mock
./mock_backend/run_mock.sh
# (note the printed DRD_CLOUD_API_TOKEN / DRD_CLOUD_API_HOST)

# terminal 2 — agent
DRD_CLOUD_API_TOKEN=... DRD_CLOUD_API_HOST=http://127.0.0.1:8080 \
  ./mock_backend/run_agent.sh

# terminal 3 — push scenarios + validate
.venv/bin/python mock_backend/seed_scenarios.py --reset
.venv/bin/python mock_backend/e2e.py
```

## Admin API (test control)

| Method | Path | Purpose |
|---|---|---|
| `POST`   | `/admin/tokens`                       | mint a token (returns `{token, label}`) |
| `GET`    | `/admin/tokens`                       | list tokens |
| `DELETE` | `/admin/tokens/{token}`               | revoke a token |
| `POST`   | `/admin/queues/connection-tests`      | enqueue a connection test (or `{items:[…]}` batch) |
| `POST`   | `/admin/queues/playbook-tasks`        | enqueue a playbook task / `ASSET_REFRESH` |
| `GET`    | `/admin/queues/{name}`                | peek pending |
| `DELETE` | `/admin/queues/{name}`                | clear queue |
| `GET`    | `/admin/recorded`                     | list recording buckets |
| `GET`    | `/admin/recorded/{bucket}`            | list events in a bucket |
| `POST`   | `/admin/reset?keep_tokens=true`       | wipe queues + recordings |

Recording buckets emitted by the proxy endpoints:
`ping_get`, `ping_post`, `register_connectors`, `connection_tests_poll`,
`connection_tests_results`, `metadata_register`, `playbook_tasks_poll`,
`playbook_tasks_results`, `unmatched`.

## Scenarios

Edit `scenarios/default.json`. Two arrays:

- `connection_tests`: each item is `{connector_name, request_id?}`. The
  agent looks up `connector_name` in `credentials/secrets.yaml`, runs a
  real connection test, and posts the result back.
- `playbook_tasks`: each item is a `playbook_task_execution` dict. Two
  task shapes are exercised by default:

  **Real kubectl tasks** (canonical proto3 JSON — `dict_to_proto` parses
  this directly into `PlaybookTask`):
  ```json
  {
    "task": {
      "source": "KUBERNETES",
      "kubernetes": {
        "type": "COMMAND",
        "command": {"command": "kubectl get pods -n drdroid -o json"}
      }
    }
  }
  ```
  These run inside the agent pod via `KubectlApiProcessor` — no
  connector configured in `secrets.yaml` is needed because the helm
  chart sets `NATIVE_KUBERNETES_API_MODE=true` and `kubectl` is in the
  agent's image. The agent's own RBAC (`drdroid-k8s-cluster-role`)
  permits pods/services/events/namespaces.

  **`ASSET_REFRESH`** (intercepted before proto parsing — wrapper-form
  `{"value": …}` here is intentional):
  ```json
  {
    "task": {
      "drd_proxy_agent": {
        "type": "ASSET_REFRESH",
        "asset_refresh": {
          "connector_name": {"value": "native_k8s"},
          "connector_type": {"value": 47},
          "extractor_method": {"value": "extract_pods"}
        }
      }
    }
  }
  ```
  `connector_type` is the protobuf `Source` enum int (KUBERNETES = 47).
  Drop `extractor_method` to run every `extract_*` method.

Underscore-prefixed keys (`_doc`, `$schema_note`) are ignored — handy for
inline documentation.

### What `e2e.py` checks for kubectl tasks

For each kubectl scenario it pulls the agent's reported output from the
recordings and asserts:

1. The command's `output` is parseable JSON.
2. A stable, deployment-managed item is present (e.g. the mock-backend
   pod must show up in `get pods -n drdroid`; the `drdroid` namespace
   in `get namespaces`).
3. **Ground-truth match** — if `kubectl` is on the host PATH and points
   at the same Kind cluster, the validator runs the same command on the
   host and asserts the *set of names* matches what the agent reported.
   Events are checked for "non-empty on both sides" only (events churn).

## Notes

- The mock holds queues in flat JSON files (`data/queues/*.json`); each
  poll drains the file. Restart-safe.
- `data/` is gitignored. Tokens live there too — they don't survive a
  hard reset (`POST /admin/reset?keep_tokens=false`).
- `scripts/start-celery-worker.sh` reads `CELERY_QUEUE`; we run a beat
  + a `celery` worker + an `exec` worker. The asset_extraction queue is
  only enabled when `NATIVE_KUBERNETES_API_MODE=true`.
