import logging

import requests
from celery import shared_task
from django.conf import settings

from drdroid_debug_toolkit.core.integrations.source_metadata_extractor import SourceMetadataExtractor
from drdroid_debug_toolkit.core.integrations.source_metadata_extractor_facade import source_metadata_extractor_facade

logger = logging.getLogger(__name__)


@shared_task(max_retries=3, default_retry_delay=10)
def populate_connector_metadata(request_id, connector_name, connector_type, connector_credentials_dict):
    logger.info(f"Running populate_connector_metadata for connector: {connector_name} with request_id: {request_id}")
    
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    
    try:
        extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
    except Exception as e:
        logger.warning(f"Exception occurred while fetching extractor class for connector: {connector_name}, "
                       f"with error: {e}")
        return False
    extractor = extractor_class(request_id=request_id, connector_name=connector_name, **connector_credentials_dict)
    # Set API credentials for metadata saving
    extractor.api_host = drd_cloud_host
    extractor.api_token = drd_cloud_api_token
    extractor_methods = [method for method in dir(extractor) if
                         callable(getattr(extractor, method)) and method not in dir(SourceMetadataExtractor)]
    for extractor_method in extractor_methods:
        logger.info(f"Running method: {extractor_method} for connector: {connector_name}")
        try:
            extractor_async_method_call.delay(request_id, connector_name, connector_type, connector_credentials_dict,
                                              extractor_method)
        except Exception as e:
            logger.error(
                f"Exception occurred while scheduling method: {extractor_method} for connector: {connector_name}, "
                f"with error: {e}")
            continue


@shared_task(max_retries=3, default_retry_delay=10)
def extractor_async_method_call(request_id, connector_name, connector_type, connector_credentials_dict,
                                extractor_method):
    logger.info(f"Running extractor_async_method_call: {extractor_method} for connector: {connector_name} with "
                f"request_id: {request_id}")
    
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    
    extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
    extractor = extractor_class(request_id=request_id, connector_name=connector_name, **connector_credentials_dict)
    # Set API credentials for metadata saving
    extractor.api_host = drd_cloud_host
    extractor.api_token = drd_cloud_api_token
    method = getattr(extractor, extractor_method)
    try:
        method()
    except Exception as e:
        logger.error(f"Exception occurred while running method: {extractor_method} for connector: {connector_name}, "
                     f"request ID: {request_id}, with error: {e}")
        return False
    return True


@shared_task(max_retries=3, default_retry_delay=10)
def fetch_asset_refresh_requests():
    """Poll for asset refresh requests from DRD Cloud"""
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN

    response = requests.post(f'{drd_cloud_host}/connectors/proxy/connector/asset/refresh/tasks',
                             headers={'Authorization': f'Bearer {drd_cloud_api_token}'}, json={})
    if response.status_code != 200:
        logger.error(f'fetch_asset_refresh_requests:: Failed to get scheduled asset refresh requests with DRD '
                     f'Cloud: {response.json()}')
        return False
    
    refresh_requests = response.json().get('requests', [])
    logger.info(f'fetch_asset_refresh_requests:: Found {len(refresh_requests)} asset refresh requests')
    
    for request in refresh_requests:
        try:
            request_id = request.get('request_id')
            connector_name = request.get('connector_name')
            connector_type = request.get('connector_type')
            extractor_method = request.get('extractor_method', None)  # Optional: specific method to run
            
            if not request_id or not connector_name or not connector_type:
                logger.error(f'fetch_asset_refresh_requests:: Missing required fields in request: {request}')
                continue
                
            # Get connector credentials
            from utils.credentilal_utils import credential_yaml_to_connector_proto, generate_credentials_dict
            from utils.static_mappings import integrations_connector_type_connector_keys_map
            
            loaded_connections = settings.LOADED_CONNECTIONS
            connector_proto = None
            for c, metadata in loaded_connections.items():
                connector_proto_temp = credential_yaml_to_connector_proto(c, metadata)
                if connector_name == connector_proto_temp.name.value:
                    connector_proto = connector_proto_temp
                    break
                    
            if not connector_proto:
                logger.error(f'fetch_asset_refresh_requests:: Connector not found: {connector_name}')
                continue
                
            credentials_dict = generate_credentials_dict(connector_proto.type, connector_proto.keys)
            if not credentials_dict:
                logger.error(f'fetch_asset_refresh_requests:: No credentials found for connector: {connector_name}')
                continue
            
            logger.info(f'fetch_asset_refresh_requests:: Scheduling asset refresh for connector: {connector_name}')
            
            if extractor_method:
                # Refresh specific method
                execute_asset_refresh_and_send_result.delay(request_id, connector_name, connector_type, 
                                                          credentials_dict, extractor_method)
            else:
                # Refresh all assets for this connector
                execute_asset_refresh_and_send_result.delay(request_id, connector_name, connector_type, 
                                                          credentials_dict, None)
                
        except Exception as e:
            logger.error(f'fetch_asset_refresh_requests:: Error while scheduling refresh: {str(e)}')
            continue
            
    return True


@shared_task(max_retries=3, default_retry_delay=10)
def execute_asset_refresh_and_send_result(request_id, connector_name, connector_type, credentials_dict, extractor_method=None):
    """Execute asset refresh and send back results to prevent duplicate processing"""
    logger.info(f'execute_asset_refresh_and_send_result:: Starting asset refresh for connector: {connector_name}, '
                f'request_id: {request_id}, method: {extractor_method}')
    
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    
    result = {
        'request_id': request_id,
        'connector_name': connector_name,
        'connector_type': connector_type,
        'extractor_method': extractor_method,
        'success': False,
        'timestamp': int(__import__('time').time())
    }
    
    try:
        if extractor_method:
            # Execute specific extractor method
            extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
            extractor = extractor_class(request_id=request_id, connector_name=connector_name, **credentials_dict)
            # Set API credentials for metadata saving
            extractor.api_host = drd_cloud_host
            extractor.api_token = drd_cloud_api_token
            
            method = getattr(extractor, extractor_method)
            method()
            result['success'] = True
            result['message'] = f'Successfully executed {extractor_method}'
        else:
            # Execute full metadata population
            success = populate_connector_metadata(request_id, connector_name, connector_type, credentials_dict)
            result['success'] = success
            result['message'] = 'Successfully executed full asset refresh' if success else 'Failed to execute full asset refresh'
            
    except Exception as e:
        logger.error(f'execute_asset_refresh_and_send_result:: Error during asset refresh: {str(e)}')
        result['success'] = False
        result['error'] = str(e)
        result['message'] = f'Failed with error: {str(e)}'
    
    # Send result back to prevent duplicate processing
    try:
        response = requests.post(f'{drd_cloud_host}/connectors/proxy/connector/asset/refresh/results',
                                headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
                                json={'results': [result]})
        
        if response.status_code != 200:
            logger.error(f'execute_asset_refresh_and_send_result:: Failed to send result to DRD Cloud: {response.json()}')
        else:
            logger.info(f'execute_asset_refresh_and_send_result:: Successfully sent result for request_id: {request_id}')
            
    except Exception as e:
        logger.error(f'execute_asset_refresh_and_send_result:: Error sending result: {str(e)}')
    
    return result['success']
