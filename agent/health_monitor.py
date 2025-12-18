"""
Enhanced health monitoring utilities for VPC Agent pods.
Provides degradation detection and early warning signals.
"""
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


class HealthStatus(Enum):
    """Health status levels for containers and pods"""
    HEALTHY = "healthy"           # All metrics normal
    DEGRADED = "degraded"         # Warning signs detected
    CRITICAL = "critical"         # Severe issues, failure imminent
    UNHEALTHY = "unhealthy"       # Failed or terminated


class HealthMetrics:
    """Calculate health metrics and scores for containers/pods"""

    # Resource usage thresholds
    CPU_WARNING_THRESHOLD = 80  # %
    CPU_CRITICAL_THRESHOLD = 95  # %
    MEMORY_WARNING_THRESHOLD = 80  # %
    MEMORY_CRITICAL_THRESHOLD = 95  # %

    # Restart count thresholds
    RESTART_WARNING_THRESHOLD = 3
    RESTART_CRITICAL_THRESHOLD = 10

    # Critical event reasons that indicate imminent failure
    CRITICAL_EVENT_REASONS = {
        'OOMKilling', 'OOMKilled', 'Evicted', 'Failed',
        'FailedMount', 'FailedAttachVolume', 'FailedScheduling',
        'CrashLoopBackOff', 'ImagePullBackOff', 'ErrImagePull'
    }

    # Warning event reasons
    WARNING_EVENT_REASONS = {
        'BackOff', 'Unhealthy', 'ProbeWarning', 'NodeNotReady',
        'Pulling', 'BackoffLimitExceeded'
    }

    @staticmethod
    def parse_resource_value(value: str, resource_type: str) -> Optional[float]:
        """
        Parse Kubernetes resource values to numeric form.

        Args:
            value: Resource value like "14271868n", "212900Ki", "1500m"
            resource_type: 'cpu' or 'memory'

        Returns:
            Normalized value (CPU in millicores, Memory in MiB)
        """
        if not value or value == 'unknown':
            return None

        try:
            if resource_type == 'cpu':
                # CPU: handle 'n' (nanocores), 'm' (millicores), or plain number
                if value.endswith('n'):
                    # nanocores to millicores: divide by 1,000,000
                    return float(value[:-1]) / 1_000_000
                elif value.endswith('m'):
                    # already in millicores
                    return float(value[:-1])
                else:
                    # cores to millicores: multiply by 1000
                    return float(value) * 1000

            elif resource_type == 'memory':
                # Memory: handle Ki, Mi, Gi, K, M, G
                units = {
                    'Ki': 1024,
                    'Mi': 1024 * 1024,
                    'Gi': 1024 * 1024 * 1024,
                    'K': 1000,
                    'M': 1000 * 1000,
                    'G': 1000 * 1000 * 1000,
                }

                for suffix, multiplier in units.items():
                    if value.endswith(suffix):
                        bytes_val = float(value[:-len(suffix)]) * multiplier
                        # Convert to MiB for consistency
                        return bytes_val / (1024 * 1024)

                # Plain bytes
                return float(value) / (1024 * 1024)

        except (ValueError, AttributeError):
            return None

        return None

    @staticmethod
    def calculate_usage_percentage(usage: str, limit: str, resource_type: str) -> Optional[float]:
        """Calculate resource usage as percentage of limit"""
        usage_val = HealthMetrics.parse_resource_value(usage, resource_type)
        limit_val = HealthMetrics.parse_resource_value(limit, resource_type)

        if usage_val is None or limit_val is None or limit_val == 0:
            return None

        return (usage_val / limit_val) * 100

    @staticmethod
    def assess_container_health(
        container_state: str,
        ready: bool,
        restart_count: int,
        cpu_usage: Optional[str] = None,
        memory_usage: Optional[str] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        exit_code: Optional[int] = None,
        termination_reason: Optional[str] = None
    ) -> Tuple[HealthStatus, List[str], int]:
        """
        Assess container health and return status, issues, and score.

        Args:
            container_state: Current state (running/terminated/waiting)
            ready: Ready status
            restart_count: Number of restarts
            cpu_usage: Current CPU usage
            memory_usage: Current memory usage
            cpu_limit: CPU limit
            memory_limit: Memory limit
            exit_code: Last exit code if terminated
            termination_reason: Reason for termination

        Returns:
            Tuple of (HealthStatus, issues_list, health_score)
            Health score: 0-100 (100 = perfect health)
        """
        issues = []
        score = 100
        status = HealthStatus.HEALTHY

        # Check container state
        if container_state == "terminated":
            status = HealthStatus.UNHEALTHY
            score = 0

            if termination_reason == "OOMKilled":
                issues.append("Container was OOM killed - increase memory limit")
            elif exit_code and exit_code != 0:
                issues.append(f"Container terminated with exit code {exit_code}")
            else:
                issues.append("Container is terminated")

        elif container_state == "waiting":
            # Waiting state indicates startup problems
            if termination_reason:
                if "CrashLoopBackOff" in termination_reason:
                    status = HealthStatus.CRITICAL
                    score = 10
                    issues.append("Container in CrashLoopBackOff - check logs for startup errors")
                elif "ImagePullBackOff" in termination_reason or "ErrImagePull" in termination_reason:
                    status = HealthStatus.CRITICAL
                    score = 15
                    issues.append("Image pull failed - check image name and registry access")
                else:
                    status = HealthStatus.DEGRADED
                    score = 40
                    issues.append(f"Container waiting: {termination_reason}")
            else:
                status = HealthStatus.DEGRADED
                score = 50
                issues.append("Container in waiting state")

        elif container_state == "running":
            # Check readiness
            if not ready:
                status = HealthStatus.DEGRADED
                score -= 30
                issues.append("Container not ready - readiness probe failing")

            # Check restart count
            if restart_count >= HealthMetrics.RESTART_CRITICAL_THRESHOLD:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.CRITICAL
                score -= 40
                issues.append(f"Excessive restarts ({restart_count}) - container unstable")
            elif restart_count >= HealthMetrics.RESTART_WARNING_THRESHOLD:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                score -= 20
                issues.append(f"Elevated restart count ({restart_count})")

            # Check CPU usage
            if cpu_usage and cpu_limit:
                cpu_pct = HealthMetrics.calculate_usage_percentage(cpu_usage, cpu_limit, 'cpu')
                if cpu_pct is not None:
                    if cpu_pct >= HealthMetrics.CPU_CRITICAL_THRESHOLD:
                        if status == HealthStatus.HEALTHY:
                            status = HealthStatus.CRITICAL
                        score -= 30
                        issues.append(f"CPU usage critical ({cpu_pct:.1f}% of limit)")
                    elif cpu_pct >= HealthMetrics.CPU_WARNING_THRESHOLD:
                        if status == HealthStatus.HEALTHY:
                            status = HealthStatus.DEGRADED
                        score -= 15
                        issues.append(f"CPU usage high ({cpu_pct:.1f}% of limit)")

            # Check memory usage
            if memory_usage and memory_limit:
                mem_pct = HealthMetrics.calculate_usage_percentage(memory_usage, memory_limit, 'memory')
                if mem_pct is not None:
                    if mem_pct >= HealthMetrics.MEMORY_CRITICAL_THRESHOLD:
                        if status == HealthStatus.HEALTHY:
                            status = HealthStatus.CRITICAL
                        score -= 30
                        issues.append(f"Memory usage critical ({mem_pct:.1f}% of limit) - OOM risk")
                    elif mem_pct >= HealthMetrics.MEMORY_WARNING_THRESHOLD:
                        if status == HealthStatus.HEALTHY:
                            status = HealthStatus.DEGRADED
                        score -= 15
                        issues.append(f"Memory usage high ({mem_pct:.1f}% of limit)")

        # Ensure score doesn't go negative
        score = max(0, score)

        return status, issues, score

    @staticmethod
    def analyze_events(events: List[Dict]) -> Tuple[List[str], bool, bool]:
        """
        Analyze Kubernetes events for warning signs.

        Args:
            events: List of event dictionaries

        Returns:
            Tuple of (critical_events, has_warnings, has_oom_killed)
        """
        critical_events = []
        has_warnings = False
        has_oom_killed = False

        for event in events:
            event_type = event.get('type', '')
            reason = event.get('reason', '')
            message = event.get('message', '')

            # Check for OOMKilled
            if reason in ['OOMKilling', 'OOMKilled']:
                has_oom_killed = True
                critical_events.append(f"OOM Event: {message}")

            # Check for critical events
            elif reason in HealthMetrics.CRITICAL_EVENT_REASONS:
                critical_events.append(f"{reason}: {message}")

            # Check for warning events
            elif reason in HealthMetrics.WARNING_EVENT_REASONS or event_type == 'Warning':
                has_warnings = True

        return critical_events, has_warnings, has_oom_killed

    @staticmethod
    def calculate_pod_health(
        containers_health: List[Dict],
        events: List[Dict],
        pod_phase: str
    ) -> Tuple[HealthStatus, List[str], int]:
        """
        Calculate overall pod health based on container health and events.

        Args:
            containers_health: List of container health assessments
            events: Pod events
            pod_phase: Pod phase (Running/Pending/Failed)

        Returns:
            Tuple of (HealthStatus, issues_list, health_score)
        """
        issues = []

        # Check pod phase first
        if pod_phase in ['Failed', 'Unknown']:
            return HealthStatus.UNHEALTHY, ["Pod in Failed state"], 0

        elif pod_phase == 'Pending':
            return HealthStatus.DEGRADED, ["Pod stuck in Pending state"], 30

        # Analyze events
        critical_events, has_warnings, has_oom_killed = HealthMetrics.analyze_events(events)

        if critical_events:
            issues.extend(critical_events)

        if has_oom_killed:
            issues.append("Pod experienced OOM kills - increase memory limits")

        # Get worst container status
        worst_status = HealthStatus.HEALTHY
        min_score = 100
        container_issues_count = 0

        for container_health in containers_health:
            status_str = container_health.get('health_status')
            score = container_health.get('health_score', 100)
            container_issues = container_health.get('issues', [])

            if container_issues:
                container_issues_count += len(container_issues)

            # Convert string status to enum
            try:
                status = HealthStatus(status_str)
            except (ValueError, TypeError):
                status = HealthStatus.HEALTHY

            # Track worst status
            status_priority = {
                HealthStatus.UNHEALTHY: 4,
                HealthStatus.CRITICAL: 3,
                HealthStatus.DEGRADED: 2,
                HealthStatus.HEALTHY: 1
            }

            if status_priority.get(status, 0) > status_priority.get(worst_status, 0):
                worst_status = status

            min_score = min(min_score, score)

        # Overall pod status is worst container status
        pod_status = worst_status

        # Apply event-based adjustments
        if has_oom_killed and pod_status.value in ['healthy', 'degraded']:
            pod_status = HealthStatus.CRITICAL
            min_score = min(min_score, 20)

        elif critical_events and pod_status == HealthStatus.HEALTHY:
            pod_status = HealthStatus.DEGRADED
            min_score = min(min_score, 60)

        elif has_warnings and pod_status == HealthStatus.HEALTHY:
            min_score = min(min_score, 80)

        # Add summary issue
        if container_issues_count > 0:
            issues.append(f"Total issues detected across containers: {container_issues_count}")

        return pod_status, issues, min_score
