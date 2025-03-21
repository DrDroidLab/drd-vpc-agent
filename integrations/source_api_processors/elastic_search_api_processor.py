import logging

from elasticsearch import Elasticsearch

from integrations.processor import Processor

logger = logging.getLogger(__name__)


class ElasticSearchApiProcessor(Processor):
    client = None

    def __init__(self, protocol: str, host: str, port: str, api_key_id: str, api_key: str, verify_certs: bool = False):
        self.protocol = protocol
        self.host = host
        self.port = int(port) if port else 9200
        self.verify_certs = verify_certs
        self.__api_key_id = api_key_id
        self.__api_key = api_key

    def get_connection(self):
        try:
            client = Elasticsearch(
                [f"{self.protocol}://{self.host}:{self.port}"],
                api_key=(self.__api_key_id, self.__api_key),
                verify_certs=self.verify_certs
            )
            return client
        except Exception as e:
            logger.error(f"Exception occurred while creating elasticsearch connection with error: {e}")
            raise e

    def test_connection(self):
        try:
            connection = self.get_connection()
            indices = connection.indices.get_alias()
            connection.close()
            if len(list(indices.keys())) > 0:
                return True
            else:
                raise Exception("Elasticsearch Connection Error:: No indices found in elasticsearch")
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch indices with error: {e}")
            raise e

    def fetch_indices(self):
        try:
            connection = self.get_connection()
            indices = connection.indices.get_alias()
            connection.close()
            return list(indices.keys())
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch indices with error: {e}")
            raise e

    def query(self, index, query):
        try:
            connection = self.get_connection()
            result = connection.search(index=index, body=query, pretty=True)
            connection.close()
            return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch data with error: {e}")
            raise e

    def get_document(self, index, doc_id):
        try:
            connection = self.get_connection()
            result = connection.get(index=index, id=doc_id, pretty=True, preference="_primary_first")
            connection.close()
            return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch data with error: {e}")
            raise e
    def get_cluster_health(self):
        try:
            connection = self.get_connection()
            result = connection.cluster.health()
            connection.close()
            
            # Convert ObjectApiResponse to dict
            if hasattr(result, 'body'):
                # For Elasticsearch 8.x client
                return result.body
            elif hasattr(result, 'meta'):
                # Alternative approach for some client versions
                return dict(result)
            else:
                # Fallback for older client versions
                return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch cluster health with error: {e}")
            raise e
            
    def get_nodes_stats(self):
        try:
            connection = self.get_connection()
            result = connection.nodes.stats()
            connection.close()
            
            # Convert response to dict
            if hasattr(result, 'body'):
                return result.body
            elif hasattr(result, 'meta'):
                return dict(result)
            else:
                return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch nodes stats with error: {e}")
            raise e

    def get_cat_indices(self):
        try:
            connection = self.get_connection()
            result = connection.cat.indices(v=True, format="json")
            connection.close()
            
            # Convert response to dict
            if hasattr(result, 'body'):
                return result.body
            elif hasattr(result, 'meta'):
                return dict(result)
            else:
                return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch cat indices with error: {e}")
            raise e

    def get_cat_thread_pool_search(self):
        try:
            connection = self.get_connection()
            result = connection.cat.thread_pool(thread_pool_patterns="search", v=True, format="json")
            connection.close()
            
            # Convert response to dict
            if hasattr(result, 'body'):
                return result.body
            elif hasattr(result, 'meta'):
                return dict(result)
            else:
                return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching elasticsearch cat thread pool search with error: {e}")
            raise e