import logging

from django.conf import settings
from google.protobuf.struct_pb2 import Struct

from integrations.utils.executor_utils import apply_result_transformer, resolve_global_variables
from utils.credentilal_utils import credential_yaml_to_connector_proto
from utils.static_mappings import integrations_connector_type_connector_keys_map
from integrations.processor import Processor
from integrations.source_api_processors.no_op_processor import NoOpProcessor
from protos.base_pb2 import TimeRange, Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType, \
    PlaybookExecutionStatusType
from protos.playbooks.playbook_pb2 import PlaybookTask
from utils.proto_utils import proto_to_dict, dict_to_proto
from integrations.utils.executor_utils import check_multiple_task_results
logger = logging.getLogger(__name__)


class SourceManager:
    source: Source = Source.UNKNOWN
    task_proto = None
    task_type_callable_map = {}

    @staticmethod
    def validate_connector(connector: ConnectorProto) -> bool:
        keys = connector.keys
        all_ck_types = [ck.key_type for ck in keys]
        required_key_types = integrations_connector_type_connector_keys_map.get(connector.type, [])
        all_keys_found = False
        for rkt in required_key_types:
            if sorted(rkt) == sorted(all_ck_types):
                all_keys_found = True
                break
        return all_keys_found

    @staticmethod
    def apply_task_result_transformer(task: PlaybookTask, task_result: PlaybookTaskResult):
        if task.execution_configuration.is_result_transformer_enabled.value:
            lambda_function = task.execution_configuration.result_transformer_lambda_function
            playbook_task_result_dict = proto_to_dict(task_result) if task_result else {}
            result_transformer_lambda_function_variable_set = apply_result_transformer(playbook_task_result_dict,
                                                                                       lambda_function)
            result_transformer_lambda_function_variable_set_proto = dict_to_proto(
                result_transformer_lambda_function_variable_set,
                Struct) if result_transformer_lambda_function_variable_set else Struct()
            task_result.result_transformer_lambda_function_variable_set.CopyFrom(
                result_transformer_lambda_function_variable_set_proto)
        return task_result

    def get_connector_processor(self, connector: ConnectorProto, **kwargs):
        return NoOpProcessor()

    def test_connector_processor(self, connector: ConnectorProto, **kwargs):
        processor: Processor = self.get_connector_processor(connector, **kwargs)
        if isinstance(processor, NoOpProcessor):
            raise Exception("No manager found for source")
        try:
            return processor.test_connection()
        except Exception as e:
            raise e

    def get_task_type_callable_map(self):
        return self.task_type_callable_map

    def get_active_connectors(self, connector_name: str, connector_id: int) -> [ConnectorProto]:
        loaded_connections = settings.LOADED_CONNECTIONS
        if not loaded_connections:
            raise Exception("No loaded connections found")

        if connector_name not in loaded_connections:
            raise Exception(f"No loaded connections found for connector: {connector_name}")

        connector_proto: ConnectorProto = credential_yaml_to_connector_proto(connector_name,
                                                                             loaded_connections[connector_name], connector_id)
        return connector_proto
    
    def get_all_active_connectors(self):
        loaded_connections = settings.LOADED_CONNECTIONS
        if not loaded_connections:
            raise Exception("No loaded connections found")
        all_active_connections = []
        for c, metadata in loaded_connections.items():
            print(c, metadata)
            connector_proto = credential_yaml_to_connector_proto(c, metadata)
            all_active_connections.append(connector_proto)
        return all_active_connections

    def get_resolved_task(self, global_variable_set: Struct, input_task: PlaybookTask):
        source = input_task.source
        if not source or source == Source.UNKNOWN or source != self.source:
            raise Exception("PlaybookSourceManager.resolve_source_task_proto:: Applicable Source not found for task")
        source_str = Source.Name(source).lower()

        task_dict = proto_to_dict(input_task)
        source_task_dict = task_dict.get(source_str, {})
        if not source_task_dict:
            raise Exception(f"PlaybookSourceManager.get_source_task:: No task definition found for: {source_str}")

        source_task_proto = dict_to_proto(source_task_dict, self.task_proto)
        task_type = source_task_proto.type
        if task_type not in self.task_type_callable_map:
            raise Exception(f"PlaybookSourceManager.get_source_task:: Task type {task_type} not supported for "
                            f"source: {source_str}")

        task_type_name = self.task_proto.TaskType.Name(task_type).lower()
        source_task_type_dict = source_task_dict.get(task_type_name, {})
        if 'form_fields' not in self.task_type_callable_map[task_type]:
            raise Exception(f"PlaybookSourceManager.get_source_task:: Form fields not found for task type: "
                            f"{task_type_name} in {source_str} source manager")

        # Resolve global variables in source_type_task_def
        form_fields = self.task_type_callable_map[task_type]['form_fields']
        resolved_source_task_type_dict, task_local_variable_map = resolve_global_variables(form_fields,
                                                                                           global_variable_set,
                                                                                           source_task_type_dict)

        # Add timeseries offsets to resolved_source_type_task_def if present in timeseries task
        if 'result_type' not in self.task_type_callable_map[task_type]:
            raise Exception(f"PlaybookSourceManager.get_source_task:: Result type not found for task type: "
                            f"{task_type_name} in {source_str} source manager")
        if self.task_type_callable_map[task_type]['result_type'] == PlaybookTaskResultType.TIMESERIES and \
                input_task.execution_configuration and input_task.execution_configuration.timeseries_offsets:
            resolved_source_task_type_dict['timeseries_offsets'] = list(
                input_task.execution_configuration.timeseries_offsets)

        source_task_dict[task_type_name] = resolved_source_task_type_dict
        resolved_source_task_proto = dict_to_proto(source_task_dict, self.task_proto)

        task_dict[source_str] = source_task_dict
        resolved_task: PlaybookTask = dict_to_proto(task_dict, PlaybookTask)

        return resolved_task, resolved_source_task_proto, task_local_variable_map

    def execute_task(self, time_range: TimeRange, global_variable_set, task: PlaybookTask):
        try:
            source_connector_proto = None
            if task.task_connector_sources and len(task.task_connector_sources) > 0:
                # TODO: Handle multiple connectors within task in future
                task_connector_source = task.task_connector_sources[0]
                if not task_connector_source.name or not task_connector_source.name.value:
                    raise Exception("Connector name not found in task")
                connector_name = task_connector_source.name.value
                connector_id = task_connector_source.id.value
                active_connector = self.get_active_connectors(connector_name, connector_id)
                source_connector_proto = active_connector
            resolved_task, resolved_source_task, task_local_variable_map = self.get_resolved_task(global_variable_set,
                                                                                                  task)
            try:
                # Execute task
                task_type = resolved_source_task.type
                playbook_task_result = self.task_type_callable_map[task_type]['executor'](
                    time_range, resolved_source_task, source_connector_proto)
                if check_multiple_task_results(playbook_task_result):
                    task_results = []
                    for result in playbook_task_result:
                        task_results.append(self.postprocess_task_result(result, resolved_task, task_local_variable_map))
                    return task_results
                return self.postprocess_task_result(playbook_task_result, resolved_task, task_local_variable_map)
            except Exception as e:
                source_str = Source.Name(resolved_task.source).lower()
                raise Exception(f"Error while executing task for source: {source_str} with error: {e}")
        except Exception as e:
            raise Exception(f"Error while executing task: {e}")

    def postprocess_task_result(self, playbook_task_result: PlaybookTaskResult, resolved_task: PlaybookTask, task_local_variable_map: dict):
        task_local_variable_map_proto = dict_to_proto(task_local_variable_map,
                                                              Struct) if task_local_variable_map else Struct()
        playbook_task_result.task_local_variable_set.CopyFrom(task_local_variable_map_proto)
        playbook_task_result.status = PlaybookExecutionStatusType.FINISHED

        # Apply result transformer
        playbook_task_result = self.apply_task_result_transformer(resolved_task, playbook_task_result)
        return playbook_task_result
