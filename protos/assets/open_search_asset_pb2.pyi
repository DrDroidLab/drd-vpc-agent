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
class OpenSearchIndexAssetModel(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    INDEX_FIELD_NUMBER: builtins.int
    @property
    def index(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    def __init__(
        self,
        *,
        index: google.protobuf.wrappers_pb2.StringValue | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["index", b"index"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["index", b"index"]) -> None: ...

global___OpenSearchIndexAssetModel = OpenSearchIndexAssetModel

@typing_extensions.final
class OpenSearchIndexAssetOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    INDEXES_FIELD_NUMBER: builtins.int
    @property
    def indexes(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        indexes: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["indexes", b"indexes"]) -> None: ...

global___OpenSearchIndexAssetOptions = OpenSearchIndexAssetOptions

@typing_extensions.final
class OpenSearchAssetModel(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ID_FIELD_NUMBER: builtins.int
    CONNECTOR_TYPE_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    LAST_UPDATED_FIELD_NUMBER: builtins.int
    OPEN_SEARCH_INDEX_FIELD_NUMBER: builtins.int
    @property
    def id(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    connector_type: protos.base_pb2.Source.ValueType
    type: protos.base_pb2.SourceModelType.ValueType
    last_updated: builtins.int
    @property
    def open_search_index(self) -> global___OpenSearchIndexAssetModel: ...
    def __init__(
        self,
        *,
        id: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
        connector_type: protos.base_pb2.Source.ValueType = ...,
        type: protos.base_pb2.SourceModelType.ValueType = ...,
        last_updated: builtins.int = ...,
        open_search_index: global___OpenSearchIndexAssetModel | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["asset", b"asset", "id", b"id", "open_search_index", b"open_search_index"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset", b"asset", "connector_type", b"connector_type", "id", b"id", "last_updated", b"last_updated", "open_search_index", b"open_search_index", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["asset", b"asset"]) -> typing_extensions.Literal["open_search_index"] | None: ...

global___OpenSearchAssetModel = OpenSearchAssetModel

@typing_extensions.final
class OpenSearchAssets(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ASSETS_FIELD_NUMBER: builtins.int
    @property
    def assets(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___OpenSearchAssetModel]: ...
    def __init__(
        self,
        *,
        assets: collections.abc.Iterable[global___OpenSearchAssetModel] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["assets", b"assets"]) -> None: ...

global___OpenSearchAssets = OpenSearchAssets
