# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/open_search_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%protos/assets/open_search_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"H\n\x19OpenSearchIndexAssetModel\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\".\n\x1bOpenSearchIndexAssetOptions\x12\x0f\n\x07indexes\x18\x01 \x03(\t\"\xf9\x01\n\x14OpenSearchAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12I\n\x11open_search_index\x18\x05 \x01(\x0b\x32,.protos.connectors.OpenSearchIndexAssetModelH\x00\x42\x07\n\x05\x61sset\"K\n\x10OpenSearchAssets\x12\x37\n\x06\x61ssets\x18\x01 \x03(\x0b\x32\'.protos.connectors.OpenSearchAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.open_search_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _OPENSEARCHINDEXASSETMODEL._serialized_start=111
  _OPENSEARCHINDEXASSETMODEL._serialized_end=183
  _OPENSEARCHINDEXASSETOPTIONS._serialized_start=185
  _OPENSEARCHINDEXASSETOPTIONS._serialized_end=231
  _OPENSEARCHASSETMODEL._serialized_start=234
  _OPENSEARCHASSETMODEL._serialized_end=483
  _OPENSEARCHASSETS._serialized_start=485
  _OPENSEARCHASSETS._serialized_end=560
# @@protoc_insertion_point(module_scope)