import logging

from sqlalchemy import create_engine, text

from integrations.processor import Processor

logger = logging.getLogger(__name__)


class DBConnectionStringProcessor(Processor):
    client = None

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_connection(self):
        try:
            engine = create_engine(self.connection_string)
            connection = engine.connect()
            return connection
        except Exception as e:
            logger.error(f"Exception occurred while creating db connection with error: {e}")
            raise e

    def test_connection(self):
        try:
            connection = self.get_connection()
            result = connection.execute(text("SELECT 1"))
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Exception occurred while testing db connection connection with error: {e}")
            raise e

    def get_query_result(self, query, timeout=120):
        try:
            connection = self.get_connection()
            result = connection.execution_options(timeout=timeout).execute(text(query))
            connection.close()
            return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching postgres databases with error: {e}")
            raise e
