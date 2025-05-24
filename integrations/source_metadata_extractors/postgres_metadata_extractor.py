import logging

from integrations.source_api_processors.postgres_db_processor import PostgresDBProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class PostgresSourceMetadataExtractor(SourceMetadataExtractor):
    """
    Extracts metadata from PostgreSQL databases including:
    - Databases
    - Tables (with columns and constraints)
    - Views
    - Stored procedures
    - etc.
    """

    def __init__(self, request_id, connector_name, host, port, user, password, database="postgres"):
        self.pg_processor = PostgresDBProcessor(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        self.default_database = database
        super().__init__(request_id, connector_name, Source.POSTGRES)

    @log_function_call
    def extract_tables(self, database=None, save_to_db=False):
        """Extract all tables from a specific database and optionally save them to the database"""
        model_data = {}
        model_type = SourceModelType.POSTGRES_TABLE
        
        try:
            db_to_use = database or self.default_database
            
            # Switch to the target database if necessary
            if db_to_use != self.pg_processor.config.get('database'):
                self.pg_processor = PostgresDBProcessor(
                    host=self.pg_processor.config.get('host'),
                    port=self.pg_processor.config.get('port'),
                    user=self.pg_processor.config.get('user'),
                    password=self.pg_processor.config.get('password'),
                    database=db_to_use
                )

            # SQL query to fetch all tables with their schemas
            tables_query = """
            SELECT 
                t.table_name, 
                t.table_schema,
                obj_description(pgc.oid, 'pg_class') as table_description,
                pg_size_pretty(pg_total_relation_size(pgc.oid)) as table_size
            FROM 
                information_schema.tables t
            JOIN 
                pg_catalog.pg_class pgc ON pgc.relname = t.table_name
            JOIN 
                pg_catalog.pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = t.table_schema
            WHERE 
                t.table_type = 'BASE TABLE' 
                AND t.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 
                t.table_schema, t.table_name;
            """
            
            tables = self.pg_processor.get_query_result(tables_query)
            
            if not tables:
                logger.warning(f"No tables found in PostgreSQL database {db_to_use}")
                return model_data
            
            # For each table, get column information
            for table in tables:
                table_name = table['table_name']
                schema_name = table['table_schema']
                
                # Fetch columns for this table
                columns_query = f"""
                SELECT 
                    c.column_name, 
                    c.data_type,
                    c.is_nullable = 'YES' as is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale,
                    col_description(pgc.oid, c.ordinal_position) as column_description
                FROM 
                    information_schema.columns c
                JOIN 
                    pg_catalog.pg_class pgc ON pgc.relname = c.table_name
                JOIN 
                    pg_catalog.pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
                WHERE 
                    c.table_schema = '{schema_name}' 
                    AND c.table_name = '{table_name}'
                ORDER BY 
                    c.ordinal_position;
                """
                
                columns = self.pg_processor.get_query_result(columns_query)
                
                # Fetch primary key information
                pk_query = f"""
                SELECT 
                    tc.constraint_name, 
                    kcu.column_name
                FROM 
                    information_schema.table_constraints tc
                JOIN 
                    information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name 
                    AND tc.table_schema = kcu.table_schema
                WHERE 
                    tc.constraint_type = 'PRIMARY KEY' 
                    AND tc.table_schema = '{schema_name}' 
                    AND tc.table_name = '{table_name}'
                ORDER BY 
                    kcu.ordinal_position;
                """
                
                primary_keys = self.pg_processor.get_query_result(pk_query)
                pk_columns = [pk['column_name'] for pk in primary_keys]
                
                # Fetch index information
                index_query = f"""
                SELECT 
                    i.relname as index_name,
                    a.attname as column_name,
                    am.amname as index_type,
                    idx.indisunique as is_unique
                FROM 
                    pg_index idx
                JOIN 
                    pg_class i ON i.oid = idx.indexrelid
                JOIN 
                    pg_class t ON t.oid = idx.indrelid
                JOIN 
                    pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
                JOIN 
                    pg_namespace n ON n.oid = t.relnamespace
                JOIN 
                    pg_am am ON am.oid = i.relam
                WHERE 
                    t.relname = '{table_name}'
                    AND n.nspname = '{schema_name}'
                ORDER BY 
                    i.relname, a.attnum;
                """
                
                indexes = self.pg_processor.get_query_result(index_query)
                
                # Process columns and add primary key flag
                processed_columns = []
                for column in columns:
                    column_data = {
                        "name": column["column_name"],
                        "data_type": column["data_type"],
                        "is_nullable": column["is_nullable"],
                        "default_value": column.get("column_default"),
                        "is_primary_key": column["column_name"] in pk_columns,
                        "description": column.get("column_description", "")
                    }
                    
                    # Add length/precision/scale if applicable
                    if column.get("character_maximum_length"):
                        column_data["max_length"] = column["character_maximum_length"]
                    if column.get("numeric_precision"):
                        column_data["precision"] = column["numeric_precision"]
                    if column.get("numeric_scale"):
                        column_data["scale"] = column["numeric_scale"]
                        
                    processed_columns.append(column_data)

                # Process indexes
                processed_indexes = []
                current_index = None
                for idx in indexes:
                    if not current_index or current_index["name"] != idx["index_name"]:
                        if current_index:
                            processed_indexes.append(current_index)
                        current_index = {
                            "name": idx["index_name"],
                            "type": idx["index_type"],
                            "is_unique": idx["is_unique"],
                            "columns": []
                        }
                    current_index["columns"].append(idx["column_name"])
                
                if current_index:
                    processed_indexes.append(current_index)
                
                # Create unique model_uid for the table
                model_uid = f"{db_to_use}.{schema_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_to_use,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "description": table.get("table_description", ""),
                    "size": table.get("table_size", ""),
                    "columns": processed_columns,
                    "primary_keys": pk_columns,
                    "indexes": processed_indexes
                }
                
                model_data[model_uid] = table_metadata
                
                if save_to_db:
                    self.create_or_update_model_metadata(model_type, model_uid, table_metadata)
            
            logger.info(f"Extracted {len(model_data)} tables from PostgreSQL database {db_to_use}")
            
        except Exception as e:
            logger.error(f'Error extracting PostgreSQL tables from database {database}: {e}')
            
        return model_data