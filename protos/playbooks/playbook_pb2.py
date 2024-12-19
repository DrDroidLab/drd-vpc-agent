# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/playbooks/playbook.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protos import base_pb2 as protos_dot_base__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from protos.playbooks import playbook_commons_pb2 as protos_dot_playbooks_dot_playbook__commons__pb2
from protos.playbooks.intelligence_layer import interpreter_pb2 as protos_dot_playbooks_dot_intelligence__layer_dot_interpreter__pb2
from protos.playbooks import playbook_task_result_evaluator_pb2 as protos_dot_playbooks_dot_playbook__task__result__evaluator__pb2
from protos.playbooks import playbook_step_result_evaluator_pb2 as protos_dot_playbooks_dot_playbook__step__result__evaluator__pb2
from protos.playbooks.source_task_definitions import cloudwatch_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_cloudwatch__task__pb2
from protos.playbooks.source_task_definitions import grafana_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_grafana__task__pb2
from protos.playbooks.source_task_definitions import new_relic_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_new__relic__task__pb2
from protos.playbooks.source_task_definitions import datadog_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_datadog__task__pb2
from protos.playbooks.source_task_definitions import eks_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_eks__task__pb2
from protos.playbooks.source_task_definitions import sql_data_fetch_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_sql__data__fetch__task__pb2
from protos.playbooks.source_task_definitions import api_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_api__task__pb2
from protos.playbooks.source_task_definitions import bash_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_bash__task__pb2
from protos.playbooks.source_task_definitions import documentation_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_documentation__task__pb2
from protos.playbooks.source_task_definitions import promql_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_promql__task__pb2
from protos.playbooks.source_task_definitions import azure_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_azure__task__pb2
from protos.playbooks.source_task_definitions import gke_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_gke__task__pb2
from protos.playbooks.source_task_definitions import elastic_search_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_elastic__search__task__pb2
from protos.playbooks.source_task_definitions import grafana_loki_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_grafana__loki__task__pb2
from protos.playbooks.source_task_definitions import kubectl_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_kubectl__task__pb2
from protos.playbooks.source_task_definitions import gcm_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_gcm__task__pb2
from protos.playbooks.source_task_definitions import email_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_email__task__pb2
from protos.playbooks.source_task_definitions import lambda_function_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_lambda__function__task__pb2
from protos.playbooks.source_task_definitions import slack_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_slack__task__pb2
from protos.playbooks.source_task_definitions import big_query_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_big__query__task__pb2
from protos.playbooks.source_task_definitions import mongodb_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_mongodb__task__pb2
from protos.playbooks.source_task_definitions import open_search_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_open__search__task__pb2
from protos.playbooks.source_task_definitions import jenkins_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_jenkins__task__pb2
from protos.playbooks.source_task_definitions import github_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_github__task__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fprotos/playbooks/playbook.proto\x12\x10protos.playbooks\x1a\x11protos/base.proto\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\'protos/playbooks/playbook_commons.proto\x1a\x35protos/playbooks/intelligence_layer/interpreter.proto\x1a\x35protos/playbooks/playbook_task_result_evaluator.proto\x1a\x35protos/playbooks/playbook_step_result_evaluator.proto\x1a>protos/playbooks/source_task_definitions/cloudwatch_task.proto\x1a;protos/playbooks/source_task_definitions/grafana_task.proto\x1a=protos/playbooks/source_task_definitions/new_relic_task.proto\x1a;protos/playbooks/source_task_definitions/datadog_task.proto\x1a\x37protos/playbooks/source_task_definitions/eks_task.proto\x1a\x42protos/playbooks/source_task_definitions/sql_data_fetch_task.proto\x1a\x37protos/playbooks/source_task_definitions/api_task.proto\x1a\x38protos/playbooks/source_task_definitions/bash_task.proto\x1a\x41protos/playbooks/source_task_definitions/documentation_task.proto\x1a:protos/playbooks/source_task_definitions/promql_task.proto\x1a\x39protos/playbooks/source_task_definitions/azure_task.proto\x1a\x37protos/playbooks/source_task_definitions/gke_task.proto\x1a\x42protos/playbooks/source_task_definitions/elastic_search_task.proto\x1a@protos/playbooks/source_task_definitions/grafana_loki_task.proto\x1a;protos/playbooks/source_task_definitions/kubectl_task.proto\x1a\x37protos/playbooks/source_task_definitions/gcm_task.proto\x1a\x39protos/playbooks/source_task_definitions/email_task.proto\x1a\x43protos/playbooks/source_task_definitions/lambda_function_task.proto\x1a\x39protos/playbooks/source_task_definitions/slack_task.proto\x1a=protos/playbooks/source_task_definitions/big_query_task.proto\x1a;protos/playbooks/source_task_definitions/mongodb_task.proto\x1a?protos/playbooks/source_task_definitions/open_search_task.proto\x1a;protos/playbooks/source_task_definitions/jenkins_task.proto\x1a:protos/playbooks/source_task_definitions/github_task.proto\"\xf7\x11\n\x0cPlaybookTask\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x1e\n\x06source\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12\x32\n\x0creference_id\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04name\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0b\x64\x65scription\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12+\n\x05notes\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x30\n\ncreated_by\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x13global_variable_set\x18\x08 \x01(\x0b\x32\x17.google.protobuf.Struct\x12;\n\x10interpreter_type\x18\t \x01(\x0e\x32!.protos.playbooks.InterpreterType\x12Z\n\x16task_connector_sources\x18\n \x03(\x0b\x32:.protos.playbooks.PlaybookTask.PlaybookTaskConnectorSource\x12V\n\x17\x65xecution_configuration\x18\x0b \x01(\x0b\x32\x35.protos.playbooks.PlaybookTask.ExecutionConfiguration\x12\x38\n\rdocumentation\x18\x65 \x01(\x0b\x32\x1f.protos.playbooks.DocumentationH\x00\x12\x32\n\ncloudwatch\x18\x66 \x01(\x0b\x32\x1c.protos.playbooks.CloudwatchH\x00\x12,\n\x07grafana\x18g \x01(\x0b\x32\x19.protos.playbooks.GrafanaH\x00\x12/\n\tnew_relic\x18h \x01(\x0b\x32\x1a.protos.playbooks.NewRelicH\x00\x12,\n\x07\x64\x61tadog\x18i \x01(\x0b\x32\x19.protos.playbooks.DatadogH\x00\x12\x34\n\nclickhouse\x18j \x01(\x0b\x32\x1e.protos.playbooks.SqlDataFetchH\x00\x12\x32\n\x08postgres\x18k \x01(\x0b\x32\x1e.protos.playbooks.SqlDataFetchH\x00\x12$\n\x03\x65ks\x18l \x01(\x0b\x32\x15.protos.playbooks.EksH\x00\x12\x41\n\x17sql_database_connection\x18m \x01(\x0b\x32\x1e.protos.playbooks.SqlDataFetchH\x00\x12$\n\x03\x61pi\x18n \x01(\x0b\x32\x15.protos.playbooks.ApiH\x00\x12&\n\x04\x62\x61sh\x18o \x01(\x0b\x32\x16.protos.playbooks.BashH\x00\x12\x31\n\rgrafana_mimir\x18p \x01(\x0b\x32\x18.protos.playbooks.PromQlH\x00\x12(\n\x05\x61zure\x18q \x01(\x0b\x32\x17.protos.playbooks.AzureH\x00\x12$\n\x03gke\x18r \x01(\x0b\x32\x15.protos.playbooks.GkeH\x00\x12\x39\n\x0e\x65lastic_search\x18s \x01(\x0b\x32\x1f.protos.playbooks.ElasticSearchH\x00\x12\x35\n\x0cgrafana_loki\x18t \x01(\x0b\x32\x1d.protos.playbooks.GrafanaLokiH\x00\x12/\n\nkubernetes\x18u \x01(\x0b\x32\x19.protos.playbooks.KubectlH\x00\x12$\n\x03gcm\x18v \x01(\x0b\x32\x15.protos.playbooks.GcmH\x00\x12&\n\x04smtp\x18w \x01(\x0b\x32\x16.protos.playbooks.SMTPH\x00\x12(\n\x05slack\x18x \x01(\x0b\x32\x17.protos.playbooks.SlackH\x00\x12/\n\tbig_query\x18y \x01(\x0b\x32\x1a.protos.playbooks.BigQueryH\x00\x12,\n\x07mongodb\x18{ \x01(\x0b\x32\x19.protos.playbooks.MongoDBH\x00\x12\x33\n\x0bopen_search\x18| \x01(\x0b\x32\x1c.protos.playbooks.OpenSearchH\x00\x12,\n\x07jenkins\x18} \x01(\x0b\x32\x19.protos.playbooks.JenkinsH\x00\x12*\n\x06github\x18~ \x01(\x0b\x32\x18.protos.playbooks.GithubH\x00\x1a\x93\x01\n\x1bPlaybookTaskConnectorSource\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x1e\n\x06source\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12*\n\x04name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xbd\x02\n\x16\x45xecutionConfiguration\x12\x35\n\x11is_bulk_execution\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12>\n\x18\x62ulk_execution_var_field\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x1a\n\x12timeseries_offsets\x18\x03 \x03(\r\x12\x41\n\x1dis_result_transformer_enabled\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12M\n\"result_transformer_lambda_function\x18\x05 \x01(\x0b\x32!.protos.playbooks.Lambda.FunctionB\x06\n\x04task\"\xf9\x02\n\x16PlaybookTaskResultRule\x12\x36\n\x04type\x18\x01 \x01(\x0e\x32(.protos.playbooks.PlaybookTaskResultType\x12,\n\x04task\x18\x02 \x01(\x0b\x32\x1e.protos.playbooks.PlaybookTask\x12<\n\ntimeseries\x18\x65 \x01(\x0b\x32&.protos.playbooks.TimeseriesResultRuleH\x00\x12\x32\n\x05table\x18\x66 \x01(\x0b\x32!.protos.playbooks.TableResultRuleH\x00\x12\x31\n\x04logs\x18g \x01(\x0b\x32!.protos.playbooks.TableResultRuleH\x00\x12L\n\x13\x62\x61sh_command_output\x18h \x01(\x0b\x32-.protos.playbooks.BashCommandOutputResultRuleH\x00\x42\x06\n\x04rule\"\x8f\x04\n\x18PlaybookTaskExecutionLog\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x11\n\ttimestamp\x18\x02 \x01(\x10\x12,\n\x04task\x18\x03 \x01(\x0b\x32\x1e.protos.playbooks.PlaybookTask\x12\x34\n\x06result\x18\x04 \x01(\x0b\x32$.protos.playbooks.PlaybookTaskResult\x12\x38\n\x0einterpretation\x18\x05 \x01(\x0b\x32 .protos.playbooks.Interpretation\x12%\n\ntime_range\x18\x06 \x01(\x0b\x32\x11.protos.TimeRange\x12\x30\n\ncreated_by\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12>\n\x1d\x65xecution_global_variable_set\x18\x08 \x01(\x0b\x32\x17.google.protobuf.Struct\x12@\n\x1aproxy_execution_request_id\x18\t \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12=\n\x06status\x18\n \x01(\x0e\x32-.protos.playbooks.PlaybookExecutionStatusType\"\xd0\x02\n\x1bPlaybookStepResultCondition\x12\x31\n\x10logical_operator\x18\x01 \x01(\x0e\x32\x17.protos.LogicalOperator\x12H\n\trule_sets\x18\x02 \x03(\x0b\x32\x35.protos.playbooks.PlaybookStepResultCondition.RuleSet\x1a\xb3\x01\n\x07RuleSet\x12\x31\n\x10logical_operator\x18\x01 \x01(\x0e\x32\x17.protos.LogicalOperator\x12\x37\n\x05rules\x18\x02 \x03(\x0b\x32(.protos.playbooks.PlaybookTaskResultRule\x12<\n\nstep_rules\x18\x03 \x03(\x0b\x32(.protos.playbooks.PlaybookStepResultRule\"\xd6\x03\n\x0cPlaybookStep\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x32\n\x0creference_id\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0b\x64\x65scription\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12+\n\x05notes\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x36\n\x0e\x65xternal_links\x18\x06 \x03(\x0b\x32\x1e.protos.playbooks.ExternalLink\x12;\n\x10interpreter_type\x18\x07 \x01(\x0e\x32!.protos.playbooks.InterpreterType\x12-\n\x05tasks\x18\x08 \x03(\x0b\x32\x1e.protos.playbooks.PlaybookTask\x12\x38\n\x08\x63hildren\x18\t \x03(\x0b\x32&.protos.playbooks.PlaybookStepRelation\"\x90\x02\n\x14PlaybookStepRelation\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12.\n\x06parent\x18\x02 \x01(\x0b\x32\x1e.protos.playbooks.PlaybookStep\x12-\n\x05\x63hild\x18\x03 \x01(\x0b\x32\x1e.protos.playbooks.PlaybookStep\x12@\n\tcondition\x18\x04 \x01(\x0b\x32-.protos.playbooks.PlaybookStepResultCondition\x12-\n\tis_active\x18\x05 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\"\xb9\x02\n PlaybookStepRelationExecutionLog\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x38\n\x08relation\x18\x02 \x01(\x0b\x32&.protos.playbooks.PlaybookStepRelation\x12\x35\n\x11\x65valuation_result\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x32\n\x11\x65valuation_output\x18\x04 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x46\n\x1cstep_relation_interpretation\x18\x05 \x01(\x0b\x32 .protos.playbooks.Interpretation\"\xf2\x03\n\x18PlaybookStepExecutionLog\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x11\n\ttimestamp\x18\x02 \x01(\x10\x12\x35\n\x0fplaybook_run_id\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12,\n\x04step\x18\x04 \x01(\x0b\x32\x1e.protos.playbooks.PlaybookStep\x12G\n\x13task_execution_logs\x18\x05 \x03(\x0b\x32*.protos.playbooks.PlaybookTaskExecutionLog\x12S\n\x17relation_execution_logs\x18\x06 \x03(\x0b\x32\x32.protos.playbooks.PlaybookStepRelationExecutionLog\x12=\n\x13step_interpretation\x18\x07 \x01(\x0b\x32 .protos.playbooks.Interpretation\x12%\n\ntime_range\x18\x08 \x01(\x0b\x32\x11.protos.TimeRange\x12\x30\n\ncreated_by\x18\t \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\x81\x04\n\x08Playbook\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12*\n\x04name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0b\x64\x65scription\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x13global_variable_set\x18\x04 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x30\n\ncreated_by\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12-\n\tis_active\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x12\n\ncreated_at\x18\x07 \x01(\x10\x12\x13\n\x0blast_run_at\x18\x08 \x01(\x10\x12=\n\x06status\x18\t \x01(\x0e\x32-.protos.playbooks.PlaybookExecutionStatusType\x12-\n\x05steps\x18\n \x03(\x0b\x32\x1e.protos.playbooks.PlaybookStep\x12>\n\x0estep_relations\x18\x0b \x03(\x0b\x32&.protos.playbooks.PlaybookStepRelation\"\x80\x04\n\x11PlaybookExecution\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x35\n\x0fplaybook_run_id\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12,\n\x08playbook\x18\x03 \x01(\x0b\x32\x1a.protos.playbooks.Playbook\x12=\n\x06status\x18\x04 \x01(\x0e\x32-.protos.playbooks.PlaybookExecutionStatusType\x12\x12\n\ncreated_at\x18\x05 \x01(\x10\x12\x12\n\nstarted_at\x18\x06 \x01(\x10\x12\x13\n\x0b\x66inished_at\x18\x07 \x01(\x10\x12%\n\ntime_range\x18\x08 \x01(\x0b\x32\x11.protos.TimeRange\x12\x30\n\ncreated_by\x18\t \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12G\n\x13step_execution_logs\x18\x0b \x03(\x0b\x32*.protos.playbooks.PlaybookStepExecutionLog\x12>\n\x1d\x65xecution_global_variable_set\x18\x0c \x01(\x0b\x32\x17.google.protobuf.Struct\"\xf6\x04\n\x10UpdatePlaybookOp\x12\x31\n\x02op\x18\x01 \x01(\x0e\x32%.protos.playbooks.UpdatePlaybookOp.Op\x12U\n\x14update_playbook_name\x18\x02 \x01(\x0b\x32\x35.protos.playbooks.UpdatePlaybookOp.UpdatePlaybookNameH\x00\x12Y\n\x16update_playbook_status\x18\x03 \x01(\x0b\x32\x37.protos.playbooks.UpdatePlaybookOp.UpdatePlaybookStatusH\x00\x12L\n\x0fupdate_playbook\x18\x04 \x01(\x0b\x32\x31.protos.playbooks.UpdatePlaybookOp.UpdatePlaybookH\x00\x1a@\n\x12UpdatePlaybookName\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\x45\n\x14UpdatePlaybookStatus\x12-\n\tis_active\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x1a>\n\x0eUpdatePlaybook\x12,\n\x08playbook\x18\x01 \x01(\x0b\x32\x1a.protos.playbooks.Playbook\"\\\n\x02Op\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x18\n\x14UPDATE_PLAYBOOK_NAME\x10\x01\x12\x1a\n\x16UPDATE_PLAYBOOK_STATUS\x10\x02\x12\x13\n\x0fUPDATE_PLAYBOOK\x10\x03\x42\x08\n\x06updateb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.playbooks.playbook_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PLAYBOOKTASK._serialized_start=1822
  _PLAYBOOKTASK._serialized_end=4117
  _PLAYBOOKTASK_PLAYBOOKTASKCONNECTORSOURCE._serialized_start=3642
  _PLAYBOOKTASK_PLAYBOOKTASKCONNECTORSOURCE._serialized_end=3789
  _PLAYBOOKTASK_EXECUTIONCONFIGURATION._serialized_start=3792
  _PLAYBOOKTASK_EXECUTIONCONFIGURATION._serialized_end=4109
  _PLAYBOOKTASKRESULTRULE._serialized_start=4120
  _PLAYBOOKTASKRESULTRULE._serialized_end=4497
  _PLAYBOOKTASKEXECUTIONLOG._serialized_start=4500
  _PLAYBOOKTASKEXECUTIONLOG._serialized_end=5027
  _PLAYBOOKSTEPRESULTCONDITION._serialized_start=5030
  _PLAYBOOKSTEPRESULTCONDITION._serialized_end=5366
  _PLAYBOOKSTEPRESULTCONDITION_RULESET._serialized_start=5187
  _PLAYBOOKSTEPRESULTCONDITION_RULESET._serialized_end=5366
  _PLAYBOOKSTEP._serialized_start=5369
  _PLAYBOOKSTEP._serialized_end=5839
  _PLAYBOOKSTEPRELATION._serialized_start=5842
  _PLAYBOOKSTEPRELATION._serialized_end=6114
  _PLAYBOOKSTEPRELATIONEXECUTIONLOG._serialized_start=6117
  _PLAYBOOKSTEPRELATIONEXECUTIONLOG._serialized_end=6430
  _PLAYBOOKSTEPEXECUTIONLOG._serialized_start=6433
  _PLAYBOOKSTEPEXECUTIONLOG._serialized_end=6931
  _PLAYBOOK._serialized_start=6934
  _PLAYBOOK._serialized_end=7447
  _PLAYBOOKEXECUTION._serialized_start=7450
  _PLAYBOOKEXECUTION._serialized_end=7962
  _UPDATEPLAYBOOKOP._serialized_start=7965
  _UPDATEPLAYBOOKOP._serialized_end=8595
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOKNAME._serialized_start=8292
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOKNAME._serialized_end=8356
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOKSTATUS._serialized_start=8358
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOKSTATUS._serialized_end=8427
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOK._serialized_start=8429
  _UPDATEPLAYBOOKOP_UPDATEPLAYBOOK._serialized_end=8491
  _UPDATEPLAYBOOKOP_OP._serialized_start=8493
  _UPDATEPLAYBOOKOP_OP._serialized_end=8585
# @@protoc_insertion_point(module_scope)
