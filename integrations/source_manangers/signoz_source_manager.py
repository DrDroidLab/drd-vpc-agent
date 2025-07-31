import json
import logging
import typing
from datetime import datetime, timezone

from google.protobuf.struct_pb2 import Struct
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    DoubleValue,
    StringValue,
)

from integrations.source_api_processors.signoz_api_processor import SignozApiProcessor
from integrations.source_manager import SourceManager

from protos.base_pb2 import Source, SourceModelType, TimeRange
from protos.connectors.connector_pb2 import (
    Connector as ConnectorProto,
)
from protos.literal_pb2 import Literal, LiteralType
from protos.playbooks.playbook_commons_pb2 import (
    ApiResponseResult,
    LabelValuePair,
    PlaybookTaskResult,
    PlaybookTaskResultType,
    TableResult,
    TextResult,
    TimeseriesResult,
)
from protos.playbooks.source_task_definitions.signoz_task_pb2 import Signoz
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict
from utils.proto_utils import dict_to_proto, proto_to_dict
from utils.time_utils import calculate_timeseries_bucket_size

logger = logging.getLogger(__name__)


def format_builder_queries(builder_queries):
    """Format builder queries ensuring double quotes and proper JSON structure."""
    json_str = json.dumps(builder_queries, ensure_ascii=False, indent=None)
    return json.loads(json_str)


class SignozDashboardQueryBuilder:
    """Handles the transformation of Signoz dashboard panel protos to API query formats."""

    def __init__(self, global_step: int, variables: dict):
        self.global_step = global_step
        self.variables = variables
        self.query_letter_ord = ord("A")

    def _get_next_query_letter(self) -> str:
        """Gets the next query letter (A, B, C...)."""
        letter = chr(self.query_letter_ord)
        self.query_letter_ord += 1
        if self.query_letter_ord > ord("Z"):
            logger.warning("More than 26 builder queries assigned letters, reusing.")
            # Reset or handle differently if needed, for now, warn and potentially reuse.
            self.query_letter_ord = ord("A")
        return letter

    def _clean_group_by_item(self, item: dict) -> dict:
        """Removes unnecessary keys from groupBy items."""
        if isinstance(item, dict):
            return {k: v for k, v in item.items() if k in ["key", "dataType", "type", "isColumn"]}
        return item

    def _clean_aggregate_attribute(self, agg_attr: dict) -> dict:
        """Removes unnecessary keys from aggregateAttribute."""
        if isinstance(agg_attr, dict):
            return {k: v for k, v in agg_attr.items() if k in ["key", "dataType", "type", "isColumn"]}
        return agg_attr

    def build_query_dict(self, query_data_proto) -> tuple[str, dict]:
        """Converts a QueryData proto to a dictionary suitable for the Signoz API."""
        query_dict = proto_to_dict(query_data_proto)
        current_letter = self._get_next_query_letter()

        # Apply global step and remove original
        query_dict.pop("step_interval", None)
        query_dict["stepInterval"] = self.global_step

        # Rename group_by
        if "group_by" in query_dict:
            query_dict["groupBy"] = query_dict.pop("group_by")

        # Clean nested structures
        if "groupBy" in query_dict and isinstance(query_dict["groupBy"], list):
            query_dict["groupBy"] = [self._clean_group_by_item(item) for item in query_dict["groupBy"]]

        if "aggregateAttribute" in query_dict:
            query_dict["aggregateAttribute"] = self._clean_aggregate_attribute(query_dict["aggregateAttribute"])

        # Remove potentially extraneous/generated keys
        query_dict.pop("aggregateOperator", None)  # Often derived server-side
        query_dict.pop("id", None)
        query_dict.pop("isJSON", None)

        # Assign query name and expression based on letter
        query_dict["queryName"] = current_letter
        query_dict["expression"] = current_letter  # Default expression

        # Set default legend from groupBy if legend is empty
        original_legend = query_dict.get("legend", "")
        group_by_keys = query_dict.get("groupBy", [])
        if not original_legend and isinstance(group_by_keys, list) and len(group_by_keys) > 0:
            first_group_key = group_by_keys[0].get("key")
            query_dict["legend"] = f"{{{{{first_group_key}}}}}" if first_group_key else ""
        else:
            # Keep original or empty legend if no suitable group by key
            query_dict["legend"] = original_legend

        # Ensure disabled field exists
        query_dict["disabled"] = query_dict.get("disabled", False)

        return current_letter, query_dict

    def build_panel_payload(self, panel_title: str, panel_type: str, panel_queries: dict, time_range: TimeRange) -> dict:
        """Builds the full API payload for a single panel's queries."""
        from_time = int(time_range.time_geq * 1000)
        to_time = int(time_range.time_lt * 1000)

        payload = {
            "start": from_time,
            "end": to_time,
            "step": self.global_step,
            "variables": self.variables,
            "compositeQuery": {
                "queryType": "builder",
                "panelType": panel_type,
                "builderQueries": panel_queries,
            },
        }
        return format_builder_queries(payload)  # Ensure correct JSON formatting


class SignozSourceManager(SourceManager):
    def __init__(self):
        self.source = Source.SIGNOZ
        self.task_proto = Signoz
        self.task_type_callable_map = {
            Signoz.TaskType.CLICKHOUSE_QUERY: {
                "executor": self.execute_clickhouse_query,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Execute Clickhouse Query",
                "category": "Query",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="query"),
                        display_name=StringValue(value="Query"),
                        description=StringValue(value="Enter Clickhouse SQL query"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.MULTILINE_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="step"),
                        display_name=StringValue(value="Step"),
                        description=StringValue(value="Step interval in seconds"),
                        data_type=LiteralType.LONG,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="fill_gaps"),
                        display_name=StringValue(value="Fill Gaps"),
                        description=StringValue(value="Fill gaps in time series data"),
                        data_type=LiteralType.BOOLEAN,
                        is_optional=True,
                        default_value=Literal(
                            type=LiteralType.BOOLEAN,
                            boolean=BoolValue(value=False),
                        ),
                        form_field_type=FormFieldType.CHECKBOX_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="panel_type"),
                        display_name=StringValue(value="Panel Type"),
                        description=StringValue(value="Type of visualization panel"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        default_value=Literal(
                            type=LiteralType.STRING,
                            string=StringValue(value="table"),
                        ),
                        form_field_type=FormFieldType.DROPDOWN_FT,
                        valid_values=[
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="table"),
                            ),
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="graph"),
                            ),
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="value"),
                            ),
                        ],
                    ),
                ],
            },
            Signoz.TaskType.BUILDER_QUERY: {
                "executor": self.execute_builder_query,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Execute Query Builder Query",
                "category": "Query",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="builder_queries"),
                        display_name=StringValue(value="Builder Queries"),
                        description=StringValue(value="Enter the builder queries configuration"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.MULTILINE_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="step"),
                        display_name=StringValue(value="Step"),
                        description=StringValue(value="Step interval in seconds"),
                        data_type=LiteralType.LONG,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="panel_type"),
                        display_name=StringValue(value="Panel Type"),
                        description=StringValue(value="Type of visualization panel"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        default_value=Literal(
                            type=LiteralType.STRING,
                            string=StringValue(value="table"),
                        ),
                        form_field_type=FormFieldType.DROPDOWN_FT,
                        valid_values=[
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="table"),
                            ),
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="graph"),
                            ),
                            Literal(
                                type=LiteralType.STRING,
                                string=StringValue(value="value"),
                            ),
                        ],
                    ),
                ],
            },
            Signoz.TaskType.DASHBOARD_DATA: {
                "executor": self.execute_dashboard_data,
                "model_types": [SourceModelType.SIGNOZ_DASHBOARD],
                "result_type": PlaybookTaskResultType.TIMESERIES,
                "display_name": "Get Dashboard Data",
                "category": "Dashboard",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="dashboard_name"),
                        display_name=StringValue(value="Dashboard Name"),
                        description=StringValue(value="Enter the dashboard name"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="step"),
                        display_name=StringValue(value="Step"),
                        description=StringValue(value="Step interval in seconds"),
                        data_type=LiteralType.LONG,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="variables_json"),
                        display_name=StringValue(value="Variables JSON"),
                        description=StringValue(value="Enter variable overrides as a JSON object"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        default_value=Literal(
                            type=LiteralType.STRING,
                            string=StringValue(value="{}"),
                        ),
                        form_field_type=FormFieldType.MULTILINE_FT,  # Use multiline for JSON
                    ),
                ],
            },
            Signoz.TaskType.FETCH_DASHBOARDS: {
                "executor": self.execute_fetch_dashboards,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Fetch Dashboards",
                "category": "Dashboard",
                "form_fields": [],
            },
            Signoz.TaskType.FETCH_DASHBOARD_DETAILS: {
                "executor": self.execute_fetch_dashboard_details,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Fetch Dashboard Details",
                "category": "Dashboard",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="dashboard_id"),
                        display_name=StringValue(value="Dashboard ID"),
                        description=StringValue(value="Enter the dashboard ID"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
            Signoz.TaskType.FETCH_SERVICES: {
                "executor": self.execute_fetch_services,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Fetch Services",
                "category": "Services",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="start_time"),
                        display_name=StringValue(value="Start Time"),
                        description=StringValue(value="Start time (RFC3339 or relative like 'now-2h')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="end_time"),
                        display_name=StringValue(value="End Time"),
                        description=StringValue(value="End time (RFC3339 or relative like 'now-30m')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="duration"),
                        display_name=StringValue(value="Duration"),
                        description=StringValue(value="Duration string (e.g., '2h', '90m')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
            Signoz.TaskType.FETCH_APM_METRICS: {
                "executor": self.execute_fetch_apm_metrics,
                "model_types": [],
                "result_type": PlaybookTaskResultType.TIMESERIES,
                "display_name": "Fetch APM Metrics",
                "category": "Metrics",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="service_name"),
                        display_name=StringValue(value="Service Name"),
                        description=StringValue(value="Name of the service to fetch metrics for"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="start_time"),
                        display_name=StringValue(value="Start Time"),
                        description=StringValue(value="Start time (RFC3339 or relative like 'now-2h')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="end_time"),
                        display_name=StringValue(value="End Time"),
                        description=StringValue(value="End time (RFC3339 or relative like 'now-30m')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="window"),
                        display_name=StringValue(value="Window"),
                        description=StringValue(value="Time window for aggregation (e.g., '1m', '5m')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        default_value=Literal(
                            type=LiteralType.STRING,
                            string=StringValue(value="1m"),
                        ),
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="operation_names"),
                        display_name=StringValue(value="Operation Names"),
                        description=StringValue(value="JSON array of operation names to filter by"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.MULTILINE_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="metrics"),
                        display_name=StringValue(value="Metrics"),
                        description=StringValue(value="JSON array of metrics to fetch (e.g., ['request_rate', 'error_rate'])"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.MULTILINE_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="duration"),
                        display_name=StringValue(value="Duration"),
                        description=StringValue(value="Duration string (e.g., '2h', '90m')"),
                        data_type=LiteralType.STRING,
                        is_optional=True,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
        }

    def get_connector_processor(self, signoz_connector, **kwargs):
        generated_credentials = generate_credentials_dict(signoz_connector.type, signoz_connector.keys)
        return SignozApiProcessor(**generated_credentials)

    # Helper function to get the step interval for queries
    def _get_step_interval(self, time_range: TimeRange, task_definition) -> int:
        """Calculates the step interval. Uses user-defined value if provided, otherwise calculates dynamically."""
        if task_definition and task_definition.HasField("step") and task_definition.step.value:
            return task_definition.step.value
        else:
            total_seconds = time_range.time_lt - time_range.time_geq
            return calculate_timeseries_bucket_size(total_seconds)

    # Helper function to convert a single Signoz query result item to TimeseriesResult
    def _convert_to_timeseries_result(
        self,
        query_result_item: dict,
        query_name: str,
        query_expression: str,
        legend: str = "",
    ) -> typing.Optional[TimeseriesResult]:
        """
        Convert a single Signoz query result item to TimeseriesResult format.
        """
        try:
            # Initialize the TimeseriesResult
            timeseries_result = TimeseriesResult(
                metric_name=StringValue(value=query_name),
                metric_expression=StringValue(value=query_expression),
            )

            # Process series directly within the item
            if "series" not in query_result_item:
                logger.warning(f"No 'series' found in query result item for {query_name}")
                return None

            for series in query_result_item["series"]:
                # Extract values
                datapoints = []
                if "values" in series:
                    for value in series["values"]:
                        if "timestamp" in value and "value" in value:
                            # Keep timestamp in milliseconds as expected by the protobuf
                            timestamp_ms = int(value["timestamp"])
                            try:
                                value_float = float(value["value"])
                                datapoints.append(
                                    TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                        timestamp=timestamp_ms,  # Pass milliseconds directly
                                        value=DoubleValue(value=value_float),
                                    )
                                )
                            except (ValueError, TypeError):
                                # Skip non-numeric values
                                logger.debug(f"Skipping non-numeric value in series for {query_name}: {value['value']}")
                                continue

                # Get labels if available
                metric_label_values = []
                if "labels" in series:
                    for label_key, label_value in series["labels"].items():
                        metric_label_values.append(
                            LabelValuePair(
                                name=StringValue(value=label_key),
                                value=StringValue(value=str(label_value)),
                            )
                        )

                # Add panel title as a label
                metric_label_values.append(
                    LabelValuePair(
                        name=StringValue(value="panel_title"),
                        value=StringValue(value=query_name),  # query_name holds the panel title
                    )
                )

                # Add legend as a label (if provided)
                query_name_letter = query_result_item.get("queryName", "")  # Get 'A', 'B', etc.
                metric_label_values.append(
                    LabelValuePair(
                        name=StringValue(value="metric_legend"),
                        # Use legend if available, otherwise fallback to query letter (A, B..)
                        value=StringValue(value=legend if legend else query_name_letter),
                    )
                )

                # Create and add the labeled metric timeseries
                if datapoints:
                    timeseries_result.labeled_metric_timeseries.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=metric_label_values,
                            unit=StringValue(value=""),  # Unit info might not be directly available here
                            datapoints=datapoints,
                        )
                    )

            return timeseries_result if timeseries_result.labeled_metric_timeseries else None
        except Exception as e:
            logger.error(
                f"Error converting single query result to timeseries result for {query_name}: {e}",
                exc_info=True,
            )
            return None

    # Helper function to convert a single Signoz query result item to TableResult
    def _convert_to_table_result(self, query_result_item: dict, query_expression: str) -> typing.Optional[TableResult]:
        """
        Convert a single Signoz query result item to TableResult format.
        """
        try:
            # Initialize TableResult
            table_result = TableResult(
                raw_query=StringValue(value=query_expression),
                searchable=BoolValue(value=True),
            )

            # Process data from the single item
            if "table" in query_result_item:
                table_data = query_result_item["table"]
                if "rows" in table_data:
                    for row_data in table_data["rows"]:
                        if "data" in row_data:
                            # Each row has data fields
                            columns = []
                            for col_name, col_value in row_data["data"].items():
                                columns.append(
                                    TableResult.TableColumn(
                                        name=StringValue(value=col_name),
                                        type=StringValue(value=type(col_value).__name__),
                                        value=StringValue(value=str(col_value)),
                                    )
                                )
                            if columns:
                                table_result.rows.append(TableResult.TableRow(columns=columns))
            elif "series" in query_result_item:
                # For series data, convert to table format
                for series in query_result_item["series"]:
                    if "values" in series:
                        for value in series["values"]:
                            if "timestamp" in value and "value" in value:
                                columns = [
                                    TableResult.TableColumn(
                                        name=StringValue(value="timestamp_ms"),  # Indicate ms
                                        type=StringValue(value="number"),
                                        value=StringValue(value=str(value["timestamp"])),
                                    ),
                                    TableResult.TableColumn(
                                        name=StringValue(value="value"),
                                        type=StringValue(value="string"),  # Keep as string for flexibility
                                        value=StringValue(value=str(value["value"])),
                                    ),
                                ]
                                # Add labels as additional columns
                                if "labels" in series:
                                    for label_key, label_value in series["labels"].items():
                                        columns.append(
                                            TableResult.TableColumn(
                                                name=StringValue(value=label_key),
                                                type=StringValue(value="string"),
                                                value=StringValue(value=str(label_value)),
                                            )
                                        )
                                # Add original query name as a column
                                if "queryName" in query_result_item:
                                    columns.append(
                                        TableResult.TableColumn(
                                            name=StringValue(value="signoz_query_id"),
                                            type=StringValue(value="string"),
                                            value=StringValue(value=query_result_item["queryName"]),
                                        )
                                    )
                                table_result.rows.append(TableResult.TableRow(columns=columns))

            return table_result if table_result.rows else None
        except Exception as e:
            logger.error(
                f"Error converting single query result to table result: {e}",
                exc_info=True,
            )
            return None

    # Helper function to create the appropriate task result based on panel_type for a single query result
    def _create_task_result(
        self,
        query_result_item: dict,
        panel_type: str,
        query_name: str,
        query_expression: str,
    ) -> typing.Optional[PlaybookTaskResult]:
        """
        Create the appropriate task result for a single query's result based on its panel_type.
        """
        if not query_result_item:
            logger.warning(f"No data provided for query '{query_name}' to create task result.")
            # Return None, let the caller decide how to handle lack of data for one query
            return None

        if panel_type == "graph":
            # For graph panels, return timeseries result
            timeseries_result = self._convert_to_timeseries_result(query_result_item, query_name, query_expression)
            if timeseries_result:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TIMESERIES,
                    timeseries=timeseries_result,
                    source=self.source,
                )
            else:
                logger.warning(f"Failed to convert graph panel data to timeseries for query '{query_name}'.")
                # Fallback or return None? Let's return None for now.
                return None
        elif panel_type == "table":
            # For table panels, return table result
            table_result = self._convert_to_table_result(query_result_item, query_expression)
            if table_result:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TABLE,
                    table=table_result,
                    source=self.source,
                )
            else:
                logger.warning(f"Failed to convert table panel data to table result for query '{query_name}'.")
                return None

        # Default or for 'value' panel type, return API response for the single query item
        try:
            # We wrap the single query result item in a minimal structure expected by dict_to_proto
            response_struct = dict_to_proto({"result": query_result_item}, Struct)
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                api_response=ApiResponseResult(
                    response_body=response_struct,
                    # Add query name/expression to metadata if needed
                ),
                source=self.source,
            )
        except Exception as e:
            logger.error(
                f"Failed to convert value/default panel data to API response for query '{query_name}': {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _format_asset_variables(asset) -> str:
        """Formats the variables section for the asset descriptor."""
        if not asset.variables:
            return ""
        var_string = "  Variables:\n"
        for variable in asset.variables:
            var_name = variable.name.value
            var_type = variable.type.value
            var_selected = variable.selected_value.value
            var_desc = variable.description.value
            var_string += f"    - Name: `{var_name}`, Type: `{var_type}`, Selected: `{var_selected}`, Desc: `{var_desc}`\n"
        return var_string

    @staticmethod
    def _format_asset_panel_query(query_data) -> str:
        """Formats a single panel query for the asset descriptor."""
        query_name = query_data.queryName.value if query_data.HasField("queryName") else "Unknown"
        # Use proto_to_dict for a structured representation
        try:
            query_dict = proto_to_dict(query_data)
            # Limit verbosity by removing potentially large fields like filters for descriptor
            query_dict.pop("filters", None)
            query_string = json.dumps(query_dict, indent=2)  # Use indent 2 for less space
        except Exception:
            query_string = "[Error formatting query]"
        return f"        - Query Name: `{query_name}`, Query: `{query_string}`\n"

    @staticmethod
    def _format_asset_panel(panel) -> str:
        """Formats the panels section for the asset descriptor."""
        panel_id = panel.id.value
        panel_title = panel.title.value
        panel_type = panel.panel_type.value
        panel_string = f"    * Panel Title: `{panel_title}`, ID: `{panel_id}`, Type: `{panel_type}`\n"

        if panel.HasField("query") and panel.query.HasField("builder") and panel.query.builder.query_data:
            panel_string += "      Queries:\n"
            for query_data in panel.query.builder.query_data:
                panel_string += SignozSourceManager._format_asset_panel_query(query_data)
        return panel_string

    def execute_clickhouse_query(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            task = signoz_task.clickhouse_query
            query = task.query.value

            step = self._get_step_interval(time_range, task)
            fill_gaps = task.fill_gaps.value if task.HasField("fill_gaps") else False
            panel_type = task.panel_type.value if task.HasField("panel_type") else "table"

            signoz_api_processor = self.get_connector_processor(signoz_connector)

            # Convert timerange to milliseconds for Signoz API
            from_time = int(time_range.time_geq * 1000)
            to_time = int(time_range.time_lt * 1000)

            # Prepare the query payload
            payload = {
                "start": from_time,
                "end": to_time,
                "step": step,
                "variables": {},
                "formatForWeb": True,
                "compositeQuery": {
                    "queryType": "clickhouse_sql",
                    "panelType": panel_type,
                    "fillGaps": fill_gaps,
                    "chQueries": {
                        "A": {
                            "name": "A",
                            "legend": "",
                            "disabled": False,
                            "query": query,
                        }
                    },
                },
            }

            # Execute the query
            result = signoz_api_processor.execute_signoz_query(payload)

            # Create the appropriate task result based on panel_type
            return self._create_task_result(result, panel_type, query, "Clickhouse Query")
        except Exception as e:
            logger.error(f"Error while executing Signoz Clickhouse query task: {e}")
            raise Exception(f"Error while executing Signoz Clickhouse query task: {e}") from e

    def execute_builder_query(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            task = signoz_task.builder_query
            # Clean and parse the builder queries
            builder_queries = json.loads(task.builder_queries.value)
            # Clean and format the queries
            cleaned_queries = format_builder_queries(builder_queries)

            step = self._get_step_interval(time_range, task)
            panel_type = task.panel_type.value if task.HasField("panel_type") else "table"

            signoz_api_processor = self.get_connector_processor(signoz_connector)

            # Convert timerange to milliseconds for Signoz API
            from_time = int(time_range.time_geq * 1000)
            to_time = int(time_range.time_lt * 1000)

            # Prepare the query payload
            payload = {
                "start": from_time,
                "end": to_time,
                "step": step,
                "variables": {},
                "compositeQuery": {
                    "queryType": "builder",
                    "panelType": panel_type,
                    "builderQueries": cleaned_queries,
                },
            }

            # Format the entire payload to ensure double quotes
            payload = format_builder_queries(payload)

            # Execute the query
            result = signoz_api_processor.execute_signoz_query(payload)
            query_name = "Builder Query"
            if cleaned_queries and isinstance(cleaned_queries, dict):
                first_key = next(iter(cleaned_queries), None)
                if first_key and "queryName" in cleaned_queries[first_key]:
                    query_name = cleaned_queries[first_key]["queryName"]
            return self._create_task_result(result, panel_type, str(cleaned_queries), query_name)
        except Exception as e:
            logger.error(f"Error while executing Signoz builder query task: {e}")
            raise Exception(f"Error while executing Signoz builder query task: {e!s}") from e



    def execute_dashboard_data(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> list[PlaybookTaskResult]:
        """Executes queries for all panels in a specified Signoz dashboard using the processor's fetch_dashboard_data method."""
        try:
            if not signoz_connector:
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.ERROR,
                        text=TextResult(output=StringValue(value="Signoz connector not found.")),
                        source=self.source,
                    )
                ]

            task = signoz_task.dashboard_data
            dashboard_name = task.dashboard_name.value
            if not dashboard_name:
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.ERROR,
                        text=TextResult(output=StringValue(value="Dashboard name must be provided.")),
                        source=self.source,
                    )
                ]

            # Get parameters
            step = task.step.value if task.HasField("step") else None
            variables_json = task.variables_json.value if task.HasField("variables_json") else None

            # Convert time range to start/end times for the processor
            start_time = datetime.fromtimestamp(time_range.time_geq, tz=timezone.utc).isoformat()
            end_time = datetime.fromtimestamp(time_range.time_lt, tz=timezone.utc).isoformat()

            signoz_api_processor = self.get_connector_processor(signoz_connector)
            result = signoz_api_processor.fetch_dashboard_data(
                dashboard_name, start_time, end_time, step, variables_json
            )

            if result and result.get("status") == "success":
                # Convert the result to a structured response
                response_struct = dict_to_proto(result, Struct)
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.API_RESPONSE,
                        api_response=ApiResponseResult(response_body=response_struct),
                        source=self.source,
                    )
                ]
            else:
                error_msg = result.get("message", "Failed to fetch dashboard data") if result else "Failed to fetch dashboard data"
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.ERROR,
                        text=TextResult(output=StringValue(value=error_msg)),
                        source=self.source,
                    )
                ]

        except Exception as e:
            logger.error(f"Error while executing Signoz dashboard data task: {e}", exc_info=True)
            return [
                PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value=f"Unexpected error executing dashboard task: {e}")),
                    source=self.source,
                )
            ]

    def execute_fetch_dashboards(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        """Executes fetch dashboards task."""
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            signoz_api_processor = self.get_connector_processor(signoz_connector)
            result = signoz_api_processor.fetch_dashboards()

            if result:
                # Handle different response formats from fetch_dashboards
                if isinstance(result, list):
                    # If result is a list of dashboards, wrap it in a dictionary
                    response_data = {"dashboards": result}
                elif isinstance(result, dict):
                    # If result is already a dictionary, use it as is
                    response_data = result
                else:
                    # Fallback: wrap in a generic structure
                    response_data = {"data": result}
                
                response_struct = dict_to_proto(response_data, Struct)
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.API_RESPONSE,
                    api_response=ApiResponseResult(response_body=response_struct),
                    source=self.source,
                )
            else:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value="Failed to fetch dashboards")),
                    source=self.source,
                )
        except Exception as e:
            logger.error(f"Error while executing Signoz fetch dashboards task: {e}")
            raise Exception(f"Error while executing Signoz fetch dashboards task: {e}") from e

    def execute_fetch_dashboard_details(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        """Executes fetch dashboard details task."""
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            task = signoz_task.fetch_dashboard_details
            dashboard_id = task.dashboard_id.value
            if not dashboard_id:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value="Dashboard ID must be provided.")),
                    source=self.source,
                )

            signoz_api_processor = self.get_connector_processor(signoz_connector)
            result = signoz_api_processor.fetch_dashboard_details(dashboard_id)

            if result:
                # Handle different response formats from fetch_dashboard_details
                if isinstance(result, dict):
                    # If result is already a dictionary, use it as is
                    response_data = result
                else:
                    # Fallback: wrap in a generic structure
                    response_data = {"data": result}
                
                response_struct = dict_to_proto(response_data, Struct)
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.API_RESPONSE,
                    api_response=ApiResponseResult(response_body=response_struct),
                    source=self.source,
                )
            else:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value=f"Failed to fetch dashboard details for ID: {dashboard_id}")),
                    source=self.source,
                )
        except Exception as e:
            logger.error(f"Error while executing Signoz fetch dashboard details task: {e}")
            raise Exception(f"Error while executing Signoz fetch dashboard details task: {e}") from e

    def execute_fetch_services(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        """Executes fetch services task."""
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            task = signoz_task.fetch_services
            start_time = task.start_time.value if task.HasField("start_time") else None
            end_time = task.end_time.value if task.HasField("end_time") else None
            duration = task.duration.value if task.HasField("duration") else None

            signoz_api_processor = self.get_connector_processor(signoz_connector)
            result = signoz_api_processor.fetch_services(start_time, end_time, duration)

            if result:
                # Handle different response formats from fetch_services
                if isinstance(result, list):
                    # If result is a list of services, wrap it in a dictionary
                    response_data = {"services": result}
                elif isinstance(result, dict):
                    # If result is already a dictionary (e.g., error response), use it as is
                    response_data = result
                else:
                    # Fallback: wrap in a generic structure
                    response_data = {"data": result}
                
                response_struct = dict_to_proto(response_data, Struct)
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.API_RESPONSE,
                    api_response=ApiResponseResult(response_body=response_struct),
                    source=self.source,
                )
            else:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value="Failed to fetch services")),
                    source=self.source,
                )
        except Exception as e:
            logger.error(f"Error while executing Signoz fetch services task: {e}")
            raise Exception(f"Error while executing Signoz fetch services task: {e}") from e

    def execute_fetch_apm_metrics(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> PlaybookTaskResult:
        """Executes fetch APM metrics task."""
        try:
            if not signoz_connector:
                raise Exception("Task execution Failed:: No Signoz source found")

            task = signoz_task.fetch_apm_metrics
            service_name = task.service_name.value
            if not service_name:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value="Service name must be provided.")),
                    source=self.source,
                )

            start_time = task.start_time.value if task.HasField("start_time") else None
            end_time = task.end_time.value if task.HasField("end_time") else None
            window = task.window.value if task.HasField("window") else "1m"
            operation_names = task.operation_names.value if task.HasField("operation_names") else None
            metrics = task.metrics.value if task.HasField("metrics") else None
            duration = task.duration.value if task.HasField("duration") else None

            # Parse JSON arrays if provided
            if operation_names:
                try:
                    operation_names = json.loads(operation_names)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid operation_names JSON: {operation_names}")
                    operation_names = None

            if metrics:
                try:
                    metrics = json.loads(metrics)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid metrics JSON: {metrics}")
                    metrics = None

            signoz_api_processor = self.get_connector_processor(signoz_connector)
            result = signoz_api_processor.fetch_apm_metrics(
                service_name, start_time, end_time, window, operation_names, metrics, duration
            )

            if result and "error" not in result:
                # Convert to timeseries result
                timeseries_result = self._convert_apm_metrics_to_timeseries(result, service_name)
                if timeseries_result:
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.TIMESERIES,
                        timeseries=timeseries_result,
                        source=self.source,
                    )
                else:
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.ERROR,
                        text=TextResult(output=StringValue(value="Failed to convert APM metrics to timeseries format")),
                        source=self.source,
                    )
            else:
                error_msg = result.get("error", "Failed to fetch APM metrics") if result else "Failed to fetch APM metrics"
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value=error_msg)),
                    source=self.source,
                )
        except Exception as e:
            logger.error(f"Error while executing Signoz fetch APM metrics task: {e}")
            raise Exception(f"Error while executing Signoz fetch APM metrics task: {e}") from e

    def _convert_apm_metrics_to_timeseries(self, apm_metrics_result: dict, service_name: str) -> typing.Optional[TimeseriesResult]:
        """Converts APM metrics result to TimeseriesResult format."""
        try:
            if not apm_metrics_result or "data" not in apm_metrics_result:
                return None

            timeseries_result = TimeseriesResult(
                metric_name=StringValue(value=f"APM Metrics - {service_name}"),
                metric_expression=StringValue(value=f"APM metrics for service: {service_name}"),
            )

            data = apm_metrics_result["data"]
            if "result" in data and isinstance(data["result"], list):
                for query_result in data["result"]:
                    if "series" in query_result:
                        for series in query_result["series"]:
                            datapoints = []
                            if "values" in series:
                                for value in series["values"]:
                                    if "timestamp" in value and "value" in value:
                                        try:
                                            timestamp_ms = int(value["timestamp"])
                                            value_float = float(value["value"])
                                            datapoints.append(
                                                TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                                    timestamp=timestamp_ms,
                                                    value=DoubleValue(value=value_float),
                                                )
                                            )
                                        except (ValueError, TypeError):
                                            continue

                            if datapoints:
                                metric_label_values = []
                                if "labels" in series:
                                    for label_key, label_value in series["labels"].items():
                                        metric_label_values.append(
                                            LabelValuePair(
                                                name=StringValue(value=label_key),
                                                value=StringValue(value=str(label_value)),
                                            )
                                        )

                                # Add service name and query info as labels
                                metric_label_values.append(
                                    LabelValuePair(
                                        name=StringValue(value="service_name"),
                                        value=StringValue(value=service_name),
                                    )
                                )
                                metric_label_values.append(
                                    LabelValuePair(
                                        name=StringValue(value="query_name"),
                                        value=StringValue(value=query_result.get("queryName", "unknown")),
                                    )
                                )

                                timeseries_result.labeled_metric_timeseries.append(
                                    TimeseriesResult.LabeledMetricTimeseries(
                                        metric_label_values=metric_label_values,
                                        unit=StringValue(value=""),
                                        datapoints=datapoints,
                                    )
                                )

            return timeseries_result if timeseries_result.labeled_metric_timeseries else None
        except Exception as e:
            logger.error(f"Error converting APM metrics to timeseries: {e}", exc_info=True)
            return None
