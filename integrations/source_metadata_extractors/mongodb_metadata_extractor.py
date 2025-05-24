import logging

from integrations.source_api_processors.mongodb_processor import MongoDBProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class MongoDBSourceMetadataExtractor(SourceMetadataExtractor):
    """MongoDB metadata extractor that extracts databases and collections."""

    def __init__(self, request_id, connector_name, connection_string):
        """Initialize MongoDB metadata extractor with connection string."""
        self.mongodb_processor = MongoDBProcessor(connection_string)
        super().__init__(request_id, connector_name, Source.MONGODB)

    @log_function_call
    def extract_mongodb_data(self, save_to_db=False):
        """Extract MongoDB databases with their collections in a single operation."""
        model_data = {}
        try:
            # Test connection and get client
            if not self.mongodb_processor.test_connection():
                logger.error("MongoDB connection test failed.")
                return model_data
            client = self.mongodb_processor.get_connection()

            # Get databases (excluding system DBs)
            databases = [db for db in client.list_database_names()
                         if db not in ['admin', 'local', 'config']]

            # Extract collections for each database
            for db_name in databases:
                collections = client[db_name].list_collection_names()
                model_data[db_name] = {"name": db_name, "collections": collections}

                # Save to DB if requested
                if save_to_db:
                    self.create_or_update_model_metadata(
                        SourceModelType.MONGODB_DATABASE, db_name, model_data[db_name])
            client.close()
        except Exception as e:
            logger.error(f'Error extracting MongoDB data: {e}')
        return model_data
