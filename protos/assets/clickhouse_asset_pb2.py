# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/clickhouse_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$protos/assets/clickhouse_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"N\n\x1c\x43lickhouseDatabaseAssetModel\x12.\n\x08\x64\x61tabase\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"3\n\x1e\x43lickhouseDatabaseAssetOptions\x12\x11\n\tdatabases\x18\x01 \x03(\t\"\x8d\x02\n\x15\x43lickhouseColumnModel\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tdata_type\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\x0bis_nullable\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x33\n\rdefault_value\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0b\x64\x65scription\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xca\x02\n\x19\x43lickhouseTableAssetModel\x12\x30\n\ntable_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x33\n\rdatabase_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12,\n\x06\x65ngine\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0b\x64\x65scription\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12*\n\x04size\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x39\n\x07\x63olumns\x18\x06 \x03(\x0b\x32(.protos.connectors.ClickhouseColumnModel\"@\n\x1b\x43lickhouseTableAssetOptions\x12\x0e\n\x06tables\x18\x01 \x03(\t\x12\x11\n\tdatabases\x18\x02 \x03(\t\"\xc8\x02\n\x14\x43lickhouseAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12N\n\x13\x63lickhouse_database\x18\x05 \x01(\x0b\x32/.protos.connectors.ClickhouseDatabaseAssetModelH\x00\x12H\n\x10\x63lickhouse_table\x18\x06 \x01(\x0b\x32,.protos.connectors.ClickhouseTableAssetModelH\x00\x42\x07\n\x05\x61sset\"K\n\x10\x43lickhouseAssets\x12\x37\n\x06\x61ssets\x18\x01 \x03(\x0b\x32\'.protos.connectors.ClickhouseAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.clickhouse_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLICKHOUSEDATABASEASSETMODEL._serialized_start=110
  _CLICKHOUSEDATABASEASSETMODEL._serialized_end=188
  _CLICKHOUSEDATABASEASSETOPTIONS._serialized_start=190
  _CLICKHOUSEDATABASEASSETOPTIONS._serialized_end=241
  _CLICKHOUSECOLUMNMODEL._serialized_start=244
  _CLICKHOUSECOLUMNMODEL._serialized_end=513
  _CLICKHOUSETABLEASSETMODEL._serialized_start=516
  _CLICKHOUSETABLEASSETMODEL._serialized_end=846
  _CLICKHOUSETABLEASSETOPTIONS._serialized_start=848
  _CLICKHOUSETABLEASSETOPTIONS._serialized_end=912
  _CLICKHOUSEASSETMODEL._serialized_start=915
  _CLICKHOUSEASSETMODEL._serialized_end=1243
  _CLICKHOUSEASSETS._serialized_start=1245
  _CLICKHOUSEASSETS._serialized_end=1320
# @@protoc_insertion_point(module_scope)
