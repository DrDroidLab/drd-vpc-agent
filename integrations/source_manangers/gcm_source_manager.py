from datetime import datetime, timezone

import logging
import re

import pytz
from google.protobuf.wrappers_pb2 import StringValue, DoubleValue, UInt64Value, Int64Value

from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import TimeseriesResult, LabelValuePair, PlaybookTaskResult, \
    PlaybookTaskResultType, TableResult
from protos.playbooks.source_task_definitions.gcm_task_pb2 import Gcm
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict

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
