import logging
from typing import Any, Dict, List, Tuple
from google.protobuf.struct_pb2 import Struct
from django.conf import settings

from integrations.source_facade import source_facade
from protos.base_pb2 import TimeRange
from protos.playbooks.playbook_pb2 import PlaybookTask
from utils.proto_utils import dict_to_proto, proto_to_dict
from utils.time_utils import current_epoch_timestamp
from utils.credentilal_utils import credential_yaml_to_connector_proto

logger = logging.getLogger(__name__)


def convert_literal_type_to_json_type(literal_type: Any) -> str:
    """Convert protobuf LiteralType to JSON Schema type string."""
    try:
        # Use enum values directly
        if literal_type == 1:  # STRING
            return "string"
        elif literal_type == 2:  # LONG
            return "integer"
        elif literal_type == 3:  # DOUBLE
            return "number"
        elif literal_type == 4:  # BOOLEAN
            return "boolean"
        elif literal_type == 5:  # STRING_ARRAY
            return "array"
        else:
            return "string"
    except:
        return "string"


def convert_form_field_to_json_schema(field: Any) -> Dict[str, Any]:
    """Convert a FormField proto to JSON Schema property definition."""
    try:
        field_schema = {
            "type": convert_literal_type_to_json_type(field.data_type),
            "description": field.description.value if hasattr(field, 'description') and field.description else
                          field.display_name.value if hasattr(field, 'display_name') and field.display_name else ""
        }

        # Handle array type
        if field.data_type == 5:  # STRING_ARRAY
            field_schema["items"] = {"type": "string"}

        # Add default value if present
        try:
            if hasattr(field, 'HasField') and field.HasField("default_value"):
                default_val = field.default_value
                if default_val.literal_type == 1:  # STRING
                    field_schema["default"] = default_val.string.value
                elif default_val.literal_type == 2:  # LONG
                    field_schema["default"] = default_val.long.value
                elif default_val.literal_type == 4:  # BOOLEAN
                    field_schema["default"] = default_val.boolean.value
        except:
            pass

        return field_schema
    except Exception as e:
        logger.error(f"Error converting form field: {e}")
        return {"type": "string", "description": ""}


def generate_mcp_tools_for_source_manager(source_manager: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Generate MCP tools and tool-to-task-type mapping for a source manager."""
    tools = []
    tool_to_task_mapping = {}

    try:
        # Check if we have any active connectors for this source
        connectors = source_manager.get_all_active_connectors()
        if not connectors:
            logger.info(f"No active connectors found for source {source_manager.source}")
            return tools, tool_to_task_mapping
    except Exception as e:
        logger.error(f"Error getting connectors for source {getattr(source_manager, 'source', 'unknown')}: {e}")
        return tools, tool_to_task_mapping

    try:
        # Get source name for tool naming - use actual source name instead of proto ID
        source_name = str(source_manager.source).lower()
        # Convert proto enum to readable source name
        source_mapping = {
            'cloudwatch': 'cloudwatch',
            'datadog': 'datadog',
            'datadog_oauth': 'datadog',
            'new_relic': 'newrelic',
            'grafana': 'grafana',
            'grafana_mimir': 'mimir',
            'azure': 'azure',
            'gke': 'gke',
            'gcm': 'gcm',
            'grafana_loki': 'loki',
            'postgres': 'postgres',
            'clickhouse': 'clickhouse',
            'sql_database_connection': 'sql',
            'elastic_search': 'elasticsearch',
            'big_query': 'bigquery',
            'mongodb': 'mongodb',
            'open_search': 'opensearch',
            'api': 'api',
            'bash': 'bash',
            'kubernetes': 'k8s',
            'smtp': 'smtp',
            'slack': 'slack',
            'documentation': 'docs',
            'rootly': 'rootly',
            'zenduty': 'zenduty',
            'github': 'github',
            'argocd': 'argocd',
            'jira_cloud': 'jira',
            'jenkins': 'jenkins',
            'posthog': 'posthog',
            'signoz': 'signoz',
            'sentry': 'sentry',
            'github_actions': 'github_actions',
            'eks': 'eks'
        }

        # Use mapping or fallback to cleaned source name
        source_name = source_mapping.get(source_name, source_name.replace('_', '').replace('.', ''))

        for task_type, task_info in source_manager.task_type_callable_map.items():
            try:
                # Create shorter task type name
                task_type_name = str(task_type).lower()
                if hasattr(source_manager, 'task_proto') and source_manager.task_proto:
                    try:
                        task_type_name = source_manager.task_proto.TaskType.Name(task_type).lower()
                        # Remove common prefixes to make it shorter
                        if task_type_name.startswith('task_type_'):
                            task_type_name = task_type_name[10:]
                        elif task_type_name.startswith('task_'):
                            task_type_name = task_type_name[5:]
                    except:
                        pass

                # Create shorter tool name: {source}_{task}
                tool_name = f"{source_name}_{task_type_name}"

                # Ensure tool name doesn't exceed 60 characters
                if len(tool_name) > 60:
                    # Truncate to 60 characters, keeping the most important parts
                    if len(source_name) > 30:
                        source_name = source_name[:30]
                    if len(task_type_name) > 30:
                        task_type_name = task_type_name[:30]
                    tool_name = f"{source_name}_{task_type_name}"
                    # Final safety check
                    if len(tool_name) > 60:
                        tool_name = tool_name[:60]

                # Convert form_fields to JSON Schema properties
                properties = {}
                required = []

                for field in task_info.get('form_fields', []):
                    try:
                        field_name = field.key_name.value if hasattr(field, 'key_name') else f"field_{len(properties)}"
                        field_schema = convert_form_field_to_json_schema(field)
                        properties[field_name] = field_schema

                        if not getattr(field, 'is_optional', True):
                            required.append(field_name)
                    except Exception as e:
                        logger.error(f"Error processing form field: {e}")
                        continue

                # Create MCP tool definition
                tool = {
                    "name": tool_name,
                    "description": task_info.get('display_name', f'{source_name.title()} task'),
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }

                tools.append(tool)
                tool_to_task_mapping[tool_name] = {
                    "source": source_manager.source,
                    "task_type": task_type,
                    "task_type_name": task_type_name
                }

            except Exception as e:
                logger.error(f"Error creating tool for task type {task_type}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error generating tools for source manager: {e}")

    return tools, tool_to_task_mapping


def generate_mcp_tools_for_connectors() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Generate MCP tools and tool-to-task-type mapping for all connectors from secrets.yaml."""
    all_tools = []
    tool_to_task_mapping = {}

    # Get loaded connections from settings
    loaded_connections = settings.LOADED_CONNECTIONS
    
    # If no connections but native k8s mode is enabled, we still want to provide k8s tools
    if not loaded_connections and not settings.NATIVE_KUBERNETES_API_MODE:
        logger.info("No credentials found in secrets.yaml and native k8s mode disabled, no tools will be generated")
        return all_tools, tool_to_task_mapping
    
    # Ensure we have an empty dict if no connections but native k8s mode is enabled
    if not loaded_connections:
        loaded_connections = {}

    # Create mapping from credential type to source enum
    from protos.base_pb2 import Source
    credential_type_to_source = {
        'CLOUDWATCH': Source.CLOUDWATCH,
        'DATADOG': Source.DATADOG,
        'DATADOG_OAUTH': Source.DATADOG_OAUTH,
        'NEW_RELIC': Source.NEW_RELIC,
        'GRAFANA': Source.GRAFANA,
        'GRAFANA_MIMIR': Source.GRAFANA_MIMIR,
        'AZURE': Source.AZURE,
        'GKE': Source.GKE,
        'GCM': Source.GCM,
        'GRAFANA_LOKI': Source.GRAFANA_LOKI,
        'POSTGRES': Source.POSTGRES,
        'CLICKHOUSE': Source.CLICKHOUSE,
        'SQL_DATABASE_CONNECTION': Source.SQL_DATABASE_CONNECTION,
        'ELASTIC_SEARCH': Source.ELASTIC_SEARCH,
        'BIG_QUERY': Source.BIG_QUERY,
        'MONGODB': Source.MONGODB,
        'OPEN_SEARCH': Source.OPEN_SEARCH,
        'API': Source.API,
        'BASH': Source.BASH,
        'KUBERNETES': Source.KUBERNETES,
        'SMTP': Source.SMTP,
        'SLACK': Source.SLACK,
        'DOCUMENTATION': Source.DOCUMENTATION,
        'ROOTLY': Source.ROOTLY,
        'ZENDUTY': Source.ZENDUTY,
        'GITHUB': Source.GITHUB,
        'ARGOCD': Source.ARGOCD,
        'JIRA_CLOUD': Source.JIRA_CLOUD,
        'JENKINS': Source.JENKINS,
        'POSTHOG': Source.POSTHOG,
        'SIGNOZ': Source.SIGNOZ,
        'SENTRY': Source.SENTRY,
        'GITHUB_ACTIONS': Source.GITHUB_ACTIONS,
        'EKS': Source.EKS
    }

    # Add native Kubernetes connector if NATIVE_KUBERNETES_API_MODE is enabled
    if settings.NATIVE_KUBERNETES_API_MODE:
        # Check if we already have a Kubernetes connector in loaded_connections
        has_k8s_connector = any(config.get('type') == 'KUBERNETES' for config in loaded_connections.values())
        
        if not has_k8s_connector:
            # Add a native Kubernetes connector
            native_k8s_connector_name = 'native_k8'
            loaded_connections[native_k8s_connector_name] = {'type': 'KUBERNETES'}
            logger.info(f"Added native Kubernetes connector: {native_k8s_connector_name}")

    # Process each connector from loaded connections
    for connector_name, connector_config in loaded_connections.items():
        try:
            if 'type' not in connector_config:
                logger.warning(f"No type found for connector {connector_name}, skipping")
                continue

            connector_type = connector_config['type']
            
            # Map credential type to source enum
            source = credential_type_to_source.get(connector_type)
            if not source:
                logger.warning(f"Unknown connector type {connector_type} for connector {connector_name}, skipping")
                continue

            # Get source manager for this source type
            source_manager = source_facade.get_source_manager(source)
            if not source_manager:
                logger.warning(f"No source manager found for source {source} (connector {connector_name}), skipping")
                continue

            # Generate tools for this connector
            connector_tools, connector_mapping = generate_mcp_tools_for_connector(
                connector_name, source, source_manager
            )
            
            all_tools.extend(connector_tools)
            tool_to_task_mapping.update(connector_mapping)
            
            logger.info(f"Generated {len(connector_tools)} tools for connector {connector_name} (type: {connector_type})")

        except Exception as e:
            logger.error(f"Error generating tools for connector {connector_name}: {e}")
            continue

    return all_tools, tool_to_task_mapping


def generate_mcp_tools_for_connector(connector_name: str, source: Any, source_manager: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Generate MCP tools and tool-to-task-type mapping for a specific connector."""
    tools = []
    tool_to_task_mapping = {}

    try:
        # Clean connector name for tool naming (remove special characters, make lowercase)
        clean_connector_name = connector_name.lower().replace(' ', '_').replace('-', '_')
        # Ensure connector name doesn't exceed reasonable length
        if len(clean_connector_name) > 30:
            clean_connector_name = clean_connector_name[:30]

        for task_type, task_info in source_manager.task_type_callable_map.items():
            try:
                # Create shorter task type name
                task_type_name = str(task_type).lower()
                if hasattr(source_manager, 'task_proto') and source_manager.task_proto:
                    try:
                        task_type_name = source_manager.task_proto.TaskType.Name(task_type).lower()
                        # Remove common prefixes to make it shorter
                        if task_type_name.startswith('task_type_'):
                            task_type_name = task_type_name[10:]
                        elif task_type_name.startswith('task_'):
                            task_type_name = task_type_name[5:]
                    except:
                        pass

                # Create tool name: {connector_name}_{task}
                tool_name = f"{clean_connector_name}_{task_type_name}"

                # Ensure tool name doesn't exceed 64 characters (common limit for tool names)
                if len(tool_name) > 64:
                    # Truncate task type name if needed
                    max_task_len = 64 - len(clean_connector_name) - 1
                    if max_task_len > 0:
                        task_type_name = task_type_name[:max_task_len]
                        tool_name = f"{clean_connector_name}_{task_type_name}"
                    else:
                        # If connector name is too long, truncate both
                        clean_connector_name = clean_connector_name[:30]
                        task_type_name = task_type_name[:30]
                        tool_name = f"{clean_connector_name}_{task_type_name}"

                # Convert form_fields to JSON Schema properties
                properties = {}
                required = []

                # Add connector_name as a parameter with default value
                properties["connector_name"] = {
                    "type": "string",
                    "description": f"Name of the connector to use (defaults to {connector_name})",
                    "default": connector_name
                }

                for field in task_info.get('form_fields', []):
                    try:
                        field_name = field.key_name.value if hasattr(field, 'key_name') else f"field_{len(properties)}"
                        field_schema = convert_form_field_to_json_schema(field)
                        properties[field_name] = field_schema

                        if not getattr(field, 'is_optional', True):
                            required.append(field_name)
                    except Exception as e:
                        logger.error(f"Error processing form field: {e}")
                        continue

                # Create MCP tool definition
                tool = {
                    "name": tool_name,
                    "description": f"{task_info.get('display_name', f'{connector_name} task')} (Connector: {connector_name})",
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }

                tools.append(tool)
                tool_to_task_mapping[tool_name] = {
                    "connector_name": connector_name,
                    "source": source,
                    "task_type": task_type,
                    "task_type_name": task_type_name
                }

            except Exception as e:
                logger.error(f"Error creating tool for task type {task_type} in connector {connector_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error generating tools for connector {connector_name}: {e}")

    return tools, tool_to_task_mapping


def build_playbook_task_from_mcp_args(source: Any, task_type: Any, task_type_name: str, arguments: Dict[str, Any], connector_id: int, connector_name: str) -> Any:
    """Build a PlaybookTask proto from MCP arguments."""
    try:
        # Import ConnectorType to get the proper name
        from protos.base_pb2 import Source as ConnectorType

        # Get source name for task structure - handle enum properly
        source_name = "unknown"
        try:
            # Use ConnectorType.Name to get the proper string name
            source_name = ConnectorType.Name(source).lower()
        except:
            # Fallback to string conversion
            try:
                source_name = str(source).lower()
                if 'source.' in source_name:
                    source_name = source_name.split('.')[-1]
                elif '.' in source_name:
                    source_name = source_name.split('.')[-1]
            except:
                raise ValueError(f"Could not determine source name for source: {source}")

        print(f"Building task with source_name: {source_name}, task_type: {task_type}, task_type_name: {task_type_name}")

        # Build the task structure
        task_dict = {
            "source": source,
            "task_connector_sources": [{
                "id": connector_id,
                "source": source,
                "name": connector_name,
            }]
        }

        # Add task-specific fields
        task_field = task_type_name.lower()
        task_dict[source_name] = {
            "type": task_type
        }
        task_dict[source_name][task_field] = arguments

        print(f"Task dict structure: {task_dict}")

        # Convert to PlaybookTask proto
        task_proto = dict_to_proto(task_dict, PlaybookTask)
        return task_proto
    except Exception as e:
        logger.error(f"Error building playbook task: {e}")
        raise


def build_playbook_task_from_mcp_args_with_connector(source: Any, task_type: Any, task_type_name: str, arguments: Dict[str, Any], connector_name: str) -> Any:
    """Build a PlaybookTask proto from MCP arguments using connector name."""
    try:
        # Import ConnectorType to get the proper name
        from protos.base_pb2 import Source as ConnectorType

        # Get source name for task structure - handle enum properly
        source_name = "unknown"
        try:
            # Use ConnectorType.Name to get the proper string name
            source_name = ConnectorType.Name(source).lower()
        except:
            # Fallback to string conversion
            try:
                source_name = str(source).lower()
                if 'source.' in source_name:
                    source_name = source_name.split('.')[-1]
                elif '.' in source_name:
                    source_name = source_name.split('.')[-1]
            except:
                raise ValueError(f"Could not determine source name for source: {source}")

        print(f"Building task with source_name: {source_name}, task_type: {task_type}, task_type_name: {task_type_name}, connector_name: {connector_name}")

        # Get connector proto from credentials using connector name
        loaded_connections = settings.LOADED_CONNECTIONS or {}
        
        # Add native Kubernetes connector if NATIVE_KUBERNETES_API_MODE is enabled and not already present
        if settings.NATIVE_KUBERNETES_API_MODE:
            has_k8s_connector = any(config.get('type') == 'KUBERNETES' for config in loaded_connections.values())
            if not has_k8s_connector:
                api_token_identifier = settings.DRD_CLOUD_API_TOKEN[-3:] if settings.DRD_CLOUD_API_TOKEN else "xxx"
                native_k8s_connector_name = f'native_k8_connection_{api_token_identifier}'
                loaded_connections[native_k8s_connector_name] = {'type': 'KUBERNETES'}
        
        if connector_name not in loaded_connections:
            raise ValueError(f"Connector {connector_name} not found in loaded connections")

        connector_config = loaded_connections[connector_name]
        # Create connector proto without connector_id (since we don't have it in MCP context)
        connector_proto = credential_yaml_to_connector_proto(connector_name, connector_config)
        
        # For the task structure, we'll use a dummy connector_id (0) since it's required for the task structure
        # but the actual connector proto doesn't need it
        connector_id = 0

        # Build the task structure
        task_dict = {
            "source": source,
            "task_connector_sources": [{
                "id": connector_id,
                "source": source,
                "name": connector_name,
            }]
        }

        # Remove connector_name from arguments since it's not part of the task parameters
        task_arguments = {k: v for k, v in arguments.items() if k != 'connector_name'}

        # Add task-specific fields
        task_field = task_type_name.lower()
        task_dict[source_name] = {
            "type": task_type
        }
        task_dict[source_name][task_field] = task_arguments

        print(f"Task dict structure: {task_dict}")

        # Convert to PlaybookTask proto
        task_proto = dict_to_proto(task_dict, PlaybookTask)
        return task_proto, connector_proto
    except Exception as e:
        logger.error(f"Error building playbook task with connector: {e}")
        raise


def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any], tool_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool using the existing playbook facade."""
    try:
        if tool_name not in tool_mapping:
            raise ValueError(f"Tool {tool_name} not found")

        tool_info = tool_mapping[tool_name]
        source = tool_info["source"]
        task_type = tool_info["task_type"]
        task_type_name = tool_info["task_type_name"]

        # Get first available connector for this source
        source_manager = source_facade.get_source_manager(source)
        if not source_manager:
            raise ValueError(f"No source manager found for source {source}")
        connectors = source_manager.get_all_active_connectors()

        if not connectors:
            raise ValueError(f"No active connectors found for source {source}")

        connector = connectors[0]  # Use first available

        # Get connector name from loaded connections
        loaded_connections = settings.LOADED_CONNECTIONS
        connector_name = None
        for c, metadata in loaded_connections.items():
            if metadata.get('id') == connector.id.value:
                connector_name = c
                break
        
        if not connector_name:
            # Fallback: use the first connector name for this source type
            for c, metadata in loaded_connections.items():
                if metadata.get('type') == str(source).lower():
                    connector_name = c
                    break
        
        if not connector_name:
            raise ValueError(f"Could not determine connector name for connector ID {connector.id.value}")

        # Build PlaybookTask proto
        task = build_playbook_task_from_mcp_args(
            source=source,
            task_type=task_type,
            task_type_name=task_type_name,
            arguments=arguments,
            connector_id=connector.id.value,
            connector_name=connector_name
        )

        # Create time range (last 4 hours like in views)
        current_time = current_epoch_timestamp()
        time_range = TimeRange(time_geq=int(current_time - 14400), time_lt=int(current_time))

        # Execute using existing facade
        result = source_facade.execute_task(
            time_range=time_range,
            global_variable_set=Struct(),
            task=task,
        )

        # Convert result to dict for JSON serialization
        try:
            # Check if result is a list/iterable (multiple results)
            if isinstance(result, list):
                return {"results": [proto_to_dict(r) for r in result]}
            else:
                # Single result
                return {"result": proto_to_dict(result)}
        except Exception as e:
            logger.error(f"Error converting result to dict: {e}")
            return {"result": {"error": str(e)}}

    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        return {"error": str(e)} 


def execute_mcp_tool_with_connector(tool_name: str, arguments: Dict[str, Any], tool_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool using connector-based approach."""
    try:
        if tool_name not in tool_mapping:
            raise ValueError(f"Tool {tool_name} not found")

        tool_info = tool_mapping[tool_name]
        connector_name = tool_info["connector_name"]
        source = tool_info["source"]
        task_type = tool_info["task_type"]
        task_type_name = tool_info["task_type_name"]

        # Use connector name from arguments if provided, otherwise use default from tool info
        actual_connector_name = arguments.get("connector_name", connector_name)

        # Get source manager for this source
        source_manager = source_facade.get_source_manager(source)
        if not source_manager:
            raise ValueError(f"No source manager found for source {source}")

        # Build PlaybookTask proto with connector
        task, connector_proto = build_playbook_task_from_mcp_args_with_connector(
            source=source,
            task_type=task_type,
            task_type_name=task_type_name,
            arguments=arguments,
            connector_name=actual_connector_name
        )

        # Create time range (last 4 hours like in views)
        current_time = current_epoch_timestamp()
        time_range = TimeRange(time_geq=int(current_time - 14400), time_lt=int(current_time))

        # Execute using source manager directly (similar to source_manager.execute_task but with our connector)
        try:
            # Get resolved task
            resolved_task, resolved_source_task, task_local_variable_map = source_manager.get_resolved_task(
                Struct(), task
            )

            # Execute task with our connector proto
            playbook_task_result = source_manager.task_type_callable_map[task_type]['executor'](
                time_range, resolved_source_task, connector_proto
            )

            # Post-process the result
            from integrations.utils.executor_utils import check_multiple_task_results
            if check_multiple_task_results(playbook_task_result):
                task_results = []
                for result in playbook_task_result:
                    processed_result = source_manager.postprocess_task_result(result, resolved_task, task_local_variable_map)
                    task_results.append(processed_result)
                return {"results": [proto_to_dict(r) for r in task_results]}
            else:
                processed_result = source_manager.postprocess_task_result(playbook_task_result, resolved_task, task_local_variable_map)
                return {"result": proto_to_dict(processed_result)}

        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"error": str(e)}

    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        return {"error": str(e)} 