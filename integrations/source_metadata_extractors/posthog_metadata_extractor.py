import logging

from integrations.source_api_processors.posthog_api_processor import PosthogApiProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class PosthogSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, posthog_host, personal_api_key, project_id):
        self.posthog_processor = PosthogApiProcessor(posthog_host, personal_api_key, project_id)
        self.project_id = project_id
        super().__init__(request_id, connector_name, Source.POSTHOG)

    @log_function_call
    def extract_property_definitions(self, save_to_db=False):
        """Extract PostHog property definitions and optionally save them to the database"""
        model_data = {}
        model_type = SourceModelType.POSTHOG_PROPERTY
        try:
            url = f"{self.posthog_processor._PosthogApiProcessor__host}/api/projects/{self.project_id}/property_definitions/"
            headers = self.posthog_processor.headers
            
            import requests
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching PostHog property definitions: {response.status_code} - {response.text}")
                return model_data
                
            property_definitions = response.json().get('results', [])
            
            if not property_definitions:
                logger.warning("No property definitions found in PostHog")
                return model_data
                
            for prop_def in property_definitions:
                prop_id = prop_def.get('id')
                prop_name = prop_def.get('name')
                
                if not prop_id or not prop_name:
                    continue
                    
                # Use the property name as the model_uid since it's what will be used in queries
                model_data[prop_name] = prop_def
                
                if save_to_db:
                    self.create_or_update_model_metadata(model_type, prop_name, prop_def)
                    
            logger.info(f"Extracted {len(model_data)} PostHog property definitions")
            
        except Exception as e:
            logger.error(f'Error extracting PostHog property definitions: {e}')
            
        return model_data 