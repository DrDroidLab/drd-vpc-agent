import logging

from integrations.source_metadata_extractor import SourceMetadataExtractor
from integrations.source_api_processors.clickhouse_db_processor import ClickhouseDBProcessor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class ClickhouseSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, interface: str, host: str, port: str, user: str,
                 password: str):
        self.__ch_db_processor = ClickhouseDBProcessor(interface, host, port, user, password)
        super().__init__(request_id, connector_name, Source.CLICKHOUSE)

    @log_function_call
    def extract_database(self):
        model_type = SourceModelType.CLICKHOUSE_DATABASE
        try:
            databases = self.__ch_db_processor.fetch_databases()
        except Exception as e:
            logger.error(f"Exception occurred while fetching clickhouse databases with error: {e}")
            return
        if not databases:
            return
        model_data = {}
        try:
            db_table_map = self.__ch_db_processor.fetch_tables(databases)
            db_table_details_map = self.__ch_db_processor.fetch_table_details(db_table_map)
            if db_table_details_map:
                for db_name, table_details in db_table_details_map.items():
                    model_data[db_name] = table_details
            self.create_or_update_model_metadata(model_type, model_data)
        except Exception as e:
            logger.error(f"Exception occurred while fetching clickhouse tables with error: {e}")
        return model_data

    @log_function_call
    def extract_tables(self, databases=None):
        """Extract all tables from specified databases and optionally save them to the database"""
        model_type = SourceModelType.CLICKHOUSE_TABLE
        model_data = {}
        
        try:
            if not databases:
                db_dict = self.extract_database()
                if not db_dict:
                    return model_data
                databases = list(db_dict.keys())
            
            # Fetch tables for each database
            database_tables = self.__ch_db_processor.fetch_tables(databases)
            if not database_tables:
                logger.warning("No tables found in Clickhouse databases")
                return model_data
                
            # Fetch detailed information for each table
            for db_name, tables in database_tables.items():
                db_processor = ClickhouseDBProcessor(
                    interface=self.__ch_db_processor.config.get('interface'),
                    host=self.__ch_db_processor.config.get('host'),
                    port=self.__ch_db_processor.config.get('port'),
                    user=self.__ch_db_processor.config.get('user'),
                    password=self.__ch_db_processor.config.get('password'),
                    database=db_name
                )
                
                for table_name in tables:
                    try:
                        # Get detailed table information
                        table_details_query = f"""
                        SELECT 
                            engine,
                            formatReadableSize(total_bytes) as size
                        FROM system.tables 
                        WHERE database = '{db_name}' AND name = '{table_name}'
                        """
                        table_details = db_processor.get_query_result(table_details_query)
                        
                        # Get column information
                        columns_query = f"DESCRIBE TABLE {db_name}.{table_name}"
                        columns_result = db_processor.get_query_result(columns_query)

                        processed_columns = []
                        for row in columns_result.result_set:
                            column_data = {
                                "name": row[0],
                                "data_type": row[1],
                                "is_nullable": "Nullable" in row[1],
                                "default_value": row[3] if len(row) > 3 else None,
                                "description": row[4] if len(row) > 4 else ""
                            }
                            processed_columns.append(column_data)
                        
                        # Create model_uid for the table
                        model_uid = f"{db_name}.{table_name}"
                        
                        # Build complete table metadata
                        if table_details and table_details.result_set:
                            engine = table_details.result_set[0][0] if len(table_details.result_set[0]) > 0 else ""
                            size = table_details.result_set[0][1] if len(table_details.result_set[0]) > 1 else ""
                        else:
                            engine = ""
                            size = ""
                            
                        table_metadata = {
                            "database_name": db_name,
                            "table_name": table_name,
                            "engine": engine,
                            "size": size,
                            "columns": processed_columns
                        }
                        
                        model_data[model_uid] = table_metadata

                    except Exception as e:
                        logger.error(f"Error extracting details for table {db_name}.{table_name}: {e}")
                        continue
                        
            logger.info(f"Extracted metadata for {len(model_data)} tables from Clickhouse databases")
            
        except Exception as e:
            logger.error(f'Error extracting Clickhouse tables: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)