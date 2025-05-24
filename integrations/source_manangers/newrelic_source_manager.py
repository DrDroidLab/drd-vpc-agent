import re
import logging
from datetime import datetime
from typing import Optional

import pytz
from google.protobuf.wrappers_pb2 import DoubleValue, StringValue

from integrations.source_api_processors.new_relic_graph_ql_processor import NewRelicGraphQlConnector
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, TimeseriesResult, LabelValuePair, \
    PlaybookTaskResultType, TextResult
from protos.playbooks.source_task_definitions.new_relic_task_pb2 import NewRelic
from protos.ui_definition_pb2 import FormField, FormFieldType
from protos.assets.asset_pb2 import AccountConnectorAssets, AccountConnectorAssetsModelFilters

from utils.credentilal_utils import generate_credentials_dict
from utils.string_utils import is_partial_match
from utils.playbooks_client import PrototypeClient
from utils.time_utils import calculate_timeseries_bucket_size
from utils.proto_utils import dict_to_proto, proto_to_dict
from utils.static_mappings import NEWRELIC_APM_QUERIES

logger = logging.getLogger(__name__)


def get_nrql_expression_result_alias(nrql_expression):
    pattern = r'AS\s+\'(.*?)\'|AS\s+(\w+)'
    match = re.search(pattern, nrql_expression, re.IGNORECASE)
    if match:
        return match.group(1) or match.group(2)
    return 'result'


class NewRelicSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.NEW_RELIC
        self.task_proto = NewRelic
        self.task_type_callable_map = {
            NewRelic.TaskType.ENTITY_APPLICATION_GOLDEN_METRIC_EXECUTION: {
                'executor': self.execute_entity_application_golden_metric_execution,
                'model_types': [SourceModelType.NEW_RELIC_ENTITY_APPLICATION],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a New Relic golden metric',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="application_entity_name"),
                              display_name=StringValue(value="Application"),
                              description=StringValue(value="Select Application"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="golden_metric_name"),
                              display_name=StringValue(value="Metric"),
                              description=StringValue(value="Select Metric"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="golden_metric_unit"),
                              display_name=StringValue(value="Unit"),
                              description=StringValue(value="Enter Unit"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="golden_metric_nrql_expression"),
                              display_name=StringValue(value="Selected Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
            NewRelic.TaskType.ENTITY_APPLICATION_APM_METRIC_EXECUTION: {
                'executor': self.execute_entity_application_apm_metric_execution,
                'model_types': [SourceModelType.NEW_RELIC_ENTITY_APPLICATION],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a New Relic APM metric',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="application_entity_name"),
                              display_name=StringValue(value="Application"),
                              description=StringValue(value="Select Application"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT,
                              valid_values=[]),
                    FormField(key_name=StringValue(value="apm_metric_names"),
                              display_name=StringValue(value="APM Metric Names (Optional)"),
                              description=StringValue(value="Comma-separated list of metric names to fetch (leave blank for all)"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
            NewRelic.TaskType.ENTITY_DASHBOARD_WIDGET_NRQL_METRIC_EXECUTION: {
                'executor': self.execute_entity_dashboard_widget_nrql_metric_execution,
                'model_types': [SourceModelType.NEW_RELIC_ENTITY_DASHBOARD],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a metric from New Relic dashboard',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="dashboard_guid"),
                              display_name=StringValue(value="Dashboard"),
                              description=StringValue(value="Select Dashboard"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="page_guid"),
                              display_name=StringValue(value="Page"),
                              description=StringValue(value="Select Page"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="widget_title"),
                              display_name=StringValue(value="Widget Title"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="widget_nrql_expression"),
                              display_name=StringValue(value="Selected Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
            NewRelic.TaskType.NRQL_METRIC_EXECUTION: {
                'executor': self.execute_nrql_metric_execution,
                'model_types': [],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch a custom NRQL query',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="metric_name"),
                              display_name=StringValue(value="Metric Name"),
                              description=StringValue(value="Enter Metric Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="unit"),
                              display_name=StringValue(value="Unit"),
                              description=StringValue(value="Enter Unit"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="nrql_expression"),
                              display_name=StringValue(value="Selected Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
            NewRelic.TaskType.FETCH_DASHBOARD_WIDGETS: {
                'executor': self.execute_fetch_dashboard_widgets,
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Fetch all widgets from a New Relic dashboard',
                'category': 'Metrics',
                'form_fields': [
                    FormField(key_name=StringValue(value="dashboard_name"),
                              display_name=StringValue(value="Dashboard Name"),
                              description=StringValue(value="Enter Dashboard Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="page_name"),
                              display_name=StringValue(value="Page Name (Optional)"),
                              description=StringValue(value="Enter Page Name to filter widgets"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                    FormField(key_name=StringValue(value="widget_names"),
                              display_name=StringValue(value="Widget Names (Optional)"),
                              description=StringValue(value="Enter widget names to filter"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            }
        }

    def get_connector_processor(self, grafana_connector, **kwargs):
        generated_credentials = generate_credentials_dict(grafana_connector.type, grafana_connector.keys)
        return NewRelicGraphQlConnector(**generated_credentials)

    def execute_entity_application_golden_metric_execution(self, time_range: TimeRange, nr_task: NewRelic,
                                                           nr_connector: ConnectorProto):
        try:
            if not nr_connector:
                raise Exception("Task execution Failed:: No New Relic source found")

            task = nr_task.entity_application_golden_metric_execution
            name = task.golden_metric_name.value
            unit = task.golden_metric_unit.value
            timeseries_offsets = task.timeseries_offsets

            nrql_expression = task.golden_metric_nrql_expression.value
            if 'timeseries' not in nrql_expression.lower():
                raise Exception("Invalid NRQL expression. TIMESERIES is missing in the NRQL expression")
            if 'limit max timeseries' in nrql_expression.lower():
                nrql_expression = re.sub('limit max timeseries', 'TIMESERIES 5 MINUTE', nrql_expression,
                                         flags=re.IGNORECASE)
            if 'since' not in nrql_expression.lower():
                time_since = time_range.time_geq
                time_until = time_range.time_lt
                total_seconds = (time_until - time_since)
                nrql_expression = nrql_expression + f' SINCE {total_seconds} SECONDS AGO'

            result_alias = get_nrql_expression_result_alias(nrql_expression)
            nr_gql_processor = self.get_connector_processor(nr_connector)

            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Nrql_Expression -> {}".format(
                    "NewRelic", nr_connector.account_id.value, nrql_expression), flush=True)

            response = nr_gql_processor.execute_nrql_query(nrql_expression)
            if not response or 'results' not in response:
                raise Exception("No data returned from New Relic")

            results = response.get('results', [])
            metric_datapoints = []
            for item in results:
                utc_timestamp = item['beginTimeSeconds']
                utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                val = item.get(result_alias)
                datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                    timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                metric_datapoints.append(datapoint)

            metric_label_values = [
                LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value='0'))
            ]
            labeled_metric_timeseries_list = [
                TimeseriesResult.LabeledMetricTimeseries(
                    metric_label_values=metric_label_values, unit=StringValue(value=unit), datapoints=metric_datapoints)
            ]

            # Process offset values if specified
            if timeseries_offsets:
                offsets = [offset for offset in timeseries_offsets]
                for offset in offsets:
                    adjusted_start_time = time_range.time_geq - offset
                    adjusted_end_time = time_range.time_lt - offset
                    total_seconds = adjusted_end_time - adjusted_start_time
                    adjusted_nrql_expression = re.sub(
                        r'SINCE\s+\d+\s+SECONDS\s+AGO', f'SINCE {total_seconds} SECONDS AGO', nrql_expression)

                    print(
                        "Playbook Task Downstream Request: Type -> {}, Account -> {}, Nrql_Expression -> {}, "
                        "Offset -> {}".format(
                            "NewRelic", nr_connector.account_id.value, adjusted_nrql_expression, offset), flush=True)

                    offset_response = nr_gql_processor.execute_nrql_query(adjusted_nrql_expression)
                    if not offset_response or 'results' not in offset_response:
                        print(f"No data returned from New Relic for offset {offset} seconds")
                        continue

                    offset_results = offset_response.get('results', [])
                    offset_metric_datapoints = []
                    for item in offset_results:
                        utc_timestamp = item['beginTimeSeconds']
                        utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                        val = item.get(result_alias)
                        datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                        offset_metric_datapoints.append(datapoint)

                    offset_metric_label_values = [
                        LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value=str(offset)))
                    ]
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=offset_metric_label_values, unit=StringValue(value=unit),
                            datapoints=offset_metric_datapoints)
                    )

            timeseries_result = TimeseriesResult(
                metric_expression=StringValue(value=nrql_expression),
                metric_name=StringValue(value=name),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )
            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source
            )
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing New Relic task: {e}")

    def execute_entity_dashboard_widget_nrql_metric_execution(self, time_range: TimeRange, nr_task: NewRelic,
                                                              nr_connector: ConnectorProto):
        try:
            if not nr_connector:
                raise Exception("Task execution Failed:: No New Relic source found")

            task = nr_task.entity_dashboard_widget_nrql_metric_execution
            metric_name = task.widget_title.value
            if task.unit and task.unit.value:
                unit = task.unit.value
            else:
                unit = ''
            timeseries_offsets = task.timeseries_offsets

            nrql_expression = task.widget_nrql_expression.value
            if 'timeseries' not in nrql_expression.lower():
                raise Exception("Invalid NRQL expression. TIMESERIES is missing in the NRQL expression")
            if 'limit max timeseries' in nrql_expression.lower():
                nrql_expression = re.sub('limit max timeseries', 'TIMESERIES 5 MINUTE', nrql_expression,
                                         flags=re.IGNORECASE)
            if 'since' not in nrql_expression.lower():
                time_since = time_range.time_geq
                time_until = time_range.time_lt
                total_seconds = (time_until - time_since)
                nrql_expression = nrql_expression + f' SINCE {total_seconds} SECONDS AGO'

            nr_gql_processor = self.get_connector_processor(nr_connector)
            response = nr_gql_processor.execute_nrql_query(nrql_expression)
            if not response:
                raise Exception("No data returned from New Relic")

            labeled_metric_timeseries_list = []
            facet_keys = response.get('metadata', {}).get('facets', [])
            results = response.get('rawResponse', {}).get('facets', [response.get('rawResponse')])

            if 'TIMESERIES' in nrql_expression:
                for item in results:
                    metric_label_values = []
                    if 'name' in item:
                        facets = item['name']
                        if isinstance(facets, str):
                            facets = [facets]
                        if len(facets) == len(facet_keys):
                            for idx, f in enumerate(facets):
                                metric_label_values.append(LabelValuePair(name=StringValue(value=facet_keys[idx]),
                                                                          value=StringValue(value=f)))
                    metric_datapoints = []
                    for ts in item['timeSeries']:
                        utc_timestamp = ts['beginTimeSeconds']
                        utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                        val = ts['results'][0].get(next(iter(ts['results'][0])), 0)
                        datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                        metric_datapoints.append(datapoint)
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(metric_label_values=metric_label_values,
                                                                 unit=StringValue(value=unit),
                                                                 datapoints=metric_datapoints))

            # Process offset values if specified
            if timeseries_offsets:
                offsets = [offset for offset in timeseries_offsets]
                for offset in offsets:
                    adjusted_start_time = time_range.time_geq - offset
                    adjusted_end_time = time_range.time_lt - offset
                    total_seconds = adjusted_end_time - adjusted_start_time
                    adjusted_nrql_expression = re.sub(
                        r'SINCE\s+\d+\s+SECONDS\s+AGO', f'SINCE {total_seconds} SECONDS AGO', nrql_expression)

                    print(
                        "Playbook Task Downstream Request: Type -> {}, Account -> {}, Nrql_Expression -> {}, "
                        "Offset -> {}".format(
                            "NewRelic", nr_connector.account_id.value, adjusted_nrql_expression, offset), flush=True)

                    offset_response = nr_gql_processor.execute_nrql_query(adjusted_nrql_expression)
                    if not offset_response:
                        print(f"No data returned from New Relic for offset {offset} seconds")
                        continue

                    facet_keys = offset_response.get('metadata', {}).get('facets', [])
                    results = offset_response.get('rawResponse', {}).get('facets', [offset_response.get('rawResponse')])
                    for item in results:
                        metric_label_values = []
                        if 'name' in item:
                            facets = item['name']
                            if isinstance(facets, str):
                                facets = [facets]
                            if len(facets) == len(facet_keys):
                                for idx, f in enumerate(facets):
                                    metric_label_values.append(LabelValuePair(name=StringValue(value=facet_keys[idx]),
                                                                              value=StringValue(value=f)))
                        metric_datapoints = []
                        for ts in item['timeSeries']:
                            utc_timestamp = ts['beginTimeSeconds']
                            utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                            utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                            val = ts['results'][0].get(next(iter(ts['results'][0])), 0)
                            datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                            metric_datapoints.append(datapoint)
                        labeled_metric_timeseries_list.append(
                            TimeseriesResult.LabeledMetricTimeseries(metric_label_values=metric_label_values,
                                                                     unit=StringValue(value=unit),
                                                                     datapoints=metric_datapoints))

            timeseries_result = TimeseriesResult(
                metric_expression=StringValue(value=nrql_expression),
                metric_name=StringValue(value=metric_name),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )
            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source
            )

            return task_result
        except Exception as e:
            raise Exception(f"Error while executing New Relic task: {e}")

    def execute_nrql_metric_execution(self, time_range: TimeRange, nr_task: NewRelic,
                                      nr_connector: ConnectorProto):
        try:
            if not nr_connector:
                raise Exception("Task execution Failed:: No New Relic source found")

            task = nr_task.nrql_metric_execution
            metric_name = task.metric_name.value
            if task.unit and task.unit.value:
                unit = task.unit.value
            else:
                unit = ''
            timeseries_offsets = task.timeseries_offsets

            nrql_expression = task.nrql_expression.value
            if 'timeseries' not in nrql_expression.lower():
                raise Exception("Invalid NRQL expression. TIMESERIES is missing in the NRQL expression")

            if 'limit max timeseries' in nrql_expression.lower():
                nrql_expression = re.sub('limit max timeseries', 'TIMESERIES 5 MINUTE', nrql_expression,
                                         flags=re.IGNORECASE)
            if 'since' not in nrql_expression.lower():
                time_since = time_range.time_geq
                time_until = time_range.time_lt
                total_seconds = (time_until - time_since)
                nrql_expression = nrql_expression + f' SINCE {total_seconds} SECONDS AGO'

            result_alias = get_nrql_expression_result_alias(nrql_expression)
            nr_gql_processor = self.get_connector_processor(nr_connector)

            print(
                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Nrql_Expression -> {}".format(
                    "NewRelic", nr_connector.account_id.value, nrql_expression), flush=True)

            response = nr_gql_processor.execute_nrql_query(nrql_expression)
            if not response:
                raise Exception("No data returned from New Relic")

            results = response.get('results', [])
            metric_datapoints = []
            for item in results:
                utc_timestamp = item['beginTimeSeconds']
                utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                val = item.get(result_alias)
                datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                    timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                metric_datapoints.append(datapoint)

            metric_label_values = [
                LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value='0'))
            ]
            labeled_metric_timeseries_list = [
                TimeseriesResult.LabeledMetricTimeseries(
                    metric_label_values=metric_label_values, unit=StringValue(value=unit), datapoints=metric_datapoints)
            ]

            # Process offset values if specified
            if timeseries_offsets:
                offsets = [offset for offset in timeseries_offsets]
                for offset in offsets:
                    adjusted_start_time = time_range.time_geq - offset
                    adjusted_end_time = time_range.time_lt - offset
                    total_seconds = adjusted_end_time - adjusted_start_time
                    adjusted_nrql_expression = re.sub(
                        r'SINCE\s+\d+\s+SECONDS\s+AGO', f'SINCE {total_seconds} SECONDS AGO', nrql_expression)

                    print(
                        "Playbook Task Downstream Request: Type -> {}, Account -> {}, Nrql_Expression -> {}, "
                        "Offset -> {}".format(
                            "NewRelic", nr_connector.account_id.value, adjusted_nrql_expression, offset), flush=True)

                    offset_response = nr_gql_processor.execute_nrql_query(adjusted_nrql_expression)
                    if not offset_response:
                        print(f"No data returned from New Relic for offset {offset} seconds")
                        continue

                    offset_results = offset_response.get('results', [])
                    offset_metric_datapoints = []
                    for item in offset_results:
                        utc_timestamp = item['beginTimeSeconds']
                        utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
                        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
                        val = item.get(result_alias)
                        datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=int(utc_datetime.timestamp() * 1000), value=DoubleValue(value=val))
                        offset_metric_datapoints.append(datapoint)

                    offset_metric_label_values = [
                        LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value=str(offset)))
                    ]
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=offset_metric_label_values, unit=StringValue(value=unit),
                            datapoints=offset_metric_datapoints)
                    )

            timeseries_result = TimeseriesResult(
                metric_expression=StringValue(value=nrql_expression),
                metric_name=StringValue(value=metric_name),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )
            task_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                timeseries=timeseries_result,
                source=self.source
            )
            return task_result
        except Exception as e:
            raise Exception(f"Error while executing New Relic task: {e}")
    
    def _find_matching_dashboard_widgets(self, nr_connector: ConnectorProto, dashboard_name: str,
                                         page_name: Optional[str] = None, widget_names: Optional[list[str]] = None) -> \
            list[dict]:
        """Finds a dashboard by name and returns its filtered widgets."""
        prototype_client = PrototypeClient()
        assets: AccountConnectorAssets = prototype_client.get_connector_assets(
            "NEW_RELIC",
            nr_connector.id.value,
            SourceModelType.NEW_RELIC_ENTITY_DASHBOARD,
            proto_to_dict(AccountConnectorAssetsModelFilters())
        )

        if not assets:
            raise Exception(f"No dashboard assets found for the account {nr_connector.account_id.value}")

        matching_widgets = []
        dashboard_found = False

        newrelic_assets = assets.new_relic.assets
        all_dashboard_entities = [newrelic_asset.new_relic_entity_dashboard for newrelic_asset
                                  in newrelic_assets if
                                  newrelic_asset.type == SourceModelType.NEW_RELIC_ENTITY_DASHBOARD]

        for dashboard_entity in all_dashboard_entities:
            current_dashboard_name = dashboard_entity.dashboard_name.value
            match = False

            if page_name:
                target_name = f"{dashboard_name} / {page_name}"
                if current_dashboard_name.lower() == target_name.lower():
                    match = True
            else:
                if current_dashboard_name.lower().startswith(dashboard_name.lower() + " / ") or \
                        current_dashboard_name.lower() == dashboard_name.lower():
                    match = True

            if match:
                dashboard_found = True
                for page in dashboard_entity.pages:
                    # If a specific page name is given, only process that page if names match case-insensitively
                    if page_name and page.page_name.value.lower() != page_name.lower():
                        continue

                    for widget in page.widgets:
                        widget_title = widget.widget_title.value if widget.widget_title.value else f"Widget {widget.widget_id.value}"
                        if widget_names and not is_partial_match(widget_title, widget_names):
                            continue

                        matching_widgets.append({
                            'title': widget_title,
                            'nrql': widget.widget_nrql_expression.value,
                            'type': widget.widget_type.value,
                            'id': widget.widget_id.value
                        })

                # If we were looking for a specific page and found it, stop searching further dashboards.
                if page_name:
                    break

        if not dashboard_found:
            raise Exception(f"Dashboard with name '{dashboard_name}' not found")

        if not matching_widgets:
            filter_msg = ""
            if page_name:
                filter_msg += f" in page '{page_name}'"
            if widget_names:
                filter_msg += f" matching names {widget_names}"
            raise Exception(f"No widgets found{filter_msg} in dashboard '{dashboard_name}'")

        return matching_widgets

    def _prepare_widget_nrql(self, nrql_expression: str, time_range: TimeRange) -> str:
        """
        Prepares the NRQL query string for execution by standardizing
        the TIMESERIES and time range clauses based on the playbook context.

        Args:
            nrql_expression: The original NRQL query from the widget.
            time_range: The TimeRange object specifying the desired start and end times.

        Returns:
            The modified NRQL query string ready for execution.
        """
        nrql_expression = nrql_expression.strip()
        original_nrql = nrql_expression  # Keep a copy for logging

        # 1. Calculate desired time range in milliseconds
        start_ms = time_range.time_geq * 1000
        end_ms = time_range.time_lt * 1000
        total_seconds = time_range.time_lt - time_range.time_geq
        if total_seconds <= 0:
            # Default to 1 hour if range is invalid, recalculate timestamps
            end_ms = int(datetime.now(tz=pytz.UTC).timestamp() * 1000)
            start_ms = end_ms - 3600 * 1000
            total_seconds = 3600
            logger.warning(
                f"Invalid time range provided (start >= end). Defaulting to last 1 hour. Original NRQL: {original_nrql}")

        # 2. Calculate appropriate bucket size
        bucket_size = calculate_timeseries_bucket_size(total_seconds)
        calculated_timeseries_clause = f'TIMESERIES {bucket_size} SECONDS'
        calculated_time_range_clause = f'SINCE {start_ms} UNTIL {end_ms}'

        # 3. Extract and remove COMPARE WITH clause
        compare_with_clause = ''
        compare_with_match = re.search(
            r'(\bCOMPARE\s+WITH\s+(.*?)(?=\b(?:LIMIT|TIMESERIES|FACET|$)))',
            nrql_expression, flags=re.IGNORECASE | re.DOTALL
        )
        if compare_with_match:
            # Extract the full clause including "COMPARE WITH"
            compare_with_clause = ' ' + compare_with_match.group(1).strip()
            # Remove the matched clause from the original expression
            nrql_expression = nrql_expression[:compare_with_match.start(0)] + nrql_expression[compare_with_match.end(0):]
            nrql_expression = nrql_expression.strip()


        # 4. Remove existing time range clauses (SINCE, UNTIL)
        # This regex handles various formats like 'X minutes ago', 'today', 'now', timestamps, etc.
        nrql_expression = re.sub(
            r'\bSINCE\s+(.*?)(?=\b(?:UNTIL|COMPARE|LIMIT|TIMESERIES|FACET|$))',
            '', nrql_expression, flags=re.IGNORECASE | re.DOTALL
        ).strip()
        nrql_expression = re.sub(
            r'\bUNTIL\s+(.*?)(?=\b(?:COMPARE|LIMIT|TIMESERIES|FACET|$))',
            '', nrql_expression, flags=re.IGNORECASE | re.DOTALL
        ).strip()
        # COMPARE WITH removal is handled above by extracting it first

        # 5. Remove/Replace existing TIMESERIES clause (any variation)
        # This regex aims to find 'TIMESERIES' possibly preceded by 'LIMIT MAX'
        # and followed by optional arguments ('MAX', 'AUTO', duration).
        # We replace whatever we find with an empty string first.
        nrql_expression = re.sub(
            r'(?:\bLIMIT\s+MAX\s+)?\bTIMESERIES(?:\s+MAX|\s+AUTO|\s+\d+\s+\w+)?',
            '', nrql_expression, flags=re.IGNORECASE
        ).strip()

        # 6. Append the calculated and extracted clauses in the correct NRQL order
        # Order: SINCE...UNTIL -> COMPARE WITH -> TIMESERIES
        nrql_expression += f' {calculated_time_range_clause}'
        if compare_with_clause:
            nrql_expression += compare_with_clause # Already includes leading space
        nrql_expression += f' {calculated_timeseries_clause}'

        # Clean up potential multiple spaces
        nrql_expression = re.sub(r'\s+', ' ', nrql_expression).strip()


        return nrql_expression

    def _prepare_apm_metric_nrql(self, nrql_expression: str, time_range: TimeRange) -> str:
        """
        Prepares the APM metric NRQL query string for execution by standardizing
        the TIMESERIES and time range clauses based on the playbook context.
        (Adapted from _prepare_widget_nrql)

        Args:
            nrql_expression: The original NRQL query from the APM metric asset.
            time_range: The TimeRange object specifying the desired start and end times.

        Returns:
            The modified NRQL query string ready for execution.
        """
        return self._prepare_widget_nrql(nrql_expression, time_range) # Reuse existing logic for now

    # Refactored _parse_nrql_response
    def _parse_nrql_response(self, response: dict, widget_title: str) -> list[TimeseriesResult.LabeledMetricTimeseries]:
        """Parses the NRQL response and extracts timeseries data, handling COMPARE WITH and facets."""
        all_labeled_metric_timeseries = []
        if isinstance(response, list) and len(response) > 0:
             response_data = response[0]
        elif isinstance(response, dict):
             response_data = response
        else:
             logger.warning(f"Widget '{widget_title}': Unexpected response type: {type(response)}. Response: {response}")
             return []

        if not response_data:
            logger.warning(f"No data returned for widget '{widget_title}'")
            return all_labeled_metric_timeseries

        # --- Structure Detection --- 
        has_comparison = False
        is_faceted = False # Default, check later
        comparison_type = None # To track which structure was found

        # Check 1: results / previousResults structure (based on user example)
        if isinstance(response_data.get('results'), list) and isinstance(response_data.get('previousResults'), list):
            has_comparison = True
            comparison_type = 'results/previousResults'
            logger.debug(f"Widget '{widget_title}': Detected COMPARE WITH structure via results/previousResults keys.")
            # Facet check for this structure might involve checking metadata or if results contain facet keys
            if 'metadata' in response_data and isinstance(response_data['metadata'], dict) and response_data['metadata'].get('facets') is not None:
                 is_faceted = True # Assume standard facet structure applies if metadata indicates it
                 logger.debug(f"Widget '{widget_title}': Detected FACETS via metadata for results/previousResults structure.")
            # Add more specific facet checks if needed for this structure

        # Check 2: current / previous structure (fallback)
        elif 'current' in response_data and 'previous' in response_data:
            has_comparison = True
            comparison_type = 'current/previous'
            logger.debug(f"Widget '{widget_title}': Detected COMPARE WITH structure via current/previous keys.")
             # Facet check for this structure
            current_data_check = response_data.get('current', {})
            previous_data_check = response_data.get('previous', {})
            if isinstance(current_data_check, dict) and current_data_check.get('facets') or \
               isinstance(previous_data_check, dict) and previous_data_check.get('facets'):
                 is_faceted = True
                 logger.debug(f"Widget '{widget_title}': Detected FACETS for current/previous structure.")

        # --- Processing Logic --- 

        if has_comparison:
            current_results = []
            previous_results = []
            current_facets = []
            previous_facets = []

            # --- Data Extraction based on detected type --- 
            if comparison_type == 'results/previousResults':
                 current_results = response_data.get('results', [])
                 previous_results = response_data.get('previousResults', [])
                 if is_faceted:
                      # Need logic to handle facets if they don't follow current/previous pattern
                      logger.warning(f"Widget '{widget_title}': Faceted results/previousResults structure not fully implemented for parsing.")
                      is_faceted = False # Override for now

            elif comparison_type == 'current/previous':
                 current_data = response_data.get('current', {})
                 previous_data = response_data.get('previous', {})
                 if not isinstance(current_data, dict): current_data = {}
                 if not isinstance(previous_data, dict): previous_data = {}
                 
                 if is_faceted:
                     # Look in standard locations ('facets') and raw response locations
                     current_facets = current_data.get('facets', response_data.get('rawResponse', {}).get('facets', []))
                     previous_facets = previous_data.get('facets', response_data.get('compareWith', {}).get('facets', []))
                     if not isinstance(current_facets, list): current_facets = []
                     if not isinstance(previous_facets, list): previous_facets = []
                 else:
                     # Data is usually under timeSeries or results key
                     current_results = current_data.get('timeSeries', current_data.get('results', []))
                     previous_results = previous_data.get('timeSeries', previous_data.get('results', []))

            # Ensure results are lists
            if not isinstance(current_results, list): current_results = []
            if not isinstance(previous_results, list): previous_results = []

            # --- Process Data --- 
            if is_faceted:
                logger.debug(f"Widget '{widget_title}': Processing FACETED COMPARE WITH.")
                processed_facet_names = set()
                if current_facets:
                     logger.debug(f"Widget '{widget_title}': Processing {len(current_facets)} CURRENT facets.")
                     # ... (rest of current facet processing logic remains the same) ...
                     for facet_data in current_facets:
                         facet_name = facet_data.get('name', 'unknown_facet')
                         processed_facet_names.add(facet_name)
                         base_labels = [
                             LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title)),
                             LabelValuePair(name=StringValue(value='comparison_period'), value=StringValue(value='current')),
                             LabelValuePair(name=StringValue(value='facet'), value=StringValue(value=facet_name))
                         ]
                         timeseries = facet_data.get('timeSeries', facet_data.get('results', []))
                         all_labeled_metric_timeseries.extend(self._process_timeseries_section(timeseries, widget_title, base_labels, comparison_type))
                else: logger.debug(f"Widget '{widget_title}': No CURRENT facets found.")
                
                if previous_facets:
                     logger.debug(f"Widget '{widget_title}': Processing {len(previous_facets)} PREVIOUS facets.")
                     # ... (rest of previous facet processing logic remains the same) ...
                     for facet_data in previous_facets:
                         facet_name = facet_data.get('name', 'unknown_facet')
                         if facet_name not in processed_facet_names: logger.warning(f"Widget '{widget_title}': Previous facet '{facet_name}' not found in current period.")
                         base_labels = [
                             LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title)),
                             LabelValuePair(name=StringValue(value='comparison_period'), value=StringValue(value='previous')),
                             LabelValuePair(name=StringValue(value='facet'), value=StringValue(value=facet_name))
                         ]
                         timeseries = facet_data.get('timeSeries', facet_data.get('results', []))
                         all_labeled_metric_timeseries.extend(self._process_timeseries_section(timeseries, widget_title, base_labels, comparison_type))
                else: logger.debug(f"Widget '{widget_title}': No PREVIOUS facets found.")

            else: # Non-faceted comparison
                logger.debug(f"Widget '{widget_title}': Processing NON-FACETED COMPARE WITH ({comparison_type} structure).")
                
                logger.debug(f"Widget '{widget_title}': Processing CURRENT period data ({len(current_results)} points)." )
                current_labels = [
                    LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title)),
                    LabelValuePair(name=StringValue(value='comparison_period'), value=StringValue(value='current'))
                ]
                all_labeled_metric_timeseries.extend(self._process_timeseries_section(current_results, widget_title, current_labels, comparison_type))

                logger.debug(f"Widget '{widget_title}': Processing PREVIOUS period data ({len(previous_results)} points).")
                previous_labels = [
                    LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title)),
                    LabelValuePair(name=StringValue(value='comparison_period'), value=StringValue(value='previous'))
                ]
                all_labeled_metric_timeseries.extend(self._process_timeseries_section(previous_results, widget_title, previous_labels, comparison_type))

        else:
            # --- Handle Standard (Non-Compared) Response --- 
            logger.debug(f"Widget '{widget_title}': Standard response structure detected.")
            direct_results = response_data.get('results', [])
            facet_results = response_data.get('facets', response_data.get('rawResponse', {}).get('facets', [])) # Check top level and rawResponse
            if not isinstance(direct_results, list): direct_results = []
            if not isinstance(facet_results, list): facet_results = []
            comparison_type = None # No comparison

            if facet_results:
                is_faceted = True
                logger.debug(f"Widget '{widget_title}': Processing FACETED standard structure.")
                # ... (rest of standard facet processing logic remains the same) ...
                for facet_data in facet_results:
                     facet_name = facet_data.get('name', 'unknown_facet')
                     base_labels = [
                         LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title)),
                         LabelValuePair(name=StringValue(value='facet'), value=StringValue(value=facet_name))
                     ]
                     timeseries = facet_data.get('timeSeries', facet_data.get('results', []))
                     all_labeled_metric_timeseries.extend(self._process_timeseries_section(timeseries, widget_title, base_labels, comparison_type))

            elif direct_results:
                logger.debug(f"Widget '{widget_title}': Processing NON-FACETED standard structure.")
                base_labels = [LabelValuePair(name=StringValue(value='widget_name'), value=StringValue(value=widget_title))]
                all_labeled_metric_timeseries.extend(self._process_timeseries_section(direct_results, widget_title, base_labels, comparison_type))
            else:
                logger.warning(f"Widget '{widget_title}': No 'results' or 'facets' found in standard response structure.")

        if not all_labeled_metric_timeseries:
            logger.warning(f"Widget '{widget_title}': Failed to parse any timeseries data from the response.")

        return all_labeled_metric_timeseries
    
    def _parse_apm_metric_response(self, response: dict, metric_name: str, unit: str) -> list[TimeseriesResult.LabeledMetricTimeseries]:
        """Parses the NRQL response for an APM metric and extracts timeseries data."""
        labeled_metric_timeseries_list = []
        if not response:
            logger.warning(f"No data returned for APM metric '{metric_name}'")
            return labeled_metric_timeseries_list

        # APM metric responses typically have 'results' or sometimes 'facets' in rawResponse
        direct_results = response.get('results', [])
        facet_results = response.get('rawResponse', {}).get('facets', [])

        results_to_process = []
        is_faceted = False
        if facet_results:
            results_to_process = facet_results
            is_faceted = True
        elif direct_results:
            results_to_process = [{'timeSeries': direct_results, 'name': 'default'}]
        else:
            logger.warning(f"No 'results' or 'facets' found in response for APM metric '{metric_name}'")
            return labeled_metric_timeseries_list

        # Process each series (facet or 'default')
        for series_data in results_to_process:
            metric_datapoints = []
            series_name = series_data.get('name', 'default')

            timeseries_data = series_data.get('timeSeries', [])
            # Handle edge cases where series_data might be the list or a single point
            if not timeseries_data and isinstance(series_data, list):
                timeseries_data = series_data
            elif not timeseries_data and 'beginTimeSeconds' in series_data:
                timeseries_data = [series_data]

            for ts in timeseries_data:
                try:
                    utc_timestamp = ts.get('beginTimeSeconds')
                    if utc_timestamp is None: continue
                    utc_datetime = datetime.utcfromtimestamp(utc_timestamp).replace(tzinfo=pytz.UTC)

                    val = None
                    potential_keys = ['result', 'score', 'count', 'average', 'sum', 'min', 'max', 'median'] # Common aggregates

                    for p_key in potential_keys:
                       if p_key in ts and isinstance(ts[p_key], dict) and 'score' in ts[p_key] and isinstance(ts[p_key]['score'], (int, float)):
                            val = float(ts[p_key]['score'])
                            break
                       elif p_key in ts and isinstance(ts[p_key], (int, float)):
                            val = float(ts[p_key])
                            break

                    # Fallback: iterate through all numeric values if specific keys not found
                    if val is None:
                        for k, v in ts.items():
                            if isinstance(v, (int, float)) and k not in ['beginTimeSeconds', 'endTimeSeconds', 'facet']:
                                val = float(v)
                                break

                    if val is None:
                        logger.warning(
                            f"Could not extract numeric value from datapoint {ts} for APM metric '{metric_name}', series '{series_name}'")
                        continue

                    datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                        timestamp=int(utc_datetime.timestamp() * 1000),
                        value=DoubleValue(value=val))
                    metric_datapoints.append(datapoint)

                except (ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning(
                        f"Error processing datapoint {ts} for APM metric '{metric_name}', series '{series_name}': {str(e)}")
                    continue

            # Create LabeledMetricTimeseries if datapoints found
            if metric_datapoints:
                metric_label_values = [
                    LabelValuePair(name=StringValue(value='apm_metric_name'), value=StringValue(value=metric_name)),
                    LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value='0'))
                ]
                if is_faceted and series_name != 'default':
                    metric_label_values.append(
                        LabelValuePair(name=StringValue(value='facet'), value=StringValue(value=series_name))
                    )

                labeled_metric_timeseries_list.append(
                    TimeseriesResult.LabeledMetricTimeseries(
                        metric_label_values=metric_label_values,
                        unit=StringValue(value=unit),
                        datapoints=metric_datapoints
                    )
                )
            else:
                 logger.warning(f"No valid datapoints found for series '{series_name}' in APM metric '{metric_name}'")


        return labeled_metric_timeseries_list

    def execute_fetch_dashboard_widgets(self, time_range: TimeRange, nr_task: NewRelic,
                                        nr_connector: ConnectorProto):
        try:
            if not nr_connector:
                raise Exception("Task execution Failed:: No New Relic source found")

            task = nr_task.fetch_dashboard_widgets
            dashboard_name = task.dashboard_name.value
            page_name = task.page_name.value if task.HasField('page_name') and task.page_name.value else None
            widget_names_str = task.widget_names.value if task.HasField(
                'widget_names') and task.widget_names.value else ''
            widget_names = [name.strip() for name in widget_names_str.split(',') if name.strip()]

            nr_gql_processor = self.get_connector_processor(nr_connector)
            task_results = []

            try:
                # 1. Find dashboard and filter widgets using V2 function
                matching_widgets = self._find_matching_dashboard_widgets_v2(
                    nr_connector, dashboard_name, page_name, widget_names
                )

                # This handles potential duplicate widgets from multiple matching dashboard entities
                unique_widgets_by_content = {}
                for widget in matching_widgets:
                    # Sort NRQL expressions to ensure consistent ordering
                    sorted_expressions = sorted(widget.get('nrql_expressions', []))
                    content_key = (widget.get('title', ''), tuple(sorted_expressions))

                    # Only keep one widget with the same content
                    if content_key not in unique_widgets_by_content:
                        unique_widgets_by_content[content_key] = widget
                
                # Replace matching_widgets with the deduplicated list
                matching_widgets = list(unique_widgets_by_content.values())
                
            except Exception as e:
                # If dashboard/widgets not found, return a text result with the error
                logger.error(f"Error finding dashboard/widgets: {e}")
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                          text=TextResult(
                                              output=StringValue(value=f'Error finding dashboard/widgets: {e}')),
                                          source=self.source)

            # 2. Process each matching widget
            for widget in matching_widgets:
                all_widget_timeseries = [] # Initialize list to aggregate series for THIS widget
                widget_title = widget.get('title', 'Untitled Widget')
                nrql_expressions = widget.get('nrql_expressions', []) # Get list of NRQLs

                try:
                    if not nrql_expressions:
                        logger.warning(f"NewRelicSourceManager.execute_fetch_dashboard_widgets:: Skipping widget "
                                       f"'{widget_title}' as it has no NRQL queries.")
                        continue

                    # Deduplicate NRQL expressions before execution
                    unique_nrql_expressions = []
                    seen_nrql = set()
                    for nrql in nrql_expressions:
                        if nrql and nrql not in seen_nrql:
                            unique_nrql_expressions.append(nrql)
                            seen_nrql.add(nrql)

                    if not unique_nrql_expressions:
                         logger.warning(f"Skipping widget '{widget_title}' as it has no unique, non-empty NRQL queries after deduplication.")
                         continue

                    # 3. Iterate through each UNIQUE NRQL query for the widget
                    for idx, nrql in enumerate(unique_nrql_expressions):
                        try:
                            prepared_nrql = self._prepare_widget_nrql(nrql, time_range)

                            print(
                                "Playbook Task Downstream Request: Type -> {}, Account -> {}, Dashboard -> {}, Widget -> {}, Query Index -> {}, Nrql_Expression -> {}".format(
                                    "NewRelicDashboardV2", nr_connector.account_id.value, dashboard_name, widget_title, idx, prepared_nrql),
                                flush=True)

                            # 5. Execute NRQL
                            response = nr_gql_processor.execute_nrql_query(prepared_nrql)

                            # 6. Parse Response
                            labeled_metric_timeseries_list = self._parse_nrql_response(response, widget_title)

                            # 7. Add query index label and aggregate to the WIDGET's list
                            print(f"labeled_metric_timeseries_list: {len(labeled_metric_timeseries_list)}")
                            for series in labeled_metric_timeseries_list:
                                updated_labels = list(series.metric_label_values)
                                # Check if 'query_index' already exists (unlikely but safe)
                                existing_qi = next((lbl for lbl in updated_labels if lbl.name.value == 'query_index'), None)
                                if existing_qi:
                                     existing_qi.value.value = str(idx)
                                else:
                                     updated_labels.append(
                                         LabelValuePair(name=StringValue(value='query_index'), value=StringValue(value=str(idx)))
                                     )
                                # Create a new LabeledMetricTimeseries object with the updated labels
                                new_series = TimeseriesResult.LabeledMetricTimeseries(
                                    metric_label_values=updated_labels,
                                    unit=series.unit,  # Reuse unit from original series
                                    datapoints=series.datapoints # Reuse datapoints from original series
                                )
                                all_widget_timeseries.append(new_series) # Append the NEW series

                        except Exception as query_err:
                             logger.error(f"Error processing NRQL query index {idx} for widget '{widget_title}': {str(query_err)}", exc_info=True)
                             continue # Continue to next query

                    # 8. Create ONE Result PER WIDGET if any data was found across its queries
                    if all_widget_timeseries:
                        # Use a representative NRQL for the metric_expression field
                        representative_nrql = self._prepare_widget_nrql(nrql_expressions[0], time_range) if nrql_expressions else "Multiple Queries"

                        timeseries_result = TimeseriesResult(
                                             metric_expression=StringValue(value=representative_nrql),
                                             metric_name=StringValue(value=widget_title),
                                             labeled_metric_timeseries=all_widget_timeseries # Aggregated list for the widget
                                             )
                        task_result = PlaybookTaskResult(type=PlaybookTaskResultType.TIMESERIES,
                                                         timeseries=timeseries_result, source=self.source)
                        task_results.append(task_result) # Append the single result for this widget
                    else:
                        logger.warning(f"No timeseries data could be parsed for any query in widget '{widget_title}'.")

                except Exception as widget_err:
                    logger.error(f"Error processing widget '{widget_title}': {str(widget_err)}", exc_info=True)
                    continue # Continue processing other widgets even if one fails

            # Check if any results were generated across all widgets
            if not task_results:
                logger.warning(f"No data retrieved for any widgets in dashboard '{dashboard_name}'.")
                # Return a text message indicating no data was found for any widget processed.
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                          text=TextResult(output=StringValue(
                                              value=f"No data found for the specified widgets in dashboard '{dashboard_name}'. Check widget configurations and time range.")),
                                          source=self.source)

            # Return the list of task results (one per widget)
            return task_results

        except Exception as e:
            logger.error(f"General Error executing Fetch Dashboard Widgets task: {str(e)}", exc_info=True)
            # Raise a generic error for failures outside the widget processing loop
            raise Exception(f"Error while executing New Relic Fetch Dashboard Widgets task: {e}")

    # V2 version of the widget finder - Applying V1 Filtering Logic
    def _find_matching_dashboard_widgets_v2(self, nr_connector: ConnectorProto, dashboard_name: str,
                                             page_name: Optional[str] = None, widget_names: Optional[list[str]] = None) -> \
                list[dict]:
        """Finds V2 dashboards/widgets using the exact filtering logic from V1."""
        prototype_client = PrototypeClient()
        assets_data: AccountConnectorAssets = prototype_client.get_connector_assets(
            "NEW_RELIC",
            nr_connector.id.value,
            SourceModelType.NEW_RELIC_ENTITY_DASHBOARD_V2, # Fetch V2 model type
            proto_to_dict(AccountConnectorAssetsModelFilters())
        )

        # Check if the primary list or the nested assets are missing/empty
        if not assets_data or not assets_data.new_relic:
            logger.warning(f"No V2 dashboard assets found for the account {nr_connector.account_id.value}")
            # Return empty list instead of raising Exception here, let caller handle no data
            return []

        newrelic_assets = assets_data.new_relic.assets

        # Filter for V2 dashboard assets specifically
        all_dashboard_entities_v2 = [
            asset.new_relic_entity_dashboard_v2
            for asset in newrelic_assets
            if asset.HasField('new_relic_entity_dashboard_v2')
        ]

        if not all_dashboard_entities_v2:
             logger.warning(f"No V2 dashboard entities found in asset list for connector {nr_connector.id.value}")
             return []

        # 1. Group entities by dashboard_guid
        entities_by_guid = {}
        for entity in all_dashboard_entities_v2:
            guid = entity.dashboard_guid.value
            if guid not in entities_by_guid:
                entities_by_guid[guid] = []
            entities_by_guid[guid].append(entity)

        # 2. Find GUIDs matching the input dashboard_name using V1 logic
        matched_guids = set()
        dashboard_found = False
        for guid, entities in entities_by_guid.items():
            for entity in entities: # Check all names associated with this GUID
                current_dashboard_name = entity.dashboard_name.value
                match = False
                if page_name:
                    target_name = f"{dashboard_name} / {page_name}"
                    if current_dashboard_name.lower() == target_name.lower():
                        match = True
                else:
                    if current_dashboard_name.lower().startswith(dashboard_name.lower() + " / ") or \
                            current_dashboard_name.lower() == dashboard_name.lower():
                        match = True
                if match:
                    matched_guids.add(guid)
                    dashboard_found = True
                    # Optimization: If we find a match for this GUID, no need to check other names for the same GUID
                    break

        if not dashboard_found:
            raise Exception(f"Dashboard with name '{dashboard_name}' not found (V2 Check)")

        # 3. Collect unique widgets from matched GUIDs, respecting filters
        unique_widgets_data = {}

        for guid in matched_guids:
            processed_pages_in_guid = set()

            for entity in entities_by_guid[guid]: # Iterate entities for this matched GUID
                for page in entity.pages:
                    page_guid = page.page_guid.value
                    current_page_name = page.page_name.value

                    # Skip if page already processed for this GUID
                    if page_guid in processed_pages_in_guid:
                        continue

                    # Apply page name filter (if provided)
                    if page_name and current_page_name.lower() != page_name.lower():
                        continue

                    # Mark page as processed for this GUID
                    processed_pages_in_guid.add(page_guid)

                    # Process widgets on this unique page
                    for widget in page.widgets:
                        widget_id = widget.widget_id.value
                        widget_title = widget.widget_title.value if widget.widget_title.value else f"Widget_{widget_id}"

                        # Apply widget name filter (if provided)
                        if widget_names and not is_partial_match(widget_title, widget_names):
                            continue

                        # Use tuple key for deduplication across entities within the same GUID
                        widget_key = (guid, page_guid, widget_id)

                        if widget_key not in unique_widgets_data:
                             nrql_expressions = [expr.value for expr in widget.widget_nrql_expressions if expr.value]
                             unique_widgets_data[widget_key] = {
                                 'title': widget_title,
                                 'nrql_expressions': nrql_expressions,
                                 'type': widget.widget_type.value,
                                 'id': widget_id,
                                 'dashboard_guid': guid,
                                 'page_guid': page_guid
                             }
                        # else: Widget already found (possibly from another entity for the same GUID), ignore.

        # 4. Convert collected widgets to list
        matching_widgets = list(unique_widgets_data.values())

        if not matching_widgets:
            # Raise exception if filters resulted in no widgets
            filter_msg = ""
            if page_name: filter_msg += f" in page '{page_name}'"
            if widget_names: filter_msg += f" matching names {widget_names}"
            raise Exception(f"No widgets found{filter_msg} in dashboard '{dashboard_name}' (V2 Check)")

        return matching_widgets

    def _process_timeseries_section(self, section_data, widget_title, labels_to_add, comparison_type):
        """
        Processes a list of timeseries data points (potentially faceted) and extracts metrics.

        Args:
            section_data: The list containing timeseries data.
            widget_title: The title of the widget for labeling.
            labels_to_add: A list of base LabelValuePair protos to add to each generated series.
            comparison_type: Indicates structure ('results/previousResults', 'current/previous', or None).

        Returns:
            A list of TimeseriesResult.LabeledMetricTimeseries protos.
        """
        processed_series_list = []
        metric_datapoints_map = {} # {metric_name: [datapoints]}

        if not section_data:
            return []
        if isinstance(section_data, dict) and ('beginTimeSeconds' in section_data or 'epoch_millis' in section_data):
            timeseries_data = [section_data]
        elif isinstance(section_data, list):
            timeseries_data = section_data
        else:
            logger.warning(f"Widget '{widget_title}': Unexpected data type in _process_timeseries_section: {type(section_data)}.")
            return []

        for ts in timeseries_data:
            try:
                utc_timestamp = ts.get('beginTimeSeconds')
                if utc_timestamp is None:
                    epoch_millis = ts.get('epoch_millis')
                    if epoch_millis is not None:
                        utc_timestamp = epoch_millis / 1000
                    else:
                        continue

                utc_datetime = datetime.utcfromtimestamp(utc_timestamp).replace(tzinfo=pytz.UTC)
                timestamp_ms = int(utc_datetime.timestamp() * 1000)
                extracted_values = {} # {metric_name: value}

                # --- Value Extraction Logic --- 

                # Style 1: results/previousResults structure (metric alias is top-level key in ts)
                if comparison_type == 'results/previousResults':
                     # Iterate keys directly, skipping known metadata
                     ignore_keys = {'beginTimeSeconds', 'endTimeSeconds', 'epoch_millis', 'comparison'}
                     for key, value in ts.items():
                          if key not in ignore_keys:
                               if isinstance(value, (int, float)):
                                    extracted_values[key] = float(value)
                                    # Assume only one metric key besides metadata per ts object
                                    break 
                               elif value is None:
                                    # Handle null metric values gracefully (skip this timestamp for this metric)
                                    logger.debug(f"Widget '{widget_title}': Skipping null value for metric '{key}' at timestamp {timestamp_ms}")
                                    continue 
                               # Add handling for complex types like percentiles if needed here

                # Style 2: current/previous structure (Apdex, nested results)
                # Also used as fallback for standard non-compared results
                else: 
                     results_list = ts.get('results', [])
                     if isinstance(results_list, list) and len(results_list) > 0:
                         result_item = results_list[0]
                         if isinstance(result_item, dict):
                             found_primary_metric = False
                             # Prioritize Apdex Score
                             if 'score' in result_item and isinstance(result_item['score'], (int, float)):
                                 extracted_values['apdex_score'] = float(result_item['score'])
                                 found_primary_metric = True
                             
                             # If not Apdex, check other aggregates
                             if not found_primary_metric:
                                 potential_metric_keys = ['count', 'average', 'sum', 'min', 'max', 'median', 'result']
                                 for p_key in potential_metric_keys:
                                     if p_key in result_item:
                                         val = result_item[p_key]
                                         if isinstance(val, (int, float)):
                                             extracted_values[p_key] = float(val)
                                             # Consider breaking if only one expected
                                         elif val is None:
                                              logger.debug(f"Widget '{widget_title}': Skipping null value for metric '{p_key}' in nested result at timestamp {timestamp_ms}")

                             # Handle Percentiles 
                             if 'percentiles' in result_item and isinstance(result_item['percentiles'], dict):
                                 for perc_key, perc_val in result_item['percentiles'].items():
                                     if isinstance(perc_val, (int, float)):
                                         try:
                                             metric_key_suffix = str(perc_key).replace('.', '_')
                                             extracted_values[f'percentile_{metric_key_suffix}'] = float(perc_val)
                                         except ValueError:
                                             logger.debug(f"Widget '{widget_title}': Non-numeric percentile key '{perc_key}'")
                                     elif perc_val is None:
                                          logger.debug(f"Widget '{widget_title}': Skipping null value for percentile '{perc_key}' at timestamp {timestamp_ms}")

                     # Fallback: Check top-level keys (if no nested 'results' or empty)
                     elif not extracted_values: 
                         ignore_keys = {'beginTimeSeconds', 'endTimeSeconds', 'epoch_millis', 'name', 'facet', 'results'}
                         for key, item_value in ts.items():
                             if key not in ignore_keys:
                                 if key == 'apdex' and isinstance(item_value, dict) and 'score' in item_value and isinstance(item_value['score'], (int, float)):
                                     if 'apdex_score' not in extracted_values:
                                         extracted_values['apdex_score'] = float(item_value['score'])
                                 elif isinstance(item_value, (int, float)):
                                     if key not in extracted_values:
                                         extracted_values[key] = float(item_value)
                                 elif item_value is None:
                                     logger.debug(f"Widget '{widget_title}': Skipping null top-level value for key '{key}' at timestamp {timestamp_ms}")

                # --- Add extracted datapoints --- 
                if not extracted_values:
                     # Log if a timeslice yields no metrics after trying all methods
                     logger.debug(f"Widget '{widget_title}': No metric values extracted for timestamp {timestamp_ms}. Data: {ts}")

                for metric_name, val in extracted_values.items():
                    datapoint = TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                        timestamp=timestamp_ms,
                        value=DoubleValue(value=val))

                    if metric_name not in metric_datapoints_map:
                        metric_datapoints_map[metric_name] = []
                    metric_datapoints_map[metric_name].append(datapoint)

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning(
                    f"Widget '{widget_title}': Error processing data point within timestamp {ts}: {str(e)}")
                continue

        # --- Create LabeledMetricTimeseries objects --- 
        if not metric_datapoints_map:
            # It's okay if a section has no data, just return empty
            # logger.debug(f"Widget '{widget_title}': No valid datapoints found for any metric in this section.")
            return []

        for metric_name, datapoints in metric_datapoints_map.items():
            if not datapoints: continue

            final_labels = list(labels_to_add)
            final_labels.append(LabelValuePair(name=StringValue(value='metric'), value=StringValue(value=metric_name)))

            processed_series_list.append(
                TimeseriesResult.LabeledMetricTimeseries(
                    metric_label_values=final_labels,
                    unit=StringValue(value=''),
                    datapoints=datapoints
                )
            )

        return processed_series_list
    
    def execute_entity_application_apm_metric_execution(self, time_range: TimeRange, nr_task: NewRelic,
                                                        nr_connector: ConnectorProto):
        try:
            if not nr_connector:
                raise Exception("Task execution Failed:: No New Relic source found")

            task = nr_task.entity_application_apm_metric_execution
            application_name = task.application_entity_name.value
            timeseries_offsets = list(task.timeseries_offsets) # Ensure it's a list
            filter_metric_names_str = task.apm_metric_names.value if task.HasField('apm_metric_names') else ''
            filter_metric_names = [name.strip().lower() for name in filter_metric_names_str.split(',') if name.strip()]

            # 1. Get the specific application asset
            prototype_client = PrototypeClient()
            assets: AccountConnectorAssets = prototype_client.get_connector_assets(
                "NEW_RELIC",
                nr_connector.id.value,
                SourceModelType.NEW_RELIC_ENTITY_APPLICATION,
                proto_to_dict(AccountConnectorAssetsModelFilters())
            )

            if not assets:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                          text=TextResult(output=StringValue(
                                              value=f"Application asset with GUID '{application_name}' not found")),
                                          source=self.source)

            application_asset = None
            for newrelic_asset in assets.new_relic.assets:
                if newrelic_asset.type == SourceModelType.NEW_RELIC_ENTITY_APPLICATION and \
                   newrelic_asset.new_relic_entity_application.application_name.value == application_name:
                    application_asset = newrelic_asset.new_relic_entity_application
                    break

            if not application_asset:
                 return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                           text=TextResult(output=StringValue(
                                               value=f"Application asset with GUID '{application_name}' not found within returned data")),
                                           source=self.source)

            # 2. Filter APM metrics if requested
            all_apm_metrics = list(application_asset.apm_metrics)
            if not all_apm_metrics:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                          text=TextResult(output=StringValue(
                                              value=f"No APM metrics defined for application with GUID '{application_name}'")),
                                          source=self.source)

            metrics_to_process = []
            if filter_metric_names:
                for metric in all_apm_metrics:
                    if metric.metric_name.value.lower() in filter_metric_names:
                        metrics_to_process.append(metric)
                if not metrics_to_process:
                     return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                           text=TextResult(output=StringValue(
                                               value=f"No APM metrics matching names {filter_metric_names_str} found for application '{application_name}'")),
                                           source=self.source)
            else:
                metrics_to_process = all_apm_metrics # Process all if no filter

            # 3. Process each APM metric
            task_results = []
            nr_gql_processor = self.get_connector_processor(nr_connector)

            for apm_metric in metrics_to_process:
                try:
                    metric_name = apm_metric.metric_name.value
                    unit = apm_metric.metric_unit.value
                    base_nrql_expression = apm_metric.metric_nrql_expression.value

                    if not base_nrql_expression:
                         logger.warning(f"Skipping APM metric '{metric_name}' for application '{application_name}' as it has no NRQL query.")
                         continue

                    all_labeled_metric_timeseries = [] # Collect base and offset series
                    prepared_nrql = self._prepare_apm_metric_nrql(base_nrql_expression, time_range)

                    print(
                        "Playbook Task Downstream Request: Type -> {}, Account -> {}, App Name -> {}, Metric -> {}, NRQL -> {}".format(
                            "NewRelicAPM", nr_connector.account_id.value, application_name, metric_name, prepared_nrql), flush=True)

                    response = nr_gql_processor.execute_nrql_query(prepared_nrql)
                    base_timeseries = self._parse_apm_metric_response(response, metric_name, unit) # Already has offset 0 label
                    all_labeled_metric_timeseries.extend(base_timeseries)

                    for offset in timeseries_offsets:
                        if offset == 0: continue # Skip 0, already processed

                        adjusted_start_time = time_range.time_geq - offset
                        adjusted_end_time = time_range.time_lt - offset
                        adjusted_time_range = TimeRange(time_geq=adjusted_start_time, time_lt=adjusted_end_time)

                        offset_nrql = self._prepare_apm_metric_nrql(base_nrql_expression, adjusted_time_range)

                        print(
                            "Playbook Task Downstream Request: Type -> {}, Account -> {}, App GUID -> {}, Metric -> {}, NRQL -> {}, Offset -> {}".format(
                                "NewRelicAPM", nr_connector.account_id.value, application_name, metric_name, offset_nrql, offset), flush=True)

                        offset_response = nr_gql_processor.execute_nrql_query(offset_nrql)
                        offset_timeseries = self._parse_apm_metric_response(offset_response, metric_name, unit)

                        # Create new LabeledMetricTimeseries objects with updated labels for the offset
                        for series in offset_timeseries:
                            updated_labels = [
                                LabelValuePair(name=StringValue(value='apm_metric_name'), value=StringValue(value=metric_name)),
                                LabelValuePair(name=StringValue(value='offset_seconds'), value=StringValue(value=str(offset)))
                            ]
                            # Preserve facet label if present
                            facet_label = None
                            for label in series.metric_label_values:
                                if label.name.value == 'facet':
                                    facet_label = label
                                    break
                            if facet_label:
                                updated_labels.append(facet_label)

                            # Create a new LabeledMetricTimeseries with updated labels
                            new_labeled_metric_timeseries = TimeseriesResult.LabeledMetricTimeseries(
                                metric_label_values=updated_labels,
                                unit=series.unit,  # Reuse unit from original series
                                datapoints=series.datapoints # Reuse datapoints from original series
                            )
                            all_labeled_metric_timeseries.append(new_labeled_metric_timeseries)

                    if all_labeled_metric_timeseries:
                         # Use the base prepared NRQL for the expression field for consistency
                        timeseries_result = TimeseriesResult(metric_expression=StringValue(value=prepared_nrql),
                                                             metric_name=StringValue(value=metric_name),
                                                             labeled_metric_timeseries=all_labeled_metric_timeseries)
                        task_result = PlaybookTaskResult(type=PlaybookTaskResultType.TIMESERIES,
                                                         timeseries=timeseries_result, source=self.source)
                        task_results.append(task_result)
                    else:
                        logger.warning(f"No timeseries data could be parsed for APM metric '{metric_name}'.")

                except Exception as e:
                    logger.error(f"Error processing APM metric '{apm_metric.metric_name.value}' for application '{application_name}': {str(e)}", exc_info=True)
                    continue

            # Check if any results were generated
            if not task_results:
                filter_msg = f" matching names '{filter_metric_names_str}'" if filter_metric_names_str else ""
                logger.warning(f"No data retrieved for any APM metrics{filter_msg} in application '{application_name}'.")
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT,
                                          text=TextResult(output=StringValue(
                                              value=f"No data found for the specified APM metrics{filter_msg} in application '{application_name}'. Check metric configurations and time range.")),
                                          source=self.source)

            return task_results # Return list of results

        except Exception as e:
            logger.error(f"General Error executing Fetch APM Metrics task for app {task.application_entity_name.value}: {str(e)}", exc_info=True)
            raise Exception(f"Error while executing New Relic Fetch APM Metrics task: {e}")
