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
class Sentry(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _TaskType:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _TaskTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[Sentry._TaskType.ValueType], builtins.type):  # noqa: F821
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNKNOWN: Sentry._TaskType.ValueType  # 0
        FETCH_ISSUE_INFO_BY_ID: Sentry._TaskType.ValueType  # 1
        FETCH_PROJECT_EVENTS: Sentry._TaskType.ValueType  # 2
        FETCH_RECENT_ERRORS: Sentry._TaskType.ValueType  # 3
        FETCH_EVENT_INFO_BY_ID: Sentry._TaskType.ValueType  # 4
        FETCH_LIST_OF_RECENT_EVENTS_WITH_SEARCH_QUERY: Sentry._TaskType.ValueType  # 5

    class TaskType(_TaskType, metaclass=_TaskTypeEnumTypeWrapper): ...
    UNKNOWN: Sentry.TaskType.ValueType  # 0
    FETCH_ISSUE_INFO_BY_ID: Sentry.TaskType.ValueType  # 1
    FETCH_PROJECT_EVENTS: Sentry.TaskType.ValueType  # 2
    FETCH_RECENT_ERRORS: Sentry.TaskType.ValueType  # 3
    FETCH_EVENT_INFO_BY_ID: Sentry.TaskType.ValueType  # 4
    FETCH_LIST_OF_RECENT_EVENTS_WITH_SEARCH_QUERY: Sentry.TaskType.ValueType  # 5

    @typing_extensions.final
    class FetchIssueInfoById(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        ISSUE_ID_FIELD_NUMBER: builtins.int
        @property
        def issue_id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            issue_id: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["issue_id", b"issue_id"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["issue_id", b"issue_id"]) -> None: ...

    @typing_extensions.final
    class FetchProjectEvents(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        PROJECT_SLUG_FIELD_NUMBER: builtins.int
        @property
        def project_slug(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            project_slug: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["project_slug", b"project_slug"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["project_slug", b"project_slug"]) -> None: ...

    @typing_extensions.final
    class FetchRecentErrors(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        PROJECT_SLUG_FIELD_NUMBER: builtins.int
        @property
        def project_slug(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            project_slug: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["project_slug", b"project_slug"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["project_slug", b"project_slug"]) -> None: ...

    @typing_extensions.final
    class FetchEventInfoById(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        EVENT_ID_FIELD_NUMBER: builtins.int
        PROJECT_SLUG_FIELD_NUMBER: builtins.int
        @property
        def event_id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def project_slug(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            event_id: google.protobuf.wrappers_pb2.StringValue | None = ...,
            project_slug: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["event_id", b"event_id", "project_slug", b"project_slug"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["event_id", b"event_id", "project_slug", b"project_slug"]) -> None: ...

    @typing_extensions.final
    class FetchListOfRecentEventsWithSearchQuery(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        PROJECT_SLUG_FIELD_NUMBER: builtins.int
        QUERY_FIELD_NUMBER: builtins.int
        MAX_EVENTS_TO_ANALYSE_FIELD_NUMBER: builtins.int
        @property
        def project_slug(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def query(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def max_events_to_analyse(self) -> google.protobuf.wrappers_pb2.Int64Value: ...
        def __init__(
            self,
            *,
            project_slug: google.protobuf.wrappers_pb2.StringValue | None = ...,
            query: google.protobuf.wrappers_pb2.StringValue | None = ...,
            max_events_to_analyse: google.protobuf.wrappers_pb2.Int64Value | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["max_events_to_analyse", b"max_events_to_analyse", "project_slug", b"project_slug", "query", b"query"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["max_events_to_analyse", b"max_events_to_analyse", "project_slug", b"project_slug", "query", b"query"]) -> None: ...

    TYPE_FIELD_NUMBER: builtins.int
    FETCH_ISSUE_INFO_BY_ID_FIELD_NUMBER: builtins.int
    FETCH_PROJECT_EVENTS_FIELD_NUMBER: builtins.int
    FETCH_RECENT_ERRORS_FIELD_NUMBER: builtins.int
    FETCH_EVENT_INFO_BY_ID_FIELD_NUMBER: builtins.int
    FETCH_LIST_OF_RECENT_EVENTS_WITH_SEARCH_QUERY_FIELD_NUMBER: builtins.int
    type: global___Sentry.TaskType.ValueType
    @property
    def fetch_issue_info_by_id(self) -> global___Sentry.FetchIssueInfoById: ...
    @property
    def fetch_project_events(self) -> global___Sentry.FetchProjectEvents: ...
    @property
    def fetch_recent_errors(self) -> global___Sentry.FetchRecentErrors: ...
    @property
    def fetch_event_info_by_id(self) -> global___Sentry.FetchEventInfoById: ...
    @property
    def fetch_list_of_recent_events_with_search_query(self) -> global___Sentry.FetchListOfRecentEventsWithSearchQuery: ...
    def __init__(
        self,
        *,
        type: global___Sentry.TaskType.ValueType = ...,
        fetch_issue_info_by_id: global___Sentry.FetchIssueInfoById | None = ...,
        fetch_project_events: global___Sentry.FetchProjectEvents | None = ...,
        fetch_recent_errors: global___Sentry.FetchRecentErrors | None = ...,
        fetch_event_info_by_id: global___Sentry.FetchEventInfoById | None = ...,
        fetch_list_of_recent_events_with_search_query: global___Sentry.FetchListOfRecentEventsWithSearchQuery | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["fetch_event_info_by_id", b"fetch_event_info_by_id", "fetch_issue_info_by_id", b"fetch_issue_info_by_id", "fetch_list_of_recent_events_with_search_query", b"fetch_list_of_recent_events_with_search_query", "fetch_project_events", b"fetch_project_events", "fetch_recent_errors", b"fetch_recent_errors", "task", b"task"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["fetch_event_info_by_id", b"fetch_event_info_by_id", "fetch_issue_info_by_id", b"fetch_issue_info_by_id", "fetch_list_of_recent_events_with_search_query", b"fetch_list_of_recent_events_with_search_query", "fetch_project_events", b"fetch_project_events", "fetch_recent_errors", b"fetch_recent_errors", "task", b"task", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["task", b"task"]) -> typing_extensions.Literal["fetch_issue_info_by_id", "fetch_project_events", "fetch_recent_errors", "fetch_event_info_by_id", "fetch_list_of_recent_events_with_search_query"] | None: ...

global___Sentry = Sentry
