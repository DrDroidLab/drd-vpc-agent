import logging
import os

from django.apps import AppConfig
from django.conf import settings

from connectors.tasks import register_connectors
from utils.credentilal_utils import credential_yaml_to_connector_proto
from utils.static_mappings import integrations_connector_type_connector_keys_map

logger = logging.getLogger(__name__)


class ConnectorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'connectors'

    def ready(self):
        if not settings.LOADED_CONNECTIONS and not settings.NATIVE_KUBERNETES_API_MODE:
            logger.warning(f'No connections found in {settings.SECRETS_FILE_PATH}')
            return
        drd_cloud_host = settings.DRD_CLOUD_API_HOST
        drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
        loaded_connections = settings.LOADED_CONNECTIONS if settings.LOADED_CONNECTIONS else {}
        if loaded_connections:
            # Only register connectors from the 'exec' queue worker to avoid duplicate registrations
            celery_queue = os.environ.get('CELERY_QUEUE', '')
            if celery_queue == 'exec':
                register_connectors(drd_cloud_host, drd_cloud_api_token, loaded_connections)
                logger.info(f'Registered {len(loaded_connections)} connectors from exec queue worker.')
            else:
                logger.info(f'Skipping connector registration on queue: {celery_queue}')

            # Validate connector keys (always run validation)
            for c, metadata in loaded_connections.items():
                connector_proto = credential_yaml_to_connector_proto(c, metadata)
                connector_name = connector_proto.name.value
                connector_keys_proto = connector_proto.keys
                all_ck_types = [ck.key_type for ck in connector_keys_proto]
                required_key_types = integrations_connector_type_connector_keys_map.get(connector_proto.type, [])
                all_keys_found = False
                for rkt in required_key_types:
                    if sorted(rkt) == sorted(all_ck_types):
                        all_keys_found = True
                        break
                if not all_keys_found:
                    raise ValueError(f'Missing required connector keys for {connector_name}')
