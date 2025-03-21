# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/playbooks/source_task_definitions/open_search_task.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n?protos/playbooks/source_task_definitions/open_search_task.proto\x12\x10protos.playbooks\x1a\x1egoogle/protobuf/wrappers.proto\"\xc5\x06\n\nOpenSearch\x12\x33\n\x04type\x18\x01 \x01(\x0e\x32%.protos.playbooks.OpenSearch.TaskType\x12<\n\nquery_logs\x18\x65 \x01(\x0b\x32&.protos.playbooks.OpenSearch.QueryLogsH\x00\x12@\n\x0c\x64\x65lete_index\x18\x66 \x01(\x0b\x32(.protos.playbooks.OpenSearch.DeleteIndexH\x00\x12\x43\n\x0eget_node_stats\x18g \x01(\x0b\x32).protos.playbooks.OpenSearch.GetNodeStatsH\x00\x12\x45\n\x0fget_index_stats\x18h \x01(\x0b\x32*.protos.playbooks.OpenSearch.GetIndexStatsH\x00\x1a\xac\x02\n\tQueryLogs\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tquery_dsl\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12+\n\x05limit\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12,\n\x06offset\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12/\n\tsort_desc\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0ftimestamp_field\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a:\n\x0b\x44\x65leteIndex\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\x0e\n\x0cGetNodeStats\x1a\x0f\n\rGetIndexStats\"b\n\x08TaskType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0e\n\nQUERY_LOGS\x10\x01\x12\x10\n\x0c\x44\x45LETE_INDEX\x10\x02\x12\x12\n\x0eGET_NODE_STATS\x10\x03\x12\x13\n\x0fGET_INDEX_STATS\x10\x04\x42\x06\n\x04taskb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.playbooks.source_task_definitions.open_search_task_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _OPENSEARCH._serialized_start=118
  _OPENSEARCH._serialized_end=955
  _OPENSEARCH_QUERYLOGS._serialized_start=454
  _OPENSEARCH_QUERYLOGS._serialized_end=754
  _OPENSEARCH_DELETEINDEX._serialized_start=756
  _OPENSEARCH_DELETEINDEX._serialized_end=814
  _OPENSEARCH_GETNODESTATS._serialized_start=816
  _OPENSEARCH_GETNODESTATS._serialized_end=830
  _OPENSEARCH_GETINDEXSTATS._serialized_start=832
  _OPENSEARCH_GETINDEXSTATS._serialized_end=847
  _OPENSEARCH_TASKTYPE._serialized_start=849
  _OPENSEARCH_TASKTYPE._serialized_end=947
# @@protoc_insertion_point(module_scope)
