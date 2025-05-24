import logging

from integrations.source_api_processors.db_connection_string_processor import DBConnectionStringProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class SqlDatabaseConnectionMetadataExtractor(SourceMetadataExtractor):
    """
    Extracts metadata from SQL databases using a connection string.
    This is a generic extractor that can work with different SQL dialects.
    
    The connection string should be in SQLAlchemy format, for example:
    - MySQL: mysql+pymysql://username:password@host:port/database
    - PostgreSQL: postgresql://username:password@host:port/database
    - Oracle: oracle://username:password@host:port/service
    - SQL Server: mssql+pyodbc://username:password@host:port/database?driver=ODBC+Driver+17+for+SQL+Server
    """

    def __init__(self, request_id: str, connector_name: str, connection_string: str):
        self.db_processor = DBConnectionStringProcessor(connection_string=connection_string)
        super().__init__(request_id, connector_name, Source.SQL_DATABASE_CONNECTION)

    @log_function_call
    def extract_tables(self):
        """Extract all tables from the database and optionally save them to the database"""
        model_data = {}
        model_type = SourceModelType.SQL_DATABASE_TABLE  # Use SQL_DATABASE_TABLE model type
        
        try:
            # Get connection to run queries
            connection = self.db_processor.get_connection()
            
            # Try to detect database dialect to use the appropriate metadata queries
            dialect = self._detect_dialect(connection)
            print(f"Dialect: {dialect}")
            if dialect == 'postgresql':
                model_data = self._extract_postgres_tables(connection)
            elif dialect == 'mysql':
                model_data = self._extract_mysql_tables(connection)
            elif dialect == 'mssql':
                model_data = self._extract_mssql_tables(connection)
            elif dialect == 'oracle':
                model_data = self._extract_oracle_tables(connection)
            elif dialect == 'sqlite':
                model_data = self._extract_sqlite_tables(connection)
            else:
                # Generic approach - try a basic SQL query that should work on most SQL databases
                model_data = self._extract_generic_tables(connection)
            
            # Close the connection
            connection.close()

            logger.info(f"Extracted {len(model_data)} tables from SQL database")
            
        except Exception as e:
            logger.error(f'Error extracting SQL database tables: {e}')
        
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
    
    def _detect_dialect(self, connection):
        """Attempt to detect database dialect from connection"""
        try:
            dialect = connection.engine.dialect.name.lower()
            return dialect
        except Exception as e:
            logger.warning(f"Could not detect SQL dialect: {e}")
            return None
    
    def _extract_postgres_tables(self, connection):
        """Extract tables from PostgreSQL database"""
        model_data = {}
        try:
            # Get database name
            db_name_query = "SELECT current_database();"
            db_name_result = connection.execute(db_name_query)
            db_name = db_name_result.scalar()
            
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
            
            tables_result = connection.execute(tables_query)
            tables = [dict(row) for row in tables_result]
            
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
                
                columns_result = connection.execute(columns_query)
                columns = [dict(row) for row in columns_result]
                
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
                
                pk_result = connection.execute(pk_query)
                primary_keys = [dict(row) for row in pk_result]
                pk_columns = [pk['column_name'] for pk in primary_keys]
                
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
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{schema_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "description": table.get("table_description", ""),
                    "size": table.get("table_size", ""),
                    "columns": processed_columns,
                    "primary_keys": pk_columns
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting PostgreSQL tables: {e}')
            
        return model_data
    
    def _extract_mysql_tables(self, connection):
        """Extract tables from MySQL database"""
        model_data = {}
        try:
            # Get database name
            db_name_query = "SELECT DATABASE();"
            db_name_result = connection.execute(db_name_query)
            db_name = db_name_result.scalar()
            
            # Get tables list
            tables_query = """
            SELECT 
                table_name,
                table_comment as table_description,
                engine,
                table_rows,
                data_length + index_length as total_size
            FROM 
                information_schema.tables 
            WHERE 
                table_schema = DATABASE()
                AND table_type = 'BASE TABLE'
            ORDER BY 
                table_name;
            """
            
            tables_result = connection.execute(tables_query)
            tables = [dict(row) for row in tables_result]
            
            for table in tables:
                table_name = table['table_name']
                
                # Get columns
                columns_query = f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable = 'YES' as is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    column_comment as column_description,
                    column_key = 'PRI' as is_primary_key
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = DATABASE()
                    AND table_name = '{table_name}'
                ORDER BY 
                    ordinal_position;
                """
                
                columns_result = connection.execute(columns_query)
                columns = [dict(row) for row in columns_result]
                
                # Process columns
                processed_columns = []
                pk_columns = []
                
                for column in columns:
                    is_pk = column.get('is_primary_key', False)
                    if is_pk:
                        pk_columns.append(column['column_name'])
                        
                    column_data = {
                        "name": column["column_name"],
                        "data_type": column["data_type"],
                        "is_nullable": column["is_nullable"],
                        "default_value": column.get("column_default"),
                        "is_primary_key": is_pk,
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
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": "",  # MySQL doesn't use schemas in the same way as PostgreSQL
                    "table_name": table_name,
                    "description": table.get("table_description", ""),
                    "size": str(table.get("total_size", "")),
                    "columns": processed_columns,
                    "primary_keys": pk_columns
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting MySQL tables: {e}')
            
        return model_data
    
    def _extract_generic_tables(self, connection):
        """A generic method to extract basic table and column information
        This should work for most SQL databases, but with limited detail"""
        model_data = {}
        try:
            # Try to get database name (different SQL dialects use different methods)
            db_name = None
            for query in [
                "SELECT current_database()",  # PostgreSQL
                "SELECT DATABASE()",          # MySQL
                "SELECT db_name()",           # SQL Server
                "SELECT database()",          # Generic
                "SELECT sys_context('userenv', 'db_name') FROM dual"  # Oracle
            ]:
                try:
                    result = connection.execute(query)
                    db_name = result.scalar()
                    if db_name:
                        break
                except:
                    continue
                    
            if not db_name:
                db_name = "unknown_database"
                
            # For most databases, information_schema.tables exists
            tables_query = """
            SELECT table_name, table_schema
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('information_schema', 'sys', 'performance_schema')
            """
            
            try:
                tables_result = connection.execute(tables_query)
                tables = [dict(row) for row in tables_result]
            except:
                # If information_schema.tables doesn't exist, try metadata approach
                # SQLAlchemy can introspect this information
                from sqlalchemy import inspect
                inspector = inspect(connection.engine)
                tables = []
                
                # Get all schema names
                try:
                    schemas = inspector.get_schema_names()
                except:
                    schemas = [None]  # Default schema
                    
                for schema in schemas:
                    if schema in ('information_schema', 'sys', 'performance_schema'):
                        continue
                        
                    for table_name in inspector.get_table_names(schema=schema):
                        tables.append({'table_name': table_name, 'table_schema': schema or 'public'})
            
            # For each table, extract column information
            for table in tables:
                table_name = table['table_name']
                schema_name = table.get('table_schema', 'public')
                
                try:
                    # Try to get columns from information_schema
                    columns_query = f"""
                    SELECT 
                        column_name, 
                        data_type,
                        is_nullable
                    FROM 
                        information_schema.columns
                    WHERE 
                        table_name = '{table_name}'
                    """
                    
                    if schema_name:
                        columns_query += f" AND table_schema = '{schema_name}'"
                        
                    columns_result = connection.execute(columns_query)
                    columns = [dict(row) for row in columns_result]
                    
                    if not columns:
                        raise Exception("No columns found")
                        
                except:
                    # Use SQLAlchemy inspector as fallback
                    from sqlalchemy import inspect
                    inspector = inspect(connection.engine)
                    columns = []
                    
                    # Get column information
                    for column in inspector.get_columns(table_name, schema=schema_name if schema_name != 'public' else None):
                        columns.append({
                            'column_name': column['name'],
                            'data_type': str(column['type']),
                            'is_nullable': column.get('nullable', True)
                        })
                
                # Try to get primary key information
                primary_keys = []
                try:
                    from sqlalchemy import inspect
                    inspector = inspect(connection.engine)
                    pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name if schema_name != 'public' else None)
                    if pk_constraint and 'constrained_columns' in pk_constraint:
                        primary_keys = pk_constraint['constrained_columns']
                except Exception as e:
                    logger.warning(f"Could not get primary key for {schema_name}.{table_name}: {e}")
                
                # Process columns
                processed_columns = []
                for column in columns:
                    column_data = {
                        "name": column["column_name"],
                        "data_type": column["data_type"],
                        "is_nullable": column.get("is_nullable", True),
                        "is_primary_key": column["column_name"] in primary_keys
                    }
                    processed_columns.append(column_data)
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{schema_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "columns": processed_columns,
                    "primary_keys": primary_keys
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting generic SQL tables: {e}')
            
        return model_data
        
    def _extract_mssql_tables(self, connection):
        """Extract tables from Microsoft SQL Server database"""
        model_data = {}
        try:
            # Get database name
            db_name_query = "SELECT DB_NAME();"
            db_name_result = connection.execute(db_name_query)
            db_name = db_name_result.scalar()
            
            # Get tables list
            tables_query = """
            SELECT 
                t.name AS table_name,
                s.name AS schema_name,
                CAST(ep.value AS NVARCHAR(MAX)) AS table_description
            FROM 
                sys.tables t
            JOIN 
                sys.schemas s ON t.schema_id = s.schema_id
            LEFT JOIN 
                sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            WHERE 
                t.type = 'U'
            ORDER BY 
                s.name, t.name;
            """
            
            tables_result = connection.execute(tables_query)
            tables = [dict(row) for row in tables_result]
            
            for table in tables:
                table_name = table['table_name']
                schema_name = table['schema_name']
                
                # Get columns
                columns_query = f"""
                SELECT 
                    c.name AS column_name,
                    t.name AS data_type,
                    c.is_nullable,
                    c.column_id,
                    CAST(ep.value AS NVARCHAR(MAX)) AS column_description
                FROM 
                    sys.columns c
                JOIN 
                    sys.types t ON c.user_type_id = t.user_type_id
                JOIN 
                    sys.tables tbl ON c.object_id = tbl.object_id
                JOIN 
                    sys.schemas s ON tbl.schema_id = s.schema_id
                LEFT JOIN 
                    sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
                WHERE 
                    tbl.name = '{table_name}'
                    AND s.name = '{schema_name}'
                ORDER BY 
                    c.column_id;
                """
                
                columns_result = connection.execute(columns_query)
                columns = [dict(row) for row in columns_result]
                
                # Get primary key information
                pk_query = f"""
                SELECT 
                    c.name AS column_name
                FROM 
                    sys.index_columns ic
                JOIN 
                    sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                JOIN 
                    sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                JOIN 
                    sys.tables t ON c.object_id = t.object_id
                JOIN 
                    sys.schemas s ON t.schema_id = s.schema_id
                WHERE 
                    i.is_primary_key = 1
                    AND t.name = '{table_name}'
                    AND s.name = '{schema_name}'
                ORDER BY 
                    ic.key_ordinal;
                """
                
                pk_result = connection.execute(pk_query)
                primary_keys = [dict(row) for row in pk_result]
                pk_columns = [pk['column_name'] for pk in primary_keys]
                
                # Process columns
                processed_columns = []
                for column in columns:
                    column_data = {
                        "name": column["column_name"],
                        "data_type": column["data_type"],
                        "is_nullable": bool(column["is_nullable"]),
                        "is_primary_key": column["column_name"] in pk_columns,
                        "description": column.get("column_description", "")
                    }
                    processed_columns.append(column_data)
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{schema_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "description": table.get("table_description", ""),
                    "columns": processed_columns,
                    "primary_keys": pk_columns
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting SQL Server tables: {e}')
            
        return model_data
    
    def _extract_oracle_tables(self, connection):
        """Extract tables from Oracle database"""
        model_data = {}
        try:
            # Get database name (for Oracle, it's usually the schema/user)
            db_name_query = "SELECT SYS_CONTEXT('USERENV', 'DB_NAME') FROM DUAL"
            db_name_result = connection.execute(db_name_query)
            db_name = db_name_result.scalar()
            
            # Get current schema/user
            schema_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL"
            schema_result = connection.execute(schema_query)
            current_schema = schema_result.scalar()
            
            # Get tables list
            tables_query = f"""
            SELECT 
                table_name,
                comments as table_description 
            FROM 
                all_tab_comments 
            WHERE 
                owner = '{current_schema}' 
                AND table_type = 'TABLE'
            ORDER BY 
                table_name
            """
            
            tables_result = connection.execute(tables_query)
            tables = [dict(row) for row in tables_result]
            
            for table in tables:
                table_name = table['table_name']
                
                # Get columns
                columns_query = f"""
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.nullable = 'Y' as is_nullable,
                    c.data_default as column_default,
                    c.char_length as character_maximum_length,
                    c.data_precision as numeric_precision,
                    c.data_scale as numeric_scale,
                    cc.comments as column_description
                FROM 
                    all_tab_columns c
                LEFT JOIN 
                    all_col_comments cc ON c.owner = cc.owner AND c.table_name = cc.table_name AND c.column_name = cc.column_name
                WHERE 
                    c.owner = '{current_schema}'
                    AND c.table_name = '{table_name}'
                ORDER BY 
                    c.column_id
                """
                
                columns_result = connection.execute(columns_query)
                columns = [dict(row) for row in columns_result]
                
                # Get primary key information
                pk_query = f"""
                SELECT 
                    cols.column_name
                FROM 
                    all_constraints cons
                JOIN 
                    all_cons_columns cols ON cons.constraint_name = cols.constraint_name AND cons.owner = cols.owner
                WHERE 
                    cons.owner = '{current_schema}'
                    AND cons.table_name = '{table_name}'
                    AND cons.constraint_type = 'P'
                ORDER BY 
                    cols.position
                """
                
                pk_result = connection.execute(pk_query)
                primary_keys = [dict(row) for row in pk_result]
                pk_columns = [pk['column_name'] for pk in primary_keys]
                
                # Process columns
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
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{current_schema}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": current_schema,
                    "table_name": table_name,
                    "description": table.get("table_description", ""),
                    "columns": processed_columns,
                    "primary_keys": pk_columns
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting Oracle tables: {e}')
            
        return model_data
    
    def _extract_sqlite_tables(self, connection):
        """Extract tables from SQLite database"""
        model_data = {}
        try:
            # For SQLite, we use the database file name as the database name
            db_path = connection.engine.url.database
            db_name = db_path.split('/')[-1] if '/' in db_path else db_path
            
            # Get tables list
            tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            tables_result = connection.execute(tables_query)
            tables = [{'table_name': row[0]} for row in tables_result]
            
            for table in tables:
                table_name = table['table_name']
                
                # Get columns and their info using PRAGMA
                columns_query = f"PRAGMA table_info('{table_name}')"
                columns_result = connection.execute(columns_query)
                columns = [dict(row) for row in columns_result]
                
                # Process columns
                processed_columns = []
                pk_columns = []
                
                for column in columns:
                    is_pk = bool(column.get('pk', 0))
                    if is_pk:
                        pk_columns.append(column['name'])
                        
                    column_data = {
                        "name": column["name"],
                        "data_type": column["type"],
                        "is_nullable": not column.get("notnull", 0),
                        "default_value": column.get("dflt_value"),
                        "is_primary_key": is_pk
                    }
                    processed_columns.append(column_data)
                
                # Create unique model_uid for the table
                model_uid = f"{db_name}.{table_name}"
                
                # Build complete table metadata
                table_metadata = {
                    "database_name": db_name,
                    "schema_name": "main",  # SQLite uses 'main' as the default schema
                    "table_name": table_name,
                    "columns": processed_columns,
                    "primary_keys": pk_columns
                }
                
                model_data[model_uid] = table_metadata
                
        except Exception as e:
            logger.error(f'Error extracting SQLite tables: {e}')
            
        return model_data 