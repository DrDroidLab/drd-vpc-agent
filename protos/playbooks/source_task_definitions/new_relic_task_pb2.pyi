"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
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
class NewRelic(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _TaskType:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _TaskTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[NewRelic._TaskType.ValueType], builtins.type):  # noqa: F821
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNKNOWN: NewRelic._TaskType.ValueType  # 0
        ENTITY_APPLICATION_GOLDEN_METRIC_EXECUTION: NewRelic._TaskType.ValueType  # 1
        ENTITY_DASHBOARD_WIDGET_NRQL_METRIC_EXECUTION: NewRelic._TaskType.ValueType  # 2
        NRQL_METRIC_EXECUTION: NewRelic._TaskType.ValueType  # 3
        DASHBOARD_MULTIPLE_WIDGETS: NewRelic._TaskType.ValueType  # 4
        ENTITY_APPLICATION_APM_METRIC_EXECUTION: NewRelic._TaskType.ValueType  # 5
        FETCH_DASHBOARD_WIDGETS: NewRelic._TaskType.ValueType  # 6

    class TaskType(_TaskType, metaclass=_TaskTypeEnumTypeWrapper): ...
    UNKNOWN: NewRelic.TaskType.ValueType  # 0
    ENTITY_APPLICATION_GOLDEN_METRIC_EXECUTION: NewRelic.TaskType.ValueType  # 1
    ENTITY_DASHBOARD_WIDGET_NRQL_METRIC_EXECUTION: NewRelic.TaskType.ValueType  # 2
    NRQL_METRIC_EXECUTION: NewRelic.TaskType.ValueType  # 3
    DASHBOARD_MULTIPLE_WIDGETS: NewRelic.TaskType.ValueType  # 4
    ENTITY_APPLICATION_APM_METRIC_EXECUTION: NewRelic.TaskType.ValueType  # 5
    FETCH_DASHBOARD_WIDGETS: NewRelic.TaskType.ValueType  # 6

    @typing_extensions.final
    class EntityApplicationGoldenMetricExecutionTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        APPLICATION_ENTITY_GUID_FIELD_NUMBER: builtins.int
        APPLICATION_ENTITY_NAME_FIELD_NUMBER: builtins.int
        GOLDEN_METRIC_NAME_FIELD_NUMBER: builtins.int
        GOLDEN_METRIC_UNIT_FIELD_NUMBER: builtins.int
        GOLDEN_METRIC_NRQL_EXPRESSION_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        @property
        def application_entity_guid(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def application_entity_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def golden_metric_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def golden_metric_unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def golden_metric_nrql_expression(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        def __init__(
            self,
            *,
            application_entity_guid: google.protobuf.wrappers_pb2.StringValue | None = ...,
            application_entity_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            golden_metric_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            golden_metric_unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            golden_metric_nrql_expression: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["application_entity_guid", b"application_entity_guid", "application_entity_name", b"application_entity_name", "golden_metric_name", b"golden_metric_name", "golden_metric_nrql_expression", b"golden_metric_nrql_expression", "golden_metric_unit", b"golden_metric_unit"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["application_entity_guid", b"application_entity_guid", "application_entity_name", b"application_entity_name", "golden_metric_name", b"golden_metric_name", "golden_metric_nrql_expression", b"golden_metric_nrql_expression", "golden_metric_unit", b"golden_metric_unit", "timeseries_offsets", b"timeseries_offsets"]) -> None: ...

    @typing_extensions.final
    class EntityApplicationAPMMetricExecutionTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        APPLICATION_ENTITY_GUID_FIELD_NUMBER: builtins.int
        APPLICATION_ENTITY_NAME_FIELD_NUMBER: builtins.int
        APM_METRIC_NAME_FIELD_NUMBER: builtins.int
        APM_METRIC_UNIT_FIELD_NUMBER: builtins.int
        APM_METRIC_NRQL_EXPRESSION_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        APM_METRIC_NAMES_FIELD_NUMBER: builtins.int
        @property
        def application_entity_guid(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def application_entity_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def apm_metric_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def apm_metric_unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def apm_metric_nrql_expression(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        @property
        def apm_metric_names(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            application_entity_guid: google.protobuf.wrappers_pb2.StringValue | None = ...,
            application_entity_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            apm_metric_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            apm_metric_unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            apm_metric_nrql_expression: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
            apm_metric_names: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["apm_metric_name", b"apm_metric_name", "apm_metric_names", b"apm_metric_names", "apm_metric_nrql_expression", b"apm_metric_nrql_expression", "apm_metric_unit", b"apm_metric_unit", "application_entity_guid", b"application_entity_guid", "application_entity_name", b"application_entity_name"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["apm_metric_name", b"apm_metric_name", "apm_metric_names", b"apm_metric_names", "apm_metric_nrql_expression", b"apm_metric_nrql_expression", "apm_metric_unit", b"apm_metric_unit", "application_entity_guid", b"application_entity_guid", "application_entity_name", b"application_entity_name", "timeseries_offsets", b"timeseries_offsets"]) -> None: ...

    @typing_extensions.final
    class EntityDashboardWidgetNRQLMetricExecutionTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        DASHBOARD_GUID_FIELD_NUMBER: builtins.int
        DASHBOARD_NAME_FIELD_NUMBER: builtins.int
        PAGE_GUID_FIELD_NUMBER: builtins.int
        PAGE_NAME_FIELD_NUMBER: builtins.int
        WIDGET_ID_FIELD_NUMBER: builtins.int
        WIDGET_TITLE_FIELD_NUMBER: builtins.int
        WIDGET_TYPE_FIELD_NUMBER: builtins.int
        WIDGET_NRQL_EXPRESSION_FIELD_NUMBER: builtins.int
        UNIT_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        @property
        def dashboard_guid(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def dashboard_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def page_guid(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def page_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_title(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_type(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_nrql_expression(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        def __init__(
            self,
            *,
            dashboard_guid: google.protobuf.wrappers_pb2.StringValue | None = ...,
            dashboard_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            page_guid: google.protobuf.wrappers_pb2.StringValue | None = ...,
            page_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_id: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_title: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_type: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_nrql_expression: google.protobuf.wrappers_pb2.StringValue | None = ...,
            unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["dashboard_guid", b"dashboard_guid", "dashboard_name", b"dashboard_name", "page_guid", b"page_guid", "page_name", b"page_name", "unit", b"unit", "widget_id", b"widget_id", "widget_nrql_expression", b"widget_nrql_expression", "widget_title", b"widget_title", "widget_type", b"widget_type"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["dashboard_guid", b"dashboard_guid", "dashboard_name", b"dashboard_name", "page_guid", b"page_guid", "page_name", b"page_name", "timeseries_offsets", b"timeseries_offsets", "unit", b"unit", "widget_id", b"widget_id", "widget_nrql_expression", b"widget_nrql_expression", "widget_title", b"widget_title", "widget_type", b"widget_type"]) -> None: ...

    @typing_extensions.final
    class DashboardWidgetByIdTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        DASHBOARD_NAME_FIELD_NUMBER: builtins.int
        WIDGET_ID_FIELD_NUMBER: builtins.int
        UNIT_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        @property
        def dashboard_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        def __init__(
            self,
            *,
            dashboard_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_id: google.protobuf.wrappers_pb2.StringValue | None = ...,
            unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["dashboard_name", b"dashboard_name", "unit", b"unit", "widget_id", b"widget_id"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["dashboard_name", b"dashboard_name", "timeseries_offsets", b"timeseries_offsets", "unit", b"unit", "widget_id", b"widget_id"]) -> None: ...

    @typing_extensions.final
    class NRQLMetricExecutionTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        METRIC_NAME_FIELD_NUMBER: builtins.int
        NRQL_EXPRESSION_FIELD_NUMBER: builtins.int
        UNIT_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        @property
        def metric_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def nrql_expression(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        def __init__(
            self,
            *,
            metric_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            nrql_expression: google.protobuf.wrappers_pb2.StringValue | None = ...,
            unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["metric_name", b"metric_name", "nrql_expression", b"nrql_expression", "unit", b"unit"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["metric_name", b"metric_name", "nrql_expression", b"nrql_expression", "timeseries_offsets", b"timeseries_offsets", "unit", b"unit"]) -> None: ...

    @typing_extensions.final
    class FetchDashboardWidgetsTask(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        DASHBOARD_NAME_FIELD_NUMBER: builtins.int
        PAGE_NAME_FIELD_NUMBER: builtins.int
        WIDGET_NAMES_FIELD_NUMBER: builtins.int
        UNIT_FIELD_NUMBER: builtins.int
        TIMESERIES_OFFSETS_FIELD_NUMBER: builtins.int
        @property
        def dashboard_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def page_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widget_names(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def unit(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def timeseries_offsets(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]: ...
        def __init__(
            self,
            *,
            dashboard_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            page_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widget_names: google.protobuf.wrappers_pb2.StringValue | None = ...,
            unit: google.protobuf.wrappers_pb2.StringValue | None = ...,
            timeseries_offsets: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["dashboard_name", b"dashboard_name", "page_name", b"page_name", "unit", b"unit", "widget_names", b"widget_names"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["dashboard_name", b"dashboard_name", "page_name", b"page_name", "timeseries_offsets", b"timeseries_offsets", "unit", b"unit", "widget_names", b"widget_names"]) -> None: ...

    TYPE_FIELD_NUMBER: builtins.int
    ENTITY_APPLICATION_GOLDEN_METRIC_EXECUTION_FIELD_NUMBER: builtins.int
    ENTITY_DASHBOARD_WIDGET_NRQL_METRIC_EXECUTION_FIELD_NUMBER: builtins.int
    NRQL_METRIC_EXECUTION_FIELD_NUMBER: builtins.int
    DASHBOARD_MULTIPLE_WIDGETS_FIELD_NUMBER: builtins.int
    ENTITY_APPLICATION_APM_METRIC_EXECUTION_FIELD_NUMBER: builtins.int
    FETCH_DASHBOARD_WIDGETS_FIELD_NUMBER: builtins.int
    type: global___NewRelic.TaskType.ValueType
    @property
    def entity_application_golden_metric_execution(self) -> global___NewRelic.EntityApplicationGoldenMetricExecutionTask: ...
    @property
    def entity_dashboard_widget_nrql_metric_execution(self) -> global___NewRelic.EntityDashboardWidgetNRQLMetricExecutionTask: ...
    @property
    def nrql_metric_execution(self) -> global___NewRelic.NRQLMetricExecutionTask: ...
    @property
    def dashboard_multiple_widgets(self) -> global___NewRelic.DashboardWidgetByIdTask: ...
    @property
    def entity_application_apm_metric_execution(self) -> global___NewRelic.EntityApplicationAPMMetricExecutionTask: ...
    @property
    def fetch_dashboard_widgets(self) -> global___NewRelic.FetchDashboardWidgetsTask: ...
    def __init__(
        self,
        *,
        type: global___NewRelic.TaskType.ValueType = ...,
        entity_application_golden_metric_execution: global___NewRelic.EntityApplicationGoldenMetricExecutionTask | None = ...,
        entity_dashboard_widget_nrql_metric_execution: global___NewRelic.EntityDashboardWidgetNRQLMetricExecutionTask | None = ...,
        nrql_metric_execution: global___NewRelic.NRQLMetricExecutionTask | None = ...,
        dashboard_multiple_widgets: global___NewRelic.DashboardWidgetByIdTask | None = ...,
        entity_application_apm_metric_execution: global___NewRelic.EntityApplicationAPMMetricExecutionTask | None = ...,
        fetch_dashboard_widgets: global___NewRelic.FetchDashboardWidgetsTask | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["dashboard_multiple_widgets", b"dashboard_multiple_widgets", "entity_application_apm_metric_execution", b"entity_application_apm_metric_execution", "entity_application_golden_metric_execution", b"entity_application_golden_metric_execution", "entity_dashboard_widget_nrql_metric_execution", b"entity_dashboard_widget_nrql_metric_execution", "fetch_dashboard_widgets", b"fetch_dashboard_widgets", "nrql_metric_execution", b"nrql_metric_execution", "task", b"task"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["dashboard_multiple_widgets", b"dashboard_multiple_widgets", "entity_application_apm_metric_execution", b"entity_application_apm_metric_execution", "entity_application_golden_metric_execution", b"entity_application_golden_metric_execution", "entity_dashboard_widget_nrql_metric_execution", b"entity_dashboard_widget_nrql_metric_execution", "fetch_dashboard_widgets", b"fetch_dashboard_widgets", "nrql_metric_execution", b"nrql_metric_execution", "task", b"task", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["task", b"task"]) -> typing_extensions.Literal["entity_application_golden_metric_execution", "entity_dashboard_widget_nrql_metric_execution", "nrql_metric_execution", "dashboard_multiple_widgets", "entity_application_apm_metric_execution", "fetch_dashboard_widgets"] | None: ...

global___NewRelic = NewRelic
