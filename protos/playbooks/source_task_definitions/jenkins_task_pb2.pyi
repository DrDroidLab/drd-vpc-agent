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
class Jenkins(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _TaskType:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _TaskTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[Jenkins._TaskType.ValueType], builtins.type):  # noqa: F821
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNKNOWN: Jenkins._TaskType.ValueType  # 0
        FETCH_LAST_BUILD_DETAILS: Jenkins._TaskType.ValueType  # 1

    class TaskType(_TaskType, metaclass=_TaskTypeEnumTypeWrapper): ...
    UNKNOWN: Jenkins.TaskType.ValueType  # 0
    FETCH_LAST_BUILD_DETAILS: Jenkins.TaskType.ValueType  # 1

    @typing_extensions.final
    class LastBuildDetails(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        JOB_NAME_FIELD_NUMBER: builtins.int
        @property
        def job_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            job_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["job_name", b"job_name"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["job_name", b"job_name"]) -> None: ...

    TYPE_FIELD_NUMBER: builtins.int
    FETCH_LAST_BUILD_DETAILS_FIELD_NUMBER: builtins.int
    type: global___Jenkins.TaskType.ValueType
    @property
    def fetch_last_build_details(self) -> global___Jenkins.LastBuildDetails: ...
    def __init__(
        self,
        *,
        type: global___Jenkins.TaskType.ValueType = ...,
        fetch_last_build_details: global___Jenkins.LastBuildDetails | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["fetch_last_build_details", b"fetch_last_build_details", "task", b"task"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["fetch_last_build_details", b"fetch_last_build_details", "task", b"task", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["task", b"task"]) -> typing_extensions.Literal["fetch_last_build_details"] | None: ...

global___Jenkins = Jenkins
