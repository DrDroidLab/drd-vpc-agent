import json
import logging

from datetime import datetime

from google.protobuf.wrappers_pb2 import DoubleValue, StringValue, UInt64Value

from integrations.source_api_processors.datadog_api_processor import DatadogApiProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, TimeseriesResult, LabelValuePair, \
    PlaybookTaskResultType, TableResult, TextResult
from protos.playbooks.source_task_definitions.datadog_task_pb2 import Datadog
from protos.assets.asset_pb2 import AccountConnectorAssets, AccountConnectorAssetsModelFilters
from protos.assets.datadog_asset_pb2 import DatadogServiceAssetModel, DatadogDashboardModel
from protos.ui_definition_pb2 import FormField, FormFieldType

from utils.credentilal_utils import generate_credentials_dict
from utils.proto_utils import proto_to_dict, dict_to_proto
from utils.string_utils import is_partial_match
from utils.playbooks_client import PrototypeClient

logger = logging.getLogger(__name__)

class DatadogSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.DATADOG
        self.task_proto = Datadog
        self.task_type_callable_map = {
            Datadog.TaskType.SERVICE_METRIC_EXECUTION: {
                'executor': self.execute_service_metric_execution,
                'model_types': [SourceModelType.DATADOG_SERVICE],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a Datadog Metric by service',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="service_name"),
                              display_name=StringValue(value="Service"),
                              description=StringValue(value='Select Service'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="environment_name"),
                              display_name=StringValue(value="Environment"),
                              description=StringValue(value='Select Environment'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="metric_family"),
                              display_name=StringValue(value="Metric Family"),
                              description=StringValue(value='Select Metric Family'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="metric"),
                              display_name=StringValue(value="Metric"),
                              description=StringValue(value='Select Metric'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_MULTIPLE_FT),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval(Seconds)"),
                              description=StringValue(value='e.g. 60, 300, 900'),
                              data_type=LiteralType.LONG,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
            Datadog.TaskType.LOG_QUERY_EXECUTION: {
                'executor': self.execute_log_query_execution,
                'model_types': [],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Fetch a Datadog log',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="query"),
                              display_name=StringValue(value="Query"),
                              description=StringValue(value='e.g. "service:web-api status:error", "env:prod source:nginx"'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT)
                ]
            },
            Datadog.TaskType.DASHBOARD_MULTIPLE_WIDGETS: {
                'executor': self.execute_dashboard_multiple_widgets_task,
                'model_types': [SourceModelType.DATADOG_DASHBOARD],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch multiple widgets by dashboard name and widget ID',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="dashboard_name"),
                              display_name=StringValue(value="Dashboard Name"),
                              description=StringValue(value='e.g. "System Overview", "API Performance"'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="widget_id"),
                              display_name=StringValue(value="Widget ID"),
                              description=StringValue(value='e.g. "cpu_usage_widget", "error_rate_chart"'),
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="")),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT,
                              is_optional=True),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval(Seconds)"),
                              description=StringValue(value='e.g. 60, 300, 900'),
                              data_type=LiteralType.LONG,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                    FormField(key_name=StringValue(value="template_variables"),
                              display_name=StringValue(value="Template Variables"),
                              description=StringValue(value='e.g. {"env": "prod", "service": "web-api"}'),
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="{}")),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.CODE_EDITOR_FT,
                              is_optional=True),
                ]
            },
            Datadog.TaskType.APM_QUERY: {
                'executor': self.execute_apm_queries,
                'model_types': [SourceModelType.DATADOG_APM],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch APM Queries',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="service_name"),
                              display_name=StringValue(value="Service Name"),
                              description=StringValue(value='e.g. "web-api", "auth-service"'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval(Seconds)"),
                              description=StringValue(value='e.g. 60, 300, 900'),
                              data_type=LiteralType.LONG,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
        }

    def get_connector_processor(self, datadog_connector, **kwargs):
        generated_credentials = generate_credentials_dict(datadog_connector.type, datadog_connector.keys)
        if 'dd_api_domain' not in generated_credentials:
            generated_credentials['dd_api_domain'] = 'datadoghq.com'
        return DatadogApiProcessor(**generated_credentials)

    def execute_service_metric_execution(self, time_range: TimeRange, dd_task: Datadog,
                                         datadog_connector: ConnectorProto):
        try:
            if not datadog_connector:
                raise Exception("Task execution Failed:: No Datadog source found")

            task = dd_task.service_metric_execution
            service_name = task.service_name.value
            env_name = task.environment_name.value
            metric = task.metric.value
            interval = task.interval.value
            if not interval:
                interval = 300

            timeseries_offsets = task.timeseries_offsets
            query_tags = f"service:{service_name},env:{env_name}"
            metric_query = f'avg:{metric}{{{query_tags}}}'
            specific_metric = {"queries": [
                {
                    "name": "query1",
                    "query": metric_query
                }
            ]}

            dd_api_processor = self.get_connector_processor(datadog_connector)

            labeled_metric_timeseries: [TimeseriesResult.LabeledMetricTimeseries] = []

            # Get current time values
            current_results = dd_api_processor.fetch_metric_timeseries(time_range, specific_metric,
                                                                       interval=interval * 1000)
            if not current_results:
                metric_str = ''
                for metric in specific_metric['queries']:
                    metric_str += metric['query']
                    metric_str += ', '
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No data returned from Datadog for service metric: {metric_str}")), source=self.source)

            for itr, item in enumerate(current_results.series.value):
                group_tags = item.group_tags.value
                metric_labels: [LabelValuePair] = []
                if item.unit:
                    unit = item.unit[0].name
                else:
                    unit = ''
                for gt in group_tags:
                    metric_labels.append(
                        LabelValuePair(name=StringValue(value='resource_name'), value=StringValue(value=gt)))

                metric_labels.append(
                    LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value='0'))
                )

                times = current_results.times.value
                values = current_results.values.value[itr].value
                datapoints: [TimeseriesResult.LabeledMetricTimeseries.Datapoint] = []
                for it, val in enumerate(values):
                    datapoints.append(TimeseriesResult.LabeledMetricTimeseries.Datapoint(timestamp=int(times[it]),
                                                                                         value=DoubleValue(
                                                                                             value=val)))

                labeled_metric_timeseries.append(
                    TimeseriesResult.LabeledMetricTimeseries(metric_label_values=metric_labels,
                                                             unit=StringValue(value=unit), datapoints=datapoints))

            # Get offset values if specified
            if timeseries_offsets:
                offsets = [offset for offset in timeseries_offsets]
                for offset in offsets:
                    adjusted_start_time = TimeRange(
                        time_geq=time_range.time_geq - offset,
                        time_lt=time_range.time_lt - offset
                    )
                    offset_results = dd_api_processor.fetch_metric_timeseries(adjusted_start_time, specific_metric,
                                                                              interval=interval * 1000)
                    if not offset_results:
                        print(f"No data returned from Datadog for offset {offset} seconds")
                        continue

                    for itr, item in enumerate(offset_results.series.value):
                        group_tags = item.group_tags.value
                        metric_labels: [LabelValuePair] = []
                        if item.unit:
                            unit = item.unit[0].name
                        else:
                            unit = ''
                        for gt in group_tags:
                            metric_labels.append(
                                LabelValuePair(name=StringValue(value='resource_name'), value=StringValue(value=gt)))

                        metric_labels.append(
                            LabelValuePair(name=StringValue(value='offset_seconds'),
                                           value=StringValue(value=str(offset)))
                        )

                        times = offset_results.times.value
                        values = offset_results.values.value[itr].value
                        datapoints: [TimeseriesResult.LabeledMetricTimeseries.Datapoint] = []
                        for it, val in enumerate(values):
                            datapoints.append(
                                TimeseriesResult.LabeledMetricTimeseries.Datapoint(timestamp=int(times[it]),
                                                                                   value=DoubleValue(
                                                                                       value=val)))

                        labeled_metric_timeseries.append(
                            TimeseriesResult.LabeledMetricTimeseries(metric_label_values=metric_labels,
                                                                     unit=StringValue(value=unit),
                                                                     datapoints=datapoints))

            timeseries_result = TimeseriesResult(metric_expression=StringValue(value=metric),
                                                 metric_name=StringValue(value=service_name),
                                                 labeled_metric_timeseries=labeled_metric_timeseries)

            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source)
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Datadog task: {e}")

    
    def execute_log_query_execution(self, time_range: TimeRange, dd_task: Datadog,
                                    datadog_connector: ConnectorProto):
        try:
            if not datadog_connector:
                raise Exception("Task execution Failed:: No Datadog source found")
            task = dd_task.log_query_execution
            query = task.query.value
            dd_api_processor = self.get_connector_processor(datadog_connector)
            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Time Range -> {}, Query -> "
                "{}".format("Datadog", datadog_connector.account_id.value, time_range, query), flush=True)
            current_results = dd_api_processor.fetch_logs(query, time_range)
            if not current_results:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No logs returned from Datadog for query: {query}")), source=self.source)
            table_rows: [TableResult.TableRow] = []
            for item in current_results:
                # Create a list to hold the columns for the current row
                table_columns: [TableResult.TableColumn] = []

                # Extracting basic fields with default values if not present
                table_columns.append(TableResult.TableColumn(name=StringValue(value='id'),
                                                             value=StringValue(value=item['id'])))
                timestamp_value = item['attributes'].get('timestamp')
                if isinstance(timestamp_value, datetime):
                    timestamp_value = str(timestamp_value.timestamp())
                else:
                    timestamp_value = ''
                table_columns.append(TableResult.TableColumn(name=StringValue(value='timestamp'),
                                                             value=StringValue(
                                                                 value=timestamp_value)))
                table_columns.append(TableResult.TableColumn(name=StringValue(value='service'),
                                                             value=StringValue(
                                                                 value=item['attributes'].get('service', ''))))
                table_columns.append(TableResult.TableColumn(name=StringValue(value='host'),
                                                             value=StringValue(
                                                                 value=item['attributes'].get('host', ''))))
                table_columns.append(TableResult.TableColumn(name=StringValue(value='status'),
                                                             value=StringValue(
                                                                 value=item['attributes'].get('status', ''))))
                table_columns.append(TableResult.TableColumn(name=StringValue(value='message'),
                                                             value=StringValue(
                                                                 value=item['attributes'].get('message', ''))))

                # Stringify tags as a JSON array
                tags = item['attributes'].get('tags', [])
                tags_string = json.dumps(tags) if tags else json.dumps([])  # Stringify the list
                table_columns.append(TableResult.TableColumn(name=StringValue(value='tags'),
                                                             value=StringValue(value=tags_string)))

                # Stringify attributes as a JSON object
                attributes = item['attributes'].get('attributes', {})
                for key, value in attributes.items():
                    if isinstance(value, datetime):
                        attributes[key] = str(value.timestamp())
                attributes_string = json.dumps(attributes) if attributes else json.dumps({})  # Stringify the dict
                table_columns.append(TableResult.TableColumn(name=StringValue(value='attributes'),
                                                             value=StringValue(value=attributes_string)))

                # Create a new TableRow with the populated columns
                table_row = TableResult.TableRow(columns=table_columns)
                table_rows.append(table_row)

            result = TableResult(
                raw_query=StringValue(value=f"Execute ```{query}```"),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            task_result = PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=result, source=self.source)
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing Datadog Log task: {e}")

    def execute_dashboard_multiple_widgets(self, 
                                           time_range: TimeRange, 
                                           dd_task: Datadog,
                                           datadog_connector: ConnectorProto,
                                           widget_id: str,
                                           dashboard_entity=None) -> PlaybookTaskResult:
        """
        Execute a task to fetch metrics from multiple widgets in a Datadog dashboard.
        
        Args:
            time_range: The time range to fetch metrics for
            dd_task: The Datadog task containing dashboard and widget information
            datadog_connector: The Datadog connector to use
            widget_id: The ID of the widget to fetch
            dashboard_entity: Optional pre-fetched dashboard entity to avoid duplicate asset lookup
            
        Returns:
            A PlaybookTaskResult containing timeseries data
        """
        try:
            if not datadog_connector:
                raise Exception("Task execution Failed:: No Datadog source found")

            task = dd_task.dashboard_multiple_widgets
            dashboard_name = task.dashboard_name.value
            template_variables = task.template_variables.value
            if task.unit and task.unit.value:
                unit = task.unit.value
            else:
                unit = ''
                
            interval = task.interval.value if task.interval else 300

            # Get the Datadog API processor
            dd_api_processor = self.get_connector_processor(datadog_connector)
            
            # Find the dashboard with the specified name
            dashboard_id = None
            widget_definition = None
            widget_title = None
            template_variables_map = {}  # Map to store template variable names to default values
            
            # If dashboard_entity is not provided, fetch it from assets
            if dashboard_entity is None:
                # Get all dashboard entities
                prototype_client = PrototypeClient()
                assets: AccountConnectorAssets = prototype_client.get_connector_assets(
                    "DATADOG",
                    datadog_connector.id.value,
                    SourceModelType.DATADOG_DASHBOARD,
                    proto_to_dict(AccountConnectorAssetsModelFilters())
                )

                if not assets:
                    return [PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                             text=TextResult(output=StringValue(
                                             value=f"No dashboard assets found for the account")),
                                             source=self.source)]

                dd_assets: [DatadogDashboardModel] = assets.datadog.assets
                all_dashboard_asset: [DatadogDashboardModel] = [dd_asset.datadog_dashboard for dd_asset in dd_assets if
                                                               dd_asset.type == SourceModelType.DATADOG_DASHBOARD]
                for dashboard_entity_item in all_dashboard_asset:
                    if is_partial_match(dashboard_entity_item.title.value, [dashboard_name]):
                        dashboard_entity = dashboard_entity_item
                        break
            
            # Process the dashboard entity if found
            if dashboard_entity:
                dashboard_id = dashboard_entity.id.value
                
                # Parse template_variables JSON string into a dictionary
                user_template_variables = {}
                if template_variables:
                    try:
                        user_template_variables = json.loads(template_variables)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse template_variables JSON: {template_variables}")

                # Extract template variables and create a mapping of variable names to their properties (value and prefix)
                if dashboard_entity.template_variables:
                    for template_var_struct in dashboard_entity.template_variables:
                        template_var = proto_to_dict(template_var_struct)
                        if 'name' in template_var:
                            var_name = template_var['name']
                            var_info = {
                                'prefix': template_var.get('prefix', ''),  # Get prefix or empty string if not present
                                'value': ''
                            }
                            
                            # Set the value - either from user input or default
                            if var_name in user_template_variables:
                                var_info['value'] = user_template_variables[var_name]
                            elif 'default' in template_var:
                                var_info['value'] = template_var['default']
                            
                            template_variables_map[var_name] = var_info
                
                # Search through all panels and widgets to find the specified widget ID
                for panel in dashboard_entity.panels:
                    for widget in panel.widgets:
                        if str(widget.id.value) == widget_id:
                            # Extract the full widget definition including the nested 'definition' field
                            widget_definition = proto_to_dict(widget)
                            widget_title = widget_definition.get('title', '') or f"Widget {widget_id}"
                            break
            
            if not dashboard_id:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                         text=TextResult(output=StringValue(
                                         value=f"Dashboard with name '{dashboard_name}' not found")),
                                         source=self.source)
            
            if not widget_definition:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                         text=TextResult(output=StringValue(
                                         value=f"Widget with ID '{widget_id}' not found in dashboard '{dashboard_name}'")),
                                         source=self.source)
            
            # Get the widget type
            widget_type = widget_definition.get('widget_type', 'timeseries')
            resource_type = widget_definition.get('response_type', 'timeseries')
            queries = widget_definition.get('queries', [])
            formulas = widget_definition.get('formulas', [])
                            
            # Process queries to replace template variables with their default values
            if queries:
                for query in queries:
                    if "query" in query:
                            # Handle all template variables
                            for var_name, var_info in template_variables_map.items():
                                if f"${var_name}" in query["query"]:
                                    if var_name in user_template_variables:
                                        query["query"] = query["query"].replace(f"${var_name}", f"{var_info['prefix']}:{var_info['value']}")
                                    else:
                                        query["query"] = query["query"].replace(f"${var_name}", f"{var_info['value']}")
                        
            # For timeseries metrics, always use the specified interval (default 5 minutes)
            interval_ms = interval * 1000
            
            # For non-timeseries data, never pass the interval parameter
            # For timeseries data, only pass it if explicitly provided by the user
            if resource_type == 'timeseries' and interval != 300:  # If it's not the default value
                response = dd_api_processor.widget_query_timeseries_points_api(
                    time_range, 
                    queries, 
                    formulas, 
                    resource_type=resource_type,
                    interval_ms=interval_ms
                )
            elif resource_type == 'event_list':
                query_string = queries[0].get('query', '')
                response = dd_api_processor.widget_query_logs_stream_api(
                    time_range, 
                    query_string
                )
            else:
                # Let the Datadog API determine the appropriate interval based on the time range
                response = dd_api_processor.widget_query_timeseries_points_api(
                    time_range,
                    queries, 
                    formulas, 
                    resource_type=resource_type
                )

            if not response:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                        text=TextResult(output=StringValue(
                                        value=f"No data returned from Datadog for widget ID '{widget_id}' in dashboard '{dashboard_name}'")),
                                        widget_id=StringValue(value=widget_id),
                                        source=self.source)

            # Process the response based on resource_type
            # For event_list resource type (log streams), return logs in a table format
            if resource_type == 'event_list':
                if 'data' in response:
                    # Extract log entries from the response
                    log_entries = response.get('data', [])
                    
                    if not log_entries or not isinstance(log_entries, list):
                        return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                                text=TextResult(output=StringValue(
                                                value=f"No log entries found in response for widget ID '{widget_id}' in dashboard '{dashboard_name}'")),
                                                widget_id=StringValue(value=widget_id),
                                                source=self.source)
                    
                    # Create table rows for each log entry
                    table_rows: [TableResult.TableRow] = []
                    
                    for log_entry in log_entries:
                        # Create a list to hold the columns for the current row
                        table_columns: [TableResult.TableColumn] = []
                        
                        # Extract log ID
                        log_id = log_entry.get('id', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='id'),
                            value=StringValue(value=log_id)
                        ))
                        
                        # Extract log type
                        log_type = log_entry.get('type', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='type'),
                            value=StringValue(value=log_type)
                        ))
                        
                        # Extract attributes
                        attributes = log_entry.get('attributes', {})
                        
                        # Extract common fields from attributes
                        service = attributes.get('service', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='service'),
                            value=StringValue(value=service)
                        ))
                        
                        host = attributes.get('host', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='host'),
                            value=StringValue(value=host)
                        ))
                        
                        message = attributes.get('message', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='message'),
                            value=StringValue(value=message)
                        ))
                        
                        status = attributes.get('status', '')
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='status'),
                            value=StringValue(value=status)
                        ))
                        
                        # Handle timestamp
                        timestamp = attributes.get('timestamp', '')
                        if isinstance(timestamp, datetime):
                            timestamp = str(timestamp.timestamp())
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='timestamp'),
                            value=StringValue(value=str(timestamp))
                        ))
                        
                        # Handle tags as JSON string
                        tags = attributes.get('tags', [])
                        tags_string = json.dumps(tags) if tags else json.dumps([])
                        table_columns.append(TableResult.TableColumn(
                            name=StringValue(value='tags'),
                            value=StringValue(value=tags_string)
                        ))
                        
                        # Create a new TableRow with the populated columns
                        table_row = TableResult.TableRow(columns=table_columns)
                        table_rows.append(table_row)
                    
                    # Create the table result
                    result = TableResult(
                        raw_query=StringValue(value=f"Dashboard: {dashboard_name}, Widget: {widget_title}"),
                        rows=table_rows,
                        total_count=UInt64Value(value=len(table_rows)),
                    )
                    
                    # Return the logs result
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.LOGS,
                        logs=result,
                        widget_id=StringValue(value=widget_id),
                        source=self.source
                    )

            # Handle scalar responses as logs with name/value columns
            if resource_type == 'scalar':
                if 'data' in response and 'attributes' in response['data']:
                    attributes = response['data']['attributes']
                    
                    # Create table rows for scalar values
                    table_rows: [TableResult.TableRow] = []
                    
                    # Handle scalar response with columns
                    if 'columns' in attributes:
                        columns = attributes['columns']
                        
                        for column in columns:
                            column_name = column.get('name', '')
                            column_type = column.get('type', '')
                            column_values = column.get('values', [])
                            
                            # Skip empty values
                            if not column_values:
                                continue
                            
                            # Get the first value (scalar responses typically have a single value per column)
                            value = column_values[0]
                            
                            # Handle group type columns (like "service")
                            if column_type == 'group' and isinstance(value, list):
                                for group_value in value:
                                    table_columns = [
                                        TableResult.TableColumn(
                                            name=StringValue(value='name'),
                                            value=StringValue(value=column_name)
                                        ),
                                        TableResult.TableColumn(
                                            name=StringValue(value='value'),
                                            value=StringValue(value=str(group_value))
                                        )
                                    ]
                                    table_rows.append(TableResult.TableRow(columns=table_columns))
                            # Handle number type columns with units
                            elif column_type == 'number':
                                # Format value with unit if available
                                formatted_value = str(value)
                                
                                # Check for unit information
                                meta = column.get('meta', {})
                                unit_info = meta.get('unit', [])
                                
                                if unit_info and unit_info[0]:
                                    unit_data = unit_info[0]
                                    short_name = unit_data.get('short_name', '')
                                    
                                    if short_name:
                                        formatted_value = f"{value}{short_name}"
                                
                                table_columns = [
                                    TableResult.TableColumn(
                                        name=StringValue(value='name'),
                                        value=StringValue(value=column_name)
                                    ),
                                    TableResult.TableColumn(
                                        name=StringValue(value='value'),
                                        value=StringValue(value=formatted_value)
                                    )
                                ]
                                table_rows.append(TableResult.TableRow(columns=table_columns))
                            # Handle other types
                            else:
                                table_columns = [
                                    TableResult.TableColumn(
                                        name=StringValue(value='name'),
                                        value=StringValue(value=column_name)
                                    ),
                                    TableResult.TableColumn(
                                        name=StringValue(value='value'),
                                        value=StringValue(value=str(value))
                                    )
                                ]
                                table_rows.append(TableResult.TableRow(columns=table_columns))
                    
                    # Handle multiple values scalar response
                    elif 'values' in attributes:
                        values = attributes['values']
                        groups = attributes.get('groups', [])
                        
                        for idx, group in enumerate(groups):
                            if idx < len(values):
                                group_value = values[idx]
                                group_by_values = group.get('by', {})
                                
                                # Format value with unit if available
                                formatted_value = str(group_value)
                                if unit:
                                    formatted_value = f"{group_value} {unit}"
                                
                                # Use the first group_by value as the name, or 'value' if none
                                name = 'value'
                                if group_by_values:
                                    first_key = next(iter(group_by_values))
                                    name = f"{first_key}: {group_by_values[first_key]}"
                                
                                table_columns = [
                                    TableResult.TableColumn(
                                        name=StringValue(value='name'),
                                        value=StringValue(value=name)
                                    ),
                                    TableResult.TableColumn(
                                        name=StringValue(value='value'),
                                        value=StringValue(value=formatted_value)
                                    )
                                ]
                                table_rows.append(TableResult.TableRow(columns=table_columns))
                    
                    # Create the table result if we have rows
                    if table_rows:
                        result = TableResult(
                            raw_query=StringValue(value=f"Dashboard: {dashboard_name}, Widget: {widget_title}"),
                            rows=table_rows,
                            total_count=UInt64Value(value=len(table_rows)),
                        )
                        
                        # Return the logs result
                        return PlaybookTaskResult(
                            type=PlaybookTaskResultType.LOGS,
                            logs=result,
                            widget_id=StringValue(value=widget_id),
                            source=self.source
                        )
                    
                    # If we couldn't extract any rows, return an error message
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(
                            value=f"Could not extract scalar values from response for widget ID '{widget_id}' in dashboard '{dashboard_name}'"
                        )),
                        widget_id=StringValue(value=widget_id),
                        source=self.source
                    )
            
            # Process the response into labeled metric timeseries for other resource types
            labeled_metric_timeseries_list = []
            
            # For timeseries responses (not scalar or event_list)
            if resource_type != 'scalar' and resource_type != 'event_list':
                if 'data' in response and 'attributes' in response['data']:
                    attributes = response['data']['attributes']
                    
                    if 'series' in attributes and 'values' in attributes:
                        series = attributes['series']
                        values = attributes['values']
                        times = attributes.get('times', [])
                    
                        # Process each series
                        for idx, series_item in enumerate(series):
                            if idx < len(values):
                                series_values = values[idx]
                                group_tags = series_item.get('group_tags', ['default'])
                                
                                # Create datapoints
                                datapoints = []
                                for time_idx, timestamp in enumerate(times):
                                    if time_idx < len(series_values):
                                        value = series_values[time_idx]
                                        datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                            timestamp=int(timestamp),
                                            value=DoubleValue(value=value)
                                        )
                                        datapoints.append(datapoint)
                                
                                # Create metric labels
                                metric_labels = [
                                    LabelValuePair(
                                        name=StringValue(value='widget_name'), 
                                        value=StringValue(value=widget_title)
                                    ),
                                    LabelValuePair(
                                        name=StringValue(value='offset_seconds'), 
                                        value=StringValue(value='0')
                                    )
                                ]
                                
                                # Add tag information
                                for tag in group_tags:
                                    metric_labels.append(
                                        LabelValuePair(
                                            name=StringValue(value='tag'), 
                                            value=StringValue(value=tag)
                                        )
                                    )
                                
                                # Add to the list
                                labeled_metric_timeseries_list.append(
                                    TimeseriesResult.LabeledMetricTimeseries(
                                        metric_label_values=metric_labels,
                                        unit=StringValue(value=unit),
                                        datapoints=datapoints
                                    )
                                )

            # Check if we have any data points
            if not labeled_metric_timeseries_list:
                error_msg = f"No data points could be extracted from the response for widget ID '{widget_id}' (type: {widget_type}) in dashboard '{dashboard_name}' using resource_type '{resource_type}'"
                logger.error(error_msg)
                # Return empty timeseries instead of error text
                timeseries_result = TimeseriesResult(
                    metric_expression=StringValue(value=json.dumps(queries)),
                    metric_name=StringValue(value=widget_title),
                    labeled_metric_timeseries=[]  # Empty list
                )
                
                task_result = PlaybookTaskResult(
                    type=PlaybookTaskResultType.TIMESERIES,
                    timeseries=timeseries_result,
                    widget_id=StringValue(value=widget_id),
                    source=self.source
                )
                return task_result
            
            # Create the final result
            timeseries_result = TimeseriesResult(
                metric_expression=StringValue(value=json.dumps(queries)),
                metric_name=StringValue(value=widget_title),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )
            
            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                widget_id=StringValue(value=widget_id),
                source=self.source
            )
            
            return task_result
        except Exception as e:
            logger.error(f"Error while executing Dashboard Widget by Name/ID task: {str(e)}")
            raise Exception(f"Error while executing Datadog task: {e}")



    def execute_dashboard_multiple_widgets_task(self, time_range: TimeRange, dd_task: Datadog,
                                          datadog_connector: ConnectorProto):
        """
        Task executor that extracts parameters from dashboard_multiple_widgets task and delegates to execute_dashboard_multiple_widgets
        
        Args:
            time_range: The time range to fetch metrics for
            dd_task: The Datadog task containing dashboard and widget information
            datadog_connector: The Datadog connector to use
            
        Returns:
            A PlaybookTaskResult containing timeseries data
        """
        # Extract all task parameters
        task = dd_task.dashboard_multiple_widgets
        widget_id = task.widget_id.value

        if widget_id:
            result = []
            response = self.execute_dashboard_multiple_widgets(
                time_range=time_range,
                dd_task=dd_task,
                widget_id=widget_id,
                datadog_connector=datadog_connector)
            result.append(response)
            return result
        
        else:
            result = []
            dashboard_name = task.dashboard_name.value
            
            # Fetch dashboard assets once
            prototype_client = PrototypeClient()
            assets: AccountConnectorAssets = prototype_client.get_connector_assets(
                "DATADOG",
                datadog_connector.id.value,
                SourceModelType.DATADOG_DASHBOARD,
                proto_to_dict(AccountConnectorAssetsModelFilters())
            )
                
            if not assets:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="No dashboard assets found for the account")),
                    source=self.source)
                    
            dd_assets: [DatadogDashboardModel] = assets.datadog.assets
            all_dashboard_asset: [DatadogDashboardModel] = [dd_asset.datadog_dashboard for dd_asset in dd_assets if 
                                                            dd_asset.type == SourceModelType.DATADOG_DASHBOARD]
            
            # Find the matching dashboard
            matching_dashboard = None
            for dashboard in all_dashboard_asset:
                if is_partial_match(dashboard.title.value, [dashboard_name]):
                    matching_dashboard = dashboard
                    break
                    
            if matching_dashboard:
                # Process all widgets in the matching dashboard
                for panel in matching_dashboard.panels:
                    for widget in panel.widgets:
                        widget_def = proto_to_dict(widget)
                        if widget_def.get("widget_type") != "note":
                            widget_id = str(widget.id.value)
                            response = self.execute_dashboard_multiple_widgets(
                                time_range=time_range,
                                dd_task=dd_task,
                                datadog_connector=datadog_connector,
                                widget_id=widget_id,
                                dashboard_entity=matching_dashboard)
                            result.append(response)
            else:
                return [PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"Dashboard with name '{dashboard_name}' not found")),
                    source=self.source)]
            return result

    def filter_using_assets(self, dd_connector: ConnectorProto, service_name, filters: dict = None):
        try:
            prototype_client = PrototypeClient()
            assets: AccountConnectorAssets = prototype_client.get_connector_assets(
                "DATADOG",
                dd_connector.id.value,
                SourceModelType.DATADOG_SERVICE,
                proto_to_dict(AccountConnectorAssetsModelFilters())
            )
            
            if not assets:
                logger.warning(f"DatadogSourceManager.filter_using_assets:: No assets "
                               f"found for account: {dd_connector.account_id.value}, connector: {dd_connector.id.value}")
                return "[]"

            dd_assets: [DatadogServiceAssetModel] = assets.datadog.assets
            all_service_asset: [DatadogServiceAssetModel] = [dd_asset.datadog_service for dd_asset in dd_assets if
                                                           dd_asset.type == SourceModelType.DATADOG_SERVICE]

            matching_metrics = []
            # Iterate through each service asset
            for service_asset in all_service_asset:
                # Check if this is the service we're looking for
                if service_asset.service_name.value == service_name:
                    # Iterate through each metric in the service asset
                    for metric in service_asset.metrics:
                        # Check if the metric family is "trace"
                        if metric.metric_family.value == "trace":
                            # Check if the metric has a tag with "service:service_name"
                            service_tag_found = False
                            for tag in metric.tags:
                                if tag.value == f"service:{service_name}":
                                    service_tag_found = True
                                    break
                            
                            # If both conditions are met, add the metric value to our results
                            if service_tag_found:
                                matching_metrics.append(metric.metric.value)
            return matching_metrics
        except Exception as e:
            logger.error(f"Error while accessing assets: {dd_connector.account_id.value}, connector: "
                     f"{dd_connector.id.value} with error: {e}")
            return None


    def execute_apm_queries(self, time_range: TimeRange, dd_task: Datadog, datadog_connector: ConnectorProto):
        
        task = dd_task.apm_query
        service_name = task.service_name.value

        dd_api_processor = self.get_connector_processor(datadog_connector)

        start_time = time_range.time_geq
        end_time = time_range.time_lt
        interval = task.interval.value if task.interval else 300
        interval = interval * 1000 # Convert to milliseconds
        matching_metrics = self.filter_using_assets(datadog_connector, filters=None, service_name=service_name)
        response = dd_api_processor.fetch_query_results(service_name=service_name, start_time=start_time, end_time=end_time, matching_metrics=matching_metrics, interval=interval)
        
        if not response:
            return [PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, 
                                      text=TextResult(output=StringValue(value=f"No data returned from Datadog for query: {service_name}")), 
                                      source=self.source)]

        # Process each dictionary in the response list
        result = []
        for item in response:
            # Create a single timeseries result for this dictionary with multiple lines
            labeled_metric_timeseries_list = []
            
            # Process each key-value pair in this dictionary
            for key, val in item.items():
                # Create a fresh datapoints list for each key-value pair
                datapoints = []
                series = val.get('series', [])
                if not series:
                    error_msg = f"No data returned from Datadog for query: {key}"
                    logger.error(error_msg)

                    # Return empty timeseries instead of error text
                    metric_labels = [
                    LabelValuePair(
                        name=StringValue(value='query'), 
                        value=StringValue(value=key)
                    )
                    ]

                    labeled_metric_timeseries = TimeseriesResult.LabeledMetricTimeseries(
                        metric_label_values=metric_labels,
                        datapoints=datapoints
                    )

                    timeseries_result = TimeseriesResult(
                        metric_expression=StringValue(value=json.dumps(key)),
                        metric_name=StringValue(value=service_name),
                        labeled_metric_timeseries=[]  # Empty list
                    )
                    
                    task_result = PlaybookTaskResult(
                        type=PlaybookTaskResultType.TIMESERIES,
                        timeseries=timeseries_result,
                        source=self.source
                    )
                    result.append(task_result)

                    continue
            
                # Extract the data points from the series
                data = series[0].get('pointlist', [])
                for datapoint in data:
                    timestamp = int(datapoint[0])
                    value = float(datapoint[1])
                    datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                                timestamp=int(timestamp),
                                                value=DoubleValue(value=value))
                    datapoints.append(datapoint)
                
                # Create metric labels for this key-value pair
                metric_labels = [
                    LabelValuePair(
                        name=StringValue(value='query'), 
                        value=StringValue(value=key)
                    )
                ]

                # Create a labeled metric timeseries for this key-value pair
                labeled_metric_timeseries = TimeseriesResult.LabeledMetricTimeseries(
                    metric_label_values=metric_labels,
                    datapoints=datapoints,
                    unit=StringValue(value='seconds')  # Assuming unit is milliseconds
                )
                
                # Add to the list for this dictionary
                labeled_metric_timeseries_list.append(labeled_metric_timeseries)
            
            # If we have any timeseries data for this dictionary
            if labeled_metric_timeseries_list:
                # Create the final result
                if "error" in key.lower() or "errors" in key.lower():
                    timeseries_result = TimeseriesResult(
                        metric_expression=StringValue(value=json.dumps(key)),
                        metric_name=StringValue(value=service_name),
                        chart_type=StringValue(value="point_chart"),
                        labeled_metric_timeseries=labeled_metric_timeseries_list
                    )
                else:
                    timeseries_result = TimeseriesResult(
                        metric_expression=StringValue(value=json.dumps(key)),
                        metric_name=StringValue(value=service_name),
                        labeled_metric_timeseries=labeled_metric_timeseries_list
                    )
                
                # Create a single task result for this dictionary
                task_result = PlaybookTaskResult(
                    type=PlaybookTaskResultType.TIMESERIES,
                    timeseries=timeseries_result,
                    source=self.source
                )
                result.append(task_result)
        return result
