from protos.base_pb2 import Source, SourceKeyType, SourceModelType

integrations_connector_type_connector_keys_map = {
    Source.PAGER_DUTY: [
        [
            SourceKeyType.PAGER_DUTY_API_KEY,
            SourceKeyType.PAGER_DUTY_CONFIGURED_EMAIL
        ]
    ],
    Source.ROOTLY: [
        [
            SourceKeyType.ROOTLY_API_KEY,
        ]
    ],
    Source.ZENDUTY: [
        [
            SourceKeyType.ZENDUTY_API_KEY,
        ]
    ],
    Source.SLACK: [
        [
            SourceKeyType.SLACK_BOT_AUTH_TOKEN,
            SourceKeyType.SLACK_APP_ID
        ]
    ],
    Source.NEW_RELIC: [
        [
            SourceKeyType.NEWRELIC_API_KEY,
            SourceKeyType.NEWRELIC_APP_ID,
            SourceKeyType.NEWRELIC_API_DOMAIN
        ]
    ],
    Source.DATADOG: [
        [
            SourceKeyType.DATADOG_API_KEY,
            SourceKeyType.DATADOG_APP_KEY,
            SourceKeyType.DATADOG_API_DOMAIN
        ]
    ],
    Source.DATADOG_OAUTH: [
        [
            SourceKeyType.DATADOG_AUTH_TOKEN,
            SourceKeyType.DATADOG_API_DOMAIN,
            SourceKeyType.DATADOG_API_KEY
        ]
    ],
    Source.GRAFANA: [
        [
            SourceKeyType.GRAFANA_HOST,
            SourceKeyType.GRAFANA_API_KEY,
            SourceKeyType.SSL_VERIFY,
        ],
        [
            SourceKeyType.GRAFANA_HOST,
            SourceKeyType.GRAFANA_API_KEY
        ]
    ],
    Source.GRAFANA_VPC: [
        [
            SourceKeyType.AGENT_PROXY_HOST,
            SourceKeyType.AGENT_PROXY_API_KEY
        ]
    ],
    Source.AGENT_PROXY: [
        [
            SourceKeyType.AGENT_PROXY_HOST,
            SourceKeyType.AGENT_PROXY_API_KEY
        ]
    ],
    Source.CLOUDWATCH: [
        [
            SourceKeyType.AWS_ACCESS_KEY,
            SourceKeyType.AWS_SECRET_KEY,
            SourceKeyType.AWS_REGION,
        ],
        [
            SourceKeyType.AWS_ASSUMED_ROLE_ARN,
            SourceKeyType.AWS_REGION,
        ]
    ],
    Source.CLICKHOUSE: [
        [
            SourceKeyType.CLICKHOUSE_INTERFACE,
            SourceKeyType.CLICKHOUSE_HOST,
            SourceKeyType.CLICKHOUSE_PORT,
            SourceKeyType.CLICKHOUSE_USER,
            SourceKeyType.CLICKHOUSE_PASSWORD
        ]
    ],
    Source.POSTGRES: [
        [
            SourceKeyType.POSTGRES_HOST,
            SourceKeyType.POSTGRES_USER,
            SourceKeyType.POSTGRES_PASSWORD,
            SourceKeyType.POSTGRES_PORT,
            SourceKeyType.POSTGRES_DATABASE
        ]
    ],
    Source.EKS: [
        [
            SourceKeyType.AWS_ACCESS_KEY,
            SourceKeyType.AWS_SECRET_KEY,
            SourceKeyType.AWS_REGION,
            SourceKeyType.EKS_ROLE_ARN,
        ],
        [
            SourceKeyType.AWS_REGION,
            SourceKeyType.AWS_ASSUMED_ROLE_ARN,
            SourceKeyType.EKS_ROLE_ARN,
        ]
    ],
    Source.SQL_DATABASE_CONNECTION: [
        [
            SourceKeyType.SQL_DATABASE_CONNECTION_STRING_URI,
        ]
    ],
    Source.OPEN_AI: [
        [
            SourceKeyType.OPEN_AI_API_KEY,
        ]
    ],
    Source.GRAFANA_MIMIR: [
        [
            SourceKeyType.MIMIR_HOST,
            SourceKeyType.X_SCOPE_ORG_ID,
            SourceKeyType.SSL_VERIFY,
        ],
        [
            SourceKeyType.MIMIR_HOST,
            SourceKeyType.X_SCOPE_ORG_ID
        ]
    ],
    Source.BASH: [
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PEM
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
            SourceKeyType.REMOTE_SERVER_PORT,

        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PASSWORD,
            SourceKeyType.REMOTE_SERVER_PORT,

        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PASSWORD
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PASSWORD
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
            SourceKeyType.REMOTE_SERVER_PORT,
        ],
        [
            SourceKeyType.REMOTE_SERVER_USER,
            SourceKeyType.REMOTE_SERVER_HOST,
        ],
        [
            SourceKeyType.REMOTE_SERVER_HOST,
        ],
        [
            SourceKeyType.REMOTE_SERVER_PORT,

        ],
        []
    ],
    Source.AZURE: [
        [
            SourceKeyType.AZURE_CLIENT_ID,
            SourceKeyType.AZURE_CLIENT_SECRET,
            SourceKeyType.AZURE_TENANT_ID,
            SourceKeyType.AZURE_SUBSCRIPTION_ID,
        ]
    ],
    Source.GKE: [
        [
            SourceKeyType.GKE_PROJECT_ID,
            SourceKeyType.GKE_SERVICE_ACCOUNT_JSON,
        ]
    ],
    Source.MS_TEAMS: [
        [
            SourceKeyType.MS_TEAMS_CONNECTOR_WEBHOOK_URL,
        ]
    ],
    Source.ELASTIC_SEARCH: [
        [
            SourceKeyType.ELASTIC_SEARCH_PROTOCOL,
            SourceKeyType.ELASTIC_SEARCH_HOST,
            SourceKeyType.ELASTIC_SEARCH_PORT,
            SourceKeyType.ELASTIC_SEARCH_API_KEY_ID,
            SourceKeyType.ELASTIC_SEARCH_API_KEY,
            SourceKeyType.SSL_VERIFY,
        ],
        [
            SourceKeyType.ELASTIC_SEARCH_PROTOCOL,
            SourceKeyType.ELASTIC_SEARCH_HOST,
            SourceKeyType.ELASTIC_SEARCH_API_KEY_ID,
            SourceKeyType.ELASTIC_SEARCH_API_KEY,
        ],
        [
            SourceKeyType.ELASTIC_SEARCH_HOST,
        ]
    ],
    Source.GRAFANA_LOKI: [
        [
            SourceKeyType.GRAFANA_LOKI_PROTOCOL,
            SourceKeyType.GRAFANA_LOKI_HOST,
            SourceKeyType.GRAFANA_LOKI_PORT,
            SourceKeyType.X_SCOPE_ORG_ID,
            SourceKeyType.SSL_VERIFY
        ],
        [
            SourceKeyType.GRAFANA_LOKI_PROTOCOL,
            SourceKeyType.GRAFANA_LOKI_HOST,
            SourceKeyType.GRAFANA_LOKI_PORT,
            SourceKeyType.X_SCOPE_ORG_ID
        ]
    ],
    Source.KUBERNETES: [
        [
            SourceKeyType.KUBERNETES_CLUSTER_NAME,
            SourceKeyType.KUBERNETES_CLUSTER_API_SERVER,
            SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
            SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_DATA,
            SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_PATH
        ],
        [
            SourceKeyType.KUBERNETES_CLUSTER_NAME,
            SourceKeyType.KUBERNETES_CLUSTER_API_SERVER,
            SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
            SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_DATA
        ],
        [
            SourceKeyType.KUBERNETES_CLUSTER_NAME,
            SourceKeyType.KUBERNETES_CLUSTER_API_SERVER,
            SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
            SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_PATH
        ],
        [
            SourceKeyType.KUBERNETES_CLUSTER_NAME,
            SourceKeyType.KUBERNETES_CLUSTER_API_SERVER,
            SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
        ],
        []
    ],
    Source.GCM: [
        [
            SourceKeyType.GCM_PROJECT_ID,
            SourceKeyType.GCM_PRIVATE_KEY,
        ],
        [
            SourceKeyType.GCM_PROJECT_ID,
            SourceKeyType.GCM_SERVICE_ACCOUNT_JSON,
        ]
    ],
    Source.SMTP: [
        [
            SourceKeyType.SMTP_HOST,
            SourceKeyType.SMTP_PORT,
            SourceKeyType.SMTP_USER,
            SourceKeyType.SMTP_PASSWORD,
        ]
    ],
    Source.BIG_QUERY: [
        [
            SourceKeyType.BIG_QUERY_PROJECT_ID,
            SourceKeyType.BIG_QUERY_SERVICE_ACCOUNT_JSON,
        ]
    ],
    Source.MONGODB: [
        [
            SourceKeyType.MONGODB_CONNECTION_STRING,
        ]
    ],
    Source.OPEN_SEARCH: [
        [
            SourceKeyType.OPEN_SEARCH_PROTOCOL,
            SourceKeyType.OPEN_SEARCH_HOST,
            SourceKeyType.OPEN_SEARCH_PORT,
            SourceKeyType.OPEN_SEARCH_USERNAME,
            SourceKeyType.OPEN_SEARCH_PASSWORD,
            SourceKeyType.SSL_VERIFY,
        ],
        [
            SourceKeyType.OPEN_SEARCH_PROTOCOL,
            SourceKeyType.OPEN_SEARCH_HOST,
            SourceKeyType.OPEN_SEARCH_USERNAME,
            SourceKeyType.OPEN_SEARCH_PASSWORD,
            SourceKeyType.SSL_VERIFY,
        ],
        [
            SourceKeyType.OPEN_SEARCH_PROTOCOL,
            SourceKeyType.OPEN_SEARCH_HOST,
            SourceKeyType.OPEN_SEARCH_PORT,
            SourceKeyType.OPEN_SEARCH_USERNAME,
            SourceKeyType.OPEN_SEARCH_PASSWORD,
        ],
        [
            SourceKeyType.OPEN_SEARCH_PROTOCOL,
            SourceKeyType.OPEN_SEARCH_HOST,
            SourceKeyType.OPEN_SEARCH_USERNAME,
            SourceKeyType.OPEN_SEARCH_PASSWORD,
        ],
        [
            SourceKeyType.OPEN_SEARCH_HOST,
        ]
    ],
    Source.GITHUB: [
        [
            SourceKeyType.GITHUB_TOKEN,
            SourceKeyType.GITHUB_ORG,
        ]
    ],
    Source.JENKINS: [
        [
            SourceKeyType.JENKINS_URL,
            SourceKeyType.JENKINS_USERNAME,
            SourceKeyType.JENKINS_API_TOKEN,
            SourceKeyType.JENKINS_CRUMB
        ],
        [
            SourceKeyType.JENKINS_URL,
            SourceKeyType.JENKINS_USERNAME,
            SourceKeyType.JENKINS_API_TOKEN
        ],
    ],
    Source.ARGOCD: [
        [
            SourceKeyType.ARGOCD_SERVER,
            SourceKeyType.ARGOCD_TOKEN,
        ]
    ],
    Source.POSTHOG: [
        [
            SourceKeyType.POSTHOG_API_KEY,
            SourceKeyType.POSTHOG_APP_HOST,
            SourceKeyType.POSTHOG_PROJECT_ID,
        ]
    ],
    Source.GITHUB_ACTIONS: [
        [
            SourceKeyType.GITHUB_ACTIONS_TOKEN,
        ]
    ],
    Source.JIRA_CLOUD: [
        [
            SourceKeyType.JIRA_CLOUD_API_KEY,
            SourceKeyType.JIRA_EMAIL,
            SourceKeyType.JIRA_DOMAIN,
        ]
    ],
}
integrations_connector_type_display_name_map = {
    Source.SLACK: 'SLACK',
    Source.GOOGLE_CHAT: 'Google Chat',
    Source.SENTRY: 'SENTRY',
    Source.NEW_RELIC: 'NEW RELIC',
    Source.DATADOG: 'DATADOG',
    Source.DATADOG_OAUTH: 'DATADOG',
    Source.GRAFANA: 'GRAFANA',
    Source.GRAFANA_VPC: 'GRAFANA VPC',
    Source.GITHUB: 'GITHUB',
    Source.ELASTIC_APM: 'ELASTIC APM',
    Source.VICTORIA_METRICS: 'VictoriaMetrics',
    Source.PROMETHEUS: 'PROMETHEUS',
    Source.CLOUDWATCH: 'CLOUDWATCH',
    Source.GCM: 'GOOGLE CLOUD MONITORING',
    Source.CLICKHOUSE: 'CLICKHOUSE',
    Source.POSTGRES: 'POSTGRES',
    Source.PAGER_DUTY: 'PAGERDUTY',
    Source.ROOTLY: 'ROOTLY',
    Source.OPS_GENIE: 'OPS GENIE',
    Source.EKS: 'EKS KUBERNETES',
    Source.SQL_DATABASE_CONNECTION: 'SQL DATABASE CONNECTION',
    Source.OPEN_AI: 'OPEN AI',
    Source.BASH: 'BASH COMMAND EXECUTOR',
    Source.GRAFANA_MIMIR: 'GRAFANA MIMIR',
    Source.AZURE: 'AZURE',
    Source.GKE: 'GKE KUBERNETES',
    Source.MS_TEAMS: 'MS TEAMS',
    Source.ELASTIC_SEARCH: 'ELASTIC SEARCH',
    Source.GRAFANA_LOKI: 'GRAFANA LOKI',
    Source.KUBERNETES: 'KUBERNETES',
    Source.SMTP: 'EMAIL SERVER',
    Source.BIG_QUERY: 'BIG QUERY',
    Source.JENKINS: 'JENKINS',
    Source.LINEAR: 'LINEAR',
    Source.GITHUB_ACTIONS: 'GITHUB ACTIONS',
    Source.ARGOCD: 'ARGOCD',
    Source.ROLLBAR: 'ROLLBAR',
    Source.POSTHOG: 'POSTHOG',
}

model_type_display_name_maps = {
    SourceModelType.CLOUDWATCH_METRIC: "Metric",
    SourceModelType.CLOUDWATCH_LOG_GROUP: "Log Group",
    SourceModelType.GRAFANA_TARGET_METRIC_PROMQL: "PromQL",
    SourceModelType.GRAFANA_PROMETHEUS_DATASOURCE: "Data Sources",
    SourceModelType.NEW_RELIC_ENTITY_APPLICATION: "Entity Application",
    SourceModelType.NEW_RELIC_ENTITY_DASHBOARD: "Entity Dashboard",
    SourceModelType.NEW_RELIC_NRQL: "Raw NRQL",
    SourceModelType.CLICKHOUSE_DATABASE: "Database",
    SourceModelType.DATADOG_SERVICE: "Service",
    SourceModelType.DATADOG_QUERY: "Custom Query",
    SourceModelType.EKS_CLUSTER: "Cluster",
    SourceModelType.SQL_DATABASE_CONNECTION_RAW_QUERY: "Query",
    SourceModelType.GRAFANA_MIMIR_PROMQL: "PromQL",
    SourceModelType.POSTGRES_QUERY: "Sql Query",
    SourceModelType.AZURE_WORKSPACE: "Azure Log Analytics Workspace",
    SourceModelType.SSH_SERVER: "SSH Server",
    SourceModelType.OPEN_SEARCH_INDEX: "Open Search Index",
    SourceModelType.GITHUB_REPOSITORY: "Repository",
}

masked_keys_types = [SourceKeyType.DATADOG_APP_KEY,
                     SourceKeyType.DATADOG_API_KEY,
                     SourceKeyType.NEWRELIC_API_KEY,
                     SourceKeyType.NEWRELIC_APP_ID,
                     SourceKeyType.NEWRELIC_QUERY_KEY,
                     SourceKeyType.SENTRY_API_KEY,
                     SourceKeyType.HONEYBADGER_USERNAME,
                     SourceKeyType.HONEYBADGER_PASSWORD,
                     SourceKeyType.HONEYBADGER_PROJECT_ID,
                     SourceKeyType.AWS_ACCESS_KEY,
                     SourceKeyType.AWS_SECRET_KEY,
                     SourceKeyType.AWS_ASSUMED_ROLE_ARN,
                     SourceKeyType.AWS_DRD_CLOUD_ROLE_ARN,
                     SourceKeyType.DATADOG_AUTH_TOKEN,
                     SourceKeyType.AGENT_PROXY_API_KEY,
                     SourceKeyType.GITHUB_TOKEN,
                     SourceKeyType.GOOGLE_CHAT_BOT_OAUTH_TOKEN,
                     SourceKeyType.SLACK_BOT_AUTH_TOKEN,
                     SourceKeyType.AGENT_PROXY_HOST,
                     SourceKeyType.CLICKHOUSE_USER,
                     SourceKeyType.CLICKHOUSE_PASSWORD,
                     SourceKeyType.GCM_PROJECT_ID,
                     SourceKeyType.GCM_PRIVATE_KEY,
                     SourceKeyType.GCM_CLIENT_EMAIL,
                     SourceKeyType.PAGER_DUTY_API_KEY,
                     SourceKeyType.POSTGRES_PASSWORD,
                     SourceKeyType.POSTGRES_USER,
                     SourceKeyType.GRAFANA_API_KEY,
                     SourceKeyType.ZENDUTY_API_KEY,
                     SourceKeyType.OPS_GENIE_API_KEY,
                     SourceKeyType.JIRA_CLOUD_API_KEY,
                     SourceKeyType.ASANA_ACCESS_TOKEN,
                     SourceKeyType.CONFLUENCE_CLOUD_API_KEY,
                     SourceKeyType.NOTION_API_KEY,
                     SourceKeyType.MONGODB_CONNECTION_STRING,
                     SourceKeyType.SQL_DATABASE_CONNECTION_STRING_URI,
                     SourceKeyType.OPEN_SEARCH_PASSWORD,
                     SourceKeyType.JENKINS_API_TOKEN,
                     SourceKeyType.LINEAR_API_KEY,
                     SourceKeyType.GITHUB_ACTIONS_TOKEN,
                     SourceKeyType.SMTP_PASSWORD,
                     SourceKeyType.ARGOCD_TOKEN,
                     SourceKeyType.ROLLBAR_ACCESS_TOKEN,
                     SourceKeyType.CUSTOM_STRATEGIES_ACCOUNT_ID,
                     SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
                     SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_DATA,
                     SourceKeyType.REMOTE_SERVER_PEM,
                     SourceKeyType.POSTHOG_API_KEY,
                     ]


GCM_SERVICE_DASHBOARD_QUERIES = {
        "Billable container instance time": {
            "sum": "fetch cloud_run_revision | metric 'run.googleapis.com/container/billable_instance_time' | align rate(1m) | every 1m | group_by [resource.service_name], [value_billable_instance_time_sum: sum(value.billable_instance_time)]",
        },
        "Container startup latency": {
            "50": "fetch cloud_run_revision | metric 'run.googleapis.com/container/startup_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_startup_latencies_percentile: percentile(value.startup_latencies, 50)]",
            "95": "fetch cloud_run_revision | metric 'run.googleapis.com/container/startup_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_startup_latencies_percentile: percentile(value.startup_latencies, 95)]",
            "99": "fetch cloud_run_revision | metric 'run.googleapis.com/container/startup_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_startup_latencies_percentile: percentile(value.startup_latencies, 99)]",
        },
        "Container CPU utilisation": {
            "50": "fetch cloud_run_revision | metric 'run.googleapis.com/container/cpu/utilizations' | group_by 1m, [value_cpu_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_cpu_utilizations_aggregate_percentile: percentile(value_cpu_utilizations_aggregate, 50)]",
            "95": "fetch cloud_run_revision | metric 'run.googleapis.com/container/cpu/utilizations' | group_by 1m, [value_cpu_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_cpu_utilizations_aggregate_percentile: percentile(value_cpu_utilizations_aggregate, 95)]",
            "99": "fetch cloud_run_revision | metric 'run.googleapis.com/container/cpu/utilizations' | group_by 1m, [value_cpu_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_cpu_utilizations_aggregate_percentile: percentile(value_cpu_utilizations_aggregate, 99)]",
        },
        "Container memory utilisation": {
            "50": "fetch cloud_run_revision | metric 'run.googleapis.com/container/memory/utilizations' | group_by 1m, [value_memory_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_memory_utilizations_aggregate_percentile: percentile(value_memory_utilizations_aggregate, 50)]",
            "95": "fetch cloud_run_revision | metric 'run.googleapis.com/container/memory/utilizations' | group_by 1m, [value_memory_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_memory_utilizations_aggregate_percentile: percentile(value_memory_utilizations_aggregate, 95)]",
            "99": "fetch cloud_run_revision | metric 'run.googleapis.com/container/memory/utilizations' | group_by 1m, [value_memory_utilizations_aggregate: aggregate(value.utilizations)] | every 1m | group_by [resource.service_name], [value_memory_utilizations_aggregate_percentile: percentile(value_memory_utilizations_aggregate, 99)]",
        },
        "Sent bytes": {
            "sum": "fetch cloud_run_revision | metric 'run.googleapis.com/container/network/sent_bytes_count'| align rate(1m) | every 1m",
        },
        "Received bytes": {
            "sum": "fetch cloud_run_revision | metric 'run.googleapis.com/container/network/received_bytes_count' | align rate(1m) | every 1m",
        },
        "Request count": {
            "sum": "fetch cloud_run_revision | metric 'run.googleapis.com/request_count' | align rate(1m) | every 1m | group_by [metric.response_code_class], [value_request_count_aggregate: aggregate(value.request_count)]",
        },
        "Request latencies": {
            "50": "fetch cloud_run_revision | metric 'run.googleapis.com/request_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_request_latencies_percentile: percentile(value.request_latencies, 50)]",
            "95": "fetch cloud_run_revision | metric 'run.googleapis.com/request_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_request_latencies_percentile: percentile(value.request_latencies, 95)]",
            "99": "fetch cloud_run_revision | metric 'run.googleapis.com/request_latencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_request_latencies_percentile: percentile(value.request_latencies, 99)]",
        },
        "Container instance count": {
            "max": "fetch cloud_run_revision | metric 'run.googleapis.com/container/instance_count' | group_by 1m, [value_instance_count_max: max(value.instance_count)] | every 1m | group_by [resource.service_name, metric.state], [value_instance_count_max_aggregate: aggregate(value_instance_count_max)]",
        },
        "Maximum concurrent requests": {
            "50": "fetch cloud_run_revision | metric 'run.googleapis.com/container/max_request_concurrencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_max_request_concurrencies_percentile: percentile(value.max_request_concurrencies, 50)]",
            "95": "fetch cloud_run_revision | metric 'run.googleapis.com/container/max_request_concurrencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_max_request_concurrencies_percentile: percentile(value.max_request_concurrencies, 95)]",
            "99": "fetch cloud_run_revision | metric 'run.googleapis.com/container/max_request_concurrencies' | align delta(1m) | every 1m | group_by [resource.service_name], [value_max_request_concurrencies_percentile: percentile(value.max_request_concurrencies, 99)]",
        },
    }

NEWRELIC_APM_QUERIES = {
    "Web transactions time": "SELECT sum(apm.service.overview.web * 1000) FROM Metric WHERE (entity.guid = {}) FACET `segmentName` LIMIT MAX TIMESERIES",
    "Apdex score": "SELECT apdex(apm.service.apdex) as 'App server' , apdex(apm.service.apdex.user) as 'End user' FROM Metric WHERE (entity.guid = {}) LIMIT MAX TIMESERIES",
    "Error rate": "SELECT sum(apm.service.error.count['count']) / count(apm.service.transaction.duration) AS 'Web errors' FROM Metric WHERE (entity.guid = {}) AND (transactionType = 'Web') LIMIT MAX TIMESERIES",
    "Error User Impact": "SELECT uniqueCount(newrelic.error.group.userImpact) as 'Total' FROM Metric WHERE (entity.guid = {}) AND ((`error.expected` != true AND metricName = 'newrelic.error.group.userImpact')) LIMIT MAX TIMESERIES",
    "Throughput": "SELECT rate(count(apm.service.transaction.duration), 1 minute) as 'Web throughput' FROM Metric WHERE (entity.guid = {}) AND (transactionType = 'Web') LIMIT MAX TIMESERIES ",
    "Logs": "SELECT count(apm.service.logging.lines) as Metric FROM Metric WHERE (entity.guid = {}) FACET `severity` LIMIT MAX TIMESERIES ",
    "Non-Web Transactions": "SELECT sum(apm.service.overview.other * 1000) FROM Metric WHERE (entity.guid = {}) FACET `segmentName` LIMIT MAX TIMESERIES",
    "Average APM service transaction time (Non-Web)": "SELECT average(convert(apm.service.transaction.duration, unit, 'ms')) AS 'Response time' FROM Metric WHERE (entity.guid = {}) AND (transactionType = 'Other') LIMIT MAX TIMESERIES"
}