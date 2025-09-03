import logging
import uuid

from django.apps import AppConfig
from django.conf import settings

from asset_manager.tasks import populate_connector_metadata
from connectors.tasks import register_connectors
from drdroid_debug_toolkit.core.protos.base_pb2 import Source
from utils.credentilal_utils import credential_yaml_to_connector_proto, generate_credentials_dict
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
            register_connectors(drd_cloud_host, drd_cloud_api_token, loaded_connections)
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
                connector_type: Source = connector_proto.type
                credentials_dict = generate_credentials_dict(connector_type, connector_keys_proto)
                if credentials_dict:
                    request_id = uuid.uuid4().hex
                    populate_connector_metadata.delay(request_id, connector_name, connector_type, credentials_dict)
                elif settings.NATIVE_KUBERNETES_API_MODE:
                    request_id = uuid.uuid4().hex
                    populate_connector_metadata.delay(request_id, connector_name, connector_type, credentials_dict)
                else:
                    logger.warning(f'No credentials found for connector {connector_name}')
