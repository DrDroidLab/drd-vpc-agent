import logging

from google.protobuf.wrappers_pb2 import StringValue

from integrations.source_manager import SourceManager
from integrations.source_manangers.api_source_manager import ApiSourceManager
from integrations.source_manangers.azure_source_manager import AzureSourceManager
from integrations.source_manangers.bash_source_manager import BashSourceManager
from integrations.source_manangers.big_query_source_manager import BigQuerySourceManager
from integrations.source_manangers.clickhouse_source_manager import ClickhouseSourceManager
from integrations.source_manangers.cloudwatch_source_manager import CloudwatchSourceManager
from integrations.source_manangers.datadog_source_manager import DatadogSourceManager
from integrations.source_manangers.datadog_oauth_soruce_manager import DatadogSourceManager as DatadogOauthSourceManager
from integrations.source_manangers.documentation_source_manager import DocumentationSourceManager
from integrations.source_manangers.eks_source_manager import EksSourceManager
from integrations.source_manangers.elastic_search_source_manager import ElasticSearchSourceManager
from integrations.source_manangers.gcm_source_manager import GcmSourceManager
from integrations.source_manangers.github_source_manager import GithubSourceManager
from integrations.source_manangers.gke_source_manager import GkeSourceManager
from integrations.source_manangers.grafana_loki_source_manager import GrafanaLokiSourceManager
from integrations.source_manangers.grafana_source_manager import GrafanaSourceManager
from integrations.source_manangers.jenkins_source_manager import JenkinsSourceManager
from integrations.source_manangers.kubernetes_source_manager import KubernetesSourceManager
from integrations.source_manangers.mimir_source_manager import MimirSourceManager
from integrations.source_manangers.mongodb_source_manager import MongoDBSourceManager
from integrations.source_manangers.newrelic_source_manager import NewRelicSourceManager
from integrations.source_manangers.open_search_source_manager import OpenSearchSourceManager
from integrations.source_manangers.postgres_source_manager import PostgresSourceManager
from integrations.source_manangers.rootly_source_manager import RootlySourceManager
from integrations.source_manangers.slack_source_manager import SlackSourceManager
from integrations.source_manangers.smtp_source_manager import SMTPSourceManager
from integrations.source_manangers.sql_database_connection_source_manager import SqlDatabaseConnectionSourceManager
from integrations.source_manangers.zenduty_source_manager import ZendutySourceManager
from integrations.source_manangers.argocd_source_manager import ArgoCDSourceManager
from integrations.source_manangers.jira_source_manager import JiraSourceManager
from integrations.source_manangers.posthog_source_manager import PosthogSourceManager
from integrations.source_manangers.signoz_source_manager import SignozSourceManager
from integrations.source_manangers.sentry_source_manager import SentrySourceManager
from integrations.source_manangers.github_actions_source_manager import GithubActionsSourceManager
from protos.base_pb2 import Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult

from protos.playbooks.playbook_pb2 import PlaybookTask

logger = logging.getLogger(__name__)


class SourceFacade:

    def __init__(self):
        self._map = {}

    def register(self, source: Source, manager: SourceManager):
        self._map[source] = manager

    def get_source_manager(self, source: Source):
        if source not in self._map:
            raise ValueError(f'No executor found for source: {source}')
        return self._map.get(source)

    def execute_task(self, time_range, global_variable_set, task: PlaybookTask):
        source = task.source
        if source not in self._map:
            raise ValueError(f'No executor found for source: {source}')
        manager = self._map[source]
        try:
            return manager.execute_task(time_range, global_variable_set, task)
        except Exception as e:
            logger.error(f'Error while executing task: {str(e)}')
            return PlaybookTaskResult(error=StringValue(value=str(e)))

    def test_source_connection(self, source_connection: ConnectorProto):
        source = source_connection.type
        if source not in self._map:
            return False, f'No executor found for source: {source}'
        manager = self._map[source]
        try:
            return manager.test_connector_processor(source_connection), None
        except Exception as e:
            logger.error(f'Error while testing source connection: {str(e)}')
            return False, str(e)


source_facade = SourceFacade()
source_facade.register(Source.CLOUDWATCH, CloudwatchSourceManager())
source_facade.register(Source.EKS, EksSourceManager())
source_facade.register(Source.DATADOG, DatadogSourceManager())
source_facade.register(Source.DATADOG_OAUTH, DatadogOauthSourceManager())
source_facade.register(Source.NEW_RELIC, NewRelicSourceManager())
source_facade.register(Source.GRAFANA, GrafanaSourceManager())
source_facade.register(Source.GRAFANA_MIMIR, MimirSourceManager())
source_facade.register(Source.AZURE, AzureSourceManager())
source_facade.register(Source.GKE, GkeSourceManager())
source_facade.register(Source.GCM, GcmSourceManager())
source_facade.register(Source.GRAFANA_LOKI, GrafanaLokiSourceManager())

source_facade.register(Source.POSTGRES, PostgresSourceManager())
source_facade.register(Source.CLICKHOUSE, ClickhouseSourceManager())
source_facade.register(Source.SQL_DATABASE_CONNECTION, SqlDatabaseConnectionSourceManager())
source_facade.register(Source.ELASTIC_SEARCH, ElasticSearchSourceManager())
source_facade.register(Source.BIG_QUERY, BigQuerySourceManager())
source_facade.register(Source.MONGODB, MongoDBSourceManager())
source_facade.register(Source.OPEN_SEARCH, OpenSearchSourceManager())

source_facade.register(Source.API, ApiSourceManager())
source_facade.register(Source.BASH, BashSourceManager())
source_facade.register(Source.KUBERNETES, KubernetesSourceManager())
source_facade.register(Source.SMTP, SMTPSourceManager())
source_facade.register(Source.SLACK, SlackSourceManager())

source_facade.register(Source.DOCUMENTATION, DocumentationSourceManager())
source_facade.register(Source.ROOTLY, RootlySourceManager())
source_facade.register(Source.ZENDUTY, ZendutySourceManager())

source_facade.register(Source.GITHUB, GithubSourceManager())
source_facade.register(Source.ARGOCD, ArgoCDSourceManager())
source_facade.register(Source.JIRA_CLOUD, JiraSourceManager())
source_facade.register(Source.JENKINS, JenkinsSourceManager())

source_facade.register(Source.POSTHOG, PosthogSourceManager())
source_facade.register(Source.SIGNOZ, SignozSourceManager())
source_facade.register(Source.SENTRY, SentrySourceManager())
source_facade.register(Source.GITHUB_ACTIONS, GithubActionsSourceManager())
