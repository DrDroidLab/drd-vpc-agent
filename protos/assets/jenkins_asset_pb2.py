# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/jenkins_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!protos/assets/jenkins_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\x11protos/base.proto\"\'\n\x17JenkinsAppsAssetOptions\x12\x0c\n\x04\x61pps\x18\x01 \x03(\t\"u\n\x15JenkinsAppsAssetModel\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x30\n\nclass_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xed\x01\n\x11JenkinsAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12@\n\x0cjenkins_apps\x18\x65 \x01(\x0b\x32(.protos.connectors.JenkinsAppsAssetModelH\x00\x42\x07\n\x05\x61sset\"E\n\rJenkinsAssets\x12\x34\n\x06\x61ssets\x18\x01 \x03(\x0b\x32$.protos.connectors.JenkinsAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.jenkins_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _JENKINSAPPSASSETOPTIONS._serialized_start=137
  _JENKINSAPPSASSETOPTIONS._serialized_end=176
  _JENKINSAPPSASSETMODEL._serialized_start=178
  _JENKINSAPPSASSETMODEL._serialized_end=295
  _JENKINSASSETMODEL._serialized_start=298
  _JENKINSASSETMODEL._serialized_end=535
  _JENKINSASSETS._serialized_start=537
  _JENKINSASSETS._serialized_end=606
# @@protoc_insertion_point(module_scope)
