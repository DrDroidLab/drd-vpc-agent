import logging
from datetime import datetime, timedelta

import boto3
import requests
from botocore.exceptions import ClientError
from django.conf import settings

from integrations.processor import Processor
from utils.time_utils import current_milli_time

logger = logging.getLogger(__name__)


def generate_aws_access_secret_session_key(aws_assumed_role_arn, aws_drd_cloud_role_arn):
    default_session = boto3.setup_default_session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                                  region_name=settings.AWS_REGION)
    uuid = str(current_milli_time())
    role_session_name = "drd_session" + uuid
    sts_client = boto3.client('sts', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION)

    assumed_role = sts_client.assume_role(
        RoleArn=aws_drd_cloud_role_arn,
        RoleSessionName=role_session_name
    )

    aws_access_key_id = assumed_role['Credentials']['AccessKeyId']
    aws_secret_access_key = assumed_role['Credentials']['SecretAccessKey']
    aws_session_token = assumed_role['Credentials']['SessionToken']
    region_name = 'us-west-2'

    assumed_client = boto3.client('sts', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key, aws_session_token=aws_session_token,
                                  region_name=region_name)

    # Assume the Prodigal role
    assumed_role_2 = assumed_client.assume_role(
        RoleArn=aws_assumed_role_arn,
        RoleSessionName="client_session"
    )

    return {'aws_access_key': assumed_role_2['Credentials']['AccessKeyId'],
            'aws_secret_key': assumed_role_2['Credentials']['SecretAccessKey'],
            'aws_session_token': assumed_role_2['Credentials']['SessionToken']}

class AWSBoto3ApiProcessor(Processor):
    def __init__(self, client_type, region, aws_access_key=None, aws_secret_key=None, aws_assumed_role_arn=None,
                 aws_drd_cloud_role_arn=None):

        if (not aws_access_key or not aws_secret_key) and not (aws_assumed_role_arn or not aws_drd_cloud_role_arn):
            raise Exception("Received invalid AWS Credentials")

        self.client_type = client_type
        self.__aws_access_key = aws_access_key
        self.__aws_secret_key = aws_secret_key
        self.region = region
        self.__aws_session_token = None
        if aws_assumed_role_arn:
            credentials = generate_aws_access_secret_session_key(aws_assumed_role_arn, aws_drd_cloud_role_arn)
            self.__aws_access_key = credentials['aws_access_key']
            self.__aws_secret_key = credentials['aws_secret_key']
            self.__aws_session_token = credentials['aws_session_token']

    def get_connection(self):
        try:
            client = boto3.client(self.client_type, aws_access_key_id=self.__aws_access_key,
                                  aws_secret_access_key=self.__aws_secret_key, region_name=self.region,
                                  aws_session_token=self.__aws_session_token)
            return client
        except Exception as e:
            logger.error(f"Exception occurred while creating boto3 client with error: {e}")
            raise e

    def test_connection(self):
        try:
            if self.client_type == 'cloudwatch':
                client = self.get_connection()
                response = client.list_metrics()
                if response:
                    return True
                else:
                    raise Exception("No metrics found in the cloudwatch connection")
            elif self.client_type == 'logs':
                log_groups = self.logs_describe_log_groups()
                if log_groups:
                    return True
                else:
                    raise Exception("No log groups found in the logs connection")
        except Exception as e:
            logger.error(f"Exception occurred while testing cloudwatch connection with error: {e}")
            raise e

    def cloudwatch_describe_alarms(self, alarm_names):
        try:
            client = self.get_connection()
            response = client.describe_alarms(AlarmNames=alarm_names)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200 and response['MetricAlarms']:
                return response['MetricAlarms']
            else:
                print(f"No alarms found for '{alarm_names}'")
        except Exception as e:
            logger.error(
                f"Exception occurred while fetching cloudwatch alarms for alarm_names: {alarm_names} with error: {e}")
            raise e

    def cloudwatch_describe_all_alarms(self):
        try:
            client = self.get_connection()
            response = client.describe_alarms()

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return {
                    'MetricAlarms': response.get('MetricAlarms', []),
                    'CompositeAlarms': response.get('CompositeAlarms', [])
                }
            else:
                logger.warning(
                    f"Unexpected response when fetching all CloudWatch alarms. Status code: {response['ResponseMetadata']['HTTPStatusCode']}")
                return {'MetricAlarms': [], 'CompositeAlarms': []}
        except Exception as e:
            logger.error(f"Exception occurred while fetching all CloudWatch alarms. Error: {e}")
            raise e

    def cloudwatch_list_metrics(self, namespace, token=None):
        try:
            client = self.get_connection()
            if token:
                metrics = client.list_metrics(NextToken=token, Namespace=namespace)
            else:
                metrics = client.list_metrics(Namespace=namespace)
            return metrics
        except Exception as e:
            logger.error(f"Exception occurred while fetching cloudwatch metrics with error: {e}")
            raise e

    def cloudwatch_get_metric_statistics(self, namespace, metric, start_time, end_time, period, statistics, dimensions):
        try:
            client = self.get_connection()
            response = client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=statistics,
                Dimensions=dimensions
            )
            return response
        except Exception as e:
            logger.error(
                f"Exception occurred while fetching cloudwatch metric statistics for metric: {metric} with error: {e}")
            raise e

    def logs_describe_log_groups(self):
        try:
            client = self.get_connection()
            paginator = client.get_paginator('describe_log_groups')
            log_groups = []
            for page in paginator.paginate():
                for log_group in page['logGroups']:
                    log_groups.append(log_group['logGroupName'])
            return log_groups
        except Exception as e:
            logger.error(f"Exception occurred while fetching log groups with error: {e}")
            raise e

    def logs_describe_log_group_queries(self):
        try:
            client = self.get_connection()
            paginator = client.get_paginator('describe_queries')
            all_queries = []

            for page in paginator.paginate():
                all_queries.extend(page['queries'])

            return all_queries
        except Exception as e:
            logger.error(f"Exception occurred while fetching log queries with error: {e}")
            raise e

    def logs_filter_events(self, log_group, query_pattern, start_time, end_time):
        try:
            client = self.get_connection()
            start_query_response = client.start_query(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query_pattern,
            )

            query_id = start_query_response['queryId']

            status = 'Running'
            query_start_time = current_milli_time()
            while status == 'Running' or status == 'Scheduled':
                print("Waiting for query to complete...")
                response = client.get_query_results(queryId=query_id)
                status = response['status']
                if status == 'Complete':
                    return response['results']
                elif current_milli_time() - query_start_time > 60000:
                    print("Query took too long to complete. Aborting...")
                    stop_query_response = client.stop_query(queryId=query_id)
                    print(f"Query stopped with response: {stop_query_response}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Exception occurred while fetching logs for log_group: {log_group} with error: {e}")
            raise e

    def rds_describe_instances(self, db_instance_identifier=None):
        try:
            client = self.get_connection()
            if db_instance_identifier:
                rds_instances = client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
            else:
                rds_instances = client.describe_db_instances()
            return rds_instances
        except Exception as e:
            logger.error(f"Exception occurred while fetching RDS instances with error: {e}")
            raise e

    def pi_describe_db_dimension_keys(self, resource_uri, performance_insights_metric='db.load.avg'):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        client = self.get_connection()
        response = client.describe_dimension_keys(
            ServiceType='RDS',
            Identifier=resource_uri,
            Metric=performance_insights_metric,
            StartTime=start_time,
            EndTime=end_time,
            GroupBy={
                'Group': 'db'
            }
        )
        keys = response['Keys']
        all_db_names = []
        for k in keys:
            if 'Dimensions' in k:
                for key, value in k['Dimensions'].items():
                    if key == 'db.name':
                        all_db_names.append(value)
        return list(set(all_db_names))

    def pi_get_long_running_queries(self, resource_uri, query_end_time, start_minutes_ago=60, service_type='RDS'):
        end_time = query_end_time if query_end_time else datetime.now()
        start_time = end_time - timedelta(minutes=start_minutes_ago)
        client = self.get_connection()
        try:
            response = client.describe_dimension_keys(
                ServiceType=service_type,
                Identifier=resource_uri,
                StartTime=start_time,
                EndTime=end_time,
                Metric='db.load.avg',
                PeriodInSeconds=300,
                GroupBy={
                    "Dimensions": ["db.sql_tokenized.id", "db.sql_tokenized.statement"],
                    "Group": "db.sql_tokenized",
                },
                AdditionalMetrics=[
                    "db.sql_tokenized.stats.sum_timer_wait_per_call.avg",
                    "db.sql_tokenized.stats.sum_rows_examined_per_call.avg",
                ],
            )
            query_data = []
            for dimension in response.get('Keys', []):
                sql = dimension.get('Dimensions', {}).get('db.sql_tokenized.statement', 'Unknown')
                additional_metrics = dimension.get('AdditionalMetrics', {})
                total_rows_examined = additional_metrics.get('db.sql_tokenized.stats.sum_rows_examined_per_call.avg', 0)
                total_wait_time_ms = additional_metrics.get('db.sql_tokenized.stats.sum_timer_wait_per_call.avg', 0)
                query_data.append({
                    'sql': sql,
                    'total_query_time_ms': total_wait_time_ms,
                    'total_rows_examined': total_rows_examined,
                })
            query_data.sort(key=lambda x: x['total_query_time_ms'], reverse=True)
            return query_data
        except Exception as e:
            print(f"Error fetching long-running queries: {e}")
        return []

    def pi_list_dimension_details(self, resource_uri, metric_type='db.sql_tokenized.stats'):
        try:
            client = self.get_connection()
            response = client.list_available_resource_metrics(
                ServiceType='RDS',
                Identifier=resource_uri,
                MetricTypes=[
                    metric_type,
                ],
            )
            return response
        except Exception as e:
            logger.error(f"Exception occurred while fetching PI dimension details with error: {e}")
            raise e

    # CloudWatch Dashboard Methods
    def cloudwatch_list_dashboards(self):
        """List all CloudWatch dashboards in the configured region."""
        try:
            client = self.get_connection()
            dashboards = []
            paginator = client.get_paginator('list_dashboards')

            for page in paginator.paginate():
                if 'DashboardEntries' in page:
                    dashboards.extend(page['DashboardEntries'])

            return dashboards
        except Exception as e:
            logger.error(f"Exception occurred while listing CloudWatch dashboards with error: {e}")
            return []

    def cloudwatch_get_dashboard(self, dashboard_name: str):
        """Get details of a specific CloudWatch dashboard by name."""
        try:
            client = self.get_connection()
            response = client.get_dashboard(DashboardName=dashboard_name)
            return response
        except Exception as e:
            logger.error(f"Exception occurred while getting CloudWatch dashboard '{dashboard_name}': {e}")
            return None

    # ECS Methods
    def list_all_clusters(self):
        """List all ECS clusters in the account."""
        try:
            client = self.get_connection()
            clusters = []
            paginator = client.get_paginator('list_clusters')
            
            for page in paginator.paginate():
                if 'clusterArns' in page:
                    clusters.extend(page['clusterArns'])
            
            # Get detailed information for each cluster
            if clusters:
                response = client.describe_clusters(clusters=clusters)
                return response.get('clusters', [])
            
            return []
        except Exception as e:
            logger.error(f"Exception occurred while listing ECS clusters with error: {e}")
            return None

    def list_tasks_in_cluster(self, cluster_arn):
        """List all tasks in a specific ECS cluster, including both running and stopped tasks."""
        try:
            client = self.get_connection()
            all_tasks = []
            
            # Get RUNNING tasks
            running_tasks = []
            paginator = client.get_paginator('list_tasks')
            for page in paginator.paginate(cluster=cluster_arn, desiredStatus='RUNNING'):
                if 'taskArns' in page and page['taskArns']:
                    running_tasks.extend(page['taskArns'])
            
            # Get STOPPED tasks
            stopped_tasks = []
            for page in paginator.paginate(cluster=cluster_arn, desiredStatus='STOPPED'):
                if 'taskArns' in page and page['taskArns']:
                    stopped_tasks.extend(page['taskArns'])
            
            # Combine all task ARNs
            all_tasks = running_tasks + stopped_tasks
            
            # Get detailed information for each task
            if all_tasks:
                # ECS API limits the number of tasks in a single describe_tasks call
                # Process in batches of 100
                task_details = []
                for i in range(0, len(all_tasks), 100):
                    batch = all_tasks[i:i+100]
                    response = client.describe_tasks(
                        cluster=cluster_arn,
                        tasks=batch
                    )
                    task_details.extend(response.get('tasks', []))
                
                return task_details
            
            return []
        except Exception as e:
            logger.error(f"Exception occurred while listing tasks in ECS cluster: {cluster_arn} with error: {e}")
            return None

    def get_task_definition(self, task_definition_arn):
        """Get details of a specific task definition."""
        try:
            client = self.get_connection()
            response = client.describe_task_definition(
                taskDefinition=task_definition_arn
            )
            return response.get('taskDefinition')
        except Exception as e:
            logger.error(f"Exception occurred while getting ECS task definition: {task_definition_arn} with error: {e}")
            return None

    def list_services_in_cluster(self, cluster_arn):
        """List all services in a specific ECS cluster."""
        try:
            client = self.get_connection()
            services = []
            paginator = client.get_paginator('list_services')
            
            for page in paginator.paginate(cluster=cluster_arn):
                if 'serviceArns' in page and page['serviceArns']:
                    service_arns = page['serviceArns']
                    # Get detailed information for each service
                    response = client.describe_services(
                        cluster=cluster_arn,
                        services=service_arns
                    )
                    services.extend(response.get('services', []))
            
            return services
        except Exception as e:
            logger.error(f"Exception occurred while listing services in ECS cluster: {cluster_arn} with error: {e}")
            return None
            
    def get_task_definitions_map(self, cluster_name):
        """
        Get a mapping of task IDs to their task definitions for a specific cluster.
        
        Args:
            cluster_name (str): The name of the ECS cluster
            
        Returns:
            dict: A dictionary mapping task IDs to their task definition names
        """
        try:
            client = self.get_connection()
            task_def_map = {}
            
            # Get all task ARNs in the cluster (both running and stopped)
            running_task_arns = client.list_tasks(cluster=cluster_name, desiredStatus="RUNNING").get("taskArns", [])
            stopped_tasks_arns = client.list_tasks(cluster=cluster_name, desiredStatus="STOPPED").get("taskArns", [])
            task_arns = running_task_arns + stopped_tasks_arns
            
            if not task_arns:
                return {}
                
            # Process tasks in batches of 100 (AWS API limit)
            for i in range(0, len(task_arns), 100):
                batch = task_arns[i:i+100]
                task_details = client.describe_tasks(cluster=cluster_name, tasks=batch)
                
                for task_info in task_details.get("tasks", []):
                    task_id = task_info.get("taskArn").split("/")[-1]
                    task_def_arn = task_info.get("taskDefinitionArn")
                    # Extract task definition name and revision (e.g., "Vidushee-Experiment:4")
                    task_def_name = task_def_arn.split("/")[-1] if task_def_arn else "unknown"
                    task_def_map[task_id] = task_def_name
                    
            return task_def_map
            
        except Exception as e:
            logger.error(f"Exception occurred while getting task definitions map for cluster: {cluster_name} with error: {e}")
            return {}
    
    def get_task_logs(self, cluster_name, max_lines=100):
        """
        Fetch logs for all running tasks in an ECS cluster.
        
        Args:
            cluster_name (str): ECS cluster name.
            task_definition_name (str): Task definition (format: "name:revision").
            max_lines (int, optional): Number of log lines to return (default: 100).
        
        Returns:
            dict: Container-wise logs for all tasks.
        """
        try:
            client = self.get_connection()
            logs_client = boto3.client('logs', 
                                      aws_access_key_id=self.__aws_access_key,
                                      aws_secret_access_key=self.__aws_secret_key, 
                                      region_name=self.region,
                                      aws_session_token=self.__aws_session_token)
            
            # Get all running and stopped tasks in the cluster
            running_task_arns = client.list_tasks(cluster=cluster_name, desiredStatus="RUNNING").get("taskArns", [])
            stopped_tasks_arns = client.list_tasks(cluster=cluster_name, desiredStatus="STOPPED").get("taskArns", [])
            task_arns = running_task_arns + stopped_tasks_arns

            if not task_arns:
                return {"error": f"No running tasks found in cluster: {cluster_name}"}

            # Step 2: Get details of all running tasks
            task_details = client.describe_tasks(cluster=cluster_name, tasks=task_arns)
            if not task_details.get("tasks"):
                return {"error": "Could not retrieve task details."}

            logs_by_task = {}

            # Step 3: Iterate through each running task
            for task_info in task_details["tasks"]:
                task_arn = task_info.get("taskArn")
                task_id = task_arn.split("/")[-1]
                task_definition_arn = task_info.get("taskDefinitionArn")

                # Get task definition to fetch log configuration
                task_def_response = client.describe_task_definition(taskDefinition=task_definition_arn)
                container_definitions = task_def_response["taskDefinition"]["containerDefinitions"]

                logs_by_task[task_id] = {}

                for container_def in container_definitions:
                    container_name = container_def["name"]
                    log_config = container_def.get("logConfiguration", {})

                    if not log_config or log_config.get("logDriver") != "awslogs":
                        logs_by_task[task_id][container_name] = {
                            "error": "Logs not configured to use CloudWatch. Check ECS task definition."
                        }
                        continue

                    # Extract CloudWatch log configuration
                    log_group = log_config["options"].get("awslogs-group")
                    log_stream_prefix = log_config["options"].get("awslogs-stream-prefix")

                    if not log_group or not log_stream_prefix:
                        logs_by_task[task_id][container_name] = {"error": "Missing log group or stream prefix."}
                        continue

                    # Construct log stream name variations
                    log_stream_variations = [
                        f"{log_stream_prefix}/{container_name}/{task_id}",
                        f"{log_stream_prefix}/{task_id}/{container_name}",
                        f"{container_name}/{task_id}"
                    ]

                    # Fetch logs from CloudWatch
                    for stream_name in log_stream_variations:
                        try:
                            # Calculate timestamps for the last 2 weeks
                            end_time = int(datetime.now().timestamp() * 1000)
                            start_time = int((datetime.now() - timedelta(weeks=2)).timestamp() * 1000)
                            
                            log_events_response = logs_client.get_log_events(
                                logGroupName=log_group,
                                logStreamName=stream_name,
                                limit=max_lines,
                                startTime=start_time,
                                endTime=end_time
                            )
                            log_messages = [event["message"] for event in log_events_response.get("events", [])]

                            if log_messages:
                                logs_by_task[task_id][container_name] = {
                                    "logGroup": log_group,
                                    "logStream": stream_name,
                                    "logs": log_messages
                                }
                                break  # Stop searching if logs are found
                        except Exception:
                            continue  # Try next log stream variation

            return logs_by_task

        except Exception as e:
            logger.error(f"Exception occurred while getting ECS task logs: {e}")
            return {"error": f"Failed to fetch logs: {str(e)}"}

    # S3 Methods
    def download_file_contents_from_s3(self, bucket_name, object_key, expiration=3600):
        """
        Generates a pre-signed URL and returns the text content of the file from S3.

        :param bucket_name: str - S3 bucket name
        :param object_key: str - Key (path) to the file in the bucket
        :param expiration: int - Pre-signed URL expiry time in seconds
        :return: str or None - File content as text if successful, None otherwise
        """
        s3_client = boto3.client('s3',
                                aws_access_key_id=self.__aws_access_key,
                                aws_secret_access_key=self.__aws_secret_key, 
                                region_name=self.region,
                                aws_session_token=self.__aws_session_token)

        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
        except ClientError as e:
            print(f"[ERROR] Failed to generate pre-signed URL: {e}")
            return None

        try:
            response = requests.get(url)
            response.raise_for_status()

            # Try decoding the content as UTF-8
            try:
                content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                print("[WARNING] File is not in UTF-8 format or is binary.")
                return None

            return content

        except requests.RequestException as e:
            print(f"[ERROR] Failed to download file: {e}")
            return None
