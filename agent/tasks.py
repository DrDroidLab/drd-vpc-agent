import logging
import threading

import requests
from celery import shared_task
from django.conf import settings
from requests.exceptions import RequestException, Timeout

from utils.time_utils import current_epoch_timestamp
from agent.health_monitor import HealthMetrics, HealthStatus

logger = logging.getLogger(__name__)

# Timeout constants (in seconds)
K8S_API_TIMEOUT = 30
HTTP_REQUEST_TIMEOUT = 30

# Kubernetes client cache (singleton pattern)
_k8s_clients_cache = {}
_k8s_config_lock = threading.Lock()
_k8s_config_loaded = False


def _get_k8s_clients():
    """
    Get or create singleton Kubernetes API clients.
    Reuses the same client instances to prevent connection leaks.
    Thread-safe for Celery workers.
    """
    global _k8s_config_loaded, _k8s_clients_cache

    # Fast path: clients already initialized
    if _k8s_clients_cache:
        return _k8s_clients_cache['v1'], _k8s_clients_cache['custom']

    # Slow path: initialize clients (thread-safe)
    with _k8s_config_lock:
        # Double-check after acquiring lock
        if _k8s_clients_cache:
            return _k8s_clients_cache['v1'], _k8s_clients_cache['custom']

        from kubernetes import client, config

        # Load Kubernetes config only once
        if not _k8s_config_loaded:
            try:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes config")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")
            _k8s_config_loaded = True

        # Create singleton API clients
        _k8s_clients_cache['v1'] = client.CoreV1Api()
        _k8s_clients_cache['custom'] = client.CustomObjectsApi()

        logger.info("Initialized Kubernetes API clients (singleton)")

    return _k8s_clients_cache['v1'], _k8s_clients_cache['custom']


def get_pod_details(namespace='drdroid'):
    """
    Fetch pod details from Kubernetes API.
    Uses cached API clients to prevent connection leaks.
    """
    try:
        # Get singleton clients (reuses existing instances)
        v1, custom_api = _get_k8s_clients()

        # Get all pods in the namespace with timeout
        pods = v1.list_namespaced_pod(namespace, _request_timeout=K8S_API_TIMEOUT)
        events = v1.list_namespaced_event(namespace, _request_timeout=K8S_API_TIMEOUT)

        # Get pod metrics for CPU/memory usage
        pod_metrics = {}
        try:
            metrics = custom_api.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                _request_timeout=K8S_API_TIMEOUT
            )
            for item in metrics.get('items', []):
                pod_name = item['metadata']['name']
                container_metrics = {}
                for container in item.get('containers', []):
                    container_metrics[container['name']] = {
                        'cpu': container['usage'].get('cpu', 'unknown'),
                        'memory': container['usage'].get('memory', 'unknown')
                    }
                pod_metrics[pod_name] = container_metrics
        except Exception as e:
            logger.warning(f"Could not fetch pod metrics (metrics-server may not be installed): {e}")

        pod_data = []

        for pod in pods.items:
            # Extract container statuses with enhanced health monitoring
            container_statuses = []

            # Build a map of container specs for resource limits
            container_specs = {}
            if pod.spec.containers:
                for spec in pod.spec.containers:
                    container_specs[spec.name] = spec

            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    # Determine container state
                    state = "unknown"
                    exit_code = None
                    termination_reason = None
                    termination_message = None

                    if container.state.running:
                        state = "running"
                    elif container.state.terminated:
                        state = "terminated"
                        exit_code = container.state.terminated.exit_code
                        termination_reason = container.state.terminated.reason
                        termination_message = container.state.terminated.message
                    elif container.state.waiting:
                        state = "waiting"
                        termination_reason = container.state.waiting.reason
                        termination_message = container.state.waiting.message

                    # Determine last state
                    last_state = "unknown"
                    last_exit_code = None
                    last_termination_reason = None

                    if container.last_state.running:
                        last_state = "running"
                    elif container.last_state.terminated:
                        last_state = "terminated"
                        last_exit_code = container.last_state.terminated.exit_code
                        last_termination_reason = container.last_state.terminated.reason
                    elif container.last_state.waiting:
                        last_state = "waiting"
                        last_termination_reason = container.last_state.waiting.reason

                    # Get resource usage
                    cpu_usage = 'unknown'
                    memory_usage = 'unknown'
                    if pod.metadata.name in pod_metrics:
                        container_usage = pod_metrics[pod.metadata.name].get(container.name, {})
                        cpu_usage = container_usage.get('cpu', 'unknown')
                        memory_usage = container_usage.get('memory', 'unknown')

                    # Get resource limits from spec
                    cpu_limit = None
                    memory_limit = None
                    cpu_request = None
                    memory_request = None

                    spec = container_specs.get(container.name)
                    if spec and spec.resources:
                        if spec.resources.limits:
                            cpu_limit = spec.resources.limits.get('cpu')
                            memory_limit = spec.resources.limits.get('memory')
                        if spec.resources.requests:
                            cpu_request = spec.resources.requests.get('cpu')
                            memory_request = spec.resources.requests.get('memory')

                    # Calculate health metrics
                    health_status, issues, health_score = HealthMetrics.assess_container_health(
                        container_state=state,
                        ready=container.ready,
                        restart_count=container.restart_count,
                        cpu_usage=cpu_usage,
                        memory_usage=memory_usage,
                        cpu_limit=cpu_limit,
                        memory_limit=memory_limit,
                        exit_code=exit_code,
                        termination_reason=termination_reason
                    )

                    # Calculate resource usage percentages for display
                    cpu_usage_pct = None
                    memory_usage_pct = None
                    if cpu_limit:
                        cpu_usage_pct = HealthMetrics.calculate_usage_percentage(cpu_usage, cpu_limit, 'cpu')
                    if memory_limit:
                        memory_usage_pct = HealthMetrics.calculate_usage_percentage(memory_usage, memory_limit, 'memory')

                    container_info = {
                        "name": container.name,
                        "state": state,
                        "last_state": last_state,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "cpu_limit": cpu_limit,
                        "memory_limit": memory_limit,
                        "cpu_request": cpu_request,
                        "memory_request": memory_request,
                        "cpu_usage_pct": round(cpu_usage_pct, 1) if cpu_usage_pct else None,
                        "memory_usage_pct": round(memory_usage_pct, 1) if memory_usage_pct else None,
                        "exit_code": exit_code,
                        "termination_reason": termination_reason,
                        "termination_message": termination_message,
                        "last_exit_code": last_exit_code,
                        "last_termination_reason": last_termination_reason,
                        "health_status": health_status.value,
                        "health_score": health_score,
                        "issues": issues
                    }

                    container_statuses.append(container_info)

            # Extract events for this pod
            pod_events = []
            for event in events.items:
                if event.involved_object.kind == 'Pod' and event.involved_object.name == pod.metadata.name:
                    pod_events.append({
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "count": event.count,
                        "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                    })

            # Calculate overall pod health
            pod_health_status, pod_issues, pod_health_score = HealthMetrics.calculate_pod_health(
                containers_health=container_statuses,
                events=pod_events,
                pod_phase=pod.status.phase
            )

            # Get pod age
            pod_age_seconds = None
            if pod.metadata.creation_timestamp:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                pod_age_seconds = int((now - pod.metadata.creation_timestamp).total_seconds())

            pod_data.append({
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "pod_health_status": pod_health_status.value,
                "pod_health_score": pod_health_score,
                "pod_issues": pod_issues,
                "pod_age_seconds": pod_age_seconds,
                "containers": container_statuses,
                "containers_total": len(container_statuses),
                "containers_ready": sum(1 for c in container_statuses if c.get('ready')),
                "events": pod_events
            })

        return pod_data

    except Exception as e:
        logger.error(f"Error fetching pod details: {e}", exc_info=True)
        return []


@shared_task
def send_ping_to_drd_cloud():
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    commit_hash = settings.VPC_AGENT_COMMIT_HASH
    current_epoch = current_epoch_timestamp()

    try:
        # Get pod details
        pod_details = get_pod_details()

        # Calculate overall cluster health summary
        total_pods = len(pod_details)
        healthy_pods = sum(1 for p in pod_details if p.get('pod_health_status') == 'healthy')
        degraded_pods = sum(1 for p in pod_details if p.get('pod_health_status') == 'degraded')
        critical_pods = sum(1 for p in pod_details if p.get('pod_health_status') == 'critical')
        unhealthy_pods = sum(1 for p in pod_details if p.get('pod_health_status') == 'unhealthy')

        # Get worst pod health status
        worst_status = 'healthy'
        if unhealthy_pods > 0:
            worst_status = 'unhealthy'
        elif critical_pods > 0:
            worst_status = 'critical'
        elif degraded_pods > 0:
            worst_status = 'degraded'

        # Calculate average health score
        avg_health_score = 0
        if total_pods > 0:
            avg_health_score = sum(p.get('pod_health_score', 0) for p in pod_details) / total_pods

        # Collect all critical issues across pods
        all_critical_issues = []
        for pod in pod_details:
            if pod.get('pod_health_status') in ['critical', 'unhealthy']:
                pod_name = pod.get('name')
                for issue in pod.get('pod_issues', []):
                    all_critical_issues.append(f"{pod_name}: {issue}")

        health_summary = {
            'total_pods': total_pods,
            'healthy_pods': healthy_pods,
            'degraded_pods': degraded_pods,
            'critical_pods': critical_pods,
            'unhealthy_pods': unhealthy_pods,
            'overall_status': worst_status,
            'avg_health_score': round(avg_health_score, 1),
            'critical_issues': all_critical_issues[:10]  # Limit to top 10 critical issues
        }

        # Establish reachability with DRD Cloud
        payload = {
            'commit_hash': commit_hash,
            'pods': pod_details,
            'health_summary': health_summary
        }

        response = requests.post(
            f'{drd_cloud_host}/connectors/proxy/ping',
            headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
            json=payload,
            timeout=HTTP_REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            logger.error(f'Failed to connect to DRD Cloud at {current_epoch} with code: {response.status_code} '
                         f'and response {response.text}')
            return False
        else:
            logger.info(f'Successfully connected to DRD Cloud at {current_epoch}. '
                        f'Health: {worst_status} ({healthy_pods}/{total_pods} healthy, '
                        f'avg_score: {round(avg_health_score, 1)})')

            # Log critical issues if any
            if all_critical_issues:
                logger.warning(f'Critical issues detected: {all_critical_issues[:3]}')

        return True

    except (RequestException, Timeout) as e:
        logger.error(f'Request error while pinging DRD Cloud at {current_epoch}: {str(e)}')
        return False
    except Exception as e:
        logger.error(f'Unexpected error while pinging DRD Cloud at {current_epoch}: {str(e)}')
        return False
