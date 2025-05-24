from django.conf import settings
from google.protobuf.wrappers_pb2 import StringValue, UInt64Value

from protos.base_pb2 import Source, SourceKeyType
from protos.connectors.connector_pb2 import Connector, ConnectorKey


def generate_credentials_dict(connector_type, connector_keys):
    credentials_dict = {}
    if connector_type == Source.NEW_RELIC:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.NEWRELIC_API_KEY:
                credentials_dict['nr_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.NEWRELIC_APP_ID:
                credentials_dict['nr_app_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.NEWRELIC_API_DOMAIN:
                credentials_dict['nr_api_domain'] = conn_key.key.value
    elif connector_type == Source.DATADOG:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.DATADOG_API_KEY:
                credentials_dict['dd_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.DATADOG_APP_KEY:
                credentials_dict['dd_app_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.DATADOG_API_DOMAIN:
                credentials_dict['dd_api_domain'] = conn_key.key.value
    elif connector_type == Source.DATADOG_OAUTH:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.DATADOG_API_KEY:
                credentials_dict['dd_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.DATADOG_APP_KEY:
                credentials_dict['dd_app_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.DATADOG_API_DOMAIN:
                credentials_dict['dd_api_domain'] = conn_key.key.value
    elif connector_type == Source.CLOUDWATCH:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.AWS_ACCESS_KEY:
                credentials_dict['aws_access_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_SECRET_KEY:
                credentials_dict['aws_secret_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_REGION:
                credentials_dict['region'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_ASSUMED_ROLE_ARN:
                credentials_dict['aws_assumed_role_arn'] = conn_key.key.value
    elif connector_type == Source.EKS:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.AWS_ACCESS_KEY:
                credentials_dict['aws_access_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_SECRET_KEY:
                credentials_dict['aws_secret_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_REGION:
                credentials_dict['region'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.EKS_ROLE_ARN:
                credentials_dict['k8_role_arn'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AWS_ASSUMED_ROLE_ARN:
                credentials_dict['aws_assumed_role_arn'] = conn_key.key.value
    elif connector_type == Source.GRAFANA:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GRAFANA_API_KEY:
                credentials_dict['grafana_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.GRAFANA_HOST:
                credentials_dict['grafana_host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SSL_VERIFY:
                credentials_dict['ssl_verify'] = 'true'
                if conn_key.key.value.lower() == 'false':
                    credentials_dict['ssl_verify'] = 'false'
    elif connector_type == Source.GRAFANA_VPC:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.AGENT_PROXY_API_KEY:
                credentials_dict['agent_proxy_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AGENT_PROXY_HOST:
                credentials_dict['agent_proxy_host'] = conn_key.key.value
            credentials_dict['parent_source'] = Source.GRAFANA_VPC
    elif connector_type == Source.GRAFANA_MIMIR:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.MIMIR_HOST:
                credentials_dict['mimir_host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.X_SCOPE_ORG_ID:
                credentials_dict['x_scope_org_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SSL_VERIFY:
                credentials_dict['ssl_verify'] = 'true'
                if conn_key.key.value.lower() == 'false':
                    credentials_dict['ssl_verify'] = 'false'
    elif connector_type == Source.CLICKHOUSE:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.CLICKHOUSE_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.CLICKHOUSE_USER:
                credentials_dict['user'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.CLICKHOUSE_PASSWORD:
                credentials_dict['password'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.CLICKHOUSE_INTERFACE:
                credentials_dict['interface'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.CLICKHOUSE_PORT:
                credentials_dict['port'] = conn_key.key.value
    elif connector_type == Source.POSTGRES:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.POSTGRES_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.POSTGRES_USER:
                credentials_dict['user'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.POSTGRES_PASSWORD:
                credentials_dict['password'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.POSTGRES_DATABASE:
                credentials_dict['database'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.POSTGRES_PORT:
                credentials_dict['port'] = conn_key.key.value
    elif connector_type == Source.SQL_DATABASE_CONNECTION:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.SQL_DATABASE_CONNECTION_STRING_URI:
                credentials_dict['connection_string'] = conn_key.key.value
    elif connector_type == Source.SLACK:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.SLACK_BOT_AUTH_TOKEN:
                credentials_dict['bot_auth_token'] = conn_key.key.value
    elif connector_type == Source.BASH:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.REMOTE_SERVER_HOST:
                ssh_servers = conn_key.key.value
                if ssh_servers:
                    ssh_servers = ssh_servers.replace(' ', '')
                    ssh_servers = ssh_servers.split(',')
                    ssh_servers = list(filter(None, ssh_servers))
                    credentials_dict['remote_host'] = ssh_servers[0]
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_USER:
                credentials_dict['remote_user'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_PEM:
                credentials_dict['remote_pem'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_PASSWORD:
                credentials_dict['remote_password'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_PORT:
                credentials_dict['port'] = conn_key.key.value
    elif connector_type == Source.AZURE:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.AZURE_CLIENT_ID:
                credentials_dict['client_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AZURE_CLIENT_SECRET:
                credentials_dict['client_secret'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AZURE_TENANT_ID:
                credentials_dict['tenant_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.AZURE_SUBSCRIPTION_ID:
                credentials_dict['subscription_id'] = conn_key.key.value
    elif connector_type == Source.GKE:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GKE_PROJECT_ID:
                credentials_dict['project_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.GKE_SERVICE_ACCOUNT_JSON:
                credentials_dict['service_account_json'] = conn_key.key.value
    elif connector_type == Source.MS_TEAMS:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.MS_TEAMS_CONNECTOR_WEBHOOK_URL:
                credentials_dict['webhook_url'] = conn_key.key.value
    elif connector_type == Source.PAGER_DUTY:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.PAGER_DUTY_API_KEY:
                credentials_dict['api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.PAGER_DUTY_CONFIGURED_EMAIL:
                credentials_dict['configured_email'] = conn_key.key.value
    elif connector_type == Source.ROOTLY:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.ROOTLY_API_KEY:
                credentials_dict['api_key'] = conn_key.key.value
    elif connector_type == Source.ZENDUTY:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.ZENDUTY_API_KEY:
                credentials_dict['api_key'] = conn_key.key.value
    elif connector_type == Source.ELASTIC_SEARCH:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.ELASTIC_SEARCH_PROTOCOL:
                credentials_dict['protocol'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.ELASTIC_SEARCH_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.ELASTIC_SEARCH_PORT:
                credentials_dict['port'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.ELASTIC_SEARCH_API_KEY_ID:
                credentials_dict['api_key_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.ELASTIC_SEARCH_API_KEY:
                credentials_dict['api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SSL_VERIFY:
                credentials_dict['verify_certs'] = True
                if conn_key.key.value.lower() == 'false':
                    credentials_dict['verify_certs'] = False
            if 'port' not in credentials_dict:
                credentials_dict['port'] = '9200'
    elif connector_type == Source.GRAFANA_LOKI:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GRAFANA_LOKI_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.GRAFANA_LOKI_PORT:
                credentials_dict['port'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.GRAFANA_LOKI_PROTOCOL:
                credentials_dict['protocol'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.X_SCOPE_ORG_ID:
                credentials_dict['x_scope_org_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SSL_VERIFY:
                credentials_dict['ssl_verify'] = 'true'
                if conn_key.key.value.lower() == 'false':
                    credentials_dict['ssl_verify'] = 'false'
    elif connector_type == Source.KUBERNETES:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.KUBERNETES_CLUSTER_API_SERVER:
                credentials_dict['api_server'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.KUBERNETES_CLUSTER_TOKEN:
                credentials_dict['token'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_DATA:
                credentials_dict['ssl_ca_cert'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.KUBERNETES_CLUSTER_CERTIFICATE_AUTHORITY_PATH:
                credentials_dict['ssl_ca_cert_path'] = conn_key.key.value
    elif connector_type == Source.GCM:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GCM_PROJECT_ID:
                credentials_dict['project_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.GCM_SERVICE_ACCOUNT_JSON:
                credentials_dict['service_account_json'] = conn_key.key.value
    elif connector_type == Source.SMTP:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.SMTP_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SMTP_PORT:
                credentials_dict['port'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SMTP_USER:
                credentials_dict['username'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SMTP_PASSWORD:
                credentials_dict['password'] = conn_key.key.value
    elif connector_type == Source.BIG_QUERY:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.BIG_QUERY_PROJECT_ID:
                credentials_dict['project_id'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.BIG_QUERY_SERVICE_ACCOUNT_JSON:
                credentials_dict['service_account_json'] = conn_key.key.value
    elif connector_type == Source.MONGODB:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.MONGODB_CONNECTION_STRING:
                credentials_dict['connection_string'] = conn_key.key.value
    elif connector_type == Source.OPEN_SEARCH:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.OPEN_SEARCH_HOST:
                credentials_dict['host'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.OPEN_SEARCH_PORT:
                credentials_dict['port'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.OPEN_SEARCH_PROTOCOL:
                credentials_dict['protocol'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.OPEN_SEARCH_USERNAME:
                credentials_dict['username'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.OPEN_SEARCH_PASSWORD:
                credentials_dict['password'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.SSL_VERIFY:
                credentials_dict['verify_certs'] = True
                if conn_key.key.value.lower() == 'false':
                    credentials_dict['verify_certs'] = False
    elif connector_type == Source.GITHUB:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GITHUB_TOKEN:
                credentials_dict['api_key'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.GITHUB_ORG:
                credentials_dict['org'] = conn_key.key.value
    elif connector_type == Source.ARGOCD:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.ARGOCD_SERVER:
                credentials_dict['argocd_server'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.ARGOCD_TOKEN:
                credentials_dict['argocd_token'] = conn_key.key.value
    elif connector_type == Source.JIRA_CLOUD:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.JIRA_DOMAIN:
                credentials_dict['jira_domain'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.JIRA_CLOUD_API_KEY:
                credentials_dict['jira_cloud_api_key'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.JIRA_EMAIL:
                credentials_dict['jira_email'] = conn_key.key.value
    elif connector_type == Source.JENKINS:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.JENKINS_URL:
                credentials_dict['url'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.JENKINS_USERNAME:
                credentials_dict['username'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.JENKINS_API_TOKEN:
                credentials_dict['api_token'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.JENKINS_CRUMB:
                credentials_dict['crumb'] = False
                if conn_key.key.value.lower() == 'true':
                    credentials_dict['crumb'] = True
    elif connector_type == Source.POSTHOG:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.POSTHOG_API_KEY:
                credentials_dict['personal_api_key'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.POSTHOG_APP_HOST:
                credentials_dict['posthog_host'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.POSTHOG_PROJECT_ID:
                credentials_dict['project_id'] = conn_key.key.value

    elif connector_type == Source.SIGNOZ:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.SIGNOZ_API_URL:
                credentials_dict['signoz_api_url'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.SIGNOZ_API_TOKEN:
                credentials_dict['signoz_api_token'] = conn_key.key.value
    
    elif connector_type == Source.SENTRY:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.SENTRY_API_KEY:
                credentials_dict['api_key'] = conn_key.key.value
            if conn_key.key_type == SourceKeyType.SENTRY_ORG_SLUG:
                credentials_dict['org_slug'] = conn_key.key.value

    elif connector_type == Source.GITHUB_ACTIONS:
        for conn_key in connector_keys:
            if conn_key.key_type == SourceKeyType.GITHUB_ACTIONS_TOKEN:
                credentials_dict['api_key'] = conn_key.key.value

    else:
        return None
    return credentials_dict


def credential_yaml_to_connector_proto(connector_name, credential_yaml, connector_id=None):
    if 'type' not in credential_yaml:
        raise Exception(f'Type not found in credential yaml for connector: {connector_name}')

    if not connector_name:
        raise Exception(f'Connector name not found in credential yaml for connector: {connector_name}')

    c_type = credential_yaml['type']
    c_keys: [ConnectorKey] = []
    if c_type == 'CLOUDWATCH':
        if 'region' not in credential_yaml:
            raise Exception(f'Region not found in credential yaml for cloudwatch source in connector: {connector_name}')

        if (not 'aws_access_key' in credential_yaml or not 'aws_secret_key' in credential_yaml) and (
                not 'aws_assumed_role_arn' in credential_yaml):
            raise Exception(
                f'No credentials found in credential yaml for cloudwatch source in connector: {connector_name}')

        c_source = Source.CLOUDWATCH

        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AWS_REGION,
            key=StringValue(value=credential_yaml['region'])
        ))
        if credential_yaml.get('aws_access_key', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_ACCESS_KEY,
                key=StringValue(value=credential_yaml['aws_access_key'])
            ))
        if credential_yaml.get('aws_secret_key', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_SECRET_KEY,
                key=StringValue(value=credential_yaml['aws_secret_key'])
            ))

        if credential_yaml.get('aws_assumed_role_arn', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_ASSUMED_ROLE_ARN,
                key=StringValue(value=credential_yaml['aws_assumed_role_arn'])
            ))
    elif c_type == 'EKS':
        if 'region' not in credential_yaml:
            raise Exception(f'Region not found in credential yaml for eks source in connector: {connector_name}')

        if (not 'aws_access_key' in credential_yaml or not 'aws_secret_key' in credential_yaml) and (
                not 'aws_assumed_role_arn' in credential_yaml):
            raise Exception(f'No credentials found in credential yaml for eks source in connector: {connector_name}')

        c_source = Source.EKS

        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AWS_REGION,
            key=StringValue(value=credential_yaml['region'])
        ))
        if credential_yaml.get('aws_access_key', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_ACCESS_KEY,
                key=StringValue(value=credential_yaml['aws_access_key'])
            ))
        if credential_yaml.get('aws_secret_key', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_SECRET_KEY,
                key=StringValue(value=credential_yaml['aws_secret_key'])
            ))
        if credential_yaml.get('k8_role_arn', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.EKS_ROLE_ARN,
                key=StringValue(value=credential_yaml['k8_role_arn'])
            ))
        if credential_yaml.get('aws_assumed_role_arn', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.AWS_ASSUMED_ROLE_ARN,
                key=StringValue(value=credential_yaml['aws_assumed_role_arn'])
            ))
    elif c_type == 'GRAFANA':
        if 'grafana_host' not in credential_yaml or 'grafana_api_key' not in credential_yaml:
            raise Exception(
                f'Host not found in credential yaml for grafana source in connector: {connector_name}')

        if 'grafana_api_key' not in credential_yaml:
            raise Exception(
                f'Api key not found in credential yaml for grafana source in connector: {connector_name}')

        c_source = Source.GRAFANA

        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_HOST,
            key=StringValue(value=credential_yaml['grafana_host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_API_KEY,
            key=StringValue(value=credential_yaml['grafana_api_key'])
        ))
        if credential_yaml.get('ssl_verify', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.SSL_VERIFY,
                key=StringValue(value=credential_yaml['ssl_verify'])
            ))
    elif c_type == 'GRAFANA_LOKI':
        if 'host' not in credential_yaml:
            raise Exception(f'Host not found in credential yaml for grafana loki source in connector: {connector_name}')

        if 'port' not in credential_yaml:
            raise Exception(f'Port not found in credential yaml for grafana loki source in connector: {connector_name}')

        if 'protocol' not in credential_yaml:
            raise Exception(f'Protocol not found in credential yaml for grafana loki source in connector: {connector_name}')

        c_source = Source.GRAFANA_LOKI

        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_LOKI_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_LOKI_PORT,
            key=StringValue(value=str(credential_yaml['port']))
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_LOKI_PROTOCOL,
            key=StringValue(value=credential_yaml['protocol'])
        ))
        if credential_yaml.get('x_scope_org_id', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.X_SCOPE_ORG_ID,
                key=StringValue(value=credential_yaml['x_scope_org_id'])
            ))
        if credential_yaml.get('ssl_verify', None):
            ssl_verify_flag = credential_yaml['ssl_verify']
            if isinstance(ssl_verify_flag, str):
                ssl_verify_flag = ssl_verify_flag.lower()
            if isinstance(ssl_verify_flag, bool):
                ssl_verify_flag = str(ssl_verify_flag).lower()
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.SSL_VERIFY,
                key=StringValue(value=ssl_verify_flag)
            ))
    elif c_type == 'SQL_DATABASE_CONNECTION':
        if 'connection_string' not in credential_yaml:
            raise Exception(
                f'connection_string not found in credential yaml for database source in connector: {connector_name}')

        c_source = Source.SQL_DATABASE_CONNECTION
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.SQL_DATABASE_CONNECTION_STRING_URI,
            key=StringValue(value=credential_yaml['connection_string'])
        ))
    elif c_type == 'BASH':
        c_source = Source.BASH
        if 'remote_user' in credential_yaml:
            c_keys.append(ConnectorKey(key_type=SourceKeyType.REMOTE_SERVER_USER,
                                       key=StringValue(value=credential_yaml['remote_user'])))
        if 'remote_host' in credential_yaml:
            c_keys.append(ConnectorKey(key_type=SourceKeyType.REMOTE_SERVER_HOST,
                                       key=StringValue(value=credential_yaml['remote_host'])))
        if 'remote_password' in credential_yaml:
            c_keys.append(ConnectorKey(key_type=SourceKeyType.REMOTE_SERVER_PASSWORD,
                                       key=StringValue(value=credential_yaml['remote_password'])))
        if 'remote_pem' in credential_yaml:
            c_keys.append(ConnectorKey(key_type=SourceKeyType.REMOTE_SERVER_PEM,
                                       key=StringValue(value=credential_yaml['remote_pem'])))
        if 'port' in credential_yaml:
            c_keys.append(ConnectorKey(key_type=SourceKeyType.REMOTE_SERVER_PORT,
                                       key=StringValue(value=credential_yaml['port'])))
    elif c_type == 'CLICKHOUSE':
        if 'host' not in credential_yaml:
            raise Exception(
                f'Host not found in credential yaml for clickhouse source in connector: {connector_name}')

        if 'port' not in credential_yaml:
            raise Exception(
                f'Port not found in credential yaml for clickhouse in connector: {connector_name}')

        if 'user' not in credential_yaml:
            raise Exception(
                f'User not found in credential yaml for clickhouse in connector: {connector_name}')

        if 'password' not in credential_yaml:
            raise Exception(
                f'Password not found in credential yaml for clickhouse in connector: {connector_name}')

        if 'interface' not in credential_yaml:
            raise Exception(
                f'Interface not found in credential yaml for clickhouse in connector: {connector_name}')

        c_source = Source.CLICKHOUSE
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.CLICKHOUSE_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.CLICKHOUSE_USER,
            key=StringValue(value=credential_yaml['user'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.CLICKHOUSE_PASSWORD,
            key=StringValue(value=credential_yaml['password'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.CLICKHOUSE_INTERFACE,
            key=StringValue(value=credential_yaml['interface'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.CLICKHOUSE_PORT,
            key=StringValue(value=credential_yaml['port'])
        ))
    elif c_type == 'OPEN_SEARCH':
        if 'host' not in credential_yaml or 'protocol' not in credential_yaml or 'username' not in credential_yaml or 'password' not in credential_yaml:
            raise Exception(
                f'Host, port, protocol, username or password not found in credential yaml for open search source in connector: {connector_name}')

        c_source = Source.OPEN_SEARCH
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_PROTOCOL,
            key=StringValue(value=credential_yaml['protocol'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_USERNAME,
            key=StringValue(value=credential_yaml['username'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_PASSWORD,
            key=StringValue(value=credential_yaml['password'])
        ))
        if credential_yaml.get('port', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.OPEN_SEARCH_PORT,
                key=StringValue(value=str(credential_yaml['port']))
            ))
        if credential_yaml.get('verify_certs', None):
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.SSL_VERIFY,
                key=StringValue(value=credential_yaml['verify_certs'])
            ))
    elif c_type == 'MONGODB':
        if 'connection_string' not in credential_yaml:
            raise Exception(
                f'uri not found in credential yaml for mongodb source in connector: {connector_name}')
        c_source = Source.MONGODB
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.MONGODB_CONNECTION_STRING,
            key=StringValue(value=credential_yaml['connection_string'])
        ))
    elif c_type == 'GITHUB':
        if 'token' not in credential_yaml:
            raise Exception(f'token not found in credential yaml for github source in connector: {connector_name}')
        if 'org' not in credential_yaml:
            raise Exception(f'org not found in credential yaml for github source in connector: {connector_name}')
        c_source = Source.GITHUB
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GITHUB_TOKEN,
            key=StringValue(value=credential_yaml['token'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GITHUB_ORG,
            key=StringValue(value=credential_yaml['org'])
        ))
    elif c_type == 'POSTGRES':
        if 'host' not in credential_yaml or 'user' not in credential_yaml or 'password' not in credential_yaml or 'database' not in credential_yaml:
            raise Exception(
                f'Host, user, password, or database not found in credential yaml for postgres source in connector: {connector_name}')
        c_source = Source.POSTGRES
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTGRES_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTGRES_USER,
            key=StringValue(value=credential_yaml['user'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTGRES_PASSWORD,
            key=StringValue(value=credential_yaml['password'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTGRES_PORT,
            key=StringValue(value=str(credential_yaml['port']))
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTGRES_DATABASE,
            key=StringValue(value=credential_yaml['database'])
        ))
    elif c_type == 'KUBERNETES':
        c_source = Source.KUBERNETES
        if not settings.NATIVE_KUBERNETES_API_MODE:
            if 'cluster_name' not in credential_yaml or 'cluster_api_server' not in credential_yaml or 'cluster_token' not in credential_yaml:
                raise Exception(
                    f'Cluster Name, Api Server or Token, or database not found in credential yaml for kubernetes source in connector: {connector_name}')
            c_source = Source.KUBERNETES
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.KUBERNETES_CLUSTER_NAME,
                key=StringValue(value=credential_yaml['cluster_name'])
            ))
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.KUBERNETES_CLUSTER_API_SERVER,
                key=StringValue(value=credential_yaml['cluster_api_server'])
            ))
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.KUBERNETES_CLUSTER_TOKEN,
                key=StringValue(value=credential_yaml['cluster_token'])
            ))
    elif c_type == 'ARGOCD':
        if 'argocd_server' not in credential_yaml or 'argocd_token' not in credential_yaml:
            raise Exception(f'Api Server or Token not found in credential yaml for ArgoCd source in '
                            f'connector: {connector_name}')
        c_source = Source.ARGOCD
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ARGOCD_SERVER,
            key=StringValue(value=credential_yaml['argocd_server'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ARGOCD_TOKEN,
            key=StringValue(value=credential_yaml['argocd_token'])
        ))
    elif c_type == 'JIRA_CLOUD':
        if 'jira_cloud_api_key' not in credential_yaml or 'jira_domain' not in credential_yaml or 'jira_email' not in credential_yaml:
            raise Exception(f'Api key or domain or email not found in credential yaml for JIRA Cloud source in '
                            f'connector: {connector_name}')
        c_source = Source.JIRA_CLOUD
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JIRA_DOMAIN,
            key=StringValue(value=credential_yaml['jira_domain'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JIRA_CLOUD_API_KEY,
            key=StringValue(value=credential_yaml['jira_cloud_api_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JIRA_EMAIL,
            key=StringValue(value=credential_yaml['jira_email'])
        ))
    elif c_type == 'JENKINS':
        if 'url' not in credential_yaml or 'username' not in credential_yaml or 'api_token' not in credential_yaml:
            raise Exception(f'Url, username or api_token not found in credential yaml for Jenkins source in '
                            f'connector: {connector_name}')
        c_source = Source.JENKINS
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JENKINS_URL,
            key=StringValue(value=credential_yaml['url'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JENKINS_USERNAME,
            key=StringValue(value=credential_yaml['username'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.JENKINS_API_TOKEN,
            key=StringValue(value=credential_yaml['api_token'])
        ))
        if 'crumb' in credential_yaml:
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.JENKINS_CRUMB,
                key=StringValue(value=credential_yaml['crumb'])
            ))
    elif c_type == 'ELASTIC_SEARCH':
        if 'host' not in credential_yaml or 'protocol' not in credential_yaml or 'api_key_id' not in credential_yaml or 'api_key' not in credential_yaml:
            raise Exception(f'Host, protocol, api_key_id or api_key not found in credential yaml for elastic search '
                            f'source in connector: {connector_name}')
        c_source = Source.ELASTIC_SEARCH
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ELASTIC_SEARCH_PROTOCOL,
            key=StringValue(value=credential_yaml['protocol'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ELASTIC_SEARCH_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ELASTIC_SEARCH_API_KEY_ID,
            key=StringValue(value=credential_yaml['api_key_id'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.ELASTIC_SEARCH_API_KEY,
            key=StringValue(value=credential_yaml['api_key'])
        ))
        if 'port' in credential_yaml:
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.ELASTIC_SEARCH_PORT,
                key=StringValue(value=str(credential_yaml['port']))
            ))
        if 'verify_certs' in credential_yaml:
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.SSL_VERIFY,
                key=StringValue(value=credential_yaml['verify_certs'])
            ))

    elif c_type == 'POSTHOG':
        if 'api_key' not in credential_yaml or 'app_host' not in credential_yaml or 'project_id' not in credential_yaml:
            raise Exception(f'Api key, app host or project id not found in credential yaml for posthog source in connector: {connector_name}')
        c_source = Source.POSTHOG
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTHOG_API_KEY,
            key=StringValue(value=credential_yaml['api_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTHOG_APP_HOST,
            key=StringValue(value=credential_yaml['app_host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.POSTHOG_PROJECT_ID,
            key=StringValue(value=credential_yaml['project_id'])
        ))

    elif c_type == 'SIGNOZ':
        if 'signoz_api_url' not in credential_yaml or 'signoz_api_token' not in credential_yaml:
            raise Exception(f'Signoz api url or token not found in credential yaml for signoz source in connector: {connector_name}')
        c_source = Source.SIGNOZ
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.SIGNOZ_API_URL,
            key=StringValue(value=credential_yaml['signoz_api_url'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.SIGNOZ_API_TOKEN,
            key=StringValue(value=credential_yaml['signoz_api_token'])
        ))

    elif c_type == 'SENTRY':
        if 'api_key' not in credential_yaml or 'org_slug' not in credential_yaml:
            raise Exception(f'Api key or org slug not found in credential yaml for sentry source in connector: {connector_name}')
        c_source = Source.SENTRY
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.SENTRY_API_KEY,
            key=StringValue(value=credential_yaml['api_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.SENTRY_ORG_SLUG,
            key=StringValue(value=credential_yaml['org_slug'])
        ))
    
    elif c_type == 'NEW_RELIC':
        if 'api_key' not in credential_yaml or 'app_id' not in credential_yaml or 'api_domain' not in credential_yaml:
            raise Exception(f'Api key, app id or api domain not found in credential yaml for new relic source in connector: {connector_name}')
        c_source = Source.NEW_RELIC
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.NEWRELIC_API_KEY,
            key=StringValue(value=credential_yaml['api_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.NEWRELIC_APP_ID,
            key=StringValue(value=credential_yaml['app_id'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.NEWRELIC_API_DOMAIN,
            key=StringValue(value=credential_yaml['api_domain'])
        ))
    elif c_type == 'GCM':
        if 'project_id' not in credential_yaml or 'service_account_json' not in credential_yaml:
            raise Exception(f'Project id or service account json not found in credential yaml for gcm source in connector: {connector_name}')
        c_source = Source.GCM
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GCM_PROJECT_ID,
            key=StringValue(value=credential_yaml['project_id'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GCM_SERVICE_ACCOUNT_JSON,
            key=StringValue(value=credential_yaml['service_account_json'])
        ))
    elif c_type == 'AZURE':
        if 'client_id' not in credential_yaml or 'client_secret' not in credential_yaml or 'tenant_id' not in credential_yaml or 'subscription_id' not in credential_yaml:
            raise Exception(f'Client id, client secret, tenant id or subscription id not found in credential yaml for azure source in connector: {connector_name}')
        c_source = Source.AZURE
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AZURE_CLIENT_ID,
            key=StringValue(value=credential_yaml['client_id'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AZURE_CLIENT_SECRET,
            key=StringValue(value=credential_yaml['client_secret'])
        ))  
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AZURE_TENANT_ID,
            key=StringValue(value=credential_yaml['tenant_id'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.AZURE_SUBSCRIPTION_ID,
            key=StringValue(value=credential_yaml['subscription_id'])
        ))
    elif c_type == 'GITHUB_ACTIONS':
        if 'token' not in credential_yaml:
            raise Exception(f'Token not found in credential yaml for github actions source in connector: {connector_name}')
        c_source = Source.GITHUB_ACTIONS
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GITHUB_ACTIONS_TOKEN,
            key=StringValue(value=credential_yaml['token'])
        ))
    elif c_type == 'DATADOG':
        if 'dd_api_key' not in credential_yaml or 'dd_app_key' not in credential_yaml or 'dd_api_domain' not in credential_yaml:
            raise Exception(f'Api key, app key or api domain not found in credential yaml for datadog source in connector: {connector_name}')
        c_source = Source.DATADOG
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.DATADOG_API_KEY, 
            key=StringValue(value=credential_yaml['dd_api_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.DATADOG_APP_KEY,
            key=StringValue(value=credential_yaml['dd_app_key'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.DATADOG_API_DOMAIN,
            key=StringValue(value=credential_yaml['dd_api_domain'])
        ))
    else:
        raise Exception(f'Invalid type in credential yaml for connector: {connector_name}')
    
    if connector_id:
        return Connector(type=c_source, name=StringValue(value=connector_name), keys=c_keys, id=UInt64Value(value=connector_id))
    else:
        return Connector(type=c_source, name=StringValue(value=connector_name), keys=c_keys)
