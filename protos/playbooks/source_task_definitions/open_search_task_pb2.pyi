"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.wrappers_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class OpenSearch(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _TaskType:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _TaskTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[OpenSearch._TaskType.ValueType], builtins.type):  # noqa: F821
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNKNOWN: OpenSearch._TaskType.ValueType  # 0
        QUERY_LOGS: OpenSearch._TaskType.ValueType  # 1
        DELETE_INDEX: OpenSearch._TaskType.ValueType  # 2
        GET_NODE_STATS: OpenSearch._TaskType.ValueType  # 3
        GET_INDEX_STATS: OpenSearch._TaskType.ValueType  # 4
        GET_CLUSTER_HEALTH: OpenSearch._TaskType.ValueType  # 5
        GET_CLUSTER_SETTINGS: OpenSearch._TaskType.ValueType  # 6
        GET_CLUSTER_STATS: OpenSearch._TaskType.ValueType  # 7
        GET_INDEX_AND_SHARD_RECOVERIES: OpenSearch._TaskType.ValueType  # 8
        GET_INDICES: OpenSearch._TaskType.ValueType  # 9
        GET_PENDING_TASKS: OpenSearch._TaskType.ValueType  # 10
        GET_SHARDS: OpenSearch._TaskType.ValueType  # 11
        GET_TASKS: OpenSearch._TaskType.ValueType  # 12

    class TaskType(_TaskType, metaclass=_TaskTypeEnumTypeWrapper): ...
    UNKNOWN: OpenSearch.TaskType.ValueType  # 0
    QUERY_LOGS: OpenSearch.TaskType.ValueType  # 1
    DELETE_INDEX: OpenSearch.TaskType.ValueType  # 2
    GET_NODE_STATS: OpenSearch.TaskType.ValueType  # 3
    GET_INDEX_STATS: OpenSearch.TaskType.ValueType  # 4
    GET_CLUSTER_HEALTH: OpenSearch.TaskType.ValueType  # 5
    GET_CLUSTER_SETTINGS: OpenSearch.TaskType.ValueType  # 6
    GET_CLUSTER_STATS: OpenSearch.TaskType.ValueType  # 7
    GET_INDEX_AND_SHARD_RECOVERIES: OpenSearch.TaskType.ValueType  # 8
    GET_INDICES: OpenSearch.TaskType.ValueType  # 9
    GET_PENDING_TASKS: OpenSearch.TaskType.ValueType  # 10
    GET_SHARDS: OpenSearch.TaskType.ValueType  # 11
    GET_TASKS: OpenSearch.TaskType.ValueType  # 12

    @typing_extensions.final
    class QueryLogs(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        INDEX_FIELD_NUMBER: builtins.int
        QUERY_DSL_FIELD_NUMBER: builtins.int
        LIMIT_FIELD_NUMBER: builtins.int
        OFFSET_FIELD_NUMBER: builtins.int
        SORT_DESC_FIELD_NUMBER: builtins.int
        TIMESTAMP_FIELD_FIELD_NUMBER: builtins.int
        @property
        def index(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def query_dsl(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def limit(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
        @property
        def offset(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
        @property
        def sort_desc(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timestamp_field(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            index: google.protobuf.wrappers_pb2.StringValue | None = ...,
            query_dsl: google.protobuf.wrappers_pb2.StringValue | None = ...,
            limit: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
            offset: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
            sort_desc: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timestamp_field: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["index", b"index", "limit", b"limit", "offset", b"offset", "query_dsl", b"query_dsl", "sort_desc", b"sort_desc", "timestamp_field", b"timestamp_field"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["index", b"index", "limit", b"limit", "offset", b"offset", "query_dsl", b"query_dsl", "sort_desc", b"sort_desc", "timestamp_field", b"timestamp_field"]) -> None: ...

    @typing_extensions.final
    class DeleteIndex(google.protobuf.message.Message):
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

    @typing_extensions.final
    class GetNodeStats(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetIndexStats(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetClusterHealth(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetClusterSettings(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetClusterStats(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetIndexAndShardRecoveries(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetIndices(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetPendingTasks(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetShards(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    @typing_extensions.final
    class GetTasks(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        def __init__(
            self,
        ) -> None: ...

    TYPE_FIELD_NUMBER: builtins.int
    QUERY_LOGS_FIELD_NUMBER: builtins.int
    DELETE_INDEX_FIELD_NUMBER: builtins.int
    GET_NODE_STATS_FIELD_NUMBER: builtins.int
    GET_INDEX_STATS_FIELD_NUMBER: builtins.int
    GET_CLUSTER_HEALTH_FIELD_NUMBER: builtins.int
    GET_CLUSTER_SETTINGS_FIELD_NUMBER: builtins.int
    GET_CLUSTER_STATS_FIELD_NUMBER: builtins.int
    GET_INDEX_AND_SHARD_RECOVERIES_FIELD_NUMBER: builtins.int
    GET_INDICES_FIELD_NUMBER: builtins.int
    GET_PENDING_TASKS_FIELD_NUMBER: builtins.int
    GET_SHARDS_FIELD_NUMBER: builtins.int
    GET_TASKS_FIELD_NUMBER: builtins.int
    type: global___OpenSearch.TaskType.ValueType
    @property
    def query_logs(self) -> global___OpenSearch.QueryLogs: ...
    @property
    def delete_index(self) -> global___OpenSearch.DeleteIndex: ...
    @property
    def get_node_stats(self) -> global___OpenSearch.GetNodeStats: ...
    @property
    def get_index_stats(self) -> global___OpenSearch.GetIndexStats: ...
    @property
    def get_cluster_health(self) -> global___OpenSearch.GetClusterHealth: ...
    @property
    def get_cluster_settings(self) -> global___OpenSearch.GetClusterSettings: ...
    @property
    def get_cluster_stats(self) -> global___OpenSearch.GetClusterStats: ...
    @property
    def get_index_and_shard_recoveries(self) -> global___OpenSearch.GetIndexAndShardRecoveries: ...
    @property
    def get_indices(self) -> global___OpenSearch.GetIndices: ...
    @property
    def get_pending_tasks(self) -> global___OpenSearch.GetPendingTasks: ...
    @property
    def get_shards(self) -> global___OpenSearch.GetShards: ...
    @property
    def get_tasks(self) -> global___OpenSearch.GetTasks: ...
    def __init__(
        self,
        *,
        type: global___OpenSearch.TaskType.ValueType = ...,
        query_logs: global___OpenSearch.QueryLogs | None = ...,
        delete_index: global___OpenSearch.DeleteIndex | None = ...,
        get_node_stats: global___OpenSearch.GetNodeStats | None = ...,
        get_index_stats: global___OpenSearch.GetIndexStats | None = ...,
        get_cluster_health: global___OpenSearch.GetClusterHealth | None = ...,
        get_cluster_settings: global___OpenSearch.GetClusterSettings | None = ...,
        get_cluster_stats: global___OpenSearch.GetClusterStats | None = ...,
        get_index_and_shard_recoveries: global___OpenSearch.GetIndexAndShardRecoveries | None = ...,
        get_indices: global___OpenSearch.GetIndices | None = ...,
        get_pending_tasks: global___OpenSearch.GetPendingTasks | None = ...,
        get_shards: global___OpenSearch.GetShards | None = ...,
        get_tasks: global___OpenSearch.GetTasks | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["delete_index", b"delete_index", "get_cluster_health", b"get_cluster_health", "get_cluster_settings", b"get_cluster_settings", "get_cluster_stats", b"get_cluster_stats", "get_index_and_shard_recoveries", b"get_index_and_shard_recoveries", "get_index_stats", b"get_index_stats", "get_indices", b"get_indices", "get_node_stats", b"get_node_stats", "get_pending_tasks", b"get_pending_tasks", "get_shards", b"get_shards", "get_tasks", b"get_tasks", "query_logs", b"query_logs", "task", b"task"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["delete_index", b"delete_index", "get_cluster_health", b"get_cluster_health", "get_cluster_settings", b"get_cluster_settings", "get_cluster_stats", b"get_cluster_stats", "get_index_and_shard_recoveries", b"get_index_and_shard_recoveries", "get_index_stats", b"get_index_stats", "get_indices", b"get_indices", "get_node_stats", b"get_node_stats", "get_pending_tasks", b"get_pending_tasks", "get_shards", b"get_shards", "get_tasks", b"get_tasks", "query_logs", b"query_logs", "task", b"task", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["task", b"task"]) -> typing_extensions.Literal["query_logs", "delete_index", "get_node_stats", "get_index_stats", "get_cluster_health", "get_cluster_settings", "get_cluster_stats", "get_index_and_shard_recoveries", "get_indices", "get_pending_tasks", "get_shards", "get_tasks"] | None: ...

global___OpenSearch = OpenSearch
