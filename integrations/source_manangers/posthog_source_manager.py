import json
import logging
from datetime import datetime
from typing import Optional

from google.protobuf.json_format import MessageToDict
from google.protobuf.wrappers_pb2 import StringValue, UInt64Value

from integrations.source_api_processors.posthog_api_processor import PosthogApiProcessor
from integrations.source_manager import SourceManager
from protos.assets.asset_pb2 import AccountConnectorAssets, AccountConnectorAssetsModelFilters
from protos.assets.posthog_asset_pb2 import PosthogAssetModel
from protos.base_pb2 import Source, SourceModelType, TimeRange
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType, TableResult, TextResult
from protos.playbooks.source_task_definitions.posthog_task_pb2 import PostHog
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict
from utils.playbooks_client import PrototypeClient
from utils.proto_utils import dict_to_proto
from utils.string_utils import is_partial_match

logger = logging.getLogger(__name__)


class PosthogSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.POSTHOG
        self.task_proto = PostHog
        self.task_type_callable_map = {
            PostHog.TaskType.HOGQL_QUERY: {
                "executor": self.execute_hogql_query,
                "asset_descriptor": self.posthog_property_asset_descriptor,
                "model_types": [SourceModelType.POSTHOG_PROPERTY],
                "result_type": PlaybookTaskResultType.TABLE,
                "display_name": "Execute HogQL Query to get events",
                "category": "Events",
                "form_fields": [
                    FormField(key_name=StringValue(value="query"),
                              display_name=StringValue(value="HogQL Query"),
                              description=StringValue(value="Enter your HogQL query"),
                              data_type=LiteralType.STRING,
                              is_optional=False,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
        }

    def get_connector_processor(self, posthog_connector, **kwargs):
        generated_credentials = generate_credentials_dict(posthog_connector.type, posthog_connector.keys)
        return PosthogApiProcessor(**generated_credentials)

    @staticmethod
    def posthog_property_asset_descriptor(posthog_connector: ConnectorProto, filters: Optional[dict] = None):
        """Generate a text description of PostHog properties to help the LLM craft queries"""
        try:
            prototype_client = PrototypeClient()
            property_assets: AccountConnectorAssets = prototype_client.get_connector_assets(
                posthog_connector,
                SourceModelType.POSTHOG_PROPERTY,
                AccountConnectorAssetsModelFilters()
            )
            property_assets = property_assets["assets"][0]["posthog"]["assets"]
            property_assets = dict_to_proto(property_assets, PosthogAssetModel)
            if not property_assets:
                logger.warning(f"PosthogSourceManager.posthog_property_asset_descriptor:: No property assets found for "
                               f"account: {posthog_connector.account_id.value}, connector: {posthog_connector.id.value}")
                return ""
                
            property_assets = property_assets[0]
            posthog_assets = property_assets.posthog.assets
            all_property_assets = [asset.posthog_property for asset in posthog_assets if 
                                   asset.type == SourceModelType.POSTHOG_PROPERTY]
            
            asset_list_string = "Available PostHog Properties:\n"
            filtered_asset_list = ""
            
            # Group properties by type
            property_by_type = {}
            for asset in all_property_assets:
                prop_type = asset.property_type.value if asset.HasField("property_type") and asset.property_type.value else "Other"
                if prop_type not in property_by_type:
                    property_by_type[prop_type] = []
                property_by_type[prop_type].append(asset)
                
            # Format the property information
            for prop_type, assets in property_by_type.items():
                asset_list_string += f"\n## {prop_type} Properties\n"
                
                for asset in assets:
                    prop_name = asset.name.value
                    is_numerical = "Numerical" if asset.is_numerical.value else "String"
                    
                    tags_str = ""
                    if asset.tags:
                        tags_str = f", Tags: `{', '.join(asset.tags)}`"
                        
                    asset_string = f"- `{prop_name}` ({is_numerical}{tags_str})\n"
                    asset_list_string += asset_string
                    
                    # Apply filters if provided
                    if filters and "property_names" in filters and is_partial_match(prop_name, filters["property_names"]):
                        filtered_asset_list += asset_string
                
            # Return filtered list if filters were applied
            if filtered_asset_list:
                return filtered_asset_list
                
            return asset_list_string
            
        except Exception as e:
            logger.error(f"PosthogSourceManager.posthog_property_asset_descriptor:: Error while generating "
                         f"property asset descriptor for account: {posthog_connector.account_id.value}, connector: "
                         f"{posthog_connector.id.value} with error: {e}")
        return ""

    def execute_event_query(self, time_range: TimeRange, ph_task: PostHog,
                            posthog_connector: ConnectorProto):
        try:
            if not posthog_connector:
                raise Exception("Task execution Failed:: No PostAog source found")
            start_time = datetime.utcfromtimestamp(time_range.time_geq)
            end_time = datetime.utcfromtimestamp(time_range.time_lt)

            task = ph_task.event_query
            event_name = task.event_name.value if task.HasField("event_name") else None
            person_id = task.person_id.value if task.HasField("person_id") else None
            limit = task.limit.value if task.HasField("limit") else 100
            # Handle properties if provided
            properties = None
            if task.HasField("properties"):  # Ensures `properties` is set
                try:
                    print(f"Properties type: {type(task.properties)}")
                    
                    # Convert ListValue to a native Python list
                    properties_dict = MessageToDict(task.properties)
                    print(f"Properties dict: {properties_dict}")

                    if isinstance(properties_dict, list):
                        properties = properties_dict
                    elif isinstance(properties_dict, dict) and "values" in properties_dict:
                        properties = properties_dict["values"]
                    else:
                        properties = []
                        
                    print(f"Final properties: {properties}")

                except Exception as e:
                    logger.error(f"Error parsing properties: {e}")
                    return PlaybookTaskResult(
                        type=PlaybookTaskResultType.TEXT,
                        text=TextResult(output=StringValue(value=f"Error parsing properties: {e}")),
                        source=self.source
                    )
            posthog_api_processor = self.get_connector_processor(posthog_connector)
            events = posthog_api_processor.fetch_events(
                event_name=event_name,
                properties=properties,
                person_id=person_id,
                limit=limit,
                before=start_time,
                after=end_time,
            )
            if not events:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="No events returned from PostHog for the given criteria")),
                    source=self.source
                )

            table_rows = []
            for event in events:
                # Extract columns
                event_columns = []

                event_columns.append(TableResult.TableColumn(
                    name=StringValue(value="event"),
                    value=StringValue(value=event.get("event", ""))
                ))
                
                event_columns.append(TableResult.TableColumn(
                    name=StringValue(value="distinct_id"),
                    value=StringValue(value=event.get("distinct_id", ""))
                ))

                event_columns.append(TableResult.TableColumn(
                    name=StringValue(value="timestamp"),
                    value=StringValue(value=event.get("timestamp", ""))
                ))
                
                properties = event.get("properties", {})
                properties_json = json.dumps(properties)
                event_columns.append(TableResult.TableColumn(
                    name=StringValue(value="properties"),
                    value=StringValue(value=properties_json)
                ))

                for prop_key, prop_value in properties.items():
                    if isinstance(prop_value, (dict, list)):
                        prop_value = json.dumps(prop_value)
                    elif not isinstance(prop_value, str):
                        prop_value = str(prop_value)
                    
                    event_columns.append(TableResult.TableColumn(
                        name=StringValue(value=f"prop_{prop_key}"),
                        value=StringValue(value=prop_value)
                    ))
                
                # Add row
                table_rows.append(TableResult.TableRow(columns=event_columns))
            
            # Create table result
            query_description = f"Event: {event_name or 'All'}"
            if start_time:
                query_description += f", After: {start_time}"
            if end_time:
                query_description += f", Before: {end_time}"

            table_result = TableResult(
                raw_query=StringValue(value=query_description),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TABLE,
                table=table_result,
                source=self.source
            )
            
        except Exception as e:
            logger.error(f"Error while executing PostHog task: {e}")
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT,
                text=TextResult(output=StringValue(value=f"Error while executing PostHog task: {e}")),
                source=self.source
            )

    def execute_hogql_query(self, time_range: TimeRange, ph_task: PostHog,
                           posthog_connector: ConnectorProto):
        try:
            if not posthog_connector:
                raise Exception("Task execution Failed:: No PostHog source found")

            task = ph_task.hogql_query
            if not task.HasField("query") or not task.query.value:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="No query provided for HogQL execution")),
                    source=self.source
                )
                
            query = task.query.value
            
            # Get the PostHog API processor
            posthog_api_processor = self.get_connector_processor(posthog_connector)
            # Execute the HogQL query
            query_result = posthog_api_processor.execute_hogql_query(query)
            # Check for errors
            if "error" in query_result:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=query_result["error"])),
                    source=self.source
                )
                
            # Get results and columns
            results = query_result.get("results", [])
            columns = query_result.get("columns", [])
            
            if not results:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="No results returned from HogQL query")),
                    source=self.source
                )
                
            # Create table rows
            table_rows = []
            for result_row in results:
                row_columns = []
                
                # Add each column value to the row
                for i, column_name in enumerate(columns):
                    value = result_row[i] if i < len(result_row) else ""
                    
                    # Convert non-string values to string
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    elif value is None:
                        value = "NULL"
                    elif not isinstance(value, str):
                        value = str(value)
                        
                    row_columns.append(TableResult.TableColumn(
                        name=StringValue(value=column_name),
                        value=StringValue(value=value)
                    ))
                
                # Add row to table
                table_rows.append(TableResult.TableRow(columns=row_columns))
            
            # Create table result
            table_result = TableResult(
                raw_query=StringValue(value=query),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TABLE,
                table=table_result,
                source=self.source
            )
            
        except Exception as e:
            logger.error(f"Error while executing PostHog HogQL query: {e}")
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT,
                text=TextResult(output=StringValue(value=f"Error while executing PostHog HogQL query: {e}")),
                source=self.source
            )
