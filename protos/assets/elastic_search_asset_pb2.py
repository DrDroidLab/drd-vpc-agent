# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/elastic_search_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(protos/assets/elastic_search_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"K\n\x1c\x45lasticSearchIndexAssetModel\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"1\n\x1e\x45lasticSearchIndexAssetOptions\x12\x0f\n\x07indexes\x18\x01 \x03(\t\"\x82\x02\n\x17\x45lasticSearchAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12O\n\x14\x65lastic_search_index\x18\x05 \x01(\x0b\x32/.protos.connectors.ElasticSearchIndexAssetModelH\x00\x42\x07\n\x05\x61sset\"Q\n\x13\x45lasticSearchAssets\x12:\n\x06\x61ssets\x18\x01 \x03(\x0b\x32*.protos.connectors.ElasticSearchAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.elastic_search_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ELASTICSEARCHINDEXASSETMODEL._serialized_start=114
  _ELASTICSEARCHINDEXASSETMODEL._serialized_end=189
  _ELASTICSEARCHINDEXASSETOPTIONS._serialized_start=191
  _ELASTICSEARCHINDEXASSETOPTIONS._serialized_end=240
  _ELASTICSEARCHASSETMODEL._serialized_start=243
  _ELASTICSEARCHASSETMODEL._serialized_end=501
  _ELASTICSEARCHASSETS._serialized_start=503
  _ELASTICSEARCHASSETS._serialized_end=584
# @@protoc_insertion_point(module_scope)
