import logging

from integrations.source_metadata_extractor import SourceMetadataExtractor
from integrations.source_api_processors.gcm_api_processor import GcmApiProcessor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call
from utils.static_mappings import GCM_SERVICE_DASHBOARD_QUERIES

logger = logging.getLogger(__name__)


class GcmSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, project_id, service_account_json):
        self.__project_id = project_id
        self.__service_account_json = service_account_json
        super().__init__(request_id, connector_name, Source.GCM)

    @log_function_call
    def extract_metric_descriptors(self):
        model_type = SourceModelType.GCM_METRIC
        model_data = {}
        gcm_api_processor = GcmApiProcessor(self.__project_id, self.__service_account_json)
        try:
            all_metric_descriptors = gcm_api_processor.fetch_metrics_list()
            for descriptor in all_metric_descriptors:
                try:
                    metric_type = descriptor['type']
                    model_data[metric_type] = {
                        'metric_type': metric_type
                    }
                except Exception as e:
                    logger.error(f'Error processing metric descriptor: {e}')
        except Exception as e:
            logger.error(f'Error extracting metric descriptors: {e}')
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_dashboard_entities(self):
        model_type = SourceModelType.GCM_DASHBOARD
        model_data = {}
        try:
            # Get all dashboards from the GCM API
            gcm_api_processor = GcmApiProcessor(self.__project_id, self.__service_account_json)
            all_dashboards = gcm_api_processor.fetch_dashboards_list()

            for dashboard in all_dashboards:
                try:
                    # Extract dashboard ID from the full resource name
                    dashboard_name = dashboard.get('name', '')
                    dashboard_id = dashboard_name.split('/')[-1] if dashboard_name else ''

                    if not dashboard_id:
                        continue

                    # Fetch detailed dashboard info with widgets
                    dashboard_detail = gcm_api_processor.fetch_dashboard(dashboard_id)

                    # Extract widgets information
                    widgets = []
                    if 'gridLayout' in dashboard_detail:
                        widgets = dashboard_detail.get('gridLayout', {}).get('widgets', [])
                    elif 'mosaicLayout' in dashboard_detail:
                        widgets = dashboard_detail.get('mosaicLayout', {}).get('widgets', [])

                    # Clean up widget data to only include necessary information
                    for widget in widgets:
                        # Remove any large or unnecessary fields
                        if 'plotData' in widget:
                            del widget['plotData']

                    # Prepare model data
                    model_data[dashboard_id] = {
                        'displayName': dashboard.get('displayName', ''),
                        'etag': dashboard.get('etag', ''),
                        'name': dashboard_name,
                        'widgets': widgets
                    }


                except Exception as e:
                    logger.error(f'Error extracting gcm dashboard entity: {e}')

        except Exception as e:
            logger.error(f'Error extracting gcm dashboard entities: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_cloud_run_services(self):
        """
        Extracts Cloud Run services and regions for the cloud_run_service_dashboard task type.

        Args:
            save_to_db (bool): Whether to save the extracted data to the database.

        Returns:
            dict: Dictionary mapping service names to their metadata.
        """
        model_type = SourceModelType.GCM_CLOUD_RUN_SERVICE_DASHBOARD
        model_data = {}

        try:
            # Use the GcmApiProcessor to fetch Cloud Run services
            gcm_api_processor = GcmApiProcessor(self.__project_id, self.__service_account_json)
            cloud_run_services = gcm_api_processor.fetch_cloud_run_services()

            for service_item in cloud_run_services:
                service_name = service_item.get('service_name')
                region = service_item.get('region')

                # Create a unique ID for this service+region combination
                model_uid = f"{service_name}:{region}"

                # Build metrics metadata using the static mappings
                metrics_data = []
                for metric_name, aggregations in GCM_SERVICE_DASHBOARD_QUERIES.items():
                    metrics_data.append({
                        'metric_name': metric_name,
                        'aggregations': list(aggregations.keys())
                    })

                # Prepare the metadata
                service_metadata = {
                    'service_name': service_name,
                    'region': region,
                    'project_id': self.__project_id,
                    'metrics': metrics_data,
                    'url': f"https://console.cloud.google.com/run/detail/{region}/{service_name}/metrics?project={self.__project_id}"
                }

                model_data[model_uid] = service_metadata


        except Exception as e:
            logger.error(f'Error extracting Cloud Run services: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
