import json
import logging
import typing
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.protobuf.struct_pb2 import Struct
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    DoubleValue,
    StringValue,
)

from integrations.source_api_processors.signoz_api_processor import SignozApiProcessor
from integrations.source_manager import SourceManager
from protos.assets.asset_pb2 import (
    AccountConnectorAssetsModelFilters,
    AccountConnectorAssets,
)
from protos.assets.signoz_asset_pb2 import (
    SignozDashboardModel,
)
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
from utils.playbooks_client import PrototypeClient
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

    def _aggregate_panel_graph_results(self, api_query_results: list, panel_title: str, panel_queries: dict) -> typing.Optional[PlaybookTaskResult]:
        """Aggregates multiple query results for a 'graph' panel into a single TimeseriesResult."""
        all_labeled_metric_timeseries = []
        for query_result_item in api_query_results:
            query_letter = query_result_item.get("queryName")
            original_query_dict = panel_queries.get(query_letter, {})
            query_legend = original_query_dict.get("legend", query_letter or "")

            if "series" not in query_result_item:
                continue

            for series in query_result_item["series"]:
                datapoints = []
                if "values" in series:
                    for value in series["values"]:
                        if "timestamp" in value and "value" in value:
                            try:
                                timestamp_ms = int(value["timestamp"])
                                value_float = float(value["value"])
                                datapoints.append(
                                    TimeseriesResult.LabeledMetricTimeseries.Datapoint(timestamp=timestamp_ms, value=DoubleValue(value=value_float))
                                )
                            except (ValueError, TypeError):
                                continue  # Skip non-numeric

                if not datapoints:
                    continue  # Don't add series with no valid data

                metric_label_values = []
                if "labels" in series:
                    metric_label_values.extend(
                        [LabelValuePair(name=StringValue(value=k), value=StringValue(value=str(v))) for k, v in series["labels"].items()]
                    )
                metric_label_values.append(LabelValuePair(name=StringValue(value="panel_title"), value=StringValue(value=panel_title)))
                metric_label_values.append(LabelValuePair(name=StringValue(value="metric_legend"), value=StringValue(value=query_legend)))

                all_labeled_metric_timeseries.append(
                    TimeseriesResult.LabeledMetricTimeseries(
                        metric_label_values=metric_label_values, unit=StringValue(value=""), datapoints=datapoints
                    )
                )

        if all_labeled_metric_timeseries:
            aggregated_timeseries = TimeseriesResult(
                metric_name=StringValue(value=panel_title),
                metric_expression=StringValue(value=f"Aggregated queries for panel: {panel_title}"),
                labeled_metric_timeseries=all_labeled_metric_timeseries,
            )
            return PlaybookTaskResult(type=PlaybookTaskResultType.TIMESERIES, timeseries=aggregated_timeseries, source=self.source)
        else:
            logger.warning(f"No timeseries data processed for graph panel '{panel_title}'.")
            return None

    def _aggregate_panel_table_results(self, api_query_results: list, panel_title: str) -> typing.Optional[PlaybookTaskResult]:
        """Aggregates multiple query results for a 'table' panel into a single TableResult."""
        all_rows = []
        for query_result_item in api_query_results:
            query_letter = query_result_item.get("queryName", "")
            if "table" in query_result_item and "rows" in query_result_item["table"]:
                for row_data in query_result_item["table"]["rows"]:
                    if "data" in row_data:
                        columns = [
                            TableResult.TableColumn(
                                name=StringValue(value=k), type=StringValue(value=type(v).__name__), value=StringValue(value=str(v))
                            )
                            for k, v in row_data["data"].items()
                        ]
                        columns.append(
                            TableResult.TableColumn(
                                name=StringValue(value="signoz_query_id"), type=StringValue(value="string"), value=StringValue(value=query_letter)
                            )
                        )
                        if columns:
                            all_rows.append(TableResult.TableRow(columns=columns))
            elif "series" in query_result_item:  # Convert series to table rows
                for series in query_result_item["series"]:
                    if "values" in series:
                        for value in series["values"]:
                            if "timestamp" in value and "value" in value:
                                columns = [
                                    TableResult.TableColumn(
                                        name=StringValue(value="timestamp_ms"),
                                        type=StringValue(value="number"),
                                        value=StringValue(value=str(value["timestamp"])),
                                    ),
                                    TableResult.TableColumn(
                                        name=StringValue(value="value"),
                                        type=StringValue(value="string"),
                                        value=StringValue(value=str(value["value"])),
                                    ),
                                ]
                                if "labels" in series:
                                    columns.extend(
                                        [
                                            TableResult.TableColumn(
                                                name=StringValue(value=k), type=StringValue(value="string"), value=StringValue(value=str(v))
                                            )
                                            for k, v in series["labels"].items()
                                        ]
                                    )
                                columns.append(
                                    TableResult.TableColumn(
                                        name=StringValue(value="signoz_query_id"),
                                        type=StringValue(value="string"),
                                        value=StringValue(value=query_letter),
                                    )
                                )
                                all_rows.append(TableResult.TableRow(columns=columns))

        if all_rows:
            aggregated_table = TableResult(
                raw_query=StringValue(value=f"Aggregated queries for panel: {panel_title}"),
                rows=all_rows,
                searchable=BoolValue(value=True),
            )
            return PlaybookTaskResult(type=PlaybookTaskResultType.TABLE, table=aggregated_table, source=self.source)
        else:
            logger.warning(f"No table data processed for table panel '{panel_title}'.")
            return None

    def _execute_panel_queries(
        self,
        panel_info: dict,
        time_range: TimeRange,
        signoz_api_processor: SignozApiProcessor,
        query_builder: SignozDashboardQueryBuilder,  # Pass builder instance
    ) -> typing.Optional[PlaybookTaskResult]:
        """Executes queries for a single panel and aggregates results."""
        try:
            panel_type = panel_info["panel_type"]
            panel_title = panel_info["panel_title"]
            panel_queries = panel_info["queries"]  # Already built dicts

            if not panel_queries:
                logger.warning(f"No queries found for panel '{panel_title}'. Skipping.")
                return None

            # Build the payload using the QueryBuilder instance
            formatted_payload = query_builder.build_panel_payload(panel_title, panel_type, panel_queries, time_range)

            logger.debug(f"Executing {len(panel_queries)} queries for panel '{panel_title}' (type: {panel_type})")
            try:
                result = signoz_api_processor.execute_signoz_query(formatted_payload)
            except Exception as api_err:
                logger.error(f"API error executing queries for panel '{panel_title}': {api_err}", exc_info=True)
                # Return an error result specific to this panel? Or let the main loop handle? Let's return None.
                return None  # Indicate failure for this panel

            if result and "data" in result and "result" in result["data"] and isinstance(result["data"]["result"], list):
                api_query_results = result["data"]["result"]
                logger.info(f"Received {len(api_query_results)} results from composite query for panel '{panel_title}'.")

                if panel_type == "graph":
                    return self._aggregate_panel_graph_results(api_query_results, panel_title, panel_queries)
                elif panel_type == "table":
                    return self._aggregate_panel_table_results(api_query_results, panel_title)
                else:  # Default to API Response for 'value' or other types, returning the full composite result
                    try:
                        response_struct = dict_to_proto(result, Struct)
                        metadata_struct = dict_to_proto({"panel_title": panel_title, "panel_type": panel_type}, Struct)
                        return PlaybookTaskResult(
                            type=PlaybookTaskResultType.API_RESPONSE,
                            api_response=ApiResponseResult(response_body=response_struct, metadata=metadata_struct),
                            source=self.source,
                        )
                    except Exception as e:
                        logger.error(f"Failed to convert raw result to API response for panel '{panel_title}': {e}", exc_info=True)
                        return None  # Indicate failure
            else:
                logger.warning(f"No valid result data received for panel '{panel_title}'. Response: {result}")
                return None

        except Exception as e:
            logger.error(f"Error executing queries for panel '{panel_info.get('panel_title', 'UNKNOWN')}': {e}", exc_info=True)
            return None  # Indicate error for this panel

    def _find_dashboard_asset(self, signoz_connector: ConnectorProto, dashboard_name: str) -> typing.Optional["SignozDashboardModel"]:
        """Finds a specific dashboard asset by name."""
        try:
            prototype_client = PrototypeClient()
            assets:AccountConnectorAssets = prototype_client.get_connector_assets(
                "SIGNOZ",
                signoz_connector.id.value,
                SourceModelType.SIGNOZ_DASHBOARD,
                proto_to_dict(AccountConnectorAssetsModelFilters()),  # Pass filters if possible later
            )
            if not assets or not assets.signoz or not assets.signoz.assets:
                logger.warning(f"No Signoz dashboard assets found for connector {signoz_connector.id.value}")
                return None

            for asset in assets.signoz.assets:
                if (
                    asset.type == SourceModelType.SIGNOZ_DASHBOARD
                    and asset.HasField("signoz_dashboard")
                    and asset.signoz_dashboard.title.value == dashboard_name
                ):
                    return asset.signoz_dashboard
            return None
        except Exception as e:
            logger.error(f"Error fetching dashboard assets for connector {signoz_connector.id.value}: {e}", exc_info=True)
            return None  # Indicate error during fetch

    def _parse_dashboard_variables(self, task: Signoz.DashboardDataTask) -> tuple[dict, typing.Optional[PlaybookTaskResult]]:
        """Parses variables JSON from task input, returning dict and error result if any."""
        variables_json = task.variables_json.value if task.HasField("variables_json") and task.variables_json.value else "{}"
        try:
            variables_dict = json.loads(variables_json) if variables_json.strip() else {}

            if not isinstance(variables_dict, dict):
                logger.warning(f"Parsed variables JSON is not a dictionary: {variables_json}. Using empty dictionary.")
                return {}, None  # Return empty dict, no error result needed for this case
            return variables_dict, None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse variables JSON: '{variables_json}'. Error: {e}", exc_info=True)
            error_result = PlaybookTaskResult(
                type=PlaybookTaskResultType.ERROR,
                text=TextResult(output=StringValue(value=f"Invalid Variables JSON provided: {e}")),
                source=self.source,
            )
            return {}, error_result  # Return empty dict and the error

    def _prepare_panel_queries(self, dashboard: "SignozDashboardModel", query_builder: SignozDashboardQueryBuilder) -> dict:
        """Processes panels to build a map of {panel_id: {panel_info}} including built query dicts."""
        panel_queries_map = {}
        for panel in dashboard.panels:
            if panel.query and panel.query.builder and panel.query.builder.query_data:
                panel_type = panel.panel_type.value if panel.panel_type.value else "graph"  # Default type
                panel_title = panel.title.value if panel.title.value else f"Panel_{panel.id.value}"
                panel_id = panel.id.value

                built_queries = {}
                for query_data_proto in panel.query.builder.query_data:
                    try:
                        query_letter, query_dict = query_builder.build_query_dict(query_data_proto)
                        built_queries[query_letter] = query_dict
                    except Exception as build_err:
                        logger.error(f"Error building query dict for panel '{panel_title}' (ID: {panel_id}): {build_err}", exc_info=True)
                        # Decide: skip query, skip panel, or raise? Let's skip the query.
                        continue

                if built_queries:  # Only add panel if it has successfully built queries
                    panel_queries_map[panel_id] = {
                        "panel_title": panel_title,
                        "panel_type": panel_type,
                        "queries": built_queries,
                    }
        return panel_queries_map

    def execute_dashboard_data(
        self,
        time_range: TimeRange,
        signoz_task: Signoz,
        signoz_connector: ConnectorProto,
    ) -> list[PlaybookTaskResult]:
        """Executes queries for all panels in a specified Signoz dashboard."""
        task_results = []
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

            # 1. Parse Variables
            variables_dict, error_result = self._parse_dashboard_variables(task)
            if error_result:
                return [error_result]

            # 2. Find Dashboard Asset
            dashboard = self._find_dashboard_asset(signoz_connector, dashboard_name)
            if not dashboard:
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(value=f"Dashboard '{dashboard_name}' not found.")),
                        source=self.source,
                    )
                ]

            # 3. Prepare Panel Queries using QueryBuilder
            global_step = self._get_step_interval(time_range, task)
            query_builder = SignozDashboardQueryBuilder(global_step=global_step, variables=variables_dict)
            panel_queries_map = self._prepare_panel_queries(dashboard, query_builder)

            if not panel_queries_map:
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(value=f"No builder queries found or prepared for dashboard: {dashboard_name}")),
                        source=self.source,
                    )
                ]

            # 4. Execute Queries Concurrently
            signoz_api_processor = self.get_connector_processor(signoz_connector)
            futures_map = {}
            # Consider making max_workers configurable or dynamic
            max_workers = min(10, len(panel_queries_map))  # Limit workers, but don't exceed number of panels

            logger.info(f"Executing queries for {len(panel_queries_map)} panels from dashboard '{dashboard_name}'...")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for panel_id, panel_info in panel_queries_map.items():
                    future = executor.submit(
                        self._execute_panel_queries,  # Pass the QueryBuilder instance
                        panel_info,
                        time_range,
                        signoz_api_processor,
                        query_builder,
                    )
                    futures_map[future] = {"panel_id": panel_id, "panel_title": panel_info["panel_title"]}

                # Collect results
                for future in as_completed(futures_map):
                    context = futures_map[future]
                    try:
                        panel_result = future.result()  # Returns PlaybookTaskResult or None
                        if panel_result:
                            task_results.append(panel_result)
                        else:
                            # Logged within _execute_panel_queries if None is returned due to no data/error
                            pass
                    except Exception as exc:
                        # This catches errors *within* the future execution if not handled internally
                        logger.error(f"Panel execution failed for '{context['panel_title']}' (ID: {context['panel_id']}): {exc}", exc_info=True)
                        # Optionally add an error task result for this panel
                        task_results.append(
                            PlaybookTaskResult(
                                type=PlaybookTaskResultType.ERROR,
                                text=TextResult(output=StringValue(value=f"Failed to execute queries for panel '{context['panel_title']}': {exc}")),
                                source=self.source,
                            )
                        )

            logger.info(f"Finished execution. Collected {len(task_results)} results for dashboard '{dashboard_name}'.")

            # Handle case where no panels yielded any processable data after execution
            if not task_results:
                return [
                    PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(value=f"No data could be processed for any panel in dashboard: {dashboard_name}")),
                        source=self.source,
                    )
                ]

            return task_results

        except Exception as e:
            logger.error(
                f"Critical error during Signoz dashboard data task for '{task.dashboard_name.value if task else 'Unknown'}': {e}", exc_info=True
            )
            return [
                PlaybookTaskResult(
                    type=PlaybookTaskResultType.ERROR,
                    text=TextResult(output=StringValue(value=f"Unexpected error executing dashboard task: {e}")),
                    source=self.source,
                )
            ]
