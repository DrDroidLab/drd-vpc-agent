"""Lightweight end-to-end validator.

Assumes the mock is running and an agent has been pointed at it. After
seeding scenarios this script polls the recordings and asserts the agent
exhibited the expected behaviours: startup ping, periodic heartbeat, drained
the queues, and reported back results for everything we enqueued.

Designed to be run after `run_e2e.sh` brings everything up. Returns
non-zero exit on failure with a human-readable diff.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        marker = "PASS" if self.ok else "FAIL"
        return f"  [{marker}] {self.name}" + (f" — {self.detail}" if self.detail else "")


@dataclass
class Report:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, ok, detail))

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def render(self) -> str:
        lines = [c.render() for c in self.checks]
        lines.append("")
        lines.append(f"  TOTAL: {sum(1 for c in self.checks if c.ok)}/{len(self.checks)} passed")
        return "\n".join(lines)


def _get(client: httpx.Client, path: str) -> dict:
    r = client.get(path)
    r.raise_for_status()
    return r.json()


def _events(client: httpx.Client, bucket: str) -> list[dict]:
    return _get(client, f"/admin/recorded/{bucket}").get("events", [])


def wait_for(client: httpx.Client, bucket: str, predicate, timeout: float, label: str) -> tuple[bool, list[dict]]:
    deadline = time.time() + timeout
    last: list[dict] = []
    while time.time() < deadline:
        last = _events(client, bucket)
        if predicate(last):
            return True, last
        time.sleep(1.0)
    return False, last


def _kubectl_command_from_scenario(scenario: dict) -> str | None:
    """Return the kubectl command string from a scenario, or None if it's not a Kubectl COMMAND task."""
    task = scenario.get("task") or {}
    if task.get("source") != "KUBERNETES":
        return None
    k = task.get("kubernetes") or {}
    if k.get("type") != "COMMAND":
        return None
    cmd = (k.get("command") or {}).get("command")
    return cmd if isinstance(cmd, str) else None


def _find_kubectl_output(results_events: list[dict], command: str) -> str | None:
    """Walk recorded playbook_tasks_results events and return the agent's
    output string for the given command (None if not found)."""
    for ev in results_events:
        body = ev.get("body") or {}
        for log in body.get("playbook_task_execution_logs", []) or []:
            result = log.get("result") or {}
            bash = result.get("bash_command_output") or {}
            for co in bash.get("command_outputs", []) or []:
                # MessageToDict gives bare strings for StringValue; older
                # encodings might give {"value": "..."} — handle both.
                cmd_field = co.get("command")
                if isinstance(cmd_field, dict):
                    cmd_field = cmd_field.get("value")
                if cmd_field == command or (cmd_field or "").strip() == command.strip():
                    out = co.get("output")
                    if isinstance(out, dict):
                        out = out.get("value")
                    return out
    return None


def _host_kubectl(args: list[str]) -> tuple[bool, str]:
    """Run kubectl on the host. Returns (ok, stdout-or-error)."""
    if not shutil.which("kubectl"):
        return False, "host kubectl not in PATH"
    try:
        proc = subprocess.run(["kubectl", *args], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return False, "host kubectl timed out"
    if proc.returncode != 0:
        return False, f"exit {proc.returncode}: {proc.stderr.strip()[:200]}"
    return True, proc.stdout


def _names_from_list(blob: str) -> set[str]:
    """Pull `metadata.name` out of a `kubectl get ... -o json` listing."""
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return set()
    return {(it.get("metadata") or {}).get("name") for it in data.get("items", []) if (it.get("metadata") or {}).get("name")}


def _check_kubectl_scenarios(client: httpx.Client, expected_pt: list[dict], report: Report, timeout: float) -> None:
    """For each kubectl scenario: assert agent reported a parseable JSON
    output, the expected stable item is present, and the set of names
    matches the host's `kubectl` snapshot when available."""
    kubectl_scenarios = [(s, _kubectl_command_from_scenario(s)) for s in expected_pt]
    kubectl_scenarios = [(s, c) for s, c in kubectl_scenarios if c]
    if not kubectl_scenarios:
        return

    # Wait for results to be in. The earlier "results posted back" check
    # already gated on this, but we re-pull fresh recordings here.
    deadline = time.time() + min(timeout, 60)
    results: list[dict] = []
    while time.time() < deadline:
        results = _events(client, "playbook_tasks_results")
        if any(_find_kubectl_output(results, c) is not None for _, c in kubectl_scenarios):
            break
        time.sleep(1.0)

    host_kubectl_available = shutil.which("kubectl") is not None
    if not host_kubectl_available:
        report.add(
            "host kubectl available for ground-truth comparison",
            False,
            "kubectl not in PATH — agent outputs will be self-checked only",
        )

    for scenario, command in kubectl_scenarios:
        output = _find_kubectl_output(results, command)
        if output is None:
            report.add(f"agent reported output for: {command}", False, "no matching command_output in recordings")
            continue

        # Parseability — every command in our default set asks for `-o json`.
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as e:
            report.add(f"agent output is valid JSON: {command}", False, f"json error: {e}")
            continue
        report.add(f"agent output is valid JSON: {command}", True)

        # Self-checks (deployment-stable invariants we set up ourselves).
        if "get pods -n drdroid" in command:
            agent_names = {(it.get("metadata") or {}).get("name") for it in parsed.get("items", [])}
            agent_names = {n for n in agent_names if n}
            mock_pod = any(n.startswith("drd-vpc-agent-mock") for n in agent_names)
            report.add("mock backend pod visible in agent's `get pods -n drdroid`", mock_pod,
                       f"saw {len(agent_names)} pods: {sorted(agent_names)[:5]}…")
            celery_pod = any(n.startswith("drd-vpc-agent-celery") or "celery" in n for n in agent_names)
            report.add("agent celery pod visible in `get pods -n drdroid`", celery_pod,
                       f"pod set: {sorted(agent_names)}")
        elif "get svc -n drdroid" in command:
            agent_names = {(it.get("metadata") or {}).get("name") for it in parsed.get("items", [])}
            agent_names = {n for n in agent_names if n}
            report.add("mock backend service visible in agent's `get svc -n drdroid`",
                       "drd-vpc-agent-mock" in agent_names,
                       f"saw services: {sorted(agent_names)}")
        elif "get namespaces" in command:
            agent_names = {(it.get("metadata") or {}).get("name") for it in parsed.get("items", [])}
            agent_names = {n for n in agent_names if n}
            report.add("`drdroid` namespace visible in agent's `get namespaces`",
                       "drdroid" in agent_names,
                       f"saw namespaces: {sorted(agent_names)}")
        elif "get events -n drdroid" in command:
            event_count = len(parsed.get("items", []))
            report.add("agent's `get events -n drdroid` returned events",
                       event_count > 0,
                       f"saw {event_count} events")

        # Host-side ground truth (skipped if host has no kubectl context for this cluster).
        if not host_kubectl_available:
            continue

        agent_set = _names_from_list(output)
        host_args: list[str] | None = None
        if "get pods -n drdroid" in command:
            host_args = ["get", "pods", "-n", "drdroid", "-o", "json"]
        elif "get svc -n drdroid" in command:
            host_args = ["get", "svc", "-n", "drdroid", "-o", "json"]
        elif "get namespaces" in command:
            host_args = ["get", "namespaces", "-o", "json"]
        elif "get events -n drdroid" in command:
            host_args = ["get", "events", "-n", "drdroid", "-o", "json"]
        if host_args is None:
            continue

        ok, host_blob = _host_kubectl(host_args)
        if not ok:
            report.add(f"host ground-truth: {' '.join(host_args)}", False, host_blob)
            continue
        host_set = _names_from_list(host_blob)

        # Quiet clusters should agree on names. Allow tiny drift for events
        # (the only churn-y resource) — for that one, just ensure both sides
        # are non-empty.
        if "events" in host_args:
            ok = bool(agent_set or len(json.loads(output).get("items", []))) and bool(host_set or len(json.loads(host_blob).get("items", [])))
            report.add(f"host vs agent both report events for `{' '.join(host_args)}`", ok)
        else:
            missing_in_agent = host_set - agent_set
            extra_in_agent = agent_set - host_set
            ok = not missing_in_agent and not extra_in_agent
            detail = f"agent={sorted(agent_set)} host={sorted(host_set)}"
            if not ok:
                detail = f"missing_in_agent={sorted(missing_in_agent)} extra_in_agent={sorted(extra_in_agent)} | {detail}"
            report.add(f"host kubectl set matches agent's: `{' '.join(host_args)}`", ok, detail)


def _configured_connector_names() -> set[str]:
    """Mirror seed_scenarios.loaded_connector_names so e2e.py and the
    seeder agree on which connection-tests will actually be queued."""
    secrets_path = Path(__file__).resolve().parent.parent / "credentials" / "secrets.yaml"
    if not secrets_path.exists():
        return set()
    try:
        import yaml  # type: ignore
    except ImportError:
        return set()
    try:
        data = yaml.safe_load(secrets_path.read_text()) or {}
    except yaml.YAMLError:
        return set()
    return set(data.keys()) if isinstance(data, dict) else set()


def run(host: str, scenarios_path: Path, timeout: float) -> Report:
    report = Report()
    scenarios = json.loads(scenarios_path.read_text())
    expected_ct = [c for c in scenarios.get("connection_tests", []) if any(not k.startswith("_") and not k.startswith("$") for k in c)]
    # Match seed_scenarios.py: skip connection-tests whose connector
    # isn't configured locally — the agent silently drops them.
    configured = _configured_connector_names()
    expected_ct = [c for c in expected_ct if c.get("connector_name") in configured]
    expected_pt = [p for p in scenarios.get("playbook_tasks", []) if any(not k.startswith("_") and not k.startswith("$") for k in p)]

    with httpx.Client(base_url=host, timeout=10.0) as client:
        # 1. startup ping.
        ok, evts = wait_for(client, "ping_get", lambda e: len(e) >= 1, timeout, "startup ping")
        report.add(
            "agent issued startup ping (GET /connectors/proxy/ping)",
            ok,
            f"saw {len(evts)} ping_get events",
        )

        # 2. periodic heartbeat — POST /connectors/proxy/ping (every 50s in
        # default schedule, so allow a generous window).
        ok, evts = wait_for(client, "ping_post", lambda e: len(e) >= 1, max(timeout, 70.0), "heartbeat")
        report.add(
            "agent sent periodic heartbeat (POST /connectors/proxy/ping)",
            ok,
            f"saw {len(evts)} ping_post events",
        )

        # 3. connection-test loop — agent polled and reported.
        ok, polls = wait_for(client, "connection_tests_poll", lambda e: len(e) >= 1, timeout, "ct poll")
        report.add(
            "agent polled connection_tests endpoint",
            ok,
            f"saw {len(polls)} polls",
        )

        if expected_ct:
            expected_request_ids = set()
            ct_drained = False
            ct_deadline = time.time() + timeout
            while time.time() < ct_deadline:
                polls = _events(client, "connection_tests_poll")
                for ev in polls:
                    for delivered in ev.get("delivered") or []:
                        if delivered.get("request_id"):
                            expected_request_ids.add(delivered["request_id"])
                # Wait for as many request_ids to be delivered as we enqueued.
                if len(expected_request_ids) >= len(expected_ct):
                    ct_drained = True
                    break
                time.sleep(1.0)
            report.add(
                f"connection_tests drained ({len(expected_ct)} enqueued)",
                ct_drained,
                f"agent received {len(expected_request_ids)} request_ids",
            )

            results = _events(client, "connection_tests_results")
            seen_results = set()
            for ev in results:
                body = ev.get("body") or {}
                for r in body.get("results", []) or []:
                    if r.get("request_id"):
                        seen_results.add(r["request_id"])
            report.add(
                "agent posted connection_tests results back",
                expected_request_ids.issubset(seen_results),
                f"reported {len(seen_results & expected_request_ids)}/{len(expected_request_ids)} request_ids",
            )

        # 4. playbook-task loop.
        ok, polls = wait_for(client, "playbook_tasks_poll", lambda e: len(e) >= 1, timeout, "pt poll")
        report.add(
            "agent polled playbook_tasks endpoint",
            ok,
            f"saw {len(polls)} polls",
        )

        if expected_pt:
            seen_request_ids: set[str] = set()
            seen_deadline = time.time() + timeout
            while time.time() < seen_deadline:
                polls = _events(client, "playbook_tasks_poll")
                for ev in polls:
                    for delivered in ev.get("delivered") or []:
                        if delivered.get("proxy_execution_request_id"):
                            seen_request_ids.add(delivered["proxy_execution_request_id"])
                if len(seen_request_ids) >= len(expected_pt):
                    break
                time.sleep(1.0)
            report.add(
                f"playbook_tasks drained ({len(expected_pt)} enqueued)",
                len(seen_request_ids) >= len(expected_pt),
                f"agent received {len(seen_request_ids)} request_ids",
            )

            # Result endpoint should fire once per task.
            result_ids: set[str] = set()
            errored: list[str] = []
            res_deadline = time.time() + timeout
            while time.time() < res_deadline:
                for ev in _events(client, "playbook_tasks_results"):
                    for s in ev.get("summary") or []:
                        if s.get("request_id"):
                            result_ids.add(s["request_id"])
                            if s.get("has_error"):
                                errored.append(f"{s['request_id']}: {s.get('error')}")
                if seen_request_ids.issubset(result_ids):
                    break
                time.sleep(1.0)
            report.add(
                "agent posted playbook_tasks results back",
                seen_request_ids.issubset(result_ids),
                f"reported {len(seen_request_ids & result_ids)}/{len(seen_request_ids)} request_ids",
            )
            if errored:
                report.add(
                    "playbook tasks executed without errors",
                    False,
                    "errors: " + "; ".join(errored[:3]) + (f" (+{len(errored)-3})" if len(errored) > 3 else ""),
                )

            # Asset refresh tasks should drive metadata/register batches.
            has_asset_refresh = any(
                (p.get("task") or {}).get("drd_proxy_agent", {}).get("type") == "ASSET_REFRESH"
                for p in expected_pt
            )
            if has_asset_refresh:
                metadata_events = _events(client, "metadata_register")
                report.add(
                    "ASSET_REFRESH produced metadata register batches",
                    len(metadata_events) >= 1,
                    f"saw {len(metadata_events)} batches",
                )

            # Real kubectl tasks: assert the agent's reported output is
            # parseable, contains expected stable items, and matches a
            # host-side `kubectl` snapshot when available.
            _check_kubectl_scenarios(client, expected_pt, report, timeout)

    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8080")
    ap.add_argument("--file", default=str(Path(__file__).parent / "scenarios/default.json"))
    ap.add_argument("--timeout", type=float, default=90.0,
                    help="seconds to wait for each phase before failing")
    args = ap.parse_args()

    print(f"[e2e] mock={args.host} scenarios={args.file} timeout={args.timeout}s", file=sys.stderr)
    report = run(args.host, Path(args.file), args.timeout)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
