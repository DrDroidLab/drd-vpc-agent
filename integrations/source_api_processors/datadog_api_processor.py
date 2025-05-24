import json
import logging

import requests
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.exceptions import ApiException
from datadog_api_client.v1.api.authentication_api import AuthenticationApi
from datadog_api_client.v1.api.aws_integration_api import AWSIntegrationApi
from datadog_api_client.v1.api.aws_logs_integration_api import AWSLogsIntegrationApi
from datadog_api_client.v1.api.azure_integration_api import AzureIntegrationApi
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.model.authentication_validation_response import AuthenticationValidationResponse
from datadog_api_client.v1.model.azure_account_list_response import AzureAccountListResponse
from datadog_api_client.v2.api.cloudflare_integration_api import CloudflareIntegrationApi
from datadog_api_client.v2.api.confluent_cloud_api import ConfluentCloudApi
from datadog_api_client.v2.api.fastly_integration_api import FastlyIntegrationApi
from datadog_api_client.v2.api.gcp_integration_api import GCPIntegrationApi
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.formula_limit import FormulaLimit
from datadog_api_client.v2.model.metrics_data_source import MetricsDataSource
from datadog_api_client.v2.model.metrics_timeseries_query import MetricsTimeseriesQuery
from datadog_api_client.v2.model.query_formula import QueryFormula
from datadog_api_client.v2.model.query_sort_order import QuerySortOrder
from datadog_api_client.v2.model.timeseries_formula_query_request import TimeseriesFormulaQueryRequest
from datadog_api_client.v2.model.timeseries_formula_query_response import TimeseriesFormulaQueryResponse
from datadog_api_client.v2.model.timeseries_formula_request import TimeseriesFormulaRequest
from datadog_api_client.v2.model.timeseries_formula_request_attributes import TimeseriesFormulaRequestAttributes
from datadog_api_client.v2.model.timeseries_formula_request_queries import TimeseriesFormulaRequestQueries
from datadog_api_client.v2.model.timeseries_formula_request_type import TimeseriesFormulaRequestType
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.model.logs_list_request import LogsListRequest
from datadog_api_client.v2.model.logs_list_request_page import LogsListRequestPage
from datadog_api_client.v2.model.logs_query_filter import LogsQueryFilter
from datadog_api_client.v2.model.logs_sort import LogsSort

from protos.base_pb2 import TimeRange
from datetime import datetime, timezone

from integrations.processor import Processor
from utils.http_utils import make_request_with_retry

logger = logging.getLogger(__name__)


class DatadogApiProcessor(Processor):
    def __init__(self, dd_app_key, dd_api_key, dd_api_domain=None):
        self.__dd_app_key = dd_app_key
        self.__dd_api_key = dd_api_key
        self.dd_api_domain = dd_api_domain

        if dd_api_domain:
            self.__dd_host = 'https://api.{}'.format(dd_api_domain)
        else:
            self.__dd_host = 'https://api.{}'.format('datadoghq.com')
        self.dd_dependencies_url = self.__dd_host + "/api/v1/service_dependencies"

        self.headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': dd_api_key,
            'DD-APPLICATION-KEY': dd_app_key,
            'Accept': 'application/json'
        }
        self._QUERY_TEMPLATES_1 = [
            ["sum:trace.django.request.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.django.request.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.django.request{{env:{env},service:{service}}}",
             "p75:trace.django.request{{env:{env},service:{service}}}",
             "p90:trace.django.request{{env:{env},service:{service}}}",
             "p95:trace.django.request{{env:{env},service:{service}}}",
             "p99:trace.django.request{{env:{env},service:{service}}}",
             "p99.9:trace.django.request{{env:{env},service:{service}}}",
             "max:trace.django.request{{env:{env},service:{service}}}"]
        ]
        self._QUERY_TEMPLATES_2 = [
            ["sum:trace.flask.request.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.flask.request.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.flask.request{{env:{env},service:{service}}}",
             "p75:trace.flask.request{{env:{env},service:{service}}}",
             "p90:trace.flask.request{{env:{env},service:{service}}}",
             "p95:trace.flask.request{{env:{env},service:{service}}}",
             "p99:trace.flask.request{{env:{env},service:{service}}}",
             "p99.9:trace.flask.request{{env:{env},service:{service}}}",
             "max:trace.flask.request{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_3 = [
            ["sum:trace.postgres.query.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.postgres.query.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.postgres.query{{env:{env},service:{service}}}",
             "p75:trace.postgres.query{{env:{env},service:{service}}}",
             "p90:trace.postgres.query{{env:{env},service:{service}}}",
             "p95:trace.postgres.query{{env:{env},service:{service}}}",
             "p99:trace.postgres.query{{env:{env},service:{service}}}",
             "p99.9:trace.postgres.query{{env:{env},service:{service}}}",
             "max:trace.postgres.query{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_4 = [
            ["sum:trace.redis.command.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.redis.command.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.redis.command{{env:{env},service:{service}}}",
             "p75:trace.redis.command{{env:{env},service:{service}}}",
             "p90:trace.redis.command{{env:{env},service:{service}}}",
             "p95:trace.redis.command{{env:{env},service:{service}}}",
             "p99:trace.redis.command{{env:{env},service:{service}}}",
             "p99.9:trace.redis.command{{env:{env},service:{service}}}",
             "max:trace.redis.command{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_5 = [
            ["sum:trace.celery.run.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.celery.run.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.celery.run{{env:{env},service:{service}}}",
             "p75:trace.celery.run{{env:{env},service:{service}}}",
             "p90:trace.celery.run{{env:{env},service:{service}}}",
             "p95:trace.celery.run{{env:{env},service:{service}}}",
             "p99:trace.celery.run{{env:{env},service:{service}}}",
             "p99.9:trace.celery.run{{env:{env},service:{service}}}",
             "max:trace.celery.run{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_6 = [
            ["sum:trace.requests.request.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.requests.request.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.requests.request{{env:{env},service:{service}}}",
             "p75:trace.requests.request{{env:{env},service:{service}}}",
             "p90:trace.requests.request{{env:{env},service:{service}}}",
             "p95:trace.requests.request{{env:{env},service:{service}}}",
             "p99:trace.requests.request{{env:{env},service:{service}}}",
             "p99.9:trace.requests.request{{env:{env},service:{service}}}",
             "max:trace.requests.request{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_7 = [
            ["sum:trace.jinja2.request.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.jinja2.request.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.jinja2.request{{env:{env},service:{service}}}",
             "p75:trace.jinja2.request{{env:{env},service:{service}}}",
             "p90:trace.jinja2.request{{env:{env},service:{service}}}",
             "p95:trace.jinja2.request{{env:{env},service:{service}}}",
             "p99:trace.jinja2.request{{env:{env},service:{service}}}",
             "p99.9:trace.jinja2.request{{env:{env},service:{service}}}",
             "max:trace.jinja2.request{{env:{env},service:{service}}}"]
        ] 
        self._QUERY_TEMPLATES_8 = [
            ["sum:trace.s3.command.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.s3.command.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.s3.command{{env:{env},service:{service}}}",
             "p75:trace.s3.command{{env:{env},service:{service}}}",
             "p90:trace.s3.command{{env:{env},service:{service}}}",
             "p95:trace.s3.command{{env:{env},service:{service}}}",
             "p99:trace.s3.command{{env:{env},service:{service}}}",
             "p99.9:trace.s3.command{{env:{env},service:{service}}}",
             "max:trace.s3.command{{env:{env},service:{service}}}"]
        ]
        self._QUERY_TEMPLATES_9 = [
            ["sum:trace.celery.beat.tick.hits{{env:{env},service:{service}}}.as_count()"],
            ["sum:trace.celery.beat.tick.errors{{env:{env},service:{service}}}.as_count()"],
            ["p50:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "p75:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "p90:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "p95:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "p99:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "p99.9:trace.celery.beat.tick{{env:{env},service:{service}}}",
             "max:trace.celery.beat.tick{{env:{env},service:{service}}}"]
        ]

        # Mapping of framework names to their respective query templates 
        # self.map_of_framework_to_query_templates = {
        #     "trace.django.request": self._QUERY_TEMPLATES_1,
        #     "trace.flask.request": self._QUERY_TEMPLATES_2,
        #     "trace.postgres.query": self._QUERY_TEMPLATES_3,
        #     "trace.redis.command": self._QUERY_TEMPLATES_4,
        #     "trace.celery.run": self._QUERY_TEMPLATES_5,
        #     "trace.requests.request": self._QUERY_TEMPLATES_6,
        #     "trace.jinja2.request": self._QUERY_TEMPLATES_7,
        #     "trace.s3.command": self._QUERY_TEMPLATES_8,
        #     "trace.celery.beat": self._QUERY_TEMPLATES_9
        # }

        # Dynamically build the map
        query_templates_list = [
            self._QUERY_TEMPLATES_1,
            self._QUERY_TEMPLATES_2,
            self._QUERY_TEMPLATES_3,
            self._QUERY_TEMPLATES_4,
            self._QUERY_TEMPLATES_5,
            self._QUERY_TEMPLATES_6,
            self._QUERY_TEMPLATES_7,
            self._QUERY_TEMPLATES_8,
            self._QUERY_TEMPLATES_9
        ]

        self.map_of_framework_to_query_templates = {}

        for template in query_templates_list:
            first_query = template[0][0]
            if '.hits' in first_query:
                key = first_query.split('sum:')[1].split('.hits')[0]
            else:
                raise ValueError(f"Unexpected query format (no '.hits' found): {first_query}")

            self.map_of_framework_to_query_templates[key] = template

    def build_queries(self, service_name="*", env="prod", matching_metrics=None):
        """
        Replaces `{service}` and `{env}` placeholders in each query template.
        """
        queries = []
        for metric in matching_metrics:
            framework_key = metric #'.'.join(metric.split('.')[:3])
            if framework_key in self.map_of_framework_to_query_templates:
                query_templates = self.map_of_framework_to_query_templates[framework_key]
                break
        if not query_templates:
            logger.error(f"No query templates found for the metric: {metric}")
            return []

        for template in query_templates:
            if len(template) == 1:
                query = template[0].format(service=service_name, env=env)
                queries.append([query])
            else:
                query_mini_list = []
                for query in template:
                    query = query.format(service=service_name, env=env)
                    query_mini_list.append(query)
                queries.append(query_mini_list)
        return queries
    
    def fetch_query_results(self, service_name="*", env="prod", start_time=None, end_time=None, matching_metrics=None, interval=300000):
        """
        Fetches query results for each generated query string.
        """
        base_url = "https://api.datadoghq.com/api/v1/query"
        
        results = []
        queries = self.build_queries(service_name, env, matching_metrics)
        if not queries:
            logger.error("No queries generated. Please check the service name and matching metrics.")
            return results

        for query_group in queries:  # each sublist
            result = {}
            for query in query_group:
                params = {
                    "from": start_time,
                    "to": end_time,
                    "query": query,
                    "interval": interval
                }
                headers = {
                    "DD-API-KEY": self.__dd_api_key,
                    "DD-APPLICATION-KEY": self.__dd_app_key
                }

                response = requests.get(base_url, params=params, headers=headers)
                if response.ok:
                    result[query] = response.json()
                else:
                    result[query] = {"error": response.text}
            
            results.append(result)  # One dictionary per sublist
        return results
    
    def get_connection(self):
        try:
            configuration = Configuration()
            configuration.api_key["apiKeyAuth"] = self.__dd_api_key
            configuration.api_key["appKeyAuth"] = self.__dd_app_key
            if self.dd_api_domain:
                configuration.server_variables["site"] = self.dd_api_domain
            configuration.unstable_operations["query_timeseries_data"] = True
            configuration.compress = False
            configuration.enable_retry = True
            configuration.max_retries = 20
            return configuration
        except Exception as e:
            logger.error(f"Error while initializing Datadog API Processor: {e}")
            raise Exception("Error while initializing Datadog API Processor: {}".format(e))

    def test_connection(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = AuthenticationApi(api_client)
                response: AuthenticationValidationResponse = api_instance.validate()
                if not response.get('valid', False):
                    raise Exception("Datadog API connection is not valid. Check API Key")
                return True
        except ApiException as e:
            logger.error("Exception when calling AuthenticationApi->validate: %s\n" % e)
            raise e

    def fetch_metric_timeseries(self, tr: TimeRange, specific_metric, interval=300000):
        metric_queries = specific_metric.get('queries', None)
        formulas = specific_metric.get('formulas', None)
        from_tr = int(tr.time_geq * 1000)
        to_tr = int(tr.time_lt * 1000)
        if not metric_queries:
            return None
        query_formulas: [QueryFormula] = []
        if formulas:
            for f in formulas:
                query_formulas.append(
                    QueryFormula(formula=f['formula'], limit=FormulaLimit(count=10, order=QuerySortOrder.DESC)))

        timeseries_queries: [MetricsTimeseriesQuery] = []
        for query in metric_queries:
            timeseries_queries.append(MetricsTimeseriesQuery(
                data_source=MetricsDataSource.METRICS,
                name=query['name'],
                query=query['query']
            ))

        body = TimeseriesFormulaQueryRequest(
            data=TimeseriesFormulaRequest(
                attributes=TimeseriesFormulaRequestAttributes(
                    formulas=query_formulas,
                    _from=from_tr,
                    interval=interval,
                    queries=TimeseriesFormulaRequestQueries(timeseries_queries),
                    to=to_tr,
                ),
                type=TimeseriesFormulaRequestType.TIMESERIES_REQUEST,
            ),
        )
        configuration = self.get_connection()
        with ApiClient(configuration) as api_client:
            api_instance = MetricsApi(api_client)
            try:
                response: TimeseriesFormulaQueryResponse = api_instance.query_timeseries_data(body=body)
                if response:
                    result = response.data.attributes
                    return result
            except Exception as e:
                logger.error(f"Exception occurred while fetching metric timeseries with error: {e}")
                raise e

    def fetch_monitor_details(self, monitor_id):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                response = api_instance.get_monitor(monitor_id)
                return response
        except Exception as e:
            logger.error(f"Exception occurred while fetching monitor details with error: {e}")
            raise e

    def get_metric_data(self, start, end, query):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = MetricsApi(api_client)
                metric_data = api_instance.query_metrics(int(start), int(end), query)
                return metric_data
        except Exception as e:
            logger.error(e)
            raise e

    def get_span_duration_aggregation(self, start, end, query):
        url = self.__dd_host + "/api/v2/spans/analytics/aggregate"

        payload = json.dumps({
            "data": {
                "attributes": {
                    "compute": [
                        {
                            "aggregation": "avg",
                            "interval": "1m",
                            "type": "timeseries"
                        }
                    ],
                    "filter": {
                        "from": start,
                        "query": query,
                        "to": end
                    },
                    "group_by": [
                        {"facet": "resource_name"}
                    ],
                },
                "type": "aggregate_request"
            }
        })

        headers = {
            'DD-APPLICATION-KEY': self.__dd_app_key,
            'DD-API-KEY': self.__dd_api_key,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    def get_span_count_aggregation(self, start, end, query):
        url = self.__dd_host + "/api/v2/spans/analytics/aggregate"

        payload = json.dumps({
            "data": {
                "attributes": {
                    "compute": [
                        {
                            "aggregation": "count",
                            "interval": "1m",
                            "type": "timeseries"
                        }
                    ],
                    "filter": {
                        "from": start,
                        "query": query,
                        "to": end
                    },
                    "group_by": [
                        {"facet": "resource_name"}
                    ],
                },
                "type": "aggregate_request"
            }
        })

        headers = {
            'DD-APPLICATION-KEY': self.__dd_app_key,
            'DD-API-KEY': self.__dd_api_key,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    def search_spans(self, start, end, query, cursor='', limit=10):
        url = self.__dd_host + "/api/v2/spans/events/search"

        payload = json.dumps({
            "data": {
                "attributes": {
                    "filter": {
                        "from": start,
                        "query": query,
                        "to": end
                    },
                    "options": {
                        "timezone": "GMT"
                    },
                    "page": {
                        "cursor": cursor,
                        "limit": limit
                    },
                    "sort": "-timestamp"
                },
                "type": "search_request",
                "cursor": cursor
            }
        })

        headers = {
            'DD-APPLICATION-KEY': self.__dd_app_key,
            'DD-API-KEY': self.__dd_api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = make_request_with_retry("POST", url, headers=headers, payload=payload, default_resend_delay=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"DatadogApiProcessor.search_spans:: Error occurred searching spans with status_code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"DatadogApiProcessor.search_spans:: Exception occurred searching spans with error: {e}")
            raise e

    def get_metric_data_using_api(self, start, end, interval, queries, query_formula):
        url = self.__dd_host + "/api/v2/query/timeseries"
        payload_dict = {"data": {
            "attributes": {"formulas": query_formula, "from": start, "interval": interval * 1000,
                           "queries": queries, "to": end}, "type": "timeseries_request"}}

        result_dict = {}
        print(url, self.headers, payload_dict)
        response = requests.request("POST", url, headers=self.headers, json=payload_dict)
        print("Datadog R2D2 Handler Log:: Query V2 TS API", {"response": response.text})
        logger.info("Datadog R2D2 Handler Log:: Query V2 TS API", {"response": response.status_code})
        if response.status_code == 429:
            logger.info('Datadog R2D2 Handler Log:: Query V2 TS API Response: 429. response.headers', response.headers)

        if response.status_code == 200:
            response_json = json.loads(response.text)
            series = response_json['data']['attributes']['series']
            data = response_json['data']['attributes']['values']
            num_of_series = len(series)
            num_of_data = len(data)
            if num_of_series == num_of_data:
                for i in range(num_of_series):
                    series_labels = series[i]['group_tags']
                    if not series_labels:
                        series_labels = ['*']
                    series_data = data[i]
                    if len(series_labels) == len(series_data):
                        for j in range(len(series_labels)):
                            result_dict[series_labels[j]] = series_data[j]
        return result_dict

    def get_downstream_services(self, service_name, env):
        if not env:
            env = 'prod'
        url = self.dd_dependencies_url + "/{}?env={}".format(service_name, env)
        response = requests.request("GET", url, headers=self.headers)
        return json.loads(response.text).get('calls', [])

    def get_upstream_services(self, service_name, env):
        if not env:
            env = 'prod'
        url = self.dd_dependencies_url + "/{}?env={}".format(service_name, env)
        response = requests.request("GET", url, headers=self.headers)
        print('get_upstream_services response', response.status_code)
        return json.loads(response.text).get('called_by', [])

    def fetch_monitors(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = MonitorsApi(api_client)
                response = api_instance.list_monitors()
                return response
        except Exception as e:
            logger.error(f"Exception occurred while fetching monitors with error: {e}")
            raise e

    def fetch_dashboards(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = DashboardsApi(api_client)
                response = api_instance.list_dashboards()
                return response.to_dict()
        except Exception as e:
            logger.error(f"Exception occurred while fetching dashboards with error: {e}")
            raise e

    def fetch_dashboard_details(self, dashboard_id):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = DashboardsApi(api_client)
                response = api_instance.get_dashboard(
                    dashboard_id=dashboard_id,
                )
                return response.to_dict()
        except Exception as e:
            logger.error(f"Exception occurred while fetching dashboard details with error: {e}")
            raise e

    def fetch_aws_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = AWSIntegrationApi(api_client)
                response = api_instance.list_aws_accounts()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling AWSIntegrationApi->list_aws_accounts: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching AWS integrations with error: {e}")
            raise e

    def fetch_aws_log_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = AWSLogsIntegrationApi(api_client)
                response = api_instance.list_aws_logs_integrations()
                return response
        except ApiException as e:
            logger.error("Exception when calling AWSLogsIntegrationApi->list_aws_logs_integrations: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching AWS log integrations with error: {e}")
            raise e

    def fetch_azure_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = AzureIntegrationApi(api_client)
                response: AzureAccountListResponse = api_instance.list_azure_integration()
                return response
        except ApiException as e:
            logger.error("Exception when calling AzureIntegrationApi->list_azure_integration: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching Azure integrations with error: {e}")
            raise e

    def fetch_cloudflare_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = CloudflareIntegrationApi(api_client)
                response = api_instance.list_cloudflare_accounts()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling CloudflareIntegrationApi->list_cloudflare_accounts: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching Cloudflare integrations with error: {e}")
            raise e

    def fetch_confluent_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = ConfluentCloudApi(api_client)
                response = api_instance.list_confluent_account()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling ConfluentCloudApi->list_confluent_account: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching Confluent integrations with error: {e}")
            raise e

    def fetch_fastly_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = FastlyIntegrationApi(api_client)
                response = api_instance.list_fastly_accounts()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling FastlyIntegrationApi->list_fastly_accounts: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching Fastly integrations with error: {e}")
            raise e

    def fetch_gcp_integrations(self):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = GCPIntegrationApi(api_client)
                response = api_instance.list_gcpsts_accounts()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling GCPIntegrationApi->list_gcpsts_accounts: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching GCP integrations with error: {e}")
            raise e

    def fetch_service_map(self, env, start=None, end=None):
        try:
            if not env:
                env = 'prod'
            url = self.dd_dependencies_url + "/?env={}".format(env)
            if start and end:
                url += "&start={}&end={}".format(int(start), int(end))

            response = requests.request("GET", url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Exception occurred while fetching service map with error: {e}")
            raise e

    def fetch_metrics(self, filter_tags=None):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = MetricsApi(api_client)
                if filter_tags:
                    response = api_instance.list_tag_configurations(filter_tags=filter_tags)
                else:
                    response = api_instance.list_tag_configurations()
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling MetricsApi->list_tag_configurations: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching metrics with error: {e}")
            raise e

    def fetch_metric_tags(self, metric_name):
        try:
            configuration = self.get_connection()
            with ApiClient(configuration) as api_client:
                api_instance = MetricsApi(api_client)
                response = api_instance.list_tags_by_metric_name(metric_name=metric_name)
                return response.to_dict()
        except ApiException as e:
            logger.error("Exception when calling MetricsApi->list_tags_by_metric_name: %s\n" % e)
            raise e
        except Exception as e:
            logger.error("Exception occurred while fetching metric tags with error: %s\n" % e)
            raise e

    def fetch_logs(self, query, tr: TimeRange):
        try:
            configuration = self.get_connection()
            from_tr = str(tr.time_geq * 1000)
            to_tr = str(tr.time_lt * 1000)
            body = LogsListRequest(
                filter=LogsQueryFilter(
                    query=query,
                    _from=from_tr,
                    to=to_tr,
                ),
                sort=LogsSort.TIMESTAMP_DESCENDING,
                page=LogsListRequestPage(
                    limit=1000,
                ),
            )
            with ApiClient(configuration) as api_client:
                api_instance = LogsApi(api_client)
                response = api_instance.list_logs(body=body)
                result = response.data
                return result

        except ApiException as e:
            logger.error("Exception when calling LogsApi->list_logs: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching logs with error: {e}")
            raise e
    

    def widget_query_timeseries_points_api(self, tr: TimeRange, queries, formulas, resource_type=None, interval_ms=None):
        try:
            request_type = 'scalar_request'
            url = self.__dd_host + "/api/v2/query/scalar"
            attribute_payload = {'queries': queries, 'formulas': formulas}
            from_tr = int(tr.time_geq * 1000)
            to_tr = int(tr.time_lt * 1000)
            attribute_payload['from'] = from_tr
            attribute_payload['to'] = to_tr

            if resource_type == 'timeseries':
                url = self.__dd_host + "/api/v2/query/timeseries"
                # Only set interval if explicitly provided
                if interval_ms:
                    attribute_payload['interval'] = interval_ms
                    logger.info(f"Using provided interval of {interval_ms} ms for time range: {from_tr} to {to_tr}")
                else:
                    logger.info(f"Letting Datadog API determine the appropriate interval for time range: {from_tr} to {to_tr}")
                request_type = 'timeseries_request'
            
            payload = {'data': {'attributes': attribute_payload, 'type': request_type}}
            response = requests.request("POST", url, headers=self.headers, json=payload)
            if response.status_code == 429:
                logger.info('Datadog R2D2 Handler Log:: Query V2 TS API Response: 429. response.headers',
                            response.headers)
                return None
            elif response.status_code == 200:
                response_json = json.loads(response.text)
                return response_json
            else:
                logger.error(f"Datadog R2D2 Handler Log:: Query V2 TS API Response: {response.status_code}. "
                             f"response.text: {response.text}")
            return None
        except ApiException as e:
            logger.error("Exception when calling MetricsApi->metric: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching metric with error: {e}")
            raise e

    def widget_query_logs_stream_api(self, tr: TimeRange, query_string: str, limit: int = 1000):
        """
        Queries logs data for a widget of type 'list_stream' using the logs/events/search API.

        :param tr: TimeRange object with time_geq and time_lt attributes (Unix time in seconds).
        :param query_string: Log query string from the widget (e.g., 'service:holocron-celery-worker AND investigation_session_id:abc123').
        :param limit: Max number of logs to retrieve (default is 1000).
        :return: Parsed JSON response or None on failure.
        """
        try:
            url = self.__dd_host + "/api/v2/logs/events/search"
            payload = {
                "filter": {
                    "from": datetime.fromtimestamp(tr.time_geq, tz=timezone.utc).isoformat(),
                    "to": datetime.fromtimestamp(tr.time_lt, tz=timezone.utc).isoformat(),

                    "query": "service:holocron-celery-worker"#query_string
                },
                "sort": "desc",
                "page": {
                    "limit": limit
                }
            }

            response = requests.request("POST", url, headers=self.headers, json=payload)

            if response.status_code == 429:
                logger.warning('Datadog R2D2 Handler Log:: Logs Stream API Response: 429 - Rate Limited. Headers: %s',
                            response.headers)
                return None
            elif response.status_code == 200:
                response_json = json.loads(response.text)
                return response_json
            else:
                logger.error(f"Datadog R2D2 Handler Log:: Logs Stream API Response: {response.status_code}. "
                            f"Response Body: {response.text}")
                return None

        except ApiException as e:
            logger.error("Exception when calling LogsApi->logs_search: %s\n" % e)
            raise e
        except Exception as e:
            logger.error(f"Exception occurred while fetching logs stream data: {e}")
            raise e
