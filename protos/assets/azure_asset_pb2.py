# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/azure_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fprotos/assets/azure_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\x1a\x1cgoogle/protobuf/struct.proto\"w\n\x18\x41zureWorkspaceAssetModel\x12/\n\tworkspace\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"]\n\x1a\x41zureWorkspaceAssetOptions\x12?\n\nworkspaces\x18\x01 \x03(\x0b\x32+.protos.connectors.AzureWorkspaceAssetModel\"(\n\x10\x41vailableMetrics\x12\x14\n\x0cmetric_names\x18\x01 \x03(\t\"\x94\x02\n\x17\x41zureResourceAssetModel\x12\x31\n\x0bresource_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04type\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08location\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12>\n\x11\x61vailable_metrics\x18\x05 \x01(\x0b\x32#.protos.connectors.AvailableMetrics\"Z\n\x19\x41zureResourceAssetOptions\x12=\n\tresources\x18\x01 \x03(\x0b\x32*.protos.connectors.AzureResourceAssetModel\"\xb7\x02\n\x0f\x41zureAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12\x46\n\x0f\x61zure_workspace\x18\x05 \x01(\x0b\x32+.protos.connectors.AzureWorkspaceAssetModelH\x00\x12\x44\n\x0e\x61zure_resource\x18\x06 \x01(\x0b\x32*.protos.connectors.AzureResourceAssetModelH\x00\x42\x07\n\x05\x61sset\"A\n\x0b\x41zureAssets\x12\x32\n\x06\x61ssets\x18\x01 \x03(\x0b\x32\".protos.connectors.AzureAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.azure_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _AZUREWORKSPACEASSETMODEL._serialized_start=135
  _AZUREWORKSPACEASSETMODEL._serialized_end=254
  _AZUREWORKSPACEASSETOPTIONS._serialized_start=256
  _AZUREWORKSPACEASSETOPTIONS._serialized_end=349
  _AVAILABLEMETRICS._serialized_start=351
  _AVAILABLEMETRICS._serialized_end=391
  _AZURERESOURCEASSETMODEL._serialized_start=394
  _AZURERESOURCEASSETMODEL._serialized_end=670
  _AZURERESOURCEASSETOPTIONS._serialized_start=672
  _AZURERESOURCEASSETOPTIONS._serialized_end=762
  _AZUREASSETMODEL._serialized_start=765
  _AZUREASSETMODEL._serialized_end=1076
  _AZUREASSETS._serialized_start=1078
  _AZUREASSETS._serialized_end=1143
# @@protoc_insertion_point(module_scope)
