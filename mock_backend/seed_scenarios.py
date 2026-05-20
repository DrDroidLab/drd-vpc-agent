"""Push a scenarios JSON file into a running mock via its admin API."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
SECRETS_PATH = REPO_ROOT / "credentials" / "secrets.yaml"


def loaded_connector_names() -> set[str]:
    """Return the set of connector names defined in credentials/secrets.yaml.

    The agent's connection-test executor silently drops requests for
    connectors not in this set (no result posted), so seeding such tests
    leaves the mock waiting forever. Filter at seed time.
    """
    if not SECRETS_PATH.exists():
        return set()
    try:
        import yaml  # type: ignore
    except ImportError:
        return set()
    try:
        data = yaml.safe_load(SECRETS_PATH.read_text()) or {}
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict):
        return set()
    return set(data.keys())


def seed(host: str, scenarios_path: Path, reset: bool = False) -> None:
    data = json.loads(scenarios_path.read_text())
    with httpx.Client(base_url=host, timeout=10.0) as client:
        if reset:
            r = client.post("/admin/reset", params={"keep_tokens": "true"})
            r.raise_for_status()
            print(f"reset: {r.json()}")

        ct = [c for c in data.get("connection_tests", []) if not str(next(iter(c), "")).startswith("$")]
        ct = [c for c in ct if not all(k.startswith("_") or k.startswith("$") for k in c)]
        # Drop connection-tests for connectors that don't exist in
        # credentials/secrets.yaml — the agent will silently no-op them.
        configured = loaded_connector_names()
        skipped = [c for c in ct if c.get("connector_name") not in configured]
        ct = [c for c in ct if c.get("connector_name") in configured]
        if skipped:
            names = ", ".join(c.get("connector_name", "?") for c in skipped)
            print(f"connection_tests skipped (no matching connector in secrets.yaml): {names}")
        if ct:
            r = client.post("/admin/queues/connection-tests", json={"items": ct})
            r.raise_for_status()
            print(f"connection_tests enqueued: {len(r.json().get('enqueued', []))}")

        pt = data.get("playbook_tasks", []) or []
        pt = [p for p in pt if any(not k.startswith("_") and not k.startswith("$") for k in p)]
        if pt:
            r = client.post("/admin/queues/playbook-tasks", json={"items": pt})
            r.raise_for_status()
            print(f"playbook_tasks enqueued: {len(r.json().get('enqueued', []))}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8080")
    ap.add_argument("--file", default=str(Path(__file__).parent / "scenarios/default.json"))
    ap.add_argument("--reset", action="store_true", help="clear queues + recordings before seeding")
    args = ap.parse_args()

    seed(args.host, Path(args.file), reset=args.reset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
