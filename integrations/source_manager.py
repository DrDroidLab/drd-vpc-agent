from typing import Dict

from django.conf import settings
from google.protobuf.struct_pb2 import Struct

from utils.credentilal_utils import credential_yaml_to_connector_proto
from utils.static_mappings import integrations_connector_type_connector_keys_map
from integrations.processor import Processor
from integrations.source_api_processors.lambda_function_processor import LambdaFunctionProcessor
from integrations.source_api_processors.no_op_processor import NoOpProcessor
from protos.base_pb2 import TimeRange, Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType
from protos.playbooks.playbook_pb2 import PlaybookTask
from protos.playbooks.source_task_definitions.lambda_function_task_pb2 import Lambda
from protos.ui_definition_pb2 import FormField
from utils.proto_utils import proto_to_dict, dict_to_proto


def apply_result_transformer(result_dict, lambda_function: Lambda.Function) -> Dict:
    lambda_function_processor = LambdaFunctionProcessor(lambda_function.definition.value,
                                                        lambda_function.requirements)
    transformer_result = lambda_function_processor.execute(result_dict)
    if not isinstance(transformer_result, Dict):
        raise ValueError("Result transformer should return a dictionary")
    transformer_result = {f"${k}" if not k.startswith("$") else k: v for k, v in transformer_result.items()}
    return transformer_result


def resolve_global_variables(form_fields: [FormField], global_variable_set: Struct,
                             source_type_task_def: Dict) -> (Dict, Dict):
    all_string_fields = [ff.key_name.value for ff in form_fields if ff.data_type == LiteralType.STRING]
    all_string_array_fields = [ff.key_name.value for ff in form_fields if ff.data_type == LiteralType.STRING_ARRAY]
    all_composite_fields = {}
    for ff in form_fields:
        if ff.is_composite:
            all_composite_fields[ff.key_name.value] = ff.composite_fields

    task_local_variable_map = {}
    for gk, gv in global_variable_set.items():
        for tk, tv in source_type_task_def.items():
            if tk in all_string_fields:
                if gv is None:
                    raise Exception(f"Global variable {gk} is None")
                source_type_task_def[tk] = tv.replace(gk, gv)
                if gk in tv:
                    task_local_variable_map[gk] = gv
            elif tk in all_string_array_fields:
                for item in source_type_task_def[tk]:
                    if gv is None:
                        raise Exception(f"Global variable {gk} is None")
                    source_type_task_def[tk] = item.replace(gk, gv)
                if gk in tv:
                    task_local_variable_map[gk] = gv
            elif tk in all_composite_fields:
                composite_fields = all_composite_fields[tk]
                for item in source_type_task_def[tk]:
                    for cf in composite_fields:
                        if cf.data_type == LiteralType.STRING:
                            if gv is None:
                                raise Exception(f"Global variable {gk} is None")
                            item[cf.key_name.value] = item[cf.key_name.value].replace(gk, gv)
                if gk in tv:
                    task_local_variable_map[gk] = gv
    return source_type_task_def, task_local_variable_map


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

    def get_active_connectors(self, connector_name: str) -> [ConnectorProto]:
        loaded_connections = settings.LOADED_CONNECTIONS
        if not loaded_connections:
            raise Exception("No loaded connections found")

        if connector_name not in loaded_connections:
            raise Exception(f"No loaded connections found for connector: {connector_name}")

        connector_proto: ConnectorProto = credential_yaml_to_connector_proto(connector_name,
                                                                             loaded_connections[connector_name])
        return connector_proto

    def execute_task(self, time_range: TimeRange, global_variable_set, task: PlaybookTask) -> PlaybookTaskResult:
        try:
            source_connector_proto = None
            if task.task_connector_sources and len(task.task_connector_sources) > 0:
                # TODO: Handle multiple connectors within task in future
                task_connector_source = task.task_connector_sources[0]
                if not task_connector_source.name or not task_connector_source.name.value:
                    raise Exception("Connector name not found in task")

                connector_name = task_connector_source.name.value
                active_connector = self.get_active_connectors(connector_name)

                source_connector_proto = active_connector

            task_dict = proto_to_dict(task)
            source = task_dict.get('source', '')
            if not source:
                raise Exception("Source not found in task")
            source_str = source.lower()
            source_task = task_dict.get(source_str, {})
            if not source_task:
                raise Exception(f"Source task not found in task: {source_str}")

            source_task_proto = dict_to_proto(source_task, self.task_proto)
            task_type = source_task_proto.type
            if task_type in self.task_type_callable_map:
                try:
                    task_type_name = self.task_proto.TaskType.Name(task_type).lower()
                    source_type_task_def = source_task.get(task_type_name, {})

                    # Update timeseries tasks with timeseries_offsets
                    if self.task_type_callable_map[task_type]['result_type'] == PlaybookTaskResultType.TIMESERIES and \
                            task.execution_configuration and task.execution_configuration.timeseries_offsets:
                        source_type_task_def['timeseries_offsets'] = list(
                            task.execution_configuration.timeseries_offsets)

                    form_fields = self.task_type_callable_map[task_type]['form_fields']

                    # Resolve global variables in source_type_task_def
                    resolved_source_type_task_def, task_local_variable_map = resolve_global_variables(
                        form_fields, global_variable_set, source_type_task_def)
                    source_task[task_type_name] = resolved_source_type_task_def
                    resolved_task_def_proto = dict_to_proto(source_task, self.task_proto)

                    # Execute task
                    playbook_task_result: PlaybookTaskResult = self.task_type_callable_map[task_type]['executor'](
                        time_range, resolved_task_def_proto, source_connector_proto)

                    # Set task local variables in playbook_task_result to be stored in database
                    task_local_variable_map_proto = dict_to_proto(task_local_variable_map,
                                                                  Struct) if task_local_variable_map else Struct()
                    playbook_task_result.task_local_variable_set.CopyFrom(task_local_variable_map_proto)

                    # Apply result transformer
                    if task.execution_configuration.is_result_transformer_enabled.value:
                        lambda_function = task.execution_configuration.result_transformer_lambda_function
                        playbook_task_result_dict = proto_to_dict(playbook_task_result) if playbook_task_result else {}
                        result_transformer_lambda_function_variable_set = apply_result_transformer(
                            playbook_task_result_dict, lambda_function)
                        result_transformer_lambda_function_variable_set_proto = dict_to_proto(
                            result_transformer_lambda_function_variable_set,
                            Struct) if result_transformer_lambda_function_variable_set else Struct()
                        playbook_task_result.result_transformer_lambda_function_variable_set.CopyFrom(
                            result_transformer_lambda_function_variable_set_proto)

                    return playbook_task_result
                except Exception as e:
                    raise Exception(f"Error while executing task for source: {source_str} with error: {e}")
            else:
                raise Exception(f"Task type {task_type} not supported for source: {source_str}")
        except Exception as e:
            raise Exception(f"Error while executing task: {e}")
