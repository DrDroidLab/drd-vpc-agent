# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/playbooks/source_task_definitions/grafana_task.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos.playbooks.source_task_definitions import promql_task_pb2 as protos_dot_playbooks_dot_source__task__definitions_dot_promql__task__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n;protos/playbooks/source_task_definitions/grafana_task.proto\x12\x10protos.playbooks\x1a\x1egoogle/protobuf/wrappers.proto\x1a:protos/playbooks/source_task_definitions/promql_task.proto\"\x9a\x0b\n\x07Grafana\x12\x30\n\x04type\x18\x01 \x01(\x0e\x32\".protos.playbooks.Grafana.TaskType\x12R\n\x17promql_metric_execution\x18\x03 \x01(\x0b\x32/.protos.playbooks.Grafana.PromQlMetricExecutionH\x00\x12`\n&prometheus_datasource_metric_execution\x18\x04 \x01(\x0b\x32..protos.playbooks.PromQl.PromQlMetricExecutionH\x00\x12_\n\x1cquery_dashboard_panel_metric\x18\x05 \x01(\x0b\x32\x37.protos.playbooks.Grafana.QueryDashboardPanelMetricTaskH\x00\x1a\xf7\x04\n\x15PromQlMetricExecution\x12\x34\n\x0e\x64\x61tasource_uid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x37\n\x11promql_expression\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12^\n\x1apromql_label_option_values\x18\x03 \x03(\x0b\x32:.protos.playbooks.Grafana.PromQlMetricExecution.LabelValue\x12\x33\n\rdashboard_uid\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61shboard_title\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08panel_id\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bpanel_title\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12=\n\x17panel_promql_expression\x18\x08 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x1a\n\x12timeseries_offsets\x18\t \x03(\r\x1a\x65\n\nLabelValue\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12+\n\x05value\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xbe\x02\n\x1dQueryDashboardPanelMetricTask\x12N\n\x07queries\x18\x01 \x03(\x0b\x32=.protos.playbooks.Grafana.QueryDashboardPanelMetricTask.Query\x12\x32\n\x0c\x64\x61shboard_id\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08panel_id\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61tasource_uid\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\x33\n\x05Query\x12*\n\x04\x65xpr\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\x82\x01\n\x08TaskType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x1b\n\x17PROMQL_METRIC_EXECUTION\x10\x01\x12*\n&PROMETHEUS_DATASOURCE_METRIC_EXECUTION\x10\x02\x12 \n\x1cQUERY_DASHBOARD_PANEL_METRIC\x10\x03\x42\x06\n\x04taskb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.playbooks.source_task_definitions.grafana_task_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GRAFANA._serialized_start=174
  _GRAFANA._serialized_end=1608
  _GRAFANA_PROMQLMETRICEXECUTION._serialized_start=515
  _GRAFANA_PROMQLMETRICEXECUTION._serialized_end=1146
  _GRAFANA_PROMQLMETRICEXECUTION_LABELVALUE._serialized_start=1045
  _GRAFANA_PROMQLMETRICEXECUTION_LABELVALUE._serialized_end=1146
  _GRAFANA_QUERYDASHBOARDPANELMETRICTASK._serialized_start=1149
  _GRAFANA_QUERYDASHBOARDPANELMETRICTASK._serialized_end=1467
  _GRAFANA_QUERYDASHBOARDPANELMETRICTASK_QUERY._serialized_start=1416
  _GRAFANA_QUERYDASHBOARDPANELMETRICTASK_QUERY._serialized_end=1467
  _GRAFANA_TASKTYPE._serialized_start=1470
  _GRAFANA_TASKTYPE._serialized_end=1600
# @@protoc_insertion_point(module_scope)
