"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.struct_pb2
import google.protobuf.wrappers_pb2
import protos.base_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class DatadogServiceAssetModel(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class Metric(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        METRIC_FAMILY_FIELD_NUMBER: builtins.int
        METRIC_FIELD_NUMBER: builtins.int
        TAGS_FIELD_NUMBER: builtins.int
        @property
        def metric_family(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def metric(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def tags(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[google.protobuf.wrappers_pb2.StringValue]: ...
        def __init__(
            self,
            *,
            metric_family: google.protobuf.wrappers_pb2.StringValue | None = ...,
            metric: google.protobuf.wrappers_pb2.StringValue | None = ...,
            tags: collections.abc.Iterable[google.protobuf.wrappers_pb2.StringValue] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["metric", b"metric", "metric_family", b"metric_family"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["metric", b"metric", "metric_family", b"metric_family", "tags", b"tags"]) -> None: ...

    SERVICE_NAME_FIELD_NUMBER: builtins.int
    ENVIRONMENTS_FIELD_NUMBER: builtins.int
    METRICS_FIELD_NUMBER: builtins.int
    @property
    def service_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def environments(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    @property
    def metrics(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___DatadogServiceAssetModel.Metric]: ...
    def __init__(
        self,
        *,
        service_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
        environments: collections.abc.Iterable[builtins.str] | None = ...,
        metrics: collections.abc.Iterable[global___DatadogServiceAssetModel.Metric] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["service_name", b"service_name"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["environments", b"environments", "metrics", b"metrics", "service_name", b"service_name"]) -> None: ...

global___DatadogServiceAssetModel = DatadogServiceAssetModel

@typing_extensions.final
class DatadogServiceAssetOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class DatadogServiceAssetOption(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        NAME_FIELD_NUMBER: builtins.int
        METRIC_FAMILIES_FIELD_NUMBER: builtins.int
        @property
        def name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def metric_families(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(
            self,
            *,
            name: google.protobuf.wrappers_pb2.StringValue | None = ...,
            metric_families: collections.abc.Iterable[builtins.str] | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["name", b"name"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["metric_families", b"metric_families", "name", b"name"]) -> None: ...

    SERVICES_FIELD_NUMBER: builtins.int
    @property
    def services(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___DatadogServiceAssetOptions.DatadogServiceAssetOption]: ...
    def __init__(
        self,
        *,
        services: collections.abc.Iterable[global___DatadogServiceAssetOptions.DatadogServiceAssetOption] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["services", b"services"]) -> None: ...

global___DatadogServiceAssetOptions = DatadogServiceAssetOptions

@typing_extensions.final
class DatadogDashboardAssetOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DASHBOARDS_FIELD_NUMBER: builtins.int
    @property
    def dashboards(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        dashboards: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["dashboards", b"dashboards"]) -> None: ...

global___DatadogDashboardAssetOptions = DatadogDashboardAssetOptions

@typing_extensions.final
class DatadogDashboardModel(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class Panel(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        @typing_extensions.final
        class Widget(google.protobuf.message.Message):
            DESCRIPTOR: google.protobuf.descriptor.Descriptor

            RESPONSE_TYPE_FIELD_NUMBER: builtins.int
            TITLE_FIELD_NUMBER: builtins.int
            QUERIES_FIELD_NUMBER: builtins.int
            FORMULAS_FIELD_NUMBER: builtins.int
            ID_FIELD_NUMBER: builtins.int
            WIDGET_TYPE_FIELD_NUMBER: builtins.int
            @property
            def response_type(self) -> google.protobuf.wrappers_pb2.StringValue: ...
            @property
            def title(self) -> google.protobuf.wrappers_pb2.StringValue: ...
            @property
            def queries(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[google.protobuf.struct_pb2.Struct]: ...
            @property
            def formulas(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[google.protobuf.struct_pb2.Struct]: ...
            @property
            def id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
            @property
            def widget_type(self) -> google.protobuf.wrappers_pb2.StringValue: ...
            def __init__(
                self,
                *,
                response_type: google.protobuf.wrappers_pb2.StringValue | None = ...,
                title: google.protobuf.wrappers_pb2.StringValue | None = ...,
                queries: collections.abc.Iterable[google.protobuf.struct_pb2.Struct] | None = ...,
                formulas: collections.abc.Iterable[google.protobuf.struct_pb2.Struct] | None = ...,
                id: google.protobuf.wrappers_pb2.StringValue | None = ...,
                widget_type: google.protobuf.wrappers_pb2.StringValue | None = ...,
            ) -> None: ...
            def HasField(self, field_name: typing_extensions.Literal["id", b"id", "response_type", b"response_type", "title", b"title", "widget_type", b"widget_type"]) -> builtins.bool: ...
            def ClearField(self, field_name: typing_extensions.Literal["formulas", b"formulas", "id", b"id", "queries", b"queries", "response_type", b"response_type", "title", b"title", "widget_type", b"widget_type"]) -> None: ...

        TITLE_FIELD_NUMBER: builtins.int
        WIDGETS_FIELD_NUMBER: builtins.int
        ID_FIELD_NUMBER: builtins.int
        @property
        def title(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        @property
        def widgets(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___DatadogDashboardModel.Panel.Widget]: ...
        @property
        def id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
        def __init__(
            self,
            *,
            title: google.protobuf.wrappers_pb2.StringValue | None = ...,
            widgets: collections.abc.Iterable[global___DatadogDashboardModel.Panel.Widget] | None = ...,
            id: google.protobuf.wrappers_pb2.StringValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["id", b"id", "title", b"title"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["id", b"id", "title", b"title", "widgets", b"widgets"]) -> None: ...

    ID_FIELD_NUMBER: builtins.int
    URL_FIELD_NUMBER: builtins.int
    TITLE_FIELD_NUMBER: builtins.int
    DESCRIPTION_FIELD_NUMBER: builtins.int
    PANELS_FIELD_NUMBER: builtins.int
    TEMPLATE_VARIABLES_FIELD_NUMBER: builtins.int
    @property
    def id(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def url(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def title(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def description(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def panels(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___DatadogDashboardModel.Panel]: ...
    @property
    def template_variables(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[google.protobuf.struct_pb2.Struct]: ...
    def __init__(
        self,
        *,
        id: google.protobuf.wrappers_pb2.StringValue | None = ...,
        url: google.protobuf.wrappers_pb2.StringValue | None = ...,
        title: google.protobuf.wrappers_pb2.StringValue | None = ...,
        description: google.protobuf.wrappers_pb2.StringValue | None = ...,
        panels: collections.abc.Iterable[global___DatadogDashboardModel.Panel] | None = ...,
        template_variables: collections.abc.Iterable[google.protobuf.struct_pb2.Struct] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["description", b"description", "id", b"id", "title", b"title", "url", b"url"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["description", b"description", "id", b"id", "panels", b"panels", "template_variables", b"template_variables", "title", b"title", "url", b"url"]) -> None: ...

global___DatadogDashboardModel = DatadogDashboardModel

@typing_extensions.final
class DatadogAssetModel(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ID_FIELD_NUMBER: builtins.int
    CONNECTOR_TYPE_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    LAST_UPDATED_FIELD_NUMBER: builtins.int
    DATADOG_SERVICE_FIELD_NUMBER: builtins.int
    DATADOG_DASHBOARD_FIELD_NUMBER: builtins.int
    @property
    def id(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    connector_type: protos.base_pb2.Source.ValueType
    type: protos.base_pb2.SourceModelType.ValueType
    last_updated: builtins.int
    @property
    def datadog_service(self) -> global___DatadogServiceAssetModel: ...
    @property
    def datadog_dashboard(self) -> global___DatadogDashboardModel: ...
    def __init__(
        self,
        *,
        id: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
        connector_type: protos.base_pb2.Source.ValueType = ...,
        type: protos.base_pb2.SourceModelType.ValueType = ...,
        last_updated: builtins.int = ...,
        datadog_service: global___DatadogServiceAssetModel | None = ...,
        datadog_dashboard: global___DatadogDashboardModel | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["asset", b"asset", "datadog_dashboard", b"datadog_dashboard", "datadog_service", b"datadog_service", "id", b"id"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset", b"asset", "connector_type", b"connector_type", "datadog_dashboard", b"datadog_dashboard", "datadog_service", b"datadog_service", "id", b"id", "last_updated", b"last_updated", "type", b"type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["asset", b"asset"]) -> typing_extensions.Literal["datadog_service", "datadog_dashboard"] | None: ...

global___DatadogAssetModel = DatadogAssetModel

@typing_extensions.final
class DatadogAssets(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ASSETS_FIELD_NUMBER: builtins.int
    @property
    def assets(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___DatadogAssetModel]: ...
    def __init__(
        self,
        *,
        assets: collections.abc.Iterable[global___DatadogAssetModel] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["assets", b"assets"]) -> None: ...

global___DatadogAssets = DatadogAssets
