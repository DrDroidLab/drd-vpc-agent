from google.protobuf.wrappers_pb2 import StringValue

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
                ssh_servers = ssh_servers.replace(' ', '')
                ssh_servers = ssh_servers.split(',')
                ssh_servers = list(filter(None, ssh_servers))
                credentials_dict['remote_host'] = ssh_servers[0]
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_PEM:
                credentials_dict['remote_pem'] = conn_key.key.value
            elif conn_key.key_type == SourceKeyType.REMOTE_SERVER_PASSWORD:
                credentials_dict['remote_password'] = conn_key.key.value
            if 'remote_pem' not in credentials_dict:
                credentials_dict['remote_pem'] = None
            if 'remote_password' not in credentials_dict:
                credentials_dict['remote_password'] = None
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
    else:
        return None
    return credentials_dict


def credential_yaml_to_connector_proto(connector_name, credential_yaml):
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
            raise Exception(
                f'No credentials found in credential yaml for eks source in connector: {connector_name}')

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

        if credential_yaml.get('aws_assumed_role_arn', None):
            pass
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
        # host: str, port: int, protocol: str, x_scope_org_id: str = 'anonymous', ssl_verify: bool = True):
        if 'host' not in credential_yaml or 'grafana_api_key' not in credential_yaml:
            raise Exception(
                f'Host not found in credential yaml for grafana loki source in connector: {connector_name}')

        if 'port' not in credential_yaml:
            raise Exception(
                f'Port not found in credential yaml for grafana loki source in connector: {connector_name}')

        if 'protocol' not in credential_yaml:
            raise Exception(
                f'Protocol not found in credential yaml for grafana loki source in connector: {connector_name}')

        c_source = Source.GRAFANA

        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_LOKI_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.GRAFANA_LOKI_PORT,
            key=StringValue(value=credential_yaml['port'])
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
            c_keys.append(ConnectorKey(
                key_type=SourceKeyType.SSL_VERIFY,
                key=StringValue(value=credential_yaml['ssl_verify'])
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
        if 'remote_host' not in credential_yaml:
            raise Exception(
                f'remote_host not found in credential yaml for bash source in connector: {connector_name}')

        c_source = Source.BASH
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.REMOTE_SERVER_HOST,
            key=StringValue(value=credential_yaml['remote_host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.REMOTE_SERVER_PASSWORD,
            key=StringValue(value=credential_yaml['remote_password'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.REMOTE_SERVER_PEM,
            key=StringValue(value=credential_yaml['remote_pem'])
        ))
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
        if 'host' not in credential_yaml or 'port' not in credential_yaml or 'protocol' not in credential_yaml or 'username' not in credential_yaml or 'password' not in credential_yaml:
            raise Exception(
                f'Host, port, protocol, username or password not found in credential yaml for open search source in connector: {connector_name}')

        c_source = Source.OPEN_SEARCH
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_HOST,
            key=StringValue(value=credential_yaml['host'])
        ))
        c_keys.append(ConnectorKey(
            key_type=SourceKeyType.OPEN_SEARCH_PORT,
            key=StringValue(value=credential_yaml['port'])
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
    else:
        raise Exception(f'Invalid type in credential yaml for connector: {connector_name}')
    return Connector(type=c_source, name=StringValue(value=connector_name), keys=c_keys)
