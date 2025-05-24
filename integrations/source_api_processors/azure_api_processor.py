import logging
import os
from datetime import timedelta, datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.monitor.query import LogsQueryClient, MetricsQueryClient
from azure.mgmt.resource import ResourceManagementClient

from integrations.processor import Processor

logger = logging.getLogger(__name__)


def query_response_to_dict(response):
    """
    Function to convert query response tables to dictionaries.
    """
    result = {}
    for table in response.tables:
        result[table.name] = []
        for row in table.rows:
            row_dict = {}
            for i, column in enumerate(table.columns):
                row_dict[column] = str(row[i])
            result[table.name].append(row_dict)
    return result


class AzureApiProcessor(Processor):
    client = None

    def __init__(self, subscription_id, tenant_id, client_id, client_secret):
        self.__subscription_id = subscription_id
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__tenant_id = tenant_id

        if not self.__client_id or not self.__client_secret or not self.__tenant_id:
            raise Exception("Azure Connection Error:: Missing client_id, client_secret, or tenant_id")

    def get_credentials(self):
        """
        Function to fetch Azure credentials using client_id, client_secret, and tenant_id.
        """
        os.environ['AZURE_CLIENT_ID'] = self.__client_id
        os.environ['AZURE_CLIENT_SECRET'] = self.__client_secret
        os.environ['AZURE_TENANT_ID'] = self.__tenant_id
        credential = DefaultAzureCredential()
        return credential 

    def test_connection(self):
        try:
            credentials = self.get_credentials()
            if not credentials:
                logger.error("Azure Connection Error:: Failed to get credentials")
                raise Exception("Azure Connection Error:: Failed to get credentials")
            log_analytics_client = LogAnalyticsManagementClient(credentials, self.__subscription_id)
            workspaces = log_analytics_client.workspaces.list()
            if not workspaces:
                raise Exception("Azure Connection Error:: No Workspaces Found")
            az_workspaces = []
            for workspace in workspaces:
                az_workspaces.append(workspace.as_dict())
            if len(az_workspaces) > 0:
                return True
            else:
                raise Exception("Azure Connection Error:: No Workspaces Found")
        except Exception as e:
            raise e

    def fetch_workspaces(self):
        try:
            credentials = self.get_credentials()
            if not credentials:
                logger.error("Azure Connection Error:: Failed to get credentials")
                return None
            log_analytics_client = LogAnalyticsManagementClient(credentials, self.__subscription_id)
            workspaces = log_analytics_client.workspaces.list()
            if not workspaces:
                logger.error("Azure Connection Error:: No Workspaces Found")
                return None
            return [workspace.as_dict() for workspace in workspaces]
        except Exception as e:
            logger.error(f"Failed to fetch workspaces with error: {e}")
            return None

    def fetch_resources(self):
        try:
            credentials = self.get_credentials()
            if not credentials:
                logger.error("Azure Connection Error:: Failed to get credentials")
                return None
            resource_client = ResourceManagementClient(credentials, self.__subscription_id)
            metrics_client = MetricsQueryClient(credentials)
            resources = resource_client.resources.list()
            if not resources:
                logger.error("Azure Connection Error:: No Resources Found")
                return None
            
            # Only include resources that actually produce metrics
            metric_producing_types = [
                "Microsoft.Compute/virtualMachines",
                "Microsoft.ContainerService/managedClusters",
                "Microsoft.Network/loadBalancers",
                "Microsoft.Network/applicationGateways",
                "Microsoft.Storage/storageAccounts",
                "Microsoft.Sql/servers/databases",
                "Microsoft.Web/sites",
                "Microsoft.Insights/components"
            ]
            # valid_resources = [
            #     resource.as_dict() for resource in resources
            #     if resource.type in metric_producing_types
            # ]
            valid_resources = []
            for resource in resources:
                if resource.type in metric_producing_types:
                    resource_dict = resource.as_dict()

                    # Get resource metrics
                    resource_id = resource.id
                    try:
                        metric_names = metrics_client.list_metric_definitions(resource_id)
                        metric_names = [metric.name for metric in metric_names]
                    except Exception as e:
                        logger.error(f"Failed to fetch metrics for resource {resource_id} with error: {e}")
                        metric_names = []

                    resource_dict["available_metrics"] = {"metric_names": metric_names}
                    valid_resources.append(resource_dict)
            return valid_resources
        except Exception as e:
            logger.error(f"Failed to fetch resources with error: {e}")
            return None

    def query_log_analytics(self, workspace_id, query, timespan=timedelta(hours=4)):
        try:
            credentials = self.get_credentials()
            if not credentials:
                logger.error("Azure Connection Error:: Failed to get credentials")
                return None
            client = LogsQueryClient(credentials)
            response = client.query_workspace(workspace_id, query, timespan=timespan)
            if not response:
                logger.error(f"Failed to query log analytics with error: {response.text}")
                return None
            results = query_response_to_dict(response)
            return results
        except Exception as e:
            logger.error(f"Failed to query log analytics with error: {e}")
            return None


    # Vidushee was here
    def query_metrics(self, resource_id, time_range, metric_names="Percentage CPU", aggregation="Average", granularity=300): # placeholer metric name
        """
        Function to fetch metrics from Azure Monitor.
        
        Parameters:
            resource_id (str): The Azure resource ID to fetch metrics for.
            metric_names (str): The names of the metric to retrieve.
            timespan (timedelta): The time range for fetching metrics.
            aggregation (str): The type of aggregation (e.g., 'Average', 'Total', 'Count', etc.).
        
        Returns:
            dict: A dictionary containing the retrieved metrics.
        """
        try:
            credentials = self.get_credentials()
            if not credentials:
                logger.error("Azure Connection Error:: Failed to get credentials")
                return None
    
            # Create Metrics Query Client
            client = MetricsQueryClient(credentials)
            # Convert Unix timestamps (in seconds) to datetime
            from_tr = datetime.fromtimestamp(time_range.time_geq, tz=timezone.utc)  # Convert start time to datetime
            to_tr = datetime.fromtimestamp(time_range.time_lt, tz=timezone.utc)  # Convert end time to datetime

            # total_seconds = (to_tr - from_tr).total_seconds()
            # Compute granularity dynamically (max 12 points)
            # granularity_seconds = total_seconds / 12  # Each interval should be total duration / 12
            # Convert to ISO 8601 duration string
            # if granularity_seconds < 60:
            #     granularity = f"PT{int(granularity_seconds)}S"  # Seconds
            # elif granularity_seconds < 3600:
            #     granularity = f"PT{int(granularity_seconds / 60)}M"  # Minutes
            # else:
            #     granularity = f"PT{int(granularity_seconds / 3600)}H"  # Hours

            # Ensure metric_names is always a list
            if isinstance(metric_names, str):
                metric_names = [m.strip() for m in metric_names.split(",")]  # Split by comma if needed

            # Fetch metrics
            response = client.query_resource(
                resource_uri=resource_id,
                metric_names=metric_names,
                timespan=(from_tr, to_tr),
                granularity=timedelta(seconds=granularity),
                aggregations=[aggregation],
            )
            
            # Convert response to a dictionary
            if not response:
                logger.error(f"Failed to fetch metrics with error: {response.text}")
                return None

            results = {}
            for metric in response.metrics:
                results[metric.name] = [
                    {
                        "timestamp": data.timestamp.isoformat(),
                        "value": data.total if aggregation == "Total" else data.average
                    }
                    for data in metric.timeseries[0].data
                ]

            return results

        except Exception as e:
            logger.error(f"Failed to fetch metrics with error: {e}")
            return None