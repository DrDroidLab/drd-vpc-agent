"""FastAPI mock of the DrDroid cloud backend.

Speaks the exact wire protocol the VPC agent expects — the agent has no
idea this isn't the real backend. Three concerns are layered on the same
FastAPI app:

1. /connectors/proxy/* and /playbooks-engine/proxy/* — the real-shaped
   endpoints. Auth via `Authorization: Bearer <token>`. Every payload is
   recorded.
2. /admin/* — test-control surface: issue tokens, enqueue scenarios
   (connection tests, playbook tasks, asset_refresh), inspect / reset
   recordings.
3. /health — orchestration probe.

Run: `uvicorn app:app --host 0.0.0.0 --port 8080` (see run_mock.sh).
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

import storage

app = FastAPI(title="DrDroid VPC-Agent Mock Backend", version="0.1.0")


# --- Auth ----------------------------------------------------------------

def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def require_token(authorization: str | None = Header(default=None)) -> str:
    token = _bearer(authorization)
    if not token or not storage.is_valid_token(token):
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")
    return token


async def _capture(request: Request) -> dict:
    """Pull body + headers + query into a serializable dict for recording."""
    try:
        body = await request.json()
    except Exception:
        try:
            body = (await request.body()).decode("utf-8", errors="replace")
        except Exception:
            body = None
    return {
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": {k: v for k, v in request.headers.items() if k.lower() != "authorization"},
        "body": body,
    }


# --- Health --------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    tokens = storage.list_tokens()
    return {
        "status": "ok",
        "tokens_issued": len(tokens),
        "pending": {
            "connection_tests": len(storage.queue_peek("connection_tests")),
            "playbook_tasks": len(storage.queue_peek("playbook_tasks")),
        },
        "recorded_buckets": storage.list_buckets(),
    }


# --- Agent: startup + heartbeat -----------------------------------------

@app.get("/connectors/proxy/ping")
async def ping_get(
    request: Request,
    commit_hash: str = Query(default=""),
    token: str = Depends(require_token),
):
    captured = await _capture(request)
    storage.record("ping_get", {"token_suffix": token[-4:], **captured})
    return {"status": "ok", "commit_hash": commit_hash}


@app.post("/connectors/proxy/ping")
async def ping_post(request: Request, token: str = Depends(require_token)):
    captured = await _capture(request)
    storage.record("ping_post", {"token_suffix": token[-4:], **captured})
    return {"status": "ok"}


# --- Agent: connector registration --------------------------------------

@app.post("/connectors/proxy/register")
async def register_connectors(
    request: Request,
    commit_hash: str = Query(default=""),
    token: str = Depends(require_token),
):
    captured = await _capture(request)
    storage.record(
        "register_connectors",
        {"token_suffix": token[-4:], "commit_hash": commit_hash, **captured},
    )
    return {"status": "ok"}


# --- Agent: connection-test poll/result ---------------------------------

@app.post("/connectors/proxy/connector/connection/tests")
async def connection_tests_poll(request: Request, token: str = Depends(require_token)):
    pending = storage.queue_take_all("connection_tests")
    response_body = {"requests": pending}
    captured = await _capture(request)
    storage.record(
        "connection_tests_poll",
        {"token_suffix": token[-4:], "delivered": pending, **captured},
    )
    return response_body


@app.post("/connectors/proxy/connector/connection/results")
async def connection_tests_result(request: Request, token: str = Depends(require_token)):
    captured = await _capture(request)
    storage.record(
        "connection_tests_results",
        {"token_suffix": token[-4:], **captured},
    )
    return {"status": "ok"}


# --- Agent: asset metadata batches --------------------------------------

@app.post("/connectors/proxy/connector/metadata/register")
async def metadata_register(request: Request, token: str = Depends(require_token)):
    captured = await _capture(request)
    body = captured.get("body") if isinstance(captured.get("body"), dict) else {}
    storage.record(
        "metadata_register",
        {
            "token_suffix": token[-4:],
            "connector": body.get("connector"),
            "model_type": body.get("model_type"),
            "refresh_id": body.get("refresh_id"),
            "has_more": body.get("has_more"),
            "asset_count": len(body.get("assets", []) or []),
            **captured,
        },
    )
    return {"status": "ok"}


# --- Agent: playbook task poll/result -----------------------------------

@app.post("/playbooks-engine/proxy/execution/tasks")
async def playbook_tasks_poll(request: Request, token: str = Depends(require_token)):
    pending = storage.queue_take_all("playbook_tasks")
    response_body = {"playbook_task_executions": pending}
    captured = await _capture(request)
    storage.record(
        "playbook_tasks_poll",
        {"token_suffix": token[-4:], "delivered": pending, **captured},
    )
    return response_body


@app.post("/playbooks-engine/proxy/execution/results")
async def playbook_tasks_result(request: Request, token: str = Depends(require_token)):
    captured = await _capture(request)
    body = captured.get("body") if isinstance(captured.get("body"), dict) else {}
    logs = body.get("playbook_task_execution_logs", []) or []
    summarised_logs = []
    for log in logs:
        result = log.get("result") or {}
        summarised_logs.append(
            {
                "request_id": log.get("proxy_execution_request_id"),
                "has_error": "error" in result,
                "error": (result.get("error") or {}).get("value") if isinstance(result.get("error"), dict) else result.get("error"),
                "result_keys": list(result.keys()),
            }
        )
    storage.record(
        "playbook_tasks_results",
        {
            "token_suffix": token[-4:],
            "log_count": len(logs),
            "summary": summarised_logs,
            **captured,
        },
    )
    return {"status": "ok"}


# --- Admin (test-control) -----------------------------------------------

@app.post("/admin/tokens")
def admin_issue_token(payload: dict | None = None) -> dict:
    label = (payload or {}).get("label")
    token = storage.issue_token(label)
    return {"token": token, "label": label or "agent"}


@app.get("/admin/tokens")
def admin_list_tokens() -> dict:
    return {"tokens": storage.list_tokens()}


@app.delete("/admin/tokens/{token}")
def admin_revoke_token(token: str) -> dict:
    return {"revoked": storage.revoke_token(token)}


@app.post("/admin/queues/connection-tests")
def admin_enqueue_connection_test(payload: dict) -> dict:
    """Body: {"connector_name": "...", "request_id": "optional-uuid"}.

    Or {"items": [{...}, ...]} for batch.
    """
    items = payload.get("items")
    if items is None:
        items = [payload]
    normalised = []
    import uuid as _uuid
    for it in items:
        if "connector_name" not in it:
            raise HTTPException(400, "connector_name required")
        normalised.append({
            "request_id": it.get("request_id") or str(_uuid.uuid4()),
            "connector_name": it["connector_name"],
        })
    storage.queue_extend("connection_tests", normalised)
    return {"enqueued": normalised}


@app.post("/admin/queues/playbook-tasks")
def admin_enqueue_playbook_task(payload: dict) -> dict:
    """Body: a single playbook_task_execution dict, or {"items": [...]}.

    Asset-refresh shape:
      {
        "task": {
          "drd_proxy_agent": {
            "type": "ASSET_REFRESH",
            "asset_refresh": {
              "connector_name": {"value": "my_k8s"},
              "connector_type": {"value": 47},
              "extractor_method": {"value": "extract_pods"}
            }
          }
        }
      }
    """
    items = payload.get("items")
    if items is None:
        items = [payload]
    import time as _time, uuid as _uuid
    normalised = []
    for it in items:
        normalised.append({
            "proxy_execution_request_id": it.get("proxy_execution_request_id") or str(_uuid.uuid4()),
            "task": it.get("task", {}),
            "time_range": it.get("time_range") or {
                "time_geq": int(_time.time()) - 300,
                "time_lt": int(_time.time()),
            },
            "execution_global_variable_set": it.get("execution_global_variable_set", {}),
        })
    storage.queue_extend("playbook_tasks", normalised)
    return {"enqueued": normalised}


@app.get("/admin/queues/{name}")
def admin_queue_peek(name: str) -> dict:
    return {"name": name, "items": storage.queue_peek(name)}


@app.delete("/admin/queues/{name}")
def admin_queue_clear(name: str) -> dict:
    storage.queue_clear(name)
    return {"cleared": name}


@app.get("/admin/recorded")
def admin_recorded_buckets() -> dict:
    return {"buckets": storage.list_buckets()}


@app.get("/admin/recorded/{bucket}")
def admin_recorded(bucket: str) -> JSONResponse:
    return JSONResponse({"bucket": bucket, "events": storage.read_records(bucket)})


@app.post("/admin/reset")
def admin_reset(keep_tokens: bool = Query(default=True)) -> dict:
    storage.reset_all(keep_tokens=keep_tokens)
    return {"reset": True, "tokens_kept": keep_tokens}


# --- Catch-all to surface unexpected agent calls ------------------------

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def catchall(full_path: str, request: Request) -> JSONResponse:
    captured = await _capture(request)
    storage.record("unmatched", {"path": "/" + full_path, **captured})
    return JSONResponse({"error": "unmatched path", "path": "/" + full_path}, status_code=404)
