import logging
import threading

import requests
from celery import shared_task
from django.conf import settings
from requests.exceptions import RequestException, Timeout

from utils.time_utils import current_epoch_timestamp

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
            # Extract container statuses
            container_statuses = []
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    state = "unknown"
                    if container.state.running:
                        state = "running"
                    elif container.state.terminated:
                        state = "terminated"
                    elif container.state.waiting:
                        state = "waiting"

                    last_state = "unknown"
                    if container.last_state.running:
                        last_state = "running"
                    elif container.last_state.terminated:
                        last_state = "terminated"
                    elif container.last_state.waiting:
                        last_state = "waiting"

                    container_info = {
                        "name": container.name,
                        "state": state,
                        "last_state": last_state,
                        "ready": container.ready,
                        "restart_count": container.restart_count
                    }

                    # Add resource usage if available
                    if pod.metadata.name in pod_metrics:
                        container_usage = pod_metrics[pod.metadata.name].get(container.name, {})
                        container_info["cpu_usage"] = container_usage.get('cpu', 'unknown')
                        container_info["memory_usage"] = container_usage.get('memory', 'unknown')

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

            pod_data.append({
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "containers": container_statuses,
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

        # Establish reachability with DRD Cloud
        payload = {
            'commit_hash': commit_hash,
            'pods': pod_details
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
            logger.info(f'Successfully connected to DRD Cloud at {current_epoch}')
        return True

    except (RequestException, Timeout) as e:
        logger.error(f'Request error while pinging DRD Cloud at {current_epoch}: {str(e)}')
        return False
    except Exception as e:
        logger.error(f'Unexpected error while pinging DRD Cloud at {current_epoch}: {str(e)}')
        return False
