"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.message
import protos.assets.argocd_asset_pb2
import protos.assets.asana_asset_pb2
import protos.assets.azure_asset_pb2
import protos.assets.bash_asset_pb2
import protos.assets.clickhouse_asset_pb2
import protos.assets.cloudwatch_asset_pb2
import protos.assets.datadog_asset_pb2
import protos.assets.eks_asset_pb2
import protos.assets.elastic_search_asset_pb2
import protos.assets.gcm_asset_pb2
import protos.assets.github_asset_pb2
import protos.assets.gke_asset_pb2
import protos.assets.grafana_asset_pb2
import protos.assets.jira_asset_pb2
import protos.assets.newrelic_asset_pb2
import protos.assets.open_search_asset_pb2
import protos.assets.postgres_asset_pb2
import protos.assets.slack_asset_pb2
import protos.connectors.connector_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class AccountConnectorAssets(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    CONNECTOR_FIELD_NUMBER: builtins.int
    CLOUDWATCH_FIELD_NUMBER: builtins.int
    GRAFANA_FIELD_NUMBER: builtins.int
    CLICKHOUSE_FIELD_NUMBER: builtins.int
    SLACK_FIELD_NUMBER: builtins.int
    NEW_RELIC_FIELD_NUMBER: builtins.int
    DATADOG_FIELD_NUMBER: builtins.int
    POSTGRES_FIELD_NUMBER: builtins.int
    EKS_FIELD_NUMBER: builtins.int
    BASH_FIELD_NUMBER: builtins.int
    AZURE_FIELD_NUMBER: builtins.int
    GKE_FIELD_NUMBER: builtins.int
    ELASTIC_SEARCH_FIELD_NUMBER: builtins.int
    GCM_FIELD_NUMBER: builtins.int
    DATADOG_OAUTH_FIELD_NUMBER: builtins.int
    OPEN_SEARCH_FIELD_NUMBER: builtins.int
    ASANA_FIELD_NUMBER: builtins.int
    GITHUB_FIELD_NUMBER: builtins.int
    JIRA_CLOUD_FIELD_NUMBER: builtins.int
    ARGOCD_FIELD_NUMBER: builtins.int
    @property
    def connector(self) -> protos.connectors.connector_pb2.Connector: ...
    @property
    def cloudwatch(self) -> protos.assets.cloudwatch_asset_pb2.CloudwatchAssets: ...
    @property
    def grafana(self) -> protos.assets.grafana_asset_pb2.GrafanaAssets: ...
    @property
    def clickhouse(self) -> protos.assets.clickhouse_asset_pb2.ClickhouseAssets: ...
    @property
    def slack(self) -> protos.assets.slack_asset_pb2.SlackAssets: ...
    @property
    def new_relic(self) -> protos.assets.newrelic_asset_pb2.NewRelicAssets: ...
    @property
    def datadog(self) -> protos.assets.datadog_asset_pb2.DatadogAssets: ...
    @property
    def postgres(self) -> protos.assets.postgres_asset_pb2.PostgresAssets: ...
    @property
    def eks(self) -> protos.assets.eks_asset_pb2.EksAssets: ...
    @property
    def bash(self) -> protos.assets.bash_asset_pb2.BashAssets: ...
    @property
    def azure(self) -> protos.assets.azure_asset_pb2.AzureAssets: ...
    @property
    def gke(self) -> protos.assets.gke_asset_pb2.GkeAssets: ...
    @property
    def elastic_search(self) -> protos.assets.elastic_search_asset_pb2.ElasticSearchAssets: ...
    @property
    def gcm(self) -> protos.assets.gcm_asset_pb2.GcmAssets: ...
    @property
    def datadog_oauth(self) -> protos.assets.datadog_asset_pb2.DatadogAssets: ...
    @property
    def open_search(self) -> protos.assets.open_search_asset_pb2.OpenSearchAssets: ...
    @property
    def asana(self) -> protos.assets.asana_asset_pb2.AsanaAssets: ...
    @property
    def github(self) -> protos.assets.github_asset_pb2.GithubAssets: ...
    @property
    def jira_cloud(self) -> protos.assets.jira_asset_pb2.JiraAssets: ...
    @property
    def argocd(self) -> protos.assets.argocd_asset_pb2.ArgoCDAssets: ...
    def __init__(
        self,
        *,
        connector: protos.connectors.connector_pb2.Connector | None = ...,
        cloudwatch: protos.assets.cloudwatch_asset_pb2.CloudwatchAssets | None = ...,
        grafana: protos.assets.grafana_asset_pb2.GrafanaAssets | None = ...,
        clickhouse: protos.assets.clickhouse_asset_pb2.ClickhouseAssets | None = ...,
        slack: protos.assets.slack_asset_pb2.SlackAssets | None = ...,
        new_relic: protos.assets.newrelic_asset_pb2.NewRelicAssets | None = ...,
        datadog: protos.assets.datadog_asset_pb2.DatadogAssets | None = ...,
        postgres: protos.assets.postgres_asset_pb2.PostgresAssets | None = ...,
        eks: protos.assets.eks_asset_pb2.EksAssets | None = ...,
        bash: protos.assets.bash_asset_pb2.BashAssets | None = ...,
        azure: protos.assets.azure_asset_pb2.AzureAssets | None = ...,
        gke: protos.assets.gke_asset_pb2.GkeAssets | None = ...,
        elastic_search: protos.assets.elastic_search_asset_pb2.ElasticSearchAssets | None = ...,
        gcm: protos.assets.gcm_asset_pb2.GcmAssets | None = ...,
        datadog_oauth: protos.assets.datadog_asset_pb2.DatadogAssets | None = ...,
        open_search: protos.assets.open_search_asset_pb2.OpenSearchAssets | None = ...,
        asana: protos.assets.asana_asset_pb2.AsanaAssets | None = ...,
        github: protos.assets.github_asset_pb2.GithubAssets | None = ...,
        jira_cloud: protos.assets.jira_asset_pb2.JiraAssets | None = ...,
        argocd: protos.assets.argocd_asset_pb2.ArgoCDAssets | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["argocd", b"argocd", "asana", b"asana", "assets", b"assets", "azure", b"azure", "bash", b"bash", "clickhouse", b"clickhouse", "cloudwatch", b"cloudwatch", "connector", b"connector", "datadog", b"datadog", "datadog_oauth", b"datadog_oauth", "eks", b"eks", "elastic_search", b"elastic_search", "gcm", b"gcm", "github", b"github", "gke", b"gke", "grafana", b"grafana", "jira_cloud", b"jira_cloud", "new_relic", b"new_relic", "open_search", b"open_search", "postgres", b"postgres", "slack", b"slack"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["argocd", b"argocd", "asana", b"asana", "assets", b"assets", "azure", b"azure", "bash", b"bash", "clickhouse", b"clickhouse", "cloudwatch", b"cloudwatch", "connector", b"connector", "datadog", b"datadog", "datadog_oauth", b"datadog_oauth", "eks", b"eks", "elastic_search", b"elastic_search", "gcm", b"gcm", "github", b"github", "gke", b"gke", "grafana", b"grafana", "jira_cloud", b"jira_cloud", "new_relic", b"new_relic", "open_search", b"open_search", "postgres", b"postgres", "slack", b"slack"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["assets", b"assets"]) -> typing_extensions.Literal["cloudwatch", "grafana", "clickhouse", "slack", "new_relic", "datadog", "postgres", "eks", "bash", "azure", "gke", "elastic_search", "gcm", "datadog_oauth", "open_search", "asana", "github", "jira_cloud", "argocd"] | None: ...

global___AccountConnectorAssets = AccountConnectorAssets
