import logging

from integrations.source_api_processors.signoz_api_processor import SignozApiProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class SignozSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, signoz_api_url, signoz_api_token=None):
        self.__signoz_api_processor = SignozApiProcessor(signoz_api_url, signoz_api_token)
        super().__init__(request_id, connector_name, Source.SIGNOZ)

    @log_function_call
    def extract_dashboards(self, save_to_db=False):
        model_type = SourceModelType.SIGNOZ_DASHBOARD
        model_data = {}
        try:
            response = self.__signoz_api_processor.fetch_dashboards()
            if not response:
                return model_data
            dashboards = response.get("data", [])
            dashboard_ids = [dashboard["uuid"] for dashboard in dashboards]
            
            for dashboard_id in dashboard_ids:
                try:
                    dashboard = self.__signoz_api_processor.fetch_dashboard_details(dashboard_id)
                except Exception as e:
                    logger.error(f"Error fetching signoz dashboard details for dashboard_id: {dashboard_id} - {e}")
                    continue
                    
                if not dashboard:
                    continue
                print(f"Fetched dashboard: {dashboard}")
                dashboard_id = str(dashboard["id"])
                model_data[dashboard_id] = dashboard
                
                if save_to_db:
                    self.create_or_update_model_metadata(model_type, dashboard_id, dashboard)
        except Exception as e:
            logger.error(f"Error extracting signoz dashboards: {e}")
            
        return model_data
