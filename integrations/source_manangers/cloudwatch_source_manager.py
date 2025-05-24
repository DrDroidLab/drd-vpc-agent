import pytz
import logging
from datetime import datetime, timedelta, date
from typing import Any

from google.protobuf.wrappers_pb2 import StringValue, DoubleValue, UInt64Value, Int64Value
from google.protobuf.struct_pb2 import Struct

from integrations.source_api_processors.aws_boto_3_api_processor import AWSBoto3ApiProcessor
from protos.base_pb2 import TimeRange, Source, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import TimeseriesResult, LabelValuePair, PlaybookTaskResult, \
    PlaybookTaskResultType, TableResult, TextResult, ApiResponseResult
from protos.playbooks.source_task_definitions.cloudwatch_task_pb2 import Cloudwatch
from protos.ui_definition_pb2 import FormField, FormFieldType
from protos.assets.cloudwatch_asset_pb2 import CloudwatchDashboardAssetModel, CloudwatchDashboardAssetOptions, CloudwatchAssetModel
from protos.assets.asset_pb2 import AccountConnectorAssetsModelFilters, AccountConnectorAssets
from integrations.source_manager import SourceManager
from utils.credentilal_utils import generate_credentials_dict
from utils.proto_utils import proto_to_dict, dict_to_proto
from utils.time_utils import calculate_timeseries_bucket_size
from utils.playbooks_client import PrototypeClient

logger = logging.getLogger(__name__)


def convert_datetime_recursive(data):
    """Recursively convert all datetime objects in a dictionary or list to ISO format strings."""
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, (datetime, date)):
                data[key] = value.isoformat()
            elif isinstance(value, dict) or isinstance(value, list):
                data[key] = convert_datetime_recursive(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (datetime, date)):
                data[i] = item.isoformat()
            elif isinstance(item, dict) or isinstance(item, list):
                data[i] = convert_datetime_recursive(item)
    return data

class CloudwatchSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.CLOUDWATCH
        self.task_proto = Cloudwatch
        self.task_type_callable_map = {
            Cloudwatch.TaskType.ECS_LIST_CLUSTERS: {
                'executor': self.ecs_list_clusters,
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'List ECS Clusters',
                'category': 'ECS',
                'form_fields': [],
                'model_types': [SourceModelType.ECS_CLUSTER],
                'permission_checks': {
                    'test_ecs_list_clusters_permission': [{'client_type': 'ecs'}]
                }
            },
            Cloudwatch.TaskType.ECS_LIST_TASKS: {
                'executor': self.ecs_list_tasks,
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'List ECS Tasks in Cluster',
                'category': 'ECS',
                'form_fields': [
                    FormField(key_name=StringValue(value="cluster_name"),
                              display_name=StringValue(value="Cluster Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT)
                ],
                'model_types': [SourceModelType.ECS_TASK],
                'permission_checks': {
                    'test_ecs_list_clusters_permission': [{'client_type': 'ecs'}]
                }
            },
            Cloudwatch.TaskType.ECS_GET_TASK_LOGS: {
                'executor': self.ecs_get_task_logs,
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Get ECS Task Logs',
                'category': 'ECS',
                'form_fields': [
                    FormField(key_name=StringValue(value="cluster_name"),
                              display_name=StringValue(value="Cluster Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="task_definition"),
                              display_name=StringValue(value="Task Definition"),
                              description=StringValue(value="Optional: Filter logs by task definition (e.g., Vidushee-Experiment:4)"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="max_lines"),
                              display_name=StringValue(value="Max Lines"),
                              data_type=LiteralType.LONG,
                              default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=1000)),
                              form_field_type=FormFieldType.TEXT_FT)
                              ],
                'model_types': [SourceModelType.ECS_TASK],
                'permission_checks': {
                    'test_ecs_list_clusters_permission': [{'client_type': 'ecs'}],
                    'test_logs_describe_log_groups_permission': [{'client_type': 'logs'}]
                }
            },
            Cloudwatch.TaskType.METRIC_EXECUTION: {
                'executor': self.execute_metric_execution,
                'model_types': [SourceModelType.CLOUDWATCH_METRIC],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a Metric from Cloudwatch',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="namespace"),
                              display_name=StringValue(value="Namespace"),
                              description=StringValue(value='Select Namespace'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="region"),
                              display_name=StringValue(value="Region"),
                              description=StringValue(value='Select Region'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="dimensions"),
                              display_name=StringValue(value="Dimensions"),
                              description=StringValue(value='Select Dimension Name'),
                              is_composite=True,
                              composite_fields=[
                                  FormField(key_name=StringValue(value="name"),
                                            display_name=StringValue(value="Dimension Name"),
                                            description=StringValue(value='Select Dimension Name'),
                                            data_type=LiteralType.STRING,
                                            form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                                  FormField(key_name=StringValue(value="value"),
                                            display_name=StringValue(value="Dimension Value"),
                                            description=StringValue(value='Select Dimension Value'),
                                            data_type=LiteralType.STRING,
                                            form_field_type=FormFieldType.TYPING_DROPDOWN_FT)
                              ],
                              form_field_type=FormFieldType.COMPOSITE_FT),
                    FormField(key_name=StringValue(value="metric_name"),
                              display_name=StringValue(value="Metric"),
                              description=StringValue(value='Add Metric'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_MULTIPLE_FT),
                    FormField(key_name=StringValue(value="period"),
                              display_name=StringValue(value="Period(Seconds)"),
                              description=StringValue(value='(Optional)Enter Period'),
                              data_type=LiteralType.LONG,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                    FormField(key_name=StringValue(value="statistic"),
                              display_name=StringValue(value="Metric Aggregation"),
                              description=StringValue(value='Select Aggregation Function'),
                              data_type=LiteralType.STRING,
                              default_value=Literal(type=LiteralType.STRING,
                                                    string=StringValue(value="Average")),
                              valid_values=[
                                  Literal(type=LiteralType.STRING, string=StringValue(value="Average")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="Sum")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="SampleCount")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="Maximum")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="Minimum"))],
                              form_field_type=FormFieldType.DROPDOWN_FT),
                ]
            },
            Cloudwatch.TaskType.FILTER_LOG_EVENTS: {
                'executor': self.execute_filter_log_events,
                'model_types': [SourceModelType.CLOUDWATCH_LOG_GROUP],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Fetch Logs from Cloudwatch',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="region"),
                              display_name=StringValue(value="Region"),
                              description=StringValue(value='Select Region'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="log_group_name"),
                              display_name=StringValue(value="Log Group"),
                              description=StringValue(value='Select Log Group'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="filter_query"),
                              display_name=StringValue(value="Filter Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT)
                ]
            },
            Cloudwatch.TaskType.RDS_GET_SQL_QUERY_PERFORMANCE_STATS: {
                'executor': self.execute_rds_get_sql_query_performance_stats,
                'model_types': [],  # [SourceModelType.RDS_INSTANCES]
                'result_type': PlaybookTaskResultType.TABLE,
                'display_name': 'Fetch Sql Query performance stats from Cloudwatch',
                'category': 'Tables',
                'form_fields': [
                    FormField(key_name=StringValue(value="db_resource_uri"),
                              display_name=StringValue(value="Db Resource URI"),
                              description=StringValue(value='Enter DB Resource URI'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                ],
                'permission_checks': {
                    'test_pi_describe_dimension_keys_permission': [{'client_type': 'pi'}]
                }
            },
            Cloudwatch.TaskType.FETCH_DASHBOARD: {
                'executor': self.execute_fetch_dashboard,
                'model_types': [SourceModelType.CLOUDWATCH_DASHBOARD],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch CloudWatch Dashboard Metrics',
                'category': 'Dashboards',
                'form_fields': [
                    FormField(key_name=StringValue(value="dashboard_name"),
                              display_name=StringValue(value="Dashboard Name"),
                              description=StringValue(value='Select the CloudWatch Dashboard to fetch metrics from'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="step"),
                              display_name=StringValue(value="Step"),
                              description=StringValue(value="Optional: Aggregation period in seconds (e.g., 60, 300). Defaults to dynamic calculation based on time range."),
                              data_type=LiteralType.LONG,
                              is_optional=True,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="period"),
                              display_name=StringValue(value="Period(Seconds)"),
                              description=StringValue(value='Optional: Enter Period'),
                              data_type=LiteralType.LONG,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
            Cloudwatch.TaskType.FETCH_S3_FILE: {
                'executor': self.execute_fetch_s3_file,
                'model_types': [],
                'result_type': PlaybookTaskResultType.TEXT,
                'display_name': 'Fetch S3 File',
                'category': 'Files',
                'form_fields': [
                    FormField(key_name=StringValue(value="bucket_name"),
                              display_name=StringValue(value="Bucket Name"),
                              description=StringValue(value='Enter the S3 Bucket name'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="object_key"),
                              display_name=StringValue(value="File Path"),
                              description=StringValue(value="Enter the File Path in S3 Bucket"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                ],
                'permission_checks': {
                    'test_s3_get_object_permission': [{'client_type': 's3'}]
                }
            },
        }

    def get_connector_processor(self, cloudwatch_connector, **kwargs):
        generated_credentials = generate_credentials_dict(cloudwatch_connector.type, cloudwatch_connector.keys)
        generated_credentials['client_type'] = kwargs.get('client_type', 'cloudwatch')
        if 'region' in kwargs:
            generated_credentials['region'] = kwargs.get('region')
        return AWSBoto3ApiProcessor(**generated_credentials)

    def test_connector_processor(self, connector: ConnectorProto, **kwargs):
        cw_processor = self.get_connector_processor(connector, client_type='cloudwatch')
        cw_logs_processor = self.get_connector_processor(connector, client_type='logs')
        try:
            return cw_processor.test_connection() and cw_logs_processor.test_connection()
        except Exception as e:
            raise e

    ########################################## CW Metric Execution Functions ####################################
    def _fetch_single_metric_timeseries(self, cloudwatch_boto3_processor, namespace: str, metric_name: str,
                                       start_time: datetime, end_time: datetime, period: int, statistic: str,
                                       dimensions: list, metric_display_name: str, offset_seconds: int = 0):
        """Helper to fetch timeseries data for a single metric config."""
        try:
            adjusted_start_time = start_time - timedelta(seconds=offset_seconds)
            adjusted_end_time = end_time - timedelta(seconds=offset_seconds)

            response = cloudwatch_boto3_processor.cloudwatch_get_metric_statistics(
                namespace, metric_name, adjusted_start_time, adjusted_end_time, period, [statistic], dimensions
            )

            if not response or not response.get('Datapoints'):
                dim_str = ', '.join([f"{d['Name']}:{d['Value']}" for d in dimensions])
                logger.warning(f"No data returned from Cloudwatch for ns={namespace}, metric={metric_name}, "
                               f"dims=[{dim_str}], stat={statistic}, period={period}s, offset={offset_seconds}s")
                return None

            # Sort datapoints by timestamp before creating the proto
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])

            metric_datapoints = [
                TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                    timestamp=int(
                        item['Timestamp'].replace(tzinfo=pytz.UTC).timestamp() * 1000),
                    value=DoubleValue(value=item[statistic])
                ) for item in datapoints
            ]

            metric_unit = response['Datapoints'][0].get('Unit', '') if response['Datapoints'] else ''

            metric_label_values = [
                LabelValuePair(name=StringValue(value='namespace'), value=StringValue(value=namespace)),
                LabelValuePair(name=StringValue(value='statistic'), value=StringValue(value=statistic)),
                LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value=str(offset_seconds))),
                LabelValuePair(name=StringValue(value='metric_display_name'), value=StringValue(value=metric_display_name))
            ]
            # Add dimension labels
            for dim in dimensions:
                 metric_label_values.append(LabelValuePair(name=StringValue(value=dim['Name']), value=StringValue(value=dim['Value'])))


            return TimeseriesResult.LabeledMetricTimeseries(
                metric_label_values=metric_label_values,
                unit=StringValue(value=metric_unit),
                datapoints=metric_datapoints
            )

        except Exception as e:
            dim_str = ', '.join([f"{d['Name']}:{d['Value']}" for d in dimensions])
            logger.error(f"Exception fetching metric: ns={namespace}, metric={metric_name}, dims=[{dim_str}], "
                         f"stat={statistic}, display_name={metric_display_name}, period={period}s, offset={offset_seconds}s. Error: {e}")
            return None


    def execute_metric_execution(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                                 cloudwatch_connector: ConnectorProto):
        try:
            if not cloudwatch_connector:
                raise Exception("Task execution Failed:: No Cloudwatch source found")

            task = cloudwatch_task.metric_execution
            region = task.region.value
            metric_name = task.metric_name.value
            namespace = task.namespace.value
            timeseries_offsets = list(task.timeseries_offsets)
            statistic = 'Average'
            if task.statistic and task.statistic.value in ['Average', 'Sum', 'SampleCount', 'Maximum', 'Minimum']:
                statistic = task.statistic.value

            # Convert dimensions from proto Struct to list of dicts
            dimensions = [{'Name': d.name.value, 'Value': d.value.value} for d in task.dimensions]

            cloudwatch_boto3_processor = self.get_connector_processor(cloudwatch_connector, client_type='cloudwatch',
                                                                      region=region)

            labeled_metric_timeseries_list = []
            start_time_dt = datetime.utcfromtimestamp(time_range.time_geq).replace(tzinfo=pytz.UTC)
            end_time_dt = datetime.utcfromtimestamp(time_range.time_lt).replace(tzinfo=pytz.UTC)

            if task.period.value > 0:
                calculated_period = task.period.value
            else:
                # Calculate dynamic period based on time range
                total_seconds = time_range.time_lt - time_range.time_geq
                calculated_period = calculate_timeseries_bucket_size(total_seconds) # No widget-defined period for this task

            # Fetch current timeseries (offset 0)
            current_timeseries = self._fetch_single_metric_timeseries(
                cloudwatch_boto3_processor, namespace, metric_name, start_time_dt, end_time_dt,
                calculated_period, statistic, dimensions,
                metric_display_name=f"{namespace}.{metric_name} ({statistic})",
                offset_seconds=0
            )
            if current_timeseries:
                labeled_metric_timeseries_list.append(current_timeseries)
            else:
                # If even the current data fails, return a message
                dimension_str = ', '.join([f"{d['Name']}:{d['Value']}" for d in dimensions])
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"No data returned from Cloudwatch for ns: {namespace}, metric: {metric_name}, "
                              f"dims: [{dimension_str}], stat: {statistic}")),
                    source=self.source)

            # Fetch offset timeseries if specified
            for offset in timeseries_offsets:
                offset_timeseries = self._fetch_single_metric_timeseries(
                    cloudwatch_boto3_processor, namespace, metric_name, start_time_dt, end_time_dt,
                    calculated_period, statistic, dimensions,
                    metric_display_name=f"{namespace}.{metric_name} ({statistic})",
                    offset_seconds=offset
                )
                if offset_timeseries:
                    labeled_metric_timeseries_list.append(offset_timeseries)

            if not labeled_metric_timeseries_list:
                # This case should ideally not be reached if current_timeseries succeeded, but as a safeguard
                dimension_str = ', '.join([f"{d['Name']}:{d['Value']}" for d in dimensions])
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"Failed to fetch any data for ns: {namespace}, metric: {metric_name}, "
                              f"dims: [{dimension_str}], stat: {statistic}")),
                    source=self.source)

            metric_metadata = f"{namespace}.{metric_name} ({statistic}) for region {region} "
            for i in dimensions:
                metric_metadata += f"where {i['Name']}='{i['Value']}' "

            timeseries_result = TimeseriesResult(
                metric_expression=StringValue(value=metric_name),
                metric_name=StringValue(value=metric_metadata.strip()),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )

            return PlaybookTaskResult(type=PlaybookTaskResultType.TIMESERIES, timeseries=timeseries_result,
                                      source=self.source)
        except Exception as e:
            logger.error(f"Error in execute_metric_execution: {e}", exc_info=True)
            raise Exception(f"Error while executing Cloudwatch metric task: {e}")

    def execute_filter_log_events(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                                  cloudwatch_connector: ConnectorProto):
        try:
            if not cloudwatch_connector:
                raise Exception("Task execution Failed:: No Cloudwatch source found")
            tr_end_time = time_range.time_lt
            end_time = int(tr_end_time * 1000)
            tr_start_time = time_range.time_geq
            start_time = int(tr_start_time * 1000)

            task = cloudwatch_task.filter_log_events
            region = task.region.value
            log_group = task.log_group_name.value
            query_pattern = task.filter_query.value

            logs_boto3_processor = self.get_connector_processor(cloudwatch_connector, client_type='logs', region=region)
            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Region -> {}, Log_Group -> {}, Query -> "
                "{}, Start_Time -> {}, End_Time -> {}".format("Cloudwatch_Logs", cloudwatch_connector.account_id.value,
                                                              region, log_group, query_pattern, start_time, end_time),
                flush=True)

            response = logs_boto3_processor.logs_filter_events(log_group, query_pattern, start_time, end_time)
            if not response:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No logs returned from Cloudwatch for query: {query_pattern} on log group: {log_group}")),
                                          source=self.source)

            table_rows: [TableResult.TableRow] = []
            for item in response:
                table_columns: [TableResult.TableColumn] = []
                for i in item:
                    table_column = TableResult.TableColumn(name=StringValue(value=i['field']),
                                                           value=StringValue(value=i['value']))
                    table_columns.append(table_column)
                table_row = TableResult.TableRow(columns=table_columns)
                table_rows.append(table_row)

            result = TableResult(
                raw_query=StringValue(
                    value=f"Execute ```{query_pattern}``` on log group {log_group} in region {region}"),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            task_result = PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=result, source=self.source)
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Cloudwatch task: {e}")

    def execute_rds_get_sql_query_performance_stats(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                                                    cloudwatch_connector: ConnectorProto):
        try:
            if not cloudwatch_connector:
                raise Exception("Task execution Failed:: No Cloudwatch source found")
            tr_end_time = time_range.time_lt
            end_time = int(tr_end_time * 1000)
            tr_start_time = time_range.time_geq
            start_time = int(tr_start_time * 1000)

            task = cloudwatch_task.rds_get_sql_query_performance_stats
            db_resource_uri = task.db_resource_uri.value
            pi_boto3_processor = self.get_connector_processor(cloudwatch_connector, client_type='pi')
            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, DB -> {}, "
                "Start_Time -> {}, End_Time -> {}".format("RDS_Performance_Stats",
                                                          cloudwatch_connector.account_id.value, db_resource_uri,
                                                          start_time, end_time), flush=True)

            end_time_dt = datetime.utcfromtimestamp(tr_end_time)
            response = pi_boto3_processor.pi_get_long_running_queries(db_resource_uri, end_time_dt)
            if not response:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No Stats returned from RDS DB for: {db_resource_uri}")), source=self.source)

            table_rows: [TableResult.TableRow] = []
            for stat in response:
                table_columns: [TableResult.TableColumn] = []
                for k, v in stat.items():
                    table_column = TableResult.TableColumn(name=StringValue(value=str(k)),
                                                           value=StringValue(value=str(v)))
                    table_columns.append(table_column)
                table_row = TableResult.TableRow(columns=table_columns)
                table_rows.append(table_row)

            result = TableResult(
                raw_query=StringValue(value=f"SQL Query Performance Stats for DB {db_resource_uri}"),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            task_result = PlaybookTaskResult(type=PlaybookTaskResultType.TABLE, table=result, source=self.source)
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Cloudwatch task: {e}")

    ########################################## ECS Task Functions ####################################
    def ecs_list_clusters(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                          cloudwatch_connector: ConnectorProto):
        try:
            processor = self.get_connector_processor(cloudwatch_connector, client_type='ecs')
            clusters = processor.list_all_clusters()
            
            if not clusters:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="No ECS clusters found")),
                    source=self.source
                )
            
            # Convert all datetime objects in the clusters data to strings
            clusters = convert_datetime_recursive(clusters)
            
            response_struct = dict_to_proto({"clusters": clusters}, Struct)
            clusters_output = ApiResponseResult(response_body=response_struct)
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=clusters_output
            )
        except Exception as e:
            raise Exception(f"Error while executing ECS list_clusters task: {e}")

    def ecs_list_tasks(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                        cloudwatch_connector: ConnectorProto):
        try:
            task = cloudwatch_task.ecs_list_tasks
            cluster_name = task.cluster_name.value
            
            processor = self.get_connector_processor(cloudwatch_connector, client_type='ecs')
            
            # First, get all clusters to find the ARN for the specified cluster name
            all_clusters = processor.list_all_clusters()
            # Convert all datetime objects in the clusters data to strings
            all_clusters = convert_datetime_recursive(all_clusters)
            cluster_arn = None
            
            for cluster in all_clusters:
                if cluster.get('clusterName') == cluster_name:
                    cluster_arn = cluster.get('clusterArn')
                    break
            
            if not cluster_arn:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"Cluster '{cluster_name}' not found")),
                    source=self.source
                )
            
            tasks = processor.list_tasks_in_cluster(cluster_arn)
            
            if not tasks:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"No tasks found in cluster '{cluster_name}'")),
                    source=self.source
                )
            
            # Convert all datetime objects in the tasks data to strings
            tasks = convert_datetime_recursive(tasks)
            
            # Restructure the response to be a dictionary where each key is a task definition
            # and each value contains an array of tasks with that definition
            restructured_tasks = {}
            
            for task in tasks:
                # Extract the task definition from the ARN
                task_definition_arn = task.get('taskDefinitionArn', '')
                # Format: arn:aws:ecs:region:account:task-definition/name:revision
                task_definition = task_definition_arn.split('/')[-1] if '/' in task_definition_arn else 'unknown'
                
                # Add the extracted task definition as a field in the task object
                task['taskDefinition'] = task_definition
                
                # Add the task to the restructured dictionary
                if task_definition not in restructured_tasks:
                    restructured_tasks[task_definition] = []
                
                # Append this task to the array for this task definition
                restructured_tasks[task_definition].append(task)
            
            response_struct = dict_to_proto(restructured_tasks, Struct)
            tasks_output = ApiResponseResult(response_body=response_struct)
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=tasks_output
            )
        except Exception as e:
            raise Exception(f"Error while executing ECS list_tasks task: {e}")
            
    def ecs_get_task_logs(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                          cloudwatch_connector: ConnectorProto):
        try:
            task = cloudwatch_task.ecs_get_task_logs
            cluster_name = task.cluster_name.value
            max_lines = task.max_lines.value
            
            # Check if a specific task definition filter was provided
            task_definition_filter = task.task_definition.value if task.HasField('task_definition') else None
            
            processor = self.get_connector_processor(cloudwatch_connector, client_type='ecs')
            
            # Get the logs for the task
            logs = processor.get_task_logs(cluster_name, max_lines)
            # Check if there was an error
            # if "error" in logs and len(logs) == 1:
            #     return PlaybookTaskResult(
            #         type=PlaybookTaskResultType.TEXT,
            #         text=TextResult(output=StringValue(value=logs["error"])),
            #         source=self.source
            #     )
            
            # Get task definitions map using the processor method
            task_def_map = processor.get_task_definitions_map(cluster_name)
            
            # Convert all datetime objects in the logs data to strings
            logs = convert_datetime_recursive(logs)
            
            # Restructure the logs by task definition with simplified structure
            restructured_logs = {}
            for task_id, task_data in logs.items():
                task_def = task_def_map.get(task_id, "unknown")
                
                # Skip if a task definition filter was provided and this task doesn't match
                if task_definition_filter and task_def != task_definition_filter:
                    continue
                
                # If this task definition isn't in the restructured logs yet, add it
                if task_def not in restructured_logs:
                    restructured_logs[task_def] = {}
                
                # For each container in the task
                for container_name, container_data in task_data.items():
                    # Extract just the logs and add them directly under the task definition
                    if "logs" in container_data:
                        # Initialize logs array if it doesn't exist yet
                        if "logs" not in restructured_logs[task_def]:
                            restructured_logs[task_def]["logs"] = []
                        
                        # Add these logs to the combined logs for this task definition
                        restructured_logs[task_def]["logs"].extend(container_data["logs"])
                    
                    # Add other metadata if not already present
                    if "logGroup" not in restructured_logs[task_def] and "logGroup" in container_data:
                        restructured_logs[task_def]["logGroup"] = container_data["logGroup"]
            
            # If a task definition filter was provided but no matching logs were found
            if task_definition_filter and not restructured_logs:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"No logs found for task definition '{task_definition_filter}' in cluster '{cluster_name}'")),
                    source=self.source
                )
            
            response_struct = dict_to_proto({"logs": restructured_logs}, Struct)
            logs_output = ApiResponseResult(response_body=response_struct)
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=logs_output
            )
        except Exception as e:
            raise Exception(f"Error while executing ECS get_task_logs task: {e}")

    ########################################## CW Fetch Dashboard Functions ####################################
    def _get_step_interval(self, time_range: TimeRange, task_definition: Any) -> int:
        """Calculates the step interval (period). Uses user-defined value if provided, otherwise calculates dynamically."""
        if task_definition and task_definition.HasField("step") and task_definition.step.value:
            # Ensure minimum period for CloudWatch is 60 seconds if user provides less
            user_step = task_definition.step.value
            if user_step < 60:
                logger.warning(f"User provided step {user_step}s is less than CloudWatch minimum (60s). Using 60s.")
                return 60
            return user_step
        else:
            total_seconds = time_range.time_lt - time_range.time_geq
            return calculate_timeseries_bucket_size(total_seconds)

    def execute_fetch_dashboard(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                                cloudwatch_connector: ConnectorProto):
        """Fetches all metrics defined in a CloudWatch Dashboard and returns them as a single TimeseriesResult."""
        try:
            if not cloudwatch_connector:
                raise Exception("Task execution Failed:: No Cloudwatch source found")

            task = cloudwatch_task.fetch_dashboard
            dashboard_name = task.dashboard_name.value

            if not dashboard_name:
                 raise ValueError("Dashboard name is required for FETCH_DASHBOARD task")

            dashboard_asset_filter = AccountConnectorAssetsModelFilters(
                cloudwatch_dashboard_model_filters=CloudwatchDashboardAssetOptions(dashboard_names=[dashboard_name])
            )
            # Use PrototypeClient to fetch the Dashboard Asset
            client = PrototypeClient()
            assets_result: AccountConnectorAssets = client.get_connector_assets(
                connector_type="CLOUDWATCH",
                connector_id=cloudwatch_connector.id.value,
                asset_type=SourceModelType.CLOUDWATCH_DASHBOARD,
                filters=proto_to_dict(dashboard_asset_filter)
            )
            if not assets_result:
                logger.error(f"Dashboard asset not found or empty for name: {dashboard_name}")
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"Could not find dashboard asset information for '{dashboard_name}'. Please ensure metadata extraction ran successfully.")))

            dashboard_asset_model: CloudwatchAssetModel = assets_result.cloudwatch.assets[0]
            dashboard_data: CloudwatchDashboardAssetModel = dashboard_asset_model.cloudwatch_dashboard

            # 2. Iterate through widgets and fetch metrics, creating individual results
            task_results = []
            start_time_dt = datetime.utcfromtimestamp(time_range.time_geq).replace(tzinfo=pytz.UTC)
            end_time_dt = datetime.utcfromtimestamp(time_range.time_lt).replace(tzinfo=pytz.UTC)

            effective_period = self._get_step_interval(time_range, task) # Use helper to get period

            # Keep track of unique boto processors per region needed
            boto_processors = {}

            for widget in dashboard_data.widgets:
                namespace = widget.namespace.value
                metric_name = widget.metric_name.value
                # Convert Struct dimensions back to list of dicts {Name: ..., Value: ...}
                dimensions = []
                for dim_struct in widget.dimensions:
                    dim_dict = proto_to_dict(dim_struct)
                    # Ensure the structure is as expected
                    if 'Name' in dim_dict and 'Value' in dim_dict:
                         dimensions.append({'Name': dim_dict['Name'], 'Value': dim_dict['Value']})
                    else:
                        logger.warning(f"Skipping invalid dimension structure in widget for dashboard {dashboard_name}: {dim_dict}")
                        continue # Skip this dimension if structure is wrong

                statistic = widget.statistic.value if widget.HasField('statistic') else 'Average'

                # Use widget region if specified, otherwise fallback to connector default
                region = widget.region.value if widget.HasField('region') and widget.region.value else cloudwatch_connector.region # Fallback to connector region

                if not namespace or not metric_name:
                    logger.warning(f"Skipping widget in dashboard {dashboard_name} due to missing namespace or metric name.")
                    continue

                # Get or create boto3 processor for the required region
                if region not in boto_processors:
                     try:
                        boto_processors[region] = self.get_connector_processor(cloudwatch_connector, client_type='cloudwatch', region=region)
                     except Exception as e:
                         logger.error(f"Failed to create boto3 processor for region {region}: {e}. Skipping metrics for this region.")
                         boto_processors[region] = None # Mark as failed to avoid retries
                         continue

                if boto_processors[region] is None:
                    continue # Skip if processor creation failed for this region

                # Construct the desired display name using the widget title
                display_name_for_legend = widget.widget_title.value if widget.HasField('widget_title') and widget.widget_title.value else f"{namespace}.{metric_name}"

                labeled_timeseries = self._fetch_single_metric_timeseries(
                    boto_processors[region], namespace, metric_name, start_time_dt, end_time_dt,
                    effective_period, statistic, dimensions,
                    metric_display_name=display_name_for_legend,
                    offset_seconds=0
                )

                if labeled_timeseries:
                    dim_str = ', '.join([f"{d['Name']}='{d['Value']}'" for d in dimensions])
                    result_metric_name = f"{display_name_for_legend} ({statistic}) {dim_str} [{region}]"

                    # Create a TimeseriesResult for this single metric
                    single_timeseries_result = TimeseriesResult(
                        metric_expression=StringValue(value=metric_name),
                        metric_name=StringValue(value=result_metric_name),
                        labeled_metric_timeseries=[labeled_timeseries]
                    )

                    # Create a PlaybookTaskResult for this specific timeseries
                    single_task_result = PlaybookTaskResult(
                        type=PlaybookTaskResultType.TIMESERIES,
                        timeseries=single_timeseries_result,
                        source=self.source
                    )
                    task_results.append(single_task_result)

            if not task_results:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No metric data could be fetched for any widget in dashboard '{dashboard_name}'.")))

            # Return the list of individual PlaybookTaskResults
            return task_results

        except ValueError as ve:
             logger.error(f"Configuration error executing FETCH_DASHBOARD for '{cloudwatch_task.fetch_dashboard.dashboard_name.value}': {ve}")
             return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(value=f"Configuration Error: {ve}")))
        except Exception as e:
            logger.error(f"Error executing FETCH_DASHBOARD for '{cloudwatch_task.fetch_dashboard.dashboard_name.value}': {e}", exc_info=True)
            raise Exception(f"Error while fetching dashboard metrics: {e}")


    ########################################## CW Fetch S3 File Functions ####################################
    def execute_fetch_s3_file(self, time_range: TimeRange, cloudwatch_task: Cloudwatch,
                              cloudwatch_connector: ConnectorProto):
        """Fetches the contents of an S3 file and returns them as a single TextResult."""
        try:
            if not cloudwatch_connector:
                raise Exception("Task execution Failed:: No Cloudwatch source found")

            task = cloudwatch_task.fetch_s3_file
            bucket_name = task.bucket_name.value
            object_key = task.object_key.value

            if not bucket_name or not object_key:
                raise ValueError("Bucket name and object key are required for FETCH_S3_FILE task")
            
            # Get the S3 file contents
            s3_processor = self.get_connector_processor(cloudwatch_connector, client_type='s3', region="us-west-2")
            if not s3_processor:
                raise Exception("Task execution Failed:: No S3 source found")
            
            # Fetch the file contents
            file_contents = s3_processor.download_file_contents_from_s3(bucket_name, object_key)

            if not file_contents:
                raise Exception("Task execution Failed:: No file contents found")
            
            return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(value=file_contents)))

        except Exception as e:
            logger.error(f"Error executing FETCH_S3_FILE for '{cloudwatch_task.fetch_s3_file.bucket_name.value}': {e}", exc_info=True)
            raise Exception(f"Error while fetching S3 file: {e}")