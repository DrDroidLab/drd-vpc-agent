from integrations.source_metadata_extractors.github_metadata_extractor import GithubSourceMetadataExtractor
from protos.base_pb2 import Source
from integrations.source_metadata_extractors.azure_metadata_extractor import AzureConnectorMetadataExtractor
from integrations.source_metadata_extractors.clickhouse_metadata_extractor import ClickhouseSourceMetadataExtractor
from integrations.source_metadata_extractors.cloudwatch_metadata_extractor import CloudwatchSourceMetadataExtractor
from integrations.source_metadata_extractors.datadog_metadata_extractor import DatadogSourceMetadataExtractor
from integrations.source_metadata_extractors.eks_metadata_extractor import EksSourceMetadataExtractor
from integrations.source_metadata_extractors.elastic_search_metadata_extractor import \
    ElasticSearchSourceMetadataExtractor
from integrations.source_metadata_extractors.gke_metadata_extractor import GkeSourceMetadataExtractor
from integrations.source_metadata_extractors.grafana_metadata_extractor import GrafanaSourceMetadataExtractor
from integrations.source_metadata_extractors.newrelic_metadata_extractor import NewrelicSourceMetadataExtractor
from integrations.source_metadata_extractors.open_search_metadata_extractor import OpenSearchSourceMetadataExtractor
from integrations.source_metadata_extractor import SourceMetadataExtractor


class SourceMetadataExtractorFacade:

    def __init__(self):
        self._map = {}

    def register(self, source: Source, metadata_extractor: SourceMetadataExtractor.__class__):
        self._map[source] = metadata_extractor

    def get_connector_metadata_extractor_class(self, connector_type: Source):
        if connector_type not in self._map:
            raise ValueError(f'No metadata extractor found for connector type: {connector_type}')
        return self._map[connector_type]


source_metadata_extractor_facade = SourceMetadataExtractorFacade()
source_metadata_extractor_facade.register(Source.DATADOG, DatadogSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.DATADOG_OAUTH, DatadogSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.CLOUDWATCH, CloudwatchSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.NEW_RELIC, NewrelicSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.GRAFANA, GrafanaSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.GKE, GkeSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.CLICKHOUSE, ClickhouseSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.EKS, EksSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.AZURE, AzureConnectorMetadataExtractor)
source_metadata_extractor_facade.register(Source.ELASTIC_SEARCH, ElasticSearchSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.OPEN_SEARCH, OpenSearchSourceMetadataExtractor)
source_metadata_extractor_facade.register(Source.GITHUB, GithubSourceMetadataExtractor)
