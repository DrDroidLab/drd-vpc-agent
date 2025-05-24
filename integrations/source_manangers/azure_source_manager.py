import logging
import pytz
from datetime import timedelta, datetime

from google.protobuf.wrappers_pb2 import StringValue, UInt64Value, DoubleValue

from integrations.source_api_processors.azure_api_processor import AzureApiProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType, TableResult, TimeseriesResult, TextResult
from protos.playbooks.source_task_definitions.azure_task_pb2 import Azure
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict

logger = logging.getLogger(__name__)


class AzureSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.AZURE
        self.task_proto = Azure
        self.task_type_callable_map = {
            Azure.TaskType.FILTER_LOG_EVENTS: {
                'executor': self.filter_log_events,
                'model_types': [SourceModelType.AZURE_WORKSPACE],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Fetch logs from Azure Log Analytics Workspace',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="workspace_id"),
                              display_name=StringValue(value="Azure Workspace ID"),
                              description=StringValue(value='Select Workspace ID'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="filter_query"),
                              display_name=StringValue(value="Log Filter Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="timespan"),
                              display_name=StringValue(value="Timespan (hours)"),
                              description=StringValue(value='Enter Timespan (hours)'),
                              data_type=LiteralType.STRING,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="1")),
                              form_field_type=FormFieldType.TEXT_FT)
                ]
            },
            Azure.TaskType.FETCH_METRICS: {
                'executor': self.fetch_metrics,
                'model_types': [SourceModelType.AZURE_RESOURCE],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch metrics from Azure Monitor',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="resource_id"),
                              display_name=StringValue(value="Azure Resource"),
                              description=StringValue(value='Select Azure Resource'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="metric_names"),
                              display_name=StringValue(value="Metric Names"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="granularity"),
                              display_name=StringValue(value="Granularity"),
                              description=StringValue(value='Optional: Select Granularity'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.DROPDOWN_FT,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="5 minutes")),
                              valid_values=[
                                  Literal(type=LiteralType.STRING, string=StringValue(value="1 minute")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="5 minutes")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="15 minutes")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="30 minutes")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="1 hour")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="6 hours")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="12 hours")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="1 day"))],
                              is_optional=True),
                    FormField(key_name=StringValue(value="aggregation"),
                              display_name=StringValue(value="Aggregation"),
                              description=StringValue(value='Select Aggregation(Default: Average)'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT)
                ]
            }
        }

    def get_connector_processor(self, azure_connector, **kwargs):
        generated_credentials = generate_credentials_dict(azure_connector.type, azure_connector.keys)
        return AzureApiProcessor(**generated_credentials)

    def filter_log_events(self, time_range: TimeRange, azure_task: Azure,
                          azure_connector: ConnectorProto):
        try:
            tr_end_time = time_range.time_lt
            end_time = int(tr_end_time * 1000)
            tr_start_time = time_range.time_geq
            start_time = int(tr_start_time * 1000)

            task: Azure.FilterLogEvents = azure_task.filter_log_events
            workspace_id = task.workspace_id.value
            timespan_delta = task.timespan.value
            timespan = timedelta(hours=int(timespan_delta)) if timespan_delta else timedelta(
                seconds=end_time - start_time)
            query_pattern = task.filter_query.value

            azure_api_processor = self.get_connector_processor(azure_connector)

            logger.info(f"Querying Azure Log Analytics workspace: {workspace_id} with query: {query_pattern}")

            response = azure_api_processor.query_log_analytics(workspace_id, query_pattern, timespan=timespan)
            if not response:
                raise Exception("No data returned from Azure Analytics workspace Logs")

            print(f"Response: {response}")
            table_rows: [TableResult.TableRow] = []
            for table, rows in response.items():
                for i in rows:
                    table_columns: [TableResult.TableRow.TableColumn] = []
                    for key, value in i.items():
                        table_column_name = f'{table}.{key}'
                        table_column = TableResult.TableColumn(
                            name=StringValue(value=table_column_name), value=StringValue(value=str(value)))
                        table_columns.append(table_column)
                    table_row = TableResult.TableRow(columns=table_columns)
                    table_rows.append(table_row)

            result = TableResult(
                raw_query=StringValue(
                    value=f'Execute {query_pattern} on Azure Log Analytics workspace: {workspace_id}'),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            task_result = PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=result, source=self.source)
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Azure task: {e}")

    def fetch_metrics(self, time_range: TimeRange, azure_task: Azure,
                      azure_connector: ConnectorProto):
        try:
            if not azure_connector:
                raise Exception("Task execution Failed:: No Azure Resource found")
            task: Azure.FetchMetrics = azure_task.fetch_metrics
            resource_id = task.resource_id.value
            metric_names = task.metric_names.value
            aggregation = task.aggregation.value if task.aggregation.value else "Average"
            azure_api_processor = self.get_connector_processor(azure_connector)
            granularity_string = task.granularity.value if task.granularity.value else "5 minutes" # default granularity 5 minutes
            map_of_granularity_to_seconds = {
                "1 minute": 60,
                "5 minutes": 300,
                "15 minutes": 900,
                "30 minutes": 1800,
                "1 hour": 3600,
                "6 hours": 21600,
                "12 hours": 43200,
                "1 day": 86400
            }
            granularity = map_of_granularity_to_seconds[granularity_string]

            logger.info(
                f"Fetching metrics from Azure Monitor for resource_id: {resource_id} and metric_names: {metric_names}")

            response = azure_api_processor.query_metrics(resource_id, time_range=time_range, metric_names=metric_names,
                                                         aggregation=aggregation, granularity=granularity)  # can pass metric_name as well, for now fethcing all metrics in api processor
            if not response:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No data returned from Azure for resource_id: {resource_id} and metric_names: {metric_names}")),
                                          source=self.source)
            # Convert Azure response into Time Series format
            time_series_data = []
            for metric_name, data_points in response.items():
                if not data_points:
                    continue  # Skip empty metric results
                metric_datapoints = []
                for data in data_points:
                    if not isinstance(data, dict):
                        logger.error(f"Unexpected metric data format: {data}")
                        continue
                    # Convert timestamp to Unix Epoch (milliseconds)
                    timestamp_iso = str(data.get("timestamp", ""))
                    if timestamp_iso:
                        timestamp_ms = int(
                            datetime.fromisoformat(timestamp_iso).replace(tzinfo=pytz.UTC).timestamp() * 1000)
                    else:
                        timestamp_ms = 0  # Handle missing timestamp case

                    metric_value = data.get("value")
                    if metric_value is None:
                        metric_value = 0.0  # Defaulting to 0.0 if missing
                    # Create TimeSeries Datapoint object
                    metric_datapoints.append(
                        TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=timestamp_ms,
                            value=DoubleValue(value=metric_value)
                        )
                    )
                time_series_data.append(
                    TimeseriesResult.LabeledMetricTimeseries(
                        datapoints=metric_datapoints
                    )
                )
            # Constructing TimeSeriesResult instead of TableResult
            result = TimeseriesResult(
                metric_name=StringValue(value=metric_names),
                labeled_metric_timeseries=time_series_data
            )
            # Updated PlaybookTaskResult with Time Series data
            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,  # Ensuring correct type
                timeseries=result,  # Using time series result
                source=self.source
            )
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Azure task: {e}")
