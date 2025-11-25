import logging

import requests
from celery import shared_task
from django.conf import settings

from utils.time_utils import current_epoch_timestamp

logger = logging.getLogger(__name__)


def get_pod_details(namespace='drdroid'):
    # Import kubernetes here to avoid loading at module import time
    from kubernetes import client, config
    
    try:
        # Try to load in-cluster config first, then local config
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        v1 = client.CoreV1Api()
        
        # Get all pods in the namespace
        pods = v1.list_namespaced_pod(namespace)
        events = v1.list_namespaced_event(namespace)
        
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

                    container_statuses.append({
                        "name": container.name,
                        "state": state,
                        "last_state": last_state,
                        "ready": container.ready,
                        "restart_count": container.restart_count
                    })

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
        logger.error(f"Error fetching pod details: {e}")
        return []


@shared_task(max_retries=3, default_retry_delay=10)
def send_ping_to_drd_cloud():
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    commit_hash = settings.VPC_AGENT_COMMIT_HASH
    current_epoch = current_epoch_timestamp()

    # Get pod details
    pod_details = get_pod_details()

    # Establish reachability with DRD Cloud
    payload = {
        'commit_hash': commit_hash,
        'pods': pod_details
    }

    response = requests.post(f'{drd_cloud_host}/connectors/proxy/ping',
                        headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
                        json=payload)

    if response.status_code != 200:
        logger.error(f'Failed to connect to DRD Cloud at {current_epoch} with code: {response.status_code} '
                     f'and response {response.text}')
        return False
    else:
        logger.info(f'Successfully connected to DRD Cloud at {current_epoch}')
    return True
