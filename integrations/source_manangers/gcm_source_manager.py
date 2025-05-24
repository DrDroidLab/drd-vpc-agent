from datetime import datetime, timezone

import logging
import re
import random

import pytz
from google.protobuf.wrappers_pb2 import StringValue, DoubleValue, UInt64Value, Int64Value

from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import TimeseriesResult, LabelValuePair, PlaybookTaskResult, \
    PlaybookTaskResultType, TableResult, TextResult
from protos.playbooks.source_task_definitions.gcm_task_pb2 import Gcm
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict
from integrations.source_api_processors.gcm_api_processor import GcmApiProcessor
from utils.static_mappings import GCM_SERVICE_DASHBOARD_QUERIES
from utils.time_utils import calculate_timeseries_bucket_size


logger = logging.getLogger(__name__)


def get_project_id(gcm_connector: ConnectorProto) -> str:
    gcm_connector_keys = gcm_connector.keys
    generated_credentials = generate_credentials_dict(gcm_connector.type, gcm_connector_keys)
    if 'project_id' not in generated_credentials:
        raise Exception("GCM project ID not configured for GCM connector")
    return generated_credentials['project_id']


class GcmSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.GCM
        self.task_proto = Gcm
        cloud_run_metrics_map = {name: {"metric": "", "aggregations": list(aggs.keys())}
                                 for name, aggs in GCM_SERVICE_DASHBOARD_QUERIES.items()}
        cloud_run_metric_literals = [
            Literal(type=LiteralType.STRING, string=StringValue(value=metric_name))
            for metric_name in cloud_run_metrics_map.keys()
        ]
        self.task_type_callable_map = {
            Gcm.TaskType.MQL_EXECUTION: {
                'executor': self.execute_mql_execution,
                'model_types': [],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Execute MQL in GCM',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="query"),
                              display_name=StringValue(value="MQL Expression"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
            Gcm.TaskType.FILTER_LOG_EVENTS: {
                'executor': self.execute_filter_log_events,
                'model_types': [],
                'result_type': PlaybookTaskResultType.TABLE,
                'display_name': 'Fetch Logs from GCM',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="filter_query"),
                              display_name=StringValue(value="Filter Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                    FormField(key_name=StringValue(value="order_by"),
                              display_name=StringValue(value="Order By"),
                              data_type=LiteralType.STRING,
                              is_optional=True,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="page_size"),
                              display_name=StringValue(value="Page Size"),
                              data_type=LiteralType.LONG,
                              default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=2000)),
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
            Gcm.TaskType.DASHBOARD_VIEW: {
                'executor': self.execute_dashboard_view,
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'View GCM Dashboard Widget',
                'category': 'Dashboards',
                'form_fields': [
                    FormField(key_name=StringValue(value="dashboard_id"),
                              display_name=StringValue(value="Dashboard ID"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="widget_name"),
                              display_name=StringValue(value="Widget Name"),
                              data_type=LiteralType.STRING,
                              is_optional=True,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval(Seconds)"),
                              description=StringValue(value='(Optional)Enter Interval'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
            Gcm.TaskType.SHEETS_DATA_FETCH: {
                'executor': self.execute_sheets_data_fetch,
                'result_type': PlaybookTaskResultType.TABLE,
                'display_name': 'Fetch Google Sheets Data',
                'category': 'Google Sheets',
                'form_fields': [
                    FormField(key_name=StringValue(value="spreadsheet_name"),
                              display_name=StringValue(value="Spreadsheet Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="sheet_name"),
                              display_name=StringValue(value="Sheet Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="max_rows"),
                              display_name=StringValue(value="Maximum Rows to Return"),
                              data_type=LiteralType.LONG,
                              default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=500)),
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="output_format"),
                              display_name=StringValue(value="Output Format"),
                              data_type=LiteralType.STRING,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="JSON")),
                              form_field_type=FormFieldType.DROPDOWN_FT,
                              valid_values=[
                                  Literal(type=LiteralType.STRING, string=StringValue(value="JSON")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="TABLE")),
                                  Literal(type=LiteralType.STRING, string=StringValue(value="CSV"))
                              ]
                            )
                ]
            },
            Gcm.TaskType.CLOUD_RUN_SERVICE_DASHBOARD: {
                'executor': self.execute_cloud_run_service_dashboard,
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'View Cloud Run Service Metrics',
                'category': 'Cloud Run',
                'form_fields': [
                    FormField(key_name=StringValue(value="service_name"),
                              display_name=StringValue(value="Service Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="region"),
                              display_name=StringValue(value="Region"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="widget_name"),
                              display_name=StringValue(value="Metric Type"),
                              description=StringValue(value="Select a metric to view"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.DROPDOWN_FT,
                              valid_values=cloud_run_metric_literals),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval(Seconds)"),
                              description=StringValue(value='(Optional)Enter Interval'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            }
        }

    def get_connector_processor(self, gcm_connector, **kwargs):
        generated_credentials = generate_credentials_dict(gcm_connector.type, gcm_connector.keys)
        return GcmApiProcessor(**generated_credentials)

    def execute_mql_execution(self, time_range: TimeRange, gcm_task: Gcm,
                              gcm_connector: ConnectorProto):
        try:
            if not gcm_connector:
                raise Exception("Task execution Failed:: No GCM source found")

            project_id = get_project_id(gcm_connector)
            gcm_api_processor = self.get_connector_processor(gcm_connector)

            mql_task = gcm_task.mql_execution
            mql = mql_task.query.value.strip()
            timeseries_offsets = mql_task.timeseries_offsets

            if "| within " in mql:
                mql = mql.split("| within ")[0].strip()

            labeled_metric_timeseries = []

            # List of time ranges to process (current + offsets)
            time_ranges_to_process = [time_range]
            if timeseries_offsets:
                offsets = [offset for offset in timeseries_offsets]
                for offset in offsets:
                    time_ranges_to_process.append(TimeRange(
                        time_geq=time_range.time_geq - offset,
                        time_lt=time_range.time_lt - offset
                    ))

            for idx, tr in enumerate(time_ranges_to_process):
                tr_end_time = tr.time_lt
                end_time = datetime.utcfromtimestamp(tr_end_time).strftime("d'%Y/%m/%d %H:%M'")
                tr_start_time = tr.time_geq
                start_time = datetime.utcfromtimestamp(tr_start_time).strftime("d'%Y/%m/%d %H:%M'")

                query_with_time = f"{mql} | within {start_time}, {end_time}"

                offset = 0 if idx == 0 else time_range.time_geq - tr.time_geq

                print(
                    f"Playbook Task Downstream Request: Type -> RUN_MQL_QUERY, Account -> {gcm_connector.account_id.value}, "
                    f"Project -> {project_id}, Query -> {query_with_time}, Start_Time -> {start_time}, End_Time -> {end_time}, "
                    f"Offset -> {offset}",
                    flush=True
                )

                response = gcm_api_processor.execute_mql(query_with_time, project_id)

                if not response:
                    print(f"No data returned from GCM for offset {offset} seconds")
                    continue

                metric_datapoints = []
                for item in response:
                    for point in item['pointData']:
                        utc_timestamp = point['timeInterval']['endTime'].rstrip('Z')
                        utc_datetime = datetime.fromisoformat(utc_timestamp)
                        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                        val = point['values'][0]['doubleValue']
                        datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                        metric_datapoints.append(datapoint)

                labeled_metric_timeseries.append(TimeseriesResult.LabeledMetricTimeseries(
                    metric_label_values=[
                        LabelValuePair(name=StringValue(value='query'), value=StringValue(value=mql)),
                        LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value=str(offset)))
                    ],
                    datapoints=metric_datapoints
                ))

            timeseries_result = TimeseriesResult(
                metric_name=StringValue(value=mql),
                metric_expression=StringValue(value=project_id),
                labeled_metric_timeseries=labeled_metric_timeseries
            )

            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source
            )
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing GCM task: {e}")

    def execute_filter_log_events(self, time_range: TimeRange, gcm_task: Gcm,
                                  gcm_connector: ConnectorProto):
        try:
            if not gcm_connector:
                raise Exception("Task execution Failed:: No GCM source found")

            log_task = gcm_task.filter_log_events
            filter_query = log_task.filter_query.value
            filter_query = filter_query.strip()
            order_by = log_task.order_by.value if log_task.order_by else "timestamp desc"
            page_size = log_task.page_size.value if log_task.page_size else 2000
            page_token = log_task.page_token.value if log_task.page_token else None
            resource_names = [r.value for r in log_task.resource_names] if log_task.resource_names else None

            timestamp_gte_match = re.search(r'timestamp\s*>=\s*"([^"]+)"', filter_query)
            timestamp_gt_match = re.search(r'timestamp\s*>\s*"([^"]+)"', filter_query)
            if timestamp_gte_match:
                start_time = datetime.strptime(timestamp_gte_match.group(1), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=timezone.utc)
                filter_query = re.sub(r'timestamp\s*>=\s*"[^"]+"', '', filter_query).strip()
            elif timestamp_gt_match:
                start_time = datetime.strptime(timestamp_gt_match.group(1), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=timezone.utc)
                filter_query = re.sub(r'timestamp\s*>=\s*"[^"]+"', '', filter_query).strip()
            else:
                start_time = datetime.utcfromtimestamp(time_range.time_geq).replace(tzinfo=timezone.utc)

            timestamp_lte_match = re.search(r'timestamp\s*<=\s*"([^"]+)"', filter_query)
            timestamp_lt_match = re.search(r'timestamp\s*<\s*"([^"]+)"', filter_query)
            if timestamp_lte_match:
                end_time = datetime.strptime(timestamp_lte_match.group(1), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=timezone.utc)
                filter_query = re.sub(r'timestamp\s*<=\s*"[^"]+"', '', filter_query).strip()
            elif timestamp_lt_match:
                end_time = datetime.strptime(timestamp_lt_match.group(1), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=timezone.utc)
                filter_query = re.sub(r'timestamp\s*<\s*"[^"]+"', '', filter_query).strip()
            else:
                end_time = datetime.utcfromtimestamp(time_range.time_lt).replace(tzinfo=timezone.utc)

            time_filter = f'timestamp >= "{start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}" AND timestamp <= "{end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}"'
            if filter_query:
                filter_query = f'({filter_query}) AND {time_filter}'
            else:
                filter_query = time_filter

            logs_api_processor = self.get_connector_processor(gcm_connector)

            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Query -> "
                "{}, Start_Time -> {}, End_Time -> {}".format("GCM_Logs", gcm_connector.account_id.value,
                                                              filter_query, start_time, end_time))

            response = logs_api_processor.fetch_logs(filter_query, order_by=order_by, page_size=page_size,
                                                     page_token=page_token, resource_names=resource_names)
            if not response:
                logger.error("No data returned from GCM Logs")
                raise Exception("No data returned from GCM Logs")

            table_rows = []
            for item in response:
                json_payload = item.get('jsonPayload', {})
                message = json_payload.get('message', '')
                if message == "failed to acquire lease gke-managed-filestorecsi/filestore-csi-storage-gke-io-node":
                    logger.error("Error: Failed to acquire lease for GKE-managed Filestore CSI.")
                    continue
                table_columns = []
                for key, value in item.items():
                    table_column = TableResult.TableColumn(name=StringValue(value=key),
                                                           value=StringValue(value=str(value)))
                    table_columns.append(table_column)
                table_row = TableResult.TableRow(columns=table_columns)
                table_rows.append(table_row)

            result = TableResult(
                raw_query=StringValue(value=filter_query),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            task_result = PlaybookTaskResult(type=PlaybookTaskResultType.TABLE, table=result, source=self.source)
            return task_result
        except Exception as e:
            logger.error(f"Error while executing GCM task: {e}")
            raise Exception(f"Error while executing GCM task: {e}")
    
    def execute_dashboard_view(self, time_range: TimeRange, gcm_task: Gcm,
                               gcm_connector: ConnectorProto):
        try:
            if not gcm_connector:
                raise Exception("Task execution Failed:: No GCM source found")

            project_id = get_project_id(gcm_connector)
            gcm_api_processor = self.get_connector_processor(gcm_connector)

            dashboard_task = gcm_task.dashboard_view
            dashboard_id = dashboard_task.dashboard_id.value
            widget_name = dashboard_task.widget_name.value if dashboard_task.widget_name else None
            interval = dashboard_task.interval.value if dashboard_task.interval else None
            if not widget_name:
                # If no widget name is provided, just return the dashboard URL
                start_time = datetime.utcfromtimestamp(time_range.time_geq).strftime("%Y-%m-%dT%H:%M:%SZ")
                end_time = datetime.utcfromtimestamp(time_range.time_lt).strftime("%Y-%m-%dT%H:%M:%SZ")

                dashboard_url = f"https://console.cloud.google.com/monitoring/dashboards/{dashboard_id}"
                dashboard_url += f"?project={project_id}&timeRange=custom:{start_time}:{end_time}"

                message = f"GCM Dashboard\n"
                message += f"Project: {project_id}\n"
                message += f"Dashboard URL: {dashboard_url}\n"

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=message)),
                    source=self.source
                )

            print(
                f"Playbook Task Downstream Request: Type -> VIEW_DASHBOARD_WIDGET, Account -> {gcm_connector.account_id.value}, "
                f"Project -> {project_id}, Dashboard ID -> {dashboard_id}, Widget name -> {widget_name}",
                flush=True
            )

            widget_info = gcm_api_processor.fetch_dashboard_widget_by_name(dashboard_id, widget_name)

            query = widget_info['query']
            if 'timeSeriesFilter' in query:
                # This is a metric filter query, convert it to MQL
                filter_str = query.get('timeSeriesFilter', {}).get('filter', '')

                metric_type = None
                if 'metric.type=' in filter_str:
                    metric_type = filter_str.split('metric.type=')[1].split(' ')[0].strip('"')

                if metric_type:
                    mql_query = f'fetch {metric_type}'

                    start_time = datetime.utcfromtimestamp(time_range.time_geq).strftime("%Y/%m/%d %H:%M")
                    end_time = datetime.utcfromtimestamp(time_range.time_lt).strftime("%Y/%m/%d %H:%M")

                    mql_query += f" | within d'{start_time}', d'{end_time}'"

                    response = gcm_api_processor.execute_mql(mql_query, project_id, interval)

                    if response:
                        labeled_metric_timeseries = []
                        metric_datapoints = []

                        print(f"MQL Response structure: {response[0].keys() if response else 'Empty'}", flush=True)

                        for item in response:
                            if 'pointData' not in item:
                                continue

                            for point in item.get('pointData', []):
                                try:
                                    if 'timeInterval' not in point or 'endTime' not in point['timeInterval']:
                                        continue

                                    utc_timestamp = point['timeInterval']['endTime'].rstrip('Z')
                                    utc_datetime = datetime.fromisoformat(utc_timestamp)
                                    utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)

                                    if 'values' not in point or not point['values']:
                                        continue

                                    value_obj = point['values'][0]

                                    # Check what type of value is present
                                    if 'doubleValue' in value_obj:
                                        val = value_obj['doubleValue']
                                    elif 'int64Value' in value_obj:
                                        val = float(value_obj['int64Value'])
                                    elif 'distributionValue' in value_obj:
                                        # Handle distribution values - use mean if available
                                        val = value_obj.get('distributionValue', {}).get('mean', 0.0)
                                    else:
                                        # Log what we found instead
                                        print(f"Unknown value type in point: {value_obj.keys()}", flush=True)
                                        continue

                                    datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                        timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                                    metric_datapoints.append(datapoint)
                                except Exception as point_error:
                                    print(f"Error processing datapoint: {point_error}", flush=True)
                                    continue

                        if metric_datapoints:
                            labeled_metric_timeseries.append(TimeseriesResult.LabeledMetricTimeseries(
                                metric_label_values=[
                                    LabelValuePair(name=StringValue(value='widget'),
                                                   value=StringValue(value=widget_info['widget_title'])),
                                    LabelValuePair(name=StringValue(value='metric'),
                                                   value=StringValue(value=metric_type))
                                ],
                                datapoints=metric_datapoints
                            ))

                            timeseries_result = TimeseriesResult(
                                metric_name=StringValue(value=widget_info['widget_title']),
                                metric_expression=StringValue(value=mql_query),
                                labeled_metric_timeseries=labeled_metric_timeseries
                            )

                            return PlaybookTaskResult(
                                type=PlaybookTaskResultType.TIMESERIES,
                                timeseries=timeseries_result,
                                source=self.source
                            )
                    else:
                        print(f"No data returned from MQL query: {mql_query}", flush=True)

            message = f"Unable to extract executable query from widget {widget_name} in dashboard {dashboard_id}.\n"
            message += f"Widget title: {widget_info['widget_title']}\n"
            message += f"Query details: {widget_info['query']}"

            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT,
                text=TextResult(output=StringValue(value=message)),
                source=self.source
            )
        except Exception as e:
            logger.error(f"Error while executing GCM dashboard task: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error while executing GCM dashboard task: {e}")

    def execute_sheets_data_fetch(self, time_range: TimeRange, gcm_task: Gcm,
                                  gcm_connector: ConnectorProto):
        """
        Execute a Google Sheets data fetch task and return the results.

        Args:
            time_range: The time range for the task (not used for Sheets)
            gcm_task: The task configuration
            gcm_connector: The GCM connector to use

        Returns:
            PlaybookTaskResult: The result of the task execution
        """
        try:
            if not gcm_connector:
                raise Exception("Task execution Failed:: No GCM source found")

            project_id = get_project_id(gcm_connector)
            gcm_api_processor = self.get_connector_processor(gcm_connector)

            sheets_task = gcm_task.sheets_data_fetch
            spreadsheet_name = sheets_task.spreadsheet_name.value
            sheet_name = sheets_task.sheet_name.value
            max_rows = sheets_task.max_rows.value if sheets_task.max_rows else 500
            output_format = sheets_task.output_format.value if sheets_task.output_format else "JSON"

            print(
                f"Playbook Task Downstream Request: Type -> SHEETS_DATA_FETCH, Account -> {gcm_connector.account_id.value}, "
                f"Project -> {project_id}, Spreadsheet Name -> {spreadsheet_name}, Sheet Name -> {sheet_name}, "
                f"Max Rows -> {max_rows}",
                flush=True
            )

            # Find the spreadsheet by name
            spreadsheet = gcm_api_processor.find_spreadsheet_by_name(spreadsheet_name)
            if not spreadsheet:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"No spreadsheet found with name: {spreadsheet_name}"
                    )),
                    source=self.source
                )

            spreadsheet_id = spreadsheet['id']

            # Fetch the spreadsheet data, limiting to max_rows
            values = gcm_api_processor.fetch_spreadsheet_values(spreadsheet_id, sheet_name, max_rows)

            if not values:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"No data found in spreadsheet '{spreadsheet_name}' in sheet '{sheet_name}'"
                    )),
                    source=self.source
                )

            # Handle the case where we want to include headers
            headers = []
            data_rows = values
            headers = values[0]
            data_rows = values[1:]

            # Randomize the order of data rows
            random.shuffle(data_rows)

            # Always return in JSON format by default
            if output_format == "JSON" or not output_format:
                # Format as JSON output
                json_rows = []
                for row in data_rows:
                    row_dict = {}
                    for i, cell in enumerate(row):
                        # Make sure we don't go out of bounds with headers
                        if i < len(headers):
                            header_name = headers[i]
                            row_dict[header_name] = cell
                    json_rows.append(row_dict)

                import json
                json_output = json.dumps(json_rows, indent=2)

                metadata = {
                    "spreadsheet_name": spreadsheet_name,
                    "sheet_name": sheet_name,
                    "total_rows": len(data_rows),
                    "row_limit": max_rows,
                    "truncated": len(data_rows) >= max_rows
                }

                result_text = (
                    f"Metadata: {json.dumps(metadata, indent=2)}\n\n"
                    f"Data: {json_output}"
                )

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=result_text)),
                    source=self.source
                )

            # Support other formats as alternative options
            elif output_format == "TABLE":
                # Convert to table result
                table_rows = []
                for row in data_rows:
                    table_columns = []
                    for i, cell in enumerate(row):
                        # Make sure we don't go out of bounds with headers
                        header_name = headers[i] if i < len(headers) else f"Column{i + 1}"
                        table_column = TableResult.TableColumn(
                            name=StringValue(value=header_name),
                            value=StringValue(value=str(cell))
                        )
                        table_columns.append(table_column)
                    table_row = TableResult.TableRow(columns=table_columns)
                    table_rows.append(table_row)

                result = TableResult(
                    raw_query=StringValue(
                        value=f"Spreadsheet: {spreadsheet_name}, Sheet: {sheet_name}, Rows: {len(data_rows)}"),
                    rows=table_rows,
                    total_count=UInt64Value(value=len(table_rows)),
                )

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TABLE,
                    table=result,
                    source=self.source
                )

            elif output_format == "CSV":
                # Format as CSV output
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)

                writer.writerow(headers)

                for row in data_rows:
                    writer.writerow(row)

                csv_content = output.getvalue()

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=csv_content)),
                    source=self.source
                )

            # Default fallback to ensure we always return a PlaybookTaskResult
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT,
                text=TextResult(output=StringValue(
                    value=f"Data retrieved from {spreadsheet_name}, but could not format with output_format={output_format}"
                )),
                source=self.source
            )

        except Exception as e:
            logger.error(f"Error while executing Google Sheets task: {e}")
            import traceback
            traceback.print_exc()
            # Return an error result rather than raising an exception
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT,
                text=TextResult(output=StringValue(
                    value=f"Error while executing Google Sheets task: {str(e)}"
                )),
                source=self.source
            )

    def execute_cloud_run_service_dashboard(self, time_range: TimeRange, gcm_task: Gcm,
                                            gcm_connector: ConnectorProto):
        try:
            if not gcm_connector:
                raise Exception("Task execution Failed:: No GCM source found")

            project_id = get_project_id(gcm_connector)

            try:
                gcm_api_processor = self.get_connector_processor(gcm_connector)
            except Exception as auth_error:
                error_message = (
                    f"Authentication error accessing Google Cloud Run: {str(auth_error)}\n\n"
                    f"Please verify your service account has the correct permissions:\n"
                    f"1. Ensure the service account has the 'Cloud Run Admin' role\n"
                    f"2. Ensure the service account has the 'Monitoring Viewer' role\n"
                    f"3. Verify the service account key is valid and not expired"
                )
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=error_message)),
                    source=self.source
                )

            cloud_run_task = gcm_task.cloud_run_service_dashboard
            service_name = cloud_run_task.service_name.value
            region = cloud_run_task.region.value
            widget_name = cloud_run_task.widget_name.value if cloud_run_task.widget_name else None

            # Convert time range to datetime objects
            start_time = datetime.utcfromtimestamp(time_range.time_geq)
            end_time = datetime.utcfromtimestamp(time_range.time_lt)

            # If no widget name provided, show available metrics
            if not widget_name:
                cloud_run_url = f"https://console.cloud.google.com/run/detail/{region}/{service_name}/metrics?project={project_id}"

                message = f"Cloud Run Service: '{service_name}' in region '{region}'\n\n"
                message += "Available metrics:\n"
                for i, metric_name in enumerate(GCM_SERVICE_DASHBOARD_QUERIES.keys(), 1):
                    message += f"{i}. {metric_name}\n"
                message += f"\nCloud Run console URL: {cloud_run_url}"

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=message)),
                    source=self.source
                )

            # Get metric info from the mapping
            if widget_name not in GCM_SERVICE_DASHBOARD_QUERIES:
                # Try case-insensitive matching
                for display_name in GCM_SERVICE_DASHBOARD_QUERIES.keys():
                    if display_name.lower() == widget_name.lower():
                        widget_name = display_name  # Use the proper case for display
                        break

                # If still not found, return an error
                if widget_name not in GCM_SERVICE_DASHBOARD_QUERIES:
                    available_metrics = "\n".join([f"- {name}" for name in GCM_SERVICE_DASHBOARD_QUERIES.keys()])
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(
                            value=f"Unknown metric type '{widget_name}'. Available metrics are:\n{available_metrics}"
                        )),
                        source=self.source
                    )

            aggregations = list(GCM_SERVICE_DASHBOARD_QUERIES[widget_name].keys())

            print(
                f"Fetching Cloud Run metric: {widget_name} with aggregations {aggregations} for service {service_name} in {region}",
                flush=True)

            total_seconds = int((end_time - start_time).total_seconds())
            bucket_size_seconds = calculate_timeseries_bucket_size(total_seconds)
            bucket_size_minutes = bucket_size_seconds // 60  # Convert to minutes for MQL

            print(
                f"Time range: {total_seconds} seconds, using bucket size: {bucket_size_seconds} seconds ({bucket_size_minutes} minutes)",
                flush=True)

            # Format times for MQL
            start_str = start_time.strftime("%Y/%m/%d %H:%M")
            end_str = end_time.strftime("%Y/%m/%d %H:%M")

            # Get data for each aggregation
            response_data = {}

            for agg in aggregations:
                try:
                    # Get the base query from our static mapping
                    base_query = GCM_SERVICE_DASHBOARD_QUERIES[widget_name][agg]

                    # Adjust the time interval in the query based on calculated bucket size
                    query = re.sub(r'align delta\(1m\)', f'align delta({bucket_size_minutes}m)', base_query)
                    query = re.sub(r'align rate\(1m\)', f'align rate({bucket_size_minutes}m)', query)
                    query = re.sub(r'every 1m', f'every {bucket_size_minutes}m', query)
                    query = re.sub(r'group_by 1m,', f'group_by {bucket_size_minutes}m,', query)

                    # Replace service name and region in the query
                    query = query.replace(
                        "filter resource.service_name",
                        f"filter resource.service_name = \"{service_name}\" | filter resource.location = \"{region}\" | "
                        if "filter resource.service_name" not in query else f"filter resource.service_name = \"{service_name}\""
                    )

                    if "filter resource.location" not in query:
                        query = query.replace(
                            "filter resource.service_name = \"" + service_name + "\"",
                            f"filter resource.service_name = \"{service_name}\" | filter resource.location = \"{region}\""
                        )

                    # Add time range
                    if "within" not in query:
                        query += f" | within d'{start_str}', d'{end_str}'"

                    print(f"Executing MQL query for {agg}: {query}", flush=True)

                    try:
                        response = gcm_api_processor.execute_mql(query, project_id)

                        if response and len(response) > 0:
                            print(f"Found data for {agg} with query", flush=True)
                            response_data[agg] = response
                        else:
                            print(f"No data returned for {agg} with query", flush=True)
                    except Exception as e:
                        print(f"Error executing query for {agg}: {str(e)}", flush=True)

                        # Try fallback to simple query if needed
                        if agg not in response_data:
                            # Try to extract the metric type from the query
                            metric_match = re.search(r"metric '([^']+)'", query)
                            metric_type = metric_match.group(1) if metric_match else ""

                            if metric_type:
                                simple_query = (f'fetch cloud_run_revision::' +
                                                f'{metric_type} | filter service_name = "{service_name}" | ' +
                                                f'filter location = "{region}" | within d\'{start_str}\', d\'{end_str}\'')

                                print(f"Trying simple fallback query for {agg}: {simple_query}", flush=True)
                                try:
                                    response = gcm_api_processor.execute_mql(simple_query, project_id)

                                    if response and len(response) > 0:
                                        print(f"Found data for {agg} with simple fallback query", flush=True)
                                        response_data[agg] = response
                                except Exception as simple_e:
                                    print(f"Error with simple fallback query for {agg}: {str(simple_e)}", flush=True)

                except Exception as e:
                    print(f"Error processing aggregation '{agg}': {e}", flush=True)

            if not response_data:
                console_url = f"https://console.cloud.google.com/run/detail/{region}/{service_name}/metrics?project={project_id}"

                error_message = f"No data found for metric '{widget_name}' from Cloud Run service '{service_name}' in '{region}'.\n\n"
                error_message += "This could be because:\n"
                error_message += "1. The service doesn't exist\n"
                error_message += "2. The service exists but has no activity for this metric\n"
                error_message += "3. You may not have sufficient permissions\n\n"
                error_message += f"Verify the service in the Cloud Run console: {console_url}"

                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=error_message)),
                    source=self.source
                )

            # Process all aggregations into a single timeseries result
            labeled_metric_timeseries = []

            print(f"Processing response data with {len(response_data)} aggregations", flush=True)
            data_point_count = 0

            for agg, response in response_data.items():
                for item_index, item in enumerate(response):
                    # Extract labels
                    labels = {}
                    if 'labels' in item:
                        labels = item.get('labels', {})

                    # Create a descriptive name for this data series
                    if agg in ["50", "95", "99"]:
                        series_name = f"{widget_name} ({agg}th percentile)"
                    elif agg == "sum":
                        series_name = f"{widget_name} (sum)"
                    elif agg == "rate":
                        series_name = f"{widget_name} (rate)"
                    elif agg == "max":
                        series_name = f"{widget_name} (max)"
                    else:
                        series_name = widget_name

                    # Process data points
                    datapoints = []

                    for point in item.get('pointData', []):
                        try:
                            # Extract timestamp
                            if 'timeInterval' not in point or 'endTime' not in point['timeInterval']:
                                continue

                            utc_timestamp = point['timeInterval']['endTime'].rstrip('Z')
                            utc_datetime = datetime.fromisoformat(utc_timestamp)
                            utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)

                            # Extract value
                            if 'values' not in point or not point['values']:
                                continue

                            value_obj = point['values'][0]
                            val = None

                            if 'doubleValue' in value_obj:
                                val = value_obj['doubleValue']
                            elif 'int64Value' in value_obj:
                                val = float(value_obj['int64Value'])
                            elif 'distributionValue' in value_obj:
                                # Handle distribution values - use mean if available
                                distribution = value_obj.get('distributionValue', {})
                                if 'mean' in distribution:
                                    val = distribution['mean']
                            else:
                                continue

                            if val is None:
                                continue

                            # Create datapoint
                            datapoints.append(TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                timestamp=int(utc_datetime.timestamp() * 1000),
                                value=DoubleValue(value=val)
                            ))
                            data_point_count += 1

                        except Exception as e:
                            print(f"Error processing datapoint: {e}", flush=True)
                            continue

                    if datapoints:
                        labeled_metric_timeseries.append(TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='service'),
                                               value=StringValue(value=service_name)),
                                LabelValuePair(name=StringValue(value='region'),
                                               value=StringValue(value=region)),
                                LabelValuePair(name=StringValue(value='aggregation'),
                                               value=StringValue(value=agg)),
                                LabelValuePair(name=StringValue(value='series'),
                                               value=StringValue(value=series_name))
                            ],
                            datapoints=datapoints
                        ))

            print(
                f"Created {len(labeled_metric_timeseries)} labeled metric timeseries with {data_point_count} total data points",
                flush=True)

            if not labeled_metric_timeseries:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(
                        value=f"Retrieved data for '{widget_name}' but couldn't process it into a timeseries chart."
                    )),
                    source=self.source
                )

            # Create timeseries result
            timeseries_result = TimeseriesResult(
                metric_name=StringValue(value=widget_name),
                metric_expression=StringValue(value=f"Cloud Run Service: {service_name}"),
                labeled_metric_timeseries=labeled_metric_timeseries
            )

            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source
            )

        except Exception as e:
            logger.error(f"Error executing Cloud Run service dashboard task: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error executing Cloud Run service dashboard task: {e}")

