import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import partial

from google.protobuf.struct_pb2 import Struct
from google.protobuf.wrappers_pb2 import Int64Value, StringValue, UInt64Value

from integrations.source_api_processors.sentry_api_processor import SentryApiProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import Literal, LiteralType
from protos.playbooks.playbook_commons_pb2 import ApiResponseResult, PlaybookTaskResult, PlaybookTaskResultType, TableResult, TextResult
from protos.playbooks.source_task_definitions.sentry_task_pb2 import Sentry
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict
from utils.proto_utils import dict_to_proto

logger = logging.getLogger(__name__)


class SentrySourceManager(SourceManager):
    def __init__(self):
        self.source = Source.SENTRY
        self.task_proto = Sentry
        self.task_type_callable_map = {
            Sentry.TaskType.FETCH_ISSUE_INFO_BY_ID: {
                "executor": self.fetch_issue_info_by_id,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Fetch Sentry Issue Related info",
                "category": "Error",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="issue_id"),
                        display_name=StringValue(value="Issue ID"),
                        description=StringValue(value="Enter Issue ID"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
            Sentry.TaskType.FETCH_EVENT_INFO_BY_ID: {
                "executor": self.fetch_event_info_by_id,
                "model_types": [],
                "result_type": PlaybookTaskResultType.API_RESPONSE,
                "display_name": "Fetch Sentry Event Info by ID",
                "category": "Error",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="event_id"),
                        display_name=StringValue(value="Event ID"),
                        description=StringValue(value="Enter Event ID"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="project_slug"),
                        display_name=StringValue(value="Project Slug"),
                        description=StringValue(value="Enter Project Slug"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
            Sentry.TaskType.FETCH_LIST_OF_RECENT_EVENTS_WITH_SEARCH_QUERY: {
                "executor": self.fetch_list_of_recent_events_with_search_query,
                "model_types": [],
                "result_type": PlaybookTaskResultType.LOGS,
                "display_name": "Fetch List of Recent Events with Search Query",
                "category": "Error",
                "form_fields": [
                    FormField(
                        key_name=StringValue(value="project_slug"),
                        display_name=StringValue(value="Project Slug"),
                        description=StringValue(value="Enter Project Slug"),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="query"),
                        display_name=StringValue(value="Query"),
                        description=StringValue(value="Enter Query"),
                        default_value=Literal(type=LiteralType.STRING, string=StringValue(value="is:unresolved")),
                        data_type=LiteralType.STRING,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                    FormField(
                        key_name=StringValue(value="max_events_to_analyse"),
                        display_name=StringValue(value="Max Events to Analyse"),
                        description=StringValue(value="Enter Max Events to Analyse"),
                        default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=10)),
                        data_type=LiteralType.LONG,
                        form_field_type=FormFieldType.TEXT_FT,
                    ),
                ],
            },
        }

    def get_connector_processor(self, sentry_connector, **kwargs):
        generated_credentials = generate_credentials_dict(sentry_connector.type, sentry_connector.keys)
        return SentryApiProcessor(**generated_credentials)

    def fetch_issue_info_by_id(self, time_range: TimeRange, sentry_task: Sentry, sentry_connector: ConnectorProto):
        try:
            if not sentry_connector:
                raise Exception("Task execution Failed:: No Sentry source found")
            task = sentry_task.fetch_issue_info_by_id
            issue_id = task.issue_id.value

            sentry_processor = self.get_connector_processor(sentry_connector)
            issue_details = sentry_processor.fetch_issue_details(issue_id)
            issue_hash_0 = sentry_processor.fetch_issue_last_event(issue_id)
            first_seen = issue_details["firstSeen"]
            last_seen = issue_details["lastSeen"]
            slug = issue_details.get("project", {}).get("slug", "")
            is_unhandled = issue_details.get("isUnhandled", False)
            users_impacted = len(issue_details["seenBy"])
            exception_entries = list(filter(lambda x: x["type"] == "exception", issue_hash_0["latestEvent"]["entries"]))
            count_exception_entries = len(exception_entries)
            tags = issue_hash_0["latestEvent"]["tags"]
            if count_exception_entries > 0:
                exception_counts = len(exception_entries[0]["data"]["values"])
                stack_trace = issue_hash_0["latestEvent"]["metadata"]
                culprit = issue_hash_0["latestEvent"]["culprit"]
            else:
                exception_counts = 0
                stack_trace = {}
                culprit = issue_hash_0["latestEvent"]["culprit"]
            request_entries = list(filter(lambda x: x["type"] == "request", issue_hash_0["latestEvent"]["entries"]))
            count_request_entries = len(request_entries)
            if count_request_entries > 0:
                url = request_entries[0]["data"]["url"]
            else:
                url = None
            response_dict = {
                "first_seen": first_seen,
                "last_seen": last_seen,
                "users_impacted": users_impacted,
                "exception_counts": exception_counts,
                "count_exception_entries": count_exception_entries,
                "stack_trace": stack_trace,
                "culprit": culprit,
                "tags": tags,
                "url": url,
                "project_slug": slug,
                "isUnhandled": is_unhandled,
            }  # VG: Added project_slug
            response_struct = dict_to_proto(response_dict, Struct)
            sentry_issue_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(type=PlaybookTaskResultType.API_RESPONSE, source=self.source, api_response=sentry_issue_output)

        except Exception as e:
            logger.error(f"Exception occurred while Sentry fetch_issue_info_by_id details with error: {e}")
            raise e

    def fetch_event_info_by_id(self, time_range: TimeRange, sentry_task: Sentry, sentry_connector: ConnectorProto):
        try:
            if not sentry_connector:
                raise Exception("Task execution Failed:: No Sentry source found")

            task = sentry_task.fetch_event_info_by_id
            event_id = task.event_id.value
            project_slug = task.project_slug.value if task.HasField("project_slug") else None

            sentry_processor = self.get_connector_processor(sentry_connector)
            event_details = sentry_processor.fetch_event_details(event_id, project_slug)

            if not event_details:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"No event found with ID: {event_id}")),
                    source=self.source,
                )

            # Convert the event details to a structured format
            response_dict = {
                "event_id": event_details.get("eventID", ""),
                "project": event_details.get("project", {}).get("slug", ""),
                "timestamp": event_details.get("dateCreated", ""),
                "message": event_details.get("message", ""),
                "title": event_details.get("title", ""),
                "tags": event_details.get("tags", []),
                "contexts": event_details.get("contexts", {}),
                "entries": [{"type": entry.get("type", ""), "data": entry.get("data", {})} for entry in event_details.get("entries", [])],
                "metadata": event_details.get("metadata", {}),
                "user": event_details.get("user", {}),
                "sdk": event_details.get("sdk", {}),
                "url": f"https://sentry.io/organizations/{sentry_processor.org_slug}/issues/{event_id}/",
            }

            response_struct = dict_to_proto(response_dict, Struct)
            event_output = ApiResponseResult(response_body=response_struct)

            return PlaybookTaskResult(type=PlaybookTaskResultType.API_RESPONSE, source=self.source, api_response=event_output)

        except Exception as e:
            logger.error(f"Exception occurred while fetching Sentry event details with error: {e}")
            raise e

    def fetch_list_of_recent_events_with_search_query(self, time_range: TimeRange, sentry_task: Sentry, sentry_connector: ConnectorProto):
        try:
            if not sentry_connector:
                raise Exception("Task execution Failed:: No Sentry source found")

            task = sentry_task.fetch_list_of_recent_events_with_search_query
            project_slug = task.project_slug.value
            query = task.query.value
            max_events_to_analyse = task.max_events_to_analyse.value

            sentry_processor = self.get_connector_processor(sentry_connector)

            start_time = datetime.fromtimestamp(time_range.time_geq, tz=timezone.utc).isoformat()
            end_time = datetime.fromtimestamp(time_range.time_lt, tz=timezone.utc).isoformat()

            # Get issues with the specified tag
            issues = sentry_processor.fetch_issues_with_query(project_slug, query, start_time, end_time)
            if not issues:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"No issues found with {query} for project: {project_slug}")),
                    source=self.source,
                )

            # filter issues where last_seen is not between start and end time. last seen is in this format -- '2025-03-20T18:19:36.613837Z' .
            issues = [
                issue
                for issue in issues
                if issue.get("lastSeen", "")
                and datetime.fromisoformat(start_time) <= datetime.fromisoformat(issue.get("lastSeen", "").replace("Z", "+00:00"))
            ]
            # each issue is a dictionary with keys like 'id', 'lastSeen'. sort in descending by 'last_seen'
            issues = sorted(issues, key=lambda x: x.get("lastSeen", 0), reverse=True)

            if not issues:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value=f"No issues found with {query} for project: {project_slug}")),
                    source=self.source,
                )

            all_events = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                process = partial(self.process_issue, time_range=time_range, sentry_processor=sentry_processor, project_slug=project_slug)
                futures = [executor.submit(process, issue) for issue in issues]
                for future in as_completed(futures):
                    all_events.extend(future.result())

            # Select 10 random events from the filtered list
            if len(all_events) > max_events_to_analyse:
                top_events = random.sample(all_events, max_events_to_analyse)
            else:
                top_events = all_events

            # Sort the selected events by timestamp in descending order
            top_events = sorted(top_events, key=lambda x: x.get("dateCreated", ""), reverse=True)

            # Create table rows for each event
            table_rows: [TableResult.TableRow] = []

            ## fetch the entire payload of every event, then add the issue_id and respective issue_count in the event.
            events_list = []
            for event in top_events:
                # Get event-specific URL
                event_id = event.get("eventID", "")
                # Get detailed event information
                event_details = sentry_processor.fetch_event_details(event_id, project_slug)
                event_details["issue_id"] = event.get("issue_id", "")
                event_details["issue_count"] = len([e for e in all_events if e.get("issue_id") == event.get("issue_id")])

                # Extract stack trace if available
                if event_details:
                    # Look for exception entries
                    exception_entries = [entry for entry in event_details.get("entries", []) if entry.get("type") == "exception"]
                    if exception_entries and "data" in exception_entries[0] and "values" in exception_entries[0]["data"]:
                        exception_value = exception_entries[0]["data"]["values"][0]
                        stacktrace = exception_value.get("stacktrace")
                        if stacktrace and isinstance(stacktrace, dict):
                            frames = stacktrace.get("frames", [])
                            if frames:
                                # Iterate over all frames and format them
                                stack_traces = [
                                    f"{frame.get('filename', 'Unknown')}:{frame.get('lineno', '?')} in {frame.get('function', 'Unknown')}"
                                    for frame in frames
                                ]
                                # Join all formatted frames into a single string (separated by newline or any delimiter)
                                full_stack_trace = "\n".join(stack_traces)
                                event_details["stack_trace"] = full_stack_trace
                events_list.append(event_details)

            # translate the events_list to a table assuming whatever keys in it as the default columns
            for event in events_list:
                table_columns: [TableResult.TableColumn] = []
                for key, value in event.items():
                    table_column = TableResult.TableColumn(name=StringValue(value=key), value=StringValue(value=str(value)))
                    table_columns.append(table_column)
                table_row = TableResult.TableRow(columns=table_columns)
                table_rows.append(table_row)

            # Create the table result
            result = TableResult(
                raw_query=StringValue(
                    value=f"Project: {project_slug}, Query: {query}, Total Events: {len(all_events)}, Showing: {len(top_events)} random events since {start_time}"
                ),
                rows=table_rows,
                total_count=UInt64Value(value=len(table_rows)),
            )

            # Return the logs result
            return PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=result, source=self.source)

        except Exception as e:
            logger.error(f"Exception occurred while fetching Sentry event details with tag with error: {e}")
            raise e

    def process_issue(self, issue, time_range, sentry_processor, project_slug):
        issue_id = issue.get("id")
        start_time_dt = datetime.fromtimestamp(time_range.time_geq, tz=timezone.utc)
        end_time_dt = datetime.fromtimestamp(time_range.time_lt, tz=timezone.utc)

        try:
            events = sentry_processor.fetch_events_inside_issue(issue_id, project_slug, start_time=start_time_dt, end_time=end_time_dt)
            filtered = [
                event
                for event in events
                if start_time_dt <= datetime.fromisoformat(event.get("dateCreated", "").replace("Z", "+00:00")) <= end_time_dt
            ]
            for event in filtered:
                event["issue_id"] = issue_id
            return filtered
        except Exception as e:
            logger.error(f"Failed to process issue {issue_id}: {e}")
            return []
