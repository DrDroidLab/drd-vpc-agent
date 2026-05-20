"""Persistence + queues for the mock backend.

Every inbound payload from the agent is appended to a JSONL file under
data/recorded/<bucket>.jsonl so tests can replay and assert on the wire
traffic. Pending work (connection tests, playbook tasks) is held in JSON
files under data/queues/ that the admin API mutates and the polling
endpoints drain.
"""
from __future__ import annotations

import json
import secrets
import threading
import time
import uuid
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).parent / "data"
RECORDED_DIR = DATA_DIR / "recorded"
QUEUES_DIR = DATA_DIR / "queues"
TOKENS_FILE = DATA_DIR / "tokens.json"

_lock = threading.Lock()


def _ensure_dirs() -> None:
    RECORDED_DIR.mkdir(parents=True, exist_ok=True)
    QUEUES_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def _dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, default=str))


# --- Token store ---------------------------------------------------------

def issue_token(label: str | None = None) -> str:
    """Mint a fresh bearer token. Returned plaintext is the only auth secret
    the agent needs."""
    with _lock:
        _ensure_dirs()
        tokens = _load_json(TOKENS_FILE, {})
        token = "mock-" + secrets.token_urlsafe(24)
        tokens[token] = {
            "label": label or "agent",
            "issued_at": time.time(),
        }
        _dump_json(TOKENS_FILE, tokens)
        return token


def list_tokens() -> dict[str, dict]:
    with _lock:
        return _load_json(TOKENS_FILE, {})


def revoke_token(token: str) -> bool:
    with _lock:
        tokens = _load_json(TOKENS_FILE, {})
        if token in tokens:
            del tokens[token]
            _dump_json(TOKENS_FILE, tokens)
            return True
        return False


def is_valid_token(token: str) -> bool:
    return token in list_tokens()


# --- Inbound recording ---------------------------------------------------

def record(bucket: str, payload: dict) -> dict:
    """Append a single event to data/recorded/<bucket>.jsonl.

    `payload` should already include the request body, headers, query
    params, and the response we returned — anything a test may want to
    assert on later.
    """
    with _lock:
        _ensure_dirs()
        event = {
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "bucket": bucket,
            **payload,
        }
        path = RECORDED_DIR / f"{bucket}.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        return event


def read_records(bucket: str) -> list[dict]:
    path = RECORDED_DIR / f"{bucket}.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def list_buckets() -> list[str]:
    if not RECORDED_DIR.exists():
        return []
    return sorted(p.stem for p in RECORDED_DIR.glob("*.jsonl"))


def clear_records() -> None:
    with _lock:
        if RECORDED_DIR.exists():
            for f in RECORDED_DIR.glob("*.jsonl"):
                f.unlink()


# --- Pending-work queues -------------------------------------------------
# Two named queues:
#   - "connection_tests": items shaped {request_id, connector_name}
#   - "playbook_tasks":  items shaped {proxy_execution_request_id, task, time_range, ...}
# `take_all` drains and returns every queued item — the agent's polling
# tasks consume the whole batch each tick.

def _queue_path(name: str) -> Path:
    _ensure_dirs()
    return QUEUES_DIR / f"{name}.json"


def queue_push(name: str, item: dict) -> dict:
    with _lock:
        path = _queue_path(name)
        items = _load_json(path, [])
        items.append(item)
        _dump_json(path, items)
        return item


def queue_extend(name: str, items: list[dict]) -> int:
    with _lock:
        path = _queue_path(name)
        existing = _load_json(path, [])
        existing.extend(items)
        _dump_json(path, existing)
        return len(items)


def queue_take_all(name: str) -> list[dict]:
    with _lock:
        path = _queue_path(name)
        items = _load_json(path, [])
        if items:
            _dump_json(path, [])
        return items


def queue_peek(name: str) -> list[dict]:
    return _load_json(_queue_path(name), [])


def queue_clear(name: str | None = None) -> None:
    with _lock:
        if name:
            p = _queue_path(name)
            if p.exists():
                p.unlink()
            return
        if QUEUES_DIR.exists():
            for f in QUEUES_DIR.glob("*.json"):
                f.unlink()


def reset_all(keep_tokens: bool = True) -> None:
    """Wipe recordings and queues. Keep tokens by default so an in-flight
    agent doesn't lose its credential mid-test."""
    clear_records()
    queue_clear()
    if not keep_tokens and TOKENS_FILE.exists():
        TOKENS_FILE.unlink()
