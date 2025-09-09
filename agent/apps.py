import logging

import requests
from django.apps import AppConfig

from agent import settings
from utils.yaml_utils import load_yaml

logger = logging.getLogger(__name__)


class AgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agent'

    def ready(self):
        # Path to your YAML file
        filepath = settings.BASE_DIR / 'credentials/secrets.yaml'

        # Load the YAML data and set it as an attribute
        self.yaml_data = load_yaml(filepath)
        if not self.yaml_data:
            logger.warning(f'No connections found in {filepath}')

        drd_cloud_host = settings.DRD_CLOUD_API_HOST
        drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
        commit_hash = settings.VPC_AGENT_COMMIT_HASH
        if settings.NATIVE_KUBERNETES_API_MODE:
            logger.info('Native Kubernetes API mode is enabled')

        # Establish reachability with DRD Cloud
        response = requests.get(f'{drd_cloud_host}/connectors/proxy/ping',
                                headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
                                params={'commit_hash': commit_hash})

        if response.status_code != 200:
            raise ValueError(f'Failed to connect to DRD Cloud: {response.text}')
