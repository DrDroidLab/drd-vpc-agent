import json
from google.protobuf.wrappers_pb2 import StringValue, UInt64Value, Int64Value, DoubleValue

from integrations.source_api_processors.elastic_search_api_processor import ElasticSearchApiProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import Source, TimeRange, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, TableResult, PlaybookTaskResultType, TextResult, \
    TimeseriesResult, LabelValuePair
from protos.playbooks.source_task_definitions.elastic_search_task_pb2 import ElasticSearch as ElasticSearchProto
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict


class ElasticSearchSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.ELASTIC_SEARCH
        self.task_proto = ElasticSearchProto
        self.task_type_callable_map = {
            ElasticSearchProto.TaskType.QUERY_LOGS: {
                'executor': self.execute_query_logs,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Query Logs from an ElasticSearch Index',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="index"),
                              display_name=StringValue(value="Index"),
                              description=StringValue(value='Select Index'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="lucene_query"),
                              display_name=StringValue(value="Lucene Query"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                    FormField(key_name=StringValue(value="limit"),
                              display_name=StringValue(value="Enter Limit"),
                              data_type=LiteralType.LONG,
                              default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=2000)),
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="offset"),
                              display_name=StringValue(value="Enter Offset"),
                              data_type=LiteralType.LONG,
                              default_value=Literal(type=LiteralType.LONG, long=Int64Value(value=0)),
                              form_field_type=FormFieldType.TEXT_FT),
                ]
            },
            ElasticSearchProto.TaskType.CHECK_CLUSTER_HEALTH: {
                'executor': self.execute_check_cluster_health,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.TEXT,
                'display_name': 'Check Elasticsearch Cluster Health',
                'category': 'Logs',
                'form_fields': []
            },
            ElasticSearchProto.TaskType.NODE_STATS: {
                'executor': self.execute_node_stats,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Get Elasticsearch Node Stats',
                'category': 'Logs',
                'form_fields': []
            },
            ElasticSearchProto.TaskType.CAT_INDICES: {
                'executor': self.execute_cat_indices,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'List Elasticsearch Indices',
                'category': 'Logs',
                'form_fields': []
            },
            ElasticSearchProto.TaskType.CAT_THREAD_POOL_SEARCH: {
                'executor': self.execute_cat_thread_pool_search,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.LOGS,
                'display_name': 'Get Elasticsearch Thread Pool Search Stats',
                'category': 'Logs',
                'form_fields': []
            },
            ElasticSearchProto.TaskType.MONITORING_CLUSTER_STATS: {
                'executor': self.execute_monitoring_cluster_stats,
                'model_types': [SourceModelType.ELASTIC_SEARCH_INDEX],
                'result_type': PlaybookTaskResultType.TIMESERIES,
                'display_name': 'Get Elasticsearch Monitoring Cluster Stats',
                'category': 'Logs',
                'form_fields': [
                    FormField(key_name=StringValue(value="widget_name"),
                              display_name=StringValue(value="Widget Name"),
                              description=StringValue(value='Enter Widget Name'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="interval"),
                              display_name=StringValue(value="Interval"),
                              description=StringValue(value="Ex. 10s, 1m, 5m, 1h"),
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value="")),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True),
                ]
            },
        }

    def get_connector_processor(self, es_connector, **kwargs):
        generated_credentials = generate_credentials_dict(es_connector.type, es_connector.keys)
        return ElasticSearchApiProcessor(**generated_credentials)

    def execute_query_logs(self, time_range: TimeRange, es_task: ElasticSearchProto,
                           es_connector: ConnectorProto):
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            query_logs = es_task.query_logs
            index = query_logs.index.value
            lucene_query = query_logs.lucene_query.value
            limit = query_logs.limit.value if query_logs.limit.value else 2000
            offset = query_logs.offset.value if query_logs.offset.value else 0
            sort_desc = query_logs.sort_desc.value if query_logs.sort_desc.value else ""
            timestamp_field = query_logs.timestamp_field.value if query_logs.timestamp_field.value else ""
            if not index:
                raise Exception("Task execution Failed:: No index found")

            lucene_query = lucene_query.strip()

            es_client = self.get_connector_processor(es_connector)

            sort = []
            if timestamp_field:
                sort.append({timestamp_field: "desc"})
            if sort_desc:
                sort.append({sort_desc: "desc"})
            sort.append({"_score": "desc"})

            if timestamp_field:
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": lucene_query
                                    }
                                },
                                {
                                    "range": {
                                        timestamp_field: {
                                            "gte": time_range.time_geq * 1000,
                                            "lt": time_range.time_lt * 1000
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "size": limit,
                    "from": offset,
                    "sort": sort
                }
            else:
                query = {
                    "query": {
                        "query_string": {
                            "query": lucene_query
                        }
                    },
                    "size": limit,
                    "from": offset,
                    "sort": sort
                }

            print("Playbook Task Downstream Request: Type -> {}, Account -> {}, Query -> {}".format(
                "ElasticSearch", es_connector.account_id.value, lucene_query), flush=True)

            result = es_client.query(index, query)
            if 'hits' not in result or not result['hits']['hits']:
                raise Exception(f"No data found for the query: {lucene_query}")

            hits = result['hits']['hits']
            count_result = len(hits)
            if count_result == 0:
                raise Exception(f"No data found for the query: {query}")

            table_rows: [TableResult.TableRow] = []
            for hit in hits:
                table_columns = []
                for column, value in hit.items():
                    if column == '_source':
                        try:
                            for key, val in value.items():
                                table_column = TableResult.TableColumn(name=StringValue(value=key),
                                                                       value=StringValue(value=str(val)))
                                table_columns.append(table_column)
                        except Exception as e:
                            table_column = TableResult.TableColumn(name=StringValue(value=column),
                                                                   value=StringValue(value=str(value)))
                            table_columns.append(table_column)
                    else:
                        table_column = TableResult.TableColumn(name=StringValue(value=column),
                                                               value=StringValue(value=str(value)))
                        table_columns.append(table_column)
                table_rows.append(TableResult.TableRow(columns=table_columns))
            table = TableResult(raw_query=StringValue(value=f"Execute ```{lucene_query}``` on index {index}"),
                                total_count=UInt64Value(value=count_result),
                                rows=table_rows)
            return PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=table, source=self.source)
        except Exception as e:
            raise Exception(f"Error while executing ElasticSearch task: {e}")

    def execute_check_cluster_health(self, time_range: TimeRange, es_task: ElasticSearchProto,
                                   es_connector: ConnectorProto):
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            es_client = self.get_connector_processor(es_connector)
            result = es_client.get_cluster_health()
            
            # Extract the key metrics we want to check
            status = result.get('status', 'unknown')
            pending_tasks = result.get('number_of_pending_tasks', 0)
            active_shards_percent = result.get('active_shards_percent_as_number', 0)
            
            # Evaluate the health status
            health_issues = []
            if status == 'red':
                health_issues.append("⚠️ Cluster status is RED - some data is unavailable")
            elif status == 'yellow':
                health_issues.append("⚠️ Cluster status is YELLOW - all data is available but some replicas are not allocated")
                
            if pending_tasks > 10:  # Threshold can be adjusted
                health_issues.append(f"⚠️ High number of pending tasks: {pending_tasks}")
                
            if active_shards_percent < 90:  # Threshold can be adjusted
                health_issues.append(f"⚠️ Low active shards percentage: {active_shards_percent}%")
            
            # Format the output
            output = f"## Elasticsearch Cluster Health\n\n"
            output += f"- **Status**: {status} {'✅' if status == 'green' else '⚠️'}\n"
            output += f"- **Number of Pending Tasks**: {pending_tasks} {'✅' if pending_tasks <= 10 else '⚠️'}\n"
            output += f"- **Active Shards Percent**: {active_shards_percent}% {'✅' if active_shards_percent >= 90 else '⚠️'}\n\n"
            
            if health_issues:
                output += "### Issues Detected:\n\n"
                for issue in health_issues:
                    output += f"- {issue}\n"
            else:
                output += "### No issues detected. Cluster is healthy! ✅\n"
            
            # Include the full health data for reference
            output += "\n### Full Cluster Health Data:\n\n```json\n"
            output += json.dumps(result, indent=2)
            output += "\n```"
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT, 
                text=TextResult(output=StringValue(value=output)),
                source=self.source
            )
        except Exception as e:
            raise Exception(f"Error while checking ElasticSearch cluster health: {e}")
            
    def execute_node_stats(self, time_range: TimeRange, es_task: ElasticSearchProto,
                          es_connector: ConnectorProto):
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            es_client = self.get_connector_processor(es_connector)
            result = es_client.get_nodes_stats()
            
            # Format the output
            output = f"## Elasticsearch Node Stats\n\n"
            
            # Include the full node stats data
            output += "### Full Node Stats Data:\n\n```json\n"
            output += json.dumps(result, indent=2)
            output += "\n```"
            
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TEXT, 
                text=TextResult(output=StringValue(value=output)),
                source=self.source
            )
        except Exception as e:
            raise Exception(f"Error while fetching ElasticSearch node stats: {e}")

    def execute_cat_indices(self, time_range: TimeRange, es_task: ElasticSearchProto,
                           es_connector: ConnectorProto):
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            es_client = self.get_connector_processor(es_connector)
            result = es_client.get_cat_indices()
            
            # Convert to table format
            table_rows = []
            if result and len(result) > 0:
                # Get headers from first item
                headers = list(result[0].keys())
                
                # Create rows
                for item in result:
                    table_columns = []
                    for key in headers:
                        table_column = TableResult.TableColumn(
                            name=StringValue(value=key),
                            value=StringValue(value=str(item.get(key, "")))
                        )
                        table_columns.append(table_column)
                    table_rows.append(TableResult.TableRow(columns=table_columns))
                
                table = TableResult(
                    raw_query=StringValue(value="GET /_cat/indices?v"),
                    total_count=UInt64Value(value=len(result)),
                    rows=table_rows
                )
                return PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=table, source=self.source)
            else:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT, 
                    text=TextResult(output=StringValue(value="No indices found")),
                    source=self.source
                )
        except Exception as e:
            raise Exception(f"Error while fetching ElasticSearch cat indices: {e}")

    def execute_cat_thread_pool_search(self, time_range: TimeRange, es_task: ElasticSearchProto,
                                      es_connector: ConnectorProto):
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            es_client = self.get_connector_processor(es_connector)
            result = es_client.get_cat_thread_pool_search()
            
            # Convert to table format
            table_rows = []
            if result and len(result) > 0:
                # Get headers from first item
                headers = list(result[0].keys())
                
                # Create rows
                for item in result:
                    table_columns = []
                    for key in headers:
                        table_column = TableResult.TableColumn(
                            name=StringValue(value=key),
                            value=StringValue(value=str(item.get(key, "")))
                        )
                        table_columns.append(table_column)
                    table_rows.append(TableResult.TableRow(columns=table_columns))
                
                table = TableResult(
                    raw_query=StringValue(value="GET /_cat/thread_pool/search?v"),
                    total_count=UInt64Value(value=len(result)),
                    rows=table_rows
                )
                return PlaybookTaskResult(type=PlaybookTaskResultType.LOGS, logs=table, source=self.source)
            else:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT, 
                    text=TextResult(output=StringValue(value="No thread pool search data found")),
                    source=self.source
                )
        except Exception as e:
            raise Exception(f"Error while fetching ElasticSearch cat thread pool search: {e}")

    def safe_delta(self, curr_bucket, prev_bucket, key):
        curr_val = curr_bucket.get(key, {}).get("value")
        prev_val = prev_bucket.get(key, {}).get("value")
        if curr_val is None or prev_val is None:
            return None
        return curr_val - prev_val if curr_val >= prev_val else curr_val  # handle resets

    def execute_monitoring_cluster_stats(self, time_range: TimeRange, es_task: ElasticSearchProto,
                                       es_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            if not es_connector:
                raise Exception("Task execution Failed:: No ElasticSearch source found")

            widget_name = ""
            if es_task.monitoring_cluster_stats.widget_name.value:
                widget_name = es_task.monitoring_cluster_stats.widget_name.value.lower()
            interval = es_task.monitoring_cluster_stats.interval.value

            es_client = self.get_connector_processor(es_connector)
            result = es_client.fetch_monitoring_cluster_stats(time_range.time_geq, time_range.time_lt, interval)

            search_rate_datapoints = []
            search_latency_datapoints = []
            indexing_rate_datapoints = []
            indexing_latency_datapoints = []
            indexing_rate_primary_datapoints = []

            buckets = result.get('aggregations', {}).get('per_minute', {}).get('buckets', [])
            if not buckets or len(buckets) < 2:
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.TEXT,
                    text=TextResult(output=StringValue(value="Not enough monitoring data to plot")),
                    source=self.source
                )

            for i in range(1, len(buckets)):
                
                curr = buckets[i]
                prev = buckets[i - 1]
                ts = curr["key"]

                def get_val(key):
                    val = curr.get(key, {}).get("value")
                    return val if val is not None else None

                # Search Rate - derived directly from Elasticsearch via derivative agg
                if get_val("search_rate") is not None:
                    search_rate_val = float(get_val("search_rate")) / 30.0
                    if search_rate_val is not None and (not widget_name or widget_name == "search rate"):
                        search_rate_datapoints.append(
                            TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                timestamp=ts,
                                value=DoubleValue(value=search_rate_val)
                            )
                        )
                
                # Compute deltas
                dq_sum = self.safe_delta( curr, prev, "query_total_sum")
                dqt = self.safe_delta(curr, prev, "query_time_sum")

                # Search Latency = total time / total queries in the interval (ms)
                if dq_sum and dqt is not None and (not widget_name or widget_name == "search latency"):
                    search_latency = dqt / dq_sum if dq_sum > 0 else 0
                    search_latency_datapoints.append(
                        TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=curr["key"],
                            value=DoubleValue(value=search_latency)
                        )
                    )
                
                # Indexing Rate Total- derived directly from Elasticsearch via derivative agg
                if get_val("indexing_rate") is not None:
                    indexing_rate_val = float(get_val("indexing_rate")) / 30.0
                    if indexing_rate_val is not None and (not widget_name or widget_name == "indexing rate"):
                        indexing_rate_datapoints.append(
                            TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                timestamp=ts,
                                value=DoubleValue(value=indexing_rate_val)
                            )
                        )
                
                # Indexing Rate Total- derived directly from Elasticsearch via derivative agg
                if get_val("indexing_rate_primary") is not None:
                    indexing_rate_val = float(get_val("indexing_rate_primary")) / 30.0
                    if indexing_rate_val is not None and (not widget_name or widget_name == "indexing rate"):
                        indexing_rate_primary_datapoints.append(
                            TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                                timestamp=ts,
                                value=DoubleValue(value=indexing_rate_val)
                            )
                        )
                # Indexing latency
                di_sum = self.safe_delta(curr, prev, "index_primary_sum")
                dit = self.safe_delta(curr, prev, "index_time")

                if di_sum and dit is not None and (not widget_name or widget_name == "indexing latency"):
                    indexing_latency = dit / di_sum if di_sum > 0 else 0
                    indexing_latency_datapoints.append(
                        TimeseriesResult.LabeledMetricTimeseries.Datapoint(
                            timestamp=ts,
                            value=DoubleValue(value=indexing_latency)
                        )
                    )

            labeled_metric_timeseries_list = []

            if not widget_name or widget_name == "search rate":
                search_rate_datapoints.sort(key=lambda x: x.timestamp)
                if search_rate_datapoints:
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='metric'), value=StringValue(value='Total Shards'))
                            ],
                            unit=StringValue(value='count/s'),
                            datapoints=search_rate_datapoints
                        )
                    )

            if not widget_name or widget_name == "search latency":
                search_latency_datapoints.sort(key=lambda x: x.timestamp)
                if search_latency_datapoints:
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='metric'), value=StringValue(value='Total Shards'))
                            ],
                            unit=StringValue(value='ms'),
                            datapoints=search_latency_datapoints
                        )
                    )

            if not widget_name or widget_name == "indexing rate":
                # Add Total Shards metric
                indexing_rate_datapoints.sort(key=lambda x: x.timestamp)
                if indexing_rate_datapoints:
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='metric'), value=StringValue(value='Total Shards'))
                            ],
                            unit=StringValue(value='count/s'),
                            datapoints=indexing_rate_datapoints
                        )
                    )
                
                # Add Primary Shards metric
                indexing_rate_primary_datapoints.sort(key=lambda x: x.timestamp)
                if indexing_rate_primary_datapoints:
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='metric'), value=StringValue(value='Primary Shards'))
                            ],
                            unit=StringValue(value='count/s'),
                            datapoints=indexing_rate_primary_datapoints
                        )
                    )

            if not widget_name or widget_name == "indexing latency":
                indexing_latency_datapoints.sort(key=lambda x: x.timestamp)
                if indexing_latency_datapoints:
                    labeled_metric_timeseries_list.append(
                        TimeseriesResult.LabeledMetricTimeseries(
                            metric_label_values=[
                                LabelValuePair(name=StringValue(value='metric'), value=StringValue(value='Primary Shards'))
                            ],
                            unit=StringValue(value='ms'),
                            datapoints=indexing_latency_datapoints
                        )
                    )

            metric_name = 'Elasticsearch Monitoring Metrics'
            if widget_name:
                metric_name = f'Elasticsearch {widget_name.title()}'

            timeseries_result = TimeseriesResult(
                metric_name=StringValue(value=metric_name),
                metric_expression=StringValue(value='Search and Indexing metrics from Elasticsearch'),
                labeled_metric_timeseries=labeled_metric_timeseries_list
            )

            return PlaybookTaskResult(
                type=PlaybookTaskResultType.TIMESERIES,
                source=self.source,
                timeseries=timeseries_result
            )

        except Exception as e:
            raise Exception(f"Error while fetching ElasticSearch monitoring cluster stats: {e}")