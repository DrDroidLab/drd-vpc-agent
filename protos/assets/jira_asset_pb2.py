# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/jira_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1eprotos/assets/jira_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xaa\x01\n\x12JiraUserAssetModel\x12\x30\n\naccount_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0c\x64isplay_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08self_url\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"-\n\x14JiraUserAssetOptions\x12\x15\n\rdisplay_names\x18\x01 \x03(\t\"\xc8\x01\n\x15JiraProjectAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12)\n\x03key\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08self_url\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"(\n\x17JiraProjectAssetOptions\x12\r\n\x05names\x18\x02 \x03(\t\"\xa6\x02\n\x0eJiraAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12@\n\x0cjira_project\x18\x65 \x01(\x0b\x32(.protos.connectors.JiraProjectAssetModelH\x00\x12:\n\tjira_user\x18\x66 \x01(\x0b\x32%.protos.connectors.JiraUserAssetModelH\x00\x42\x07\n\x05\x61sset\"?\n\nJiraAssets\x12\x31\n\x06\x61ssets\x18\x01 \x03(\x0b\x32!.protos.connectors.JiraAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.jira_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _JIRAUSERASSETMODEL._serialized_start=105
  _JIRAUSERASSETMODEL._serialized_end=275
  _JIRAUSERASSETOPTIONS._serialized_start=277
  _JIRAUSERASSETOPTIONS._serialized_end=322
  _JIRAPROJECTASSETMODEL._serialized_start=325
  _JIRAPROJECTASSETMODEL._serialized_end=525
  _JIRAPROJECTASSETOPTIONS._serialized_start=527
  _JIRAPROJECTASSETOPTIONS._serialized_end=567
  _JIRAASSETMODEL._serialized_start=570
  _JIRAASSETMODEL._serialized_end=864
  _JIRAASSETS._serialized_start=866
  _JIRAASSETS._serialized_end=929
# @@protoc_insertion_point(module_scope)
