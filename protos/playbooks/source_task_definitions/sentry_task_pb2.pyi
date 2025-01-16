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
        FETCH_ISSUE_INFO: Sentry._TaskType.ValueType  # 1
        FETCH_PROJECT_EVENTS: Sentry._TaskType.ValueType  # 2
        FETCH_RECENT_ERRORS: Sentry._TaskType.ValueType  # 3

    class TaskType(_TaskType, metaclass=_TaskTypeEnumTypeWrapper): ...
    UNKNOWN: Sentry.TaskType.ValueType  # 0
    FETCH_ISSUE_INFO: Sentry.TaskType.ValueType  # 1
    FETCH_PROJECT_EVENTS: Sentry.TaskType.ValueType  # 2
    FETCH_RECENT_ERRORS: Sentry.TaskType.ValueType  # 3

    @typing_extensions.final
    class FetchIssueInfo(google.protobuf.message.Message):
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

    TYPE_FIELD_NUMBER: builtins.int
    FETCH_ISSUE_INFO_FIELD_NUMBER: builtins.int
    FETCH_PROJECT_EVENTS_FIELD_NUMBER: builtins.int
    FETCH_RECENT_ERRORS_FIELD_NUMBER: builtins.int
    type: global___Sentry.TaskType.ValueType
    @property
    def fetch_issue_info(self) -> global___Sentry.FetchIssueInfo: ...
    @property
    def fetch_project_events(self) -> global___Sentry.FetchProjectEvents: ...
    @property
    def fetch_recent_errors(self) -> global___Sentry.FetchRecentErrors: ...
    def __init__(
        self,
        *,
        type: global___Sentry.TaskType.ValueType = ...,
        fetch_issue_info: global___Sentry.FetchIssueInfo | None = ...,
        fetch_project_events: global___Sentry.FetchProjectEvents | None = ...,
        fetch_recent_errors: global___Sentry.FetchRecentErrors | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["fetch_issue_info", b"fetch_issue_info", "fetch_project_events", b"fetch_project_events", "fetch_recent_errors", b"fetch_recent_errors", "task", b"task"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["fetch_issue_info", b"fetch_issue_info", "fetch_project_events", b"fetch_project_events", "fetch_recent_errors", b"fetch_recent_errors", "task", b"task", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["task", b"task"]) -> typing_extensions.Literal["fetch_issue_info", "fetch_project_events", "fetch_recent_errors"] | None: ...

global___Sentry = Sentry
