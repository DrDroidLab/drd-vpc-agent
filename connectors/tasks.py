import logging

import requests
from celery import shared_task
from django.conf import settings

from drdroid_debug_toolkit.core.integrations.source_facade import source_facade
from drdroid_debug_toolkit.core.protos.connectors.connector_pb2 import Connector
from utils.credentilal_utils import credential_yaml_to_connector_proto
from utils.proto_utils import proto_to_dict

logger = logging.getLogger(__name__)


@shared_task(max_retries=3, default_retry_delay=10)
def fetch_connector_connections_tests():
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN

    response = requests.post(f'{drd_cloud_host}/connectors/proxy/connector/connection/tests',
                             headers={'Authorization': f'Bearer {drd_cloud_api_token}'}, json={})
    if response.status_code != 200:
        logger.error(f'fetch_connector_connections_tests:: Failed to get scheduled connection tests with DRD '
                     f'Cloud: {response.json()}')
        return False
    connection_test_requests = response.json().get('requests', [])
    logger.info(f'fetch_connector_connections_tests:: Found {len(connection_test_requests)} connection test requests')
    for r in connection_test_requests:
        try:
            request_id = r.get('request_id', None)
            if not request_id:
                logger.error(f'fetch_connector_connections_tests:: Request ID not found in request: {r}')
                continue
            logger.info(f'fetch_connector_connections_tests:: Scheduling connection test request for: '
                        f'{request_id}')
            execute_connection_test_and_send.delay(r)
        except Exception as e:
            logger.error(f'fetch_connector_connections_tests:: Error while scheduling request: {str(e)}')
            continue
    return True


@shared_task(max_retries=3, default_retry_delay=10)
def execute_connection_test_and_send(test_connection_request):
    try:
        drd_cloud_host = settings.DRD_CLOUD_API_HOST
        drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
        loaded_connections = settings.LOADED_CONNECTIONS

        request_id = test_connection_request.get('request_id')
        connector_name = test_connection_request.get('connector_name')
        test_connector_proto = None
        for c, metadata in loaded_connections.items():
            connector_proto = credential_yaml_to_connector_proto(c, metadata)
            if connector_name == connector_proto.name.value:
                test_connector_proto = connector_proto
                break
        if not test_connector_proto:
            logger.error(f'execute_connection_test_and_send:: Connector not found for: {connector_name}')
            return False
        try:
            is_connection_state_successful, error = source_facade.test_source_connection(test_connector_proto)
            result = {
                'request_id': request_id,
                'is_connection_state_successful': is_connection_state_successful,
            }
            if error:
                result['error'] = error
        except Exception as e:
            logger.error(f'execute_connection_test_and_send:: Error while testing connection: {str(e)}')
            result = {
                'request_id': request_id,
                'is_connection_state_successful': False,
                'error': str(e)
            }

        response = requests.post(f'{drd_cloud_host}/connectors/proxy/connector/connection/results',
                                 headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
                                 json={'results': [result]})

        if response.status_code != 200:
            logger.error(f'execute_connection_test_and_send:: Failed to send test result to Doctor Droid Cloud with '
                         f'code: {response.status_code} and response: {response.text}')
            return False
        return True
    except Exception as e:
        logger.error(f'execute_connection_test_and_send:: Error while executing task: {str(e)}')
        return False


@shared_task(max_retries=3, default_retry_delay=10)
def register_connectors(drd_cloud_host, drd_cloud_api_token, loaded_connections):
    connectors = []
    for c, metadata in loaded_connections.items():
        connector_proto = credential_yaml_to_connector_proto(c, metadata)
        connectors.append(proto_to_dict(Connector(name=connector_proto.name, type=connector_proto.type)))

    response = requests.post(f'{drd_cloud_host}/connectors/proxy/register',
                             headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
                             json={'connectors': connectors})
    if response.status_code != 200:
        logger.error(f'Failed to register connectors with DRD Cloud: {response.json()}')
