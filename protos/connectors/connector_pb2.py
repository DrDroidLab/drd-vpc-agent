# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/connectors/connector.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!protos/connectors/connector.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xe0\x01\n\tConnector\x12\x30\n\naccount_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x1c\n\x04type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12*\n\x04name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12-\n\x04keys\x18\x04 \x03(\x0b\x32\x1f.protos.connectors.ConnectorKey\x12(\n\x02id\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\"\x98\x01\n\x0c\x43onnectorKey\x12\'\n\x08key_type\x18\x01 \x01(\x0e\x32\x15.protos.SourceKeyType\x12)\n\x03key\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x63onnector_name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValueb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.connectors.connector_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CONNECTOR._serialized_start=108
  _CONNECTOR._serialized_end=332
  _CONNECTORKEY._serialized_start=335
  _CONNECTORKEY._serialized_end=487
# @@protoc_insertion_point(module_scope)
