"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.message
import google.protobuf.wrappers_pb2
import protos.base_pb2
import protos.connectors.connector_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class FetchAssetRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    META_FIELD_NUMBER: builtins.int
    CONNECTOR_FIELD_NUMBER: builtins.int
    @property
    def meta(self) -> protos.base_pb2.Meta: ...
    @property
    def connector(self) -> protos.connectors.connector_pb2.Connector: ...
    def __init__(
        self,
        *,
        meta: protos.base_pb2.Meta | None = ...,
        connector: protos.connectors.connector_pb2.Connector | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["connector", b"connector", "meta", b"meta"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["connector", b"connector", "meta", b"meta"]) -> None: ...

global___FetchAssetRequest = FetchAssetRequest

@typing_extensions.final
class FetchAssetResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    META_FIELD_NUMBER: builtins.int
    SUCCESS_FIELD_NUMBER: builtins.int
    MESSAGE_FIELD_NUMBER: builtins.int
    REQUEST_ID_FIELD_NUMBER: builtins.int
    @property
    def meta(self) -> protos.base_pb2.Meta: ...
    @property
    def success(self) -> google.protobuf.wrappers_pb2.BoolValue: ...
    @property
    def message(self) -> protos.base_pb2.Message: ...
    @property
    def request_id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    def __init__(
        self,
        *,
        meta: protos.base_pb2.Meta | None = ...,
        success: google.protobuf.wrappers_pb2.BoolValue | None = ...,
        message: protos.base_pb2.Message | None = ...,
        request_id: google.protobuf.wrappers_pb2.StringValue | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["message", b"message", "meta", b"meta", "request_id", b"request_id", "success", b"success"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["message", b"message", "meta", b"meta", "request_id", b"request_id", "success", b"success"]) -> None: ...

global___FetchAssetResponse = FetchAssetResponse
