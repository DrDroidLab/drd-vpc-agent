# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/accounts/account.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dprotos/accounts/account.proto\x12\x0fprotos.accounts\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1egoogle/protobuf/wrappers.proto\"v\n\x0f\x41\x63\x63ountApiToken\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x12\n\ncreated_by\x18\x02 \x01(\t\x12.\n\ncreated_at\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x12\n\naccount_id\x18\x04 \x01(\x04\"x\n\tUserFlags\x12\x35\n\x11is_email_verified\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x34\n\x10is_account_owner\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.BoolValue\"x\n\x04User\x12\n\n\x02id\x18\x01 \x01(\x04\x12\r\n\x05\x65mail\x18\x02 \x01(\t\x12\x12\n\nfirst_name\x18\x03 \x01(\t\x12\x11\n\tlast_name\x18\x04 \x01(\t\x12.\n\nuser_flags\x18\x05 \x01(\x0b\x32\x1a.protos.accounts.UserFlags*$\n\x0bSSOProvider\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x08\n\x04OKTA\x10\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.accounts.account_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SSOPROVIDER._serialized_start=479
  _SSOPROVIDER._serialized_end=515
  _ACCOUNTAPITOKEN._serialized_start=115
  _ACCOUNTAPITOKEN._serialized_end=233
  _USERFLAGS._serialized_start=235
  _USERFLAGS._serialized_end=355
  _USER._serialized_start=357
  _USER._serialized_end=477
# @@protoc_insertion_point(module_scope)
