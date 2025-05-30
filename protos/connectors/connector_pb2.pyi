"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.wrappers_pb2
import protos.base_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class Connector(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ACCOUNT_ID_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    KEYS_FIELD_NUMBER: builtins.int
    ID_FIELD_NUMBER: builtins.int
    @property
    def account_id(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    type: protos.base_pb2.Source.ValueType
    @property
    def name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def keys(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ConnectorKey]: ...
    @property
    def id(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    def __init__(
        self,
        *,
        account_id: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
        type: protos.base_pb2.Source.ValueType = ...,
        name: google.protobuf.wrappers_pb2.StringValue | None = ...,
        keys: collections.abc.Iterable[global___ConnectorKey] | None = ...,
        id: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["account_id", b"account_id", "id", b"id", "name", b"name"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["account_id", b"account_id", "id", b"id", "keys", b"keys", "name", b"name", "type", b"type"]) -> None: ...

global___Connector = Connector

@typing_extensions.final
class ConnectorKey(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_TYPE_FIELD_NUMBER: builtins.int
    KEY_FIELD_NUMBER: builtins.int
    CONNECTOR_NAME_FIELD_NUMBER: builtins.int
    key_type: protos.base_pb2.SourceKeyType.ValueType
    @property
    def key(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def connector_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    def __init__(
        self,
        *,
        key_type: protos.base_pb2.SourceKeyType.ValueType = ...,
        key: google.protobuf.wrappers_pb2.StringValue | None = ...,
        connector_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["connector_name", b"connector_name", "key", b"key"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["connector_name", b"connector_name", "key", b"key", "key_type", b"key_type"]) -> None: ...

global___ConnectorKey = ConnectorKey
