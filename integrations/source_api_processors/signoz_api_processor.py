import logging

import requests

from integrations.processor import Processor
from protos.base_pb2 import TimeRange

logger = logging.getLogger(__name__)


class SignozApiProcessor(Processor):
    def __init__(self, signoz_api_url, signoz_api_token=None):
        self.signoz_api_url = signoz_api_url.rstrip("/") if signoz_api_url else ""
        
        if not self.signoz_api_url:
            raise ValueError("SignozApiProcessor: API URL cannot be empty")
            
        # Set default headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication if provided
        if signoz_api_token:
            # Use SIGNOZ-API-KEY header for authentication instead of Authorization
            self.headers["SIGNOZ-API-KEY"] = signoz_api_token
            
            logger.debug(f"SignozApiProcessor initialized with URL: {self.signoz_api_url} and API key")
        else:
            logger.warning("SignozApiProcessor initialized without API key")
    
    def test_connection(self):
        """Test the connection to Signoz API"""
        try:
            response = requests.get(
                f"{self.signoz_api_url}/api", 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code < 300:
                return True
            else:
                logger.error(f"Failed to connect to Signoz API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception when testing connection to Signoz API: {e}")
            raise e
    
    def fetch_dashboards(self):
        """Fetch all dashboards from Signoz"""
        try:
            response = requests.get(
                f"{self.signoz_api_url}/api/v1/dashboards", 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch dashboards: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when fetching dashboards: {e}")
            raise e
    
    def fetch_dashboard_details(self, dashboard_id):
        """Fetch details of a specific dashboard"""
        try:
            print(f"Fetching dashboard details for {dashboard_id}")
            response = requests.get(
                f"{self.signoz_api_url}/api/v1/dashboards/{dashboard_id}", 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                logger.error(f"Failed to fetch dashboard details: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when fetching dashboard details: {e}")
            raise e
    
    def fetch_alerts(self):
        """Fetch all alerts from Signoz"""
        try:
            # Make a debug log of the headers and URL being used
            logger.debug(f"Fetching alerts from: {self.signoz_api_url}/api/v1/alerts")
            logger.debug(f"Using headers: {self.headers}")
            
            response = requests.get(
                f"{self.signoz_api_url}/api/v1/alerts", 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch alerts: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when fetching alerts: {e}")
            raise e
    
    def fetch_alert_details(self, alert_id):
        """Fetch details of a specific alert"""
        try:
            response = requests.get(
                f"{self.signoz_api_url}/api/v1/alerts/{alert_id}", 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch alert details: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when fetching alert details: {e}")
            raise e
    
    def query_metrics(self, time_range: TimeRange, query, step=None, aggregation=None):
        """Query metrics from Signoz ClickhouseDB"""
        try:
            from_time = int(time_range.time_geq * 1000)
            to_time = int(time_range.time_lt * 1000)
            
            payload = {
                "query": query,
                "start": from_time,
                "end": to_time
            }
            
            if step:
                payload["step"] = step
                
            if aggregation:
                payload["aggregation"] = aggregation
            
            response = requests.post(
                f"{self.signoz_api_url}/api/v1/metrics/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to query metrics: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when querying metrics: {e}")
            raise e
    
    def query_dashboard_panel(self, time_range: TimeRange, dashboard_id, panel_id):
        """Query metrics for a specific dashboard panel"""
        try:
            # First get the dashboard details to extract the panel query
            dashboard = self.fetch_dashboard_details(dashboard_id)
            if not dashboard:
                logger.error(f"Failed to fetch dashboard {dashboard_id}")
                return None
            
            panel = None
            for p in dashboard.get("panels", []):
                if p.get("id") == panel_id:
                    panel = p
                    break
            
            if not panel:
                logger.error(f"Panel {panel_id} not found in dashboard {dashboard_id}")
                return None
            
            # Extract query from panel
            queries = panel.get("queries", [])
            if not queries:
                logger.error(f"No queries found in panel {panel_id}")
                return None
            
            # Execute each query
            results = []
            for query in queries:
                query_result = self.query_metrics(
                    time_range,
                    query.get("query"),
                    step=panel.get("step"),
                    aggregation=panel.get("aggregation")
                )
                if query_result:
                    results.append(query_result)
            
            return {
                "panel": panel,
                "results": results
            }
        except Exception as e:
            logger.error(f"Exception when querying dashboard panel: {e}")
            raise e

    def execute_signoz_query(self, query_payload):
        """Execute a Clickhouse SQL query using the Signoz query range API"""
        try:
            logger.debug(f"Executing Clickhouse query with payload: {query_payload}")
            
            response = requests.post(
                f"{self.signoz_api_url}/api/v4/query_range",
                headers=self.headers,
                json=query_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to execute Clickhouse query: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception when executing Clickhouse query: {e}")
            raise e 