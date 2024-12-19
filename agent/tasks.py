import logging

import requests
from celery import shared_task
from django.conf import settings

from utils.time_utils import current_epoch_timestamp

logger = logging.getLogger(__name__)


@shared_task(max_retries=3, default_retry_delay=10)
def send_ping_to_drd_cloud():
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    current_epoch = current_epoch_timestamp()

    # Establish reachability with DRD Cloud
    response = requests.get(f'{drd_cloud_host}/connectors/proxy/ping',
                            headers={'Authorization': f'Bearer {drd_cloud_api_token}'})

    if response.status_code != 200:
        logger.error(f'Failed to connect to DRD Cloud at {current_epoch} with code: {response.status_code} '
                     f'and response {response.text}')
    else:
        logger.info(f'Successfully connected to DRD Cloud at {current_epoch}')
