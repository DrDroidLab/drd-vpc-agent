import json
import logging

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

from integrations.processor import Processor

logger = logging.getLogger(__name__)


def get_gcm_credentials(service_account_json_str):
    service_account_json = json.loads(service_account_json_str)
    scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/monitoring.read"]
    credentials = service_account.Credentials.from_service_account_info(service_account_json, scopes=scopes)

    # Refresh the credentials
    auth_req = Request()
    credentials.refresh(auth_req)

    return credentials


class GcmApiProcessor(Processor):
    def __init__(self, project_id, service_account_json):
        self.__service_account_json = service_account_json
        self.__project_id = project_id
        self.__credentials = get_gcm_credentials(self.__service_account_json)

    def test_connection(self):
        try:
            service = build('monitoring', 'v3', credentials=self.__credentials)
            request = service.projects().metricDescriptors().list(name=f"projects/{self.__project_id}")
            response = request.execute()
            if len(response.get('metricDescriptors', [])) > 0:
                return True
            else:
                raise Exception("Failed to connect with GCM. No metric descriptors found")
        except Exception as e:
            logger.error(f"Exception occurred while testing connection: {e}")
            raise e

    def fetch_metrics(self, metric_type, start_time, end_time):
        try:
            service = build('monitoring', 'v3', credentials=self.__credentials)
            request = service.projects().timeSeries().list(
                name=f"projects/{self.__project_id}",
                filter=f'metric.type="{metric_type}"',
                interval_startTime=start_time.isoformat() + 'Z',
                interval_endTime=end_time.isoformat() + 'Z',
                view='FULL'
            )
            response = request.execute()
            return response.get('timeSeries', [])
        except Exception as e:
            logger.error(f"Exception occurred while fetching metrics: {e}")
            raise e

    def fetch_metrics_list(self):
        try:
            service = build('monitoring', 'v3', credentials=self.__credentials)
            request = service.projects().metricDescriptors().list(name=f"projects/{self.__project_id}")
            response = request.execute()
            return response.get('metricDescriptors', [])
        except Exception as e:
            logger.error(f"Exception occurred while fetching metric descriptors: {e}")
            raise e

    def fetch_logs(self, filter_str, order_by="timestamp desc", page_size=2000, page_token=None, resource_names=None):
        try:
            service = build('logging', 'v2', credentials=self.__credentials)
            resource_names = resource_names or [f"projects/{self.__project_id}"]
            body = {
                "resourceNames": resource_names,
                "filter": filter_str,
                "orderBy": order_by,
                "pageSize": page_size
            }
            if page_token:
                body['pageToken'] = page_token

            logger.debug(f"Fetching logs with body: {body}")

            request = service.entries().list(body=body)
            response = request.execute()

            logger.debug(f"Received response: {response}")

            return response.get('entries', [])
        except Exception as e:
            logger.error(f"Exception occurred while fetching logs: {e}")
            raise e

    def execute_mql(self, query, project_id):
        try:
            service = build('monitoring', 'v3', credentials=self.__credentials)
            request = service.projects().timeSeries().query(
                name=f"projects/{project_id}",
                body={"query": query}
            )
            response = request.execute()

            logger.debug(f"MQL Query Response: {response}")

            if 'timeSeriesData' in response:
                time_series_data = response['timeSeriesData']
                return time_series_data
            else:
                logger.error("'timeSeriesData' not found in response")

            return []
        except Exception as e:
            logger.error(f"Exception occurred while executing MQL query: {e}")
            raise e
