import logging
import copy

import requests
from celery import shared_task
from django.conf import settings
from google.protobuf.struct_pb2 import Struct
from google.protobuf.wrappers_pb2 import StringValue

from drdroid_debug_toolkit.core.integrations.source_facade import source_facade
from drdroid_debug_toolkit.core.protos.base_pb2 import TimeRange
from drdroid_debug_toolkit.core.protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult
from drdroid_debug_toolkit.core.protos.playbooks.playbook_pb2 import PlaybookTask
from utils.proto_utils import dict_to_proto, proto_to_dict
from utils.credentilal_utils import credential_yaml_to_connector_proto
from drdroid_debug_toolkit.core.integrations.utils.executor_utils import check_multiple_task_results

logger = logging.getLogger(__name__)


def _execute_asset_refresh_task(playbook_task_execution_log):
    """Execute asset refresh task using the playbook infrastructure"""
    from drdroid_debug_toolkit.core.integrations.source_metadata_extractor_facade import source_metadata_extractor_facade
    from utils.credentilal_utils import credential_yaml_to_connector_proto, generate_credentials_dict
    
    try:
        # Extract asset refresh parameters from the new payload structure
        request_id = playbook_task_execution_log.get('proxy_execution_request_id')
        task_definition = playbook_task_execution_log.get('proxy_execution_task_definition', {})
        connector_id = task_definition.get('connector_id')
        extractor_method = task_definition.get('extractor_method')  # Optional field for specific method
        
        logger.info(f'_execute_asset_refresh_task:: Starting asset refresh for connector_id: {connector_id}, '
                    f'request_id: {request_id}, method: {extractor_method}')
        
        if not request_id or not connector_id:
            raise ValueError(f'Missing required fields: request_id={request_id}, connector_id={connector_id}')
        
        # Get connector credentials by connector_id
        loaded_connections = settings.LOADED_CONNECTIONS
        connector_proto = None
        connector_name = None
        for c, metadata in loaded_connections.items():
            # Check if this connector matches the ID
            if metadata.get('id') == connector_id:
                connector_proto = credential_yaml_to_connector_proto(c, metadata)
                connector_name = connector_proto.name.value
                break
                
        if not connector_proto:
            raise ValueError(f'Connector not found for connector_id: {connector_id}')
            
        credentials_dict = generate_credentials_dict(connector_proto.type, connector_proto.keys)
        if not credentials_dict:
            raise ValueError(f'No credentials found for connector: {connector_name}')
        
        # Get API credentials
        drd_cloud_host = settings.DRD_CLOUD_API_HOST
        drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
        
        # Execute asset refresh
        connector_type = connector_proto.type
        if extractor_method:
            # Execute specific extractor method
            extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
            extractor = extractor_class(request_id=request_id, connector_name=connector_name, **credentials_dict)
            # Set API credentials for metadata saving
            extractor.api_host = drd_cloud_host
            extractor.api_token = drd_cloud_api_token
            
            method = getattr(extractor, extractor_method)
            method()
            message = f'Successfully executed {extractor_method} for connector {connector_name}'
        else:
            # Execute full metadata population
            from asset_manager.tasks import populate_connector_metadata
            success = populate_connector_metadata(request_id, connector_name, connector_type, credentials_dict)
            if not success:
                raise ValueError('Full asset refresh failed')
            message = f'Successfully executed full asset refresh for connector {connector_name}'
        
        # Create success result
        result = PlaybookTaskResult(
            output=StringValue(value=message),
            error=StringValue(value="")
        )
        
    except Exception as e:
        logger.error(f'_execute_asset_refresh_task:: Error during asset refresh: {str(e)}')
        result = PlaybookTaskResult(error=StringValue(value=str(e)))
    
    # Create processed log in the same format as normal playbook tasks
    processed_log = copy.deepcopy(playbook_task_execution_log)
    result_dict = proto_to_dict(result)
    processed_log['result'] = result_dict
    
    # Send results using existing playbook infrastructure
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
    
    response = requests.post(
        f'{drd_cloud_host}/playbooks-engine/proxy/execution/results',
        headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
        json={'playbook_task_execution_logs': [processed_log]}
    )
    
    if response.status_code != 200:
        logger.error(f'_execute_asset_refresh_task:: Failed to send result to DRD Cloud: {response.json()}')
    else:
        logger.info(f'_execute_asset_refresh_task:: Successfully sent result for request_id: {request_id}')
    
    return True


def _execute_playbook_task(task_proto, time_range, global_variable_set):
    """Execute a playbook task and return results."""
    # Ensure connections are loaded
    loaded_connections = settings.LOADED_CONNECTIONS or {}
    
    # Add native Kubernetes connector if NATIVE_KUBERNETES_API_MODE is enabled
    if settings.NATIVE_KUBERNETES_API_MODE:
        has_k8s_connector = any(config.get('type') == 'KUBERNETES' for config in loaded_connections.values())
        if not has_k8s_connector:
            api_token_identifier = settings.DRD_CLOUD_API_TOKEN[-3:] if settings.DRD_CLOUD_API_TOKEN else "xxx"
            native_k8s_connector_name = f'native_k8_connection_{api_token_identifier}'
            loaded_connections[native_k8s_connector_name] = {'type': 'KUBERNETES'}
            logger.info(f"Added native Kubernetes connector: {native_k8s_connector_name}")
    
    # Get source manager
    source = task_proto.source
    source_manager = source_facade.get_source_manager(source)
    if not source_manager:
        raise ValueError(f"No source manager found for source {source}")
    
    # Extract task type and source name
    from drdroid_debug_toolkit.core.protos.base_pb2 import Source
    source_name = Source.Name(source).lower()
    
    # Get task type from source-specific field
    if not hasattr(task_proto, source_name):
        raise ValueError(f"Could not determine task type from task proto")
    
    source_task = getattr(task_proto, source_name)
    if not hasattr(source_task, 'type'):
        raise ValueError(f"Could not determine task type from task proto")
    
    task_type = source_task.type
    
    # Find connector
    connector_name = None
    connector_proto = None
    
    # First, try to get connector from task_connector_sources
    if hasattr(task_proto, 'task_connector_sources') and task_proto.task_connector_sources:
        connector_id = task_proto.task_connector_sources[0].id
        for name, config in loaded_connections.items():
            if config.get('id') == connector_id:
                connector_name = name
                connector_proto = credential_yaml_to_connector_proto(name, config)
                break
    
    # If not found by ID, try to find by source type
    if not connector_proto:
        for name, config in loaded_connections.items():
            if config.get('type') == source_name.upper():
                connector_name = name
                connector_proto = credential_yaml_to_connector_proto(name, config)
                break
    
    if not connector_proto:
        raise ValueError(f"No connector found for source {source_name}")
    
    logger.info(f"Using connector: {connector_name} for source: {source_name}")
    
    # Execute task
    resolved_task, resolved_source_task, task_local_variable_map = source_manager.get_resolved_task(
        global_variable_set, task_proto
    )
    
    playbook_task_result = source_manager.task_type_callable_map[task_type]['executor'](
        time_range, resolved_source_task, connector_proto
    )
    
    # Post-process the result
    if check_multiple_task_results(playbook_task_result):
        results = []
        for result in playbook_task_result:
            processed_result = source_manager.postprocess_task_result(result, resolved_task, task_local_variable_map)
            results.append(processed_result)
    else:
        processed_result = source_manager.postprocess_task_result(playbook_task_result, resolved_task, task_local_variable_map)
        results = [processed_result]
    
    return results


@shared_task(max_retries=3, default_retry_delay=10)
def fetch_playbook_execution_tasks():
    drd_cloud_host = settings.DRD_CLOUD_API_HOST
    drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN

    response = requests.post(f'{drd_cloud_host}/playbooks-engine/proxy/execution/tasks',
                             headers={'Authorization': f'Bearer {drd_cloud_api_token}'}, json={})
    if response.status_code != 200:
        logger.error(f'fetch_playbook_execution_tasks:: Failed to get scheduled tasks with DRD '
                     f'Cloud: {response.json()}')
        return False
    playbook_task_executions = response.json().get('playbook_task_executions', [])
    num_playbook_task_executions = len(playbook_task_executions) if check_multiple_task_results(playbook_task_executions) else 1
    logger.info(f'fetch_playbook_execution_tasks:: Found {num_playbook_task_executions} playbook task executions')
    for pet in playbook_task_executions:
        try:
            request_id = pet.get('proxy_execution_request_id', None)
            if not request_id:
                logger.error(f'fetch_playbook_execution_tasks:: Request ID not found in playbook task execution: {pet}')
                continue
            logger.info(f'fetch_playbook_execution_tasks:: Scheduling task execution for execution_request_id: '
                        f'{request_id}')
            execute_task_and_send_result.delay(pet)
        except Exception as e:
            logger.error(f'fetch_playbook_execution_tasks:: Error while scheduling task: {str(e)}')
            continue
    return True


@shared_task(max_retries=3, default_retry_delay=10)
def execute_task_and_send_result(playbook_task_execution_log):
    try:
        # Check if this is an asset refresh task
        task_definition = playbook_task_execution_log.get('proxy_execution_task_definition', {})
        if task_definition.get('task_type') == 'ASSET_REFRESH':
            return _execute_asset_refresh_task(playbook_task_execution_log)
        
        # Parse input data for normal playbook tasks
        task = playbook_task_execution_log.get('task', {})
        task_proto = dict_to_proto(task, PlaybookTask)

        time_range_dict = playbook_task_execution_log.get('time_range', {})
        time_range = dict_to_proto(time_range_dict, TimeRange)

        global_variable_set_dict = playbook_task_execution_log.get('execution_global_variable_set', {})
        global_variable_set = dict_to_proto(global_variable_set_dict, Struct) if global_variable_set_dict else Struct()

        processed_logs = []
        
        try:
            # Execute task
            results = _execute_playbook_task(task_proto, time_range, global_variable_set)
            
            # Create processed logs
            for result in results:
                current_log_copy = copy.deepcopy(playbook_task_execution_log)
                result_dict = proto_to_dict(result)
                current_log_copy['result'] = result_dict
                processed_logs.append(current_log_copy)
                
        except Exception as e:
            logger.error(f'execute_task_and_send_result:: Error while executing tasks: {str(e)}')
            current_log_copy = copy.deepcopy(playbook_task_execution_log)
            error_result = PlaybookTaskResult(error=StringValue(value=str(e)))
            current_log_copy['result'] = proto_to_dict(error_result)
            processed_logs.append(current_log_copy)

        # Send results
        if not processed_logs:
            logger.warning(f'execute_task_and_send_result:: No results to send for task: {task.get("id")}')
            return True
        
        drd_cloud_host = settings.DRD_CLOUD_API_HOST
        drd_cloud_api_token = settings.DRD_CLOUD_API_TOKEN
        
        response = requests.post(
            f'{drd_cloud_host}/playbooks-engine/proxy/execution/results',
            headers={'Authorization': f'Bearer {drd_cloud_api_token}'},
            json={'playbook_task_execution_logs': processed_logs}
        )
        
        if response.status_code != 200:
            logger.error(f'execute_task_and_send_result:: Failed to send task result to Doctor Droid Cloud with code: '
                         f'{response.status_code} and response: {response.text}')
            return False
        
        return True
        
    except Exception as e:
        logger.error(f'execute_task_and_send_result:: Error while executing task: {str(e)}')
        return False
