# Doctor Droid Python Proxy Agent

The present repository contains the source code of the Doctor Droid Python Proxy Agent version 1.0.0.
Read more [here](https://github.com/DrDroidLab/drd-vpc-agent).
![VPC Agent](https://github.com/user-attachments/assets/a17b8904-7811-4597-b4cc-bae34f02cb48)

## Documentation

The Agent runs inside your VPC and acts as a reverse proxy to connect with your metric sources and send
metrics and related data to doctor droid cloud platform. The agent is designed to be lightweight and easy to deploy
with only egress tcp calls to Doctor Droid Cloud Platform.

Currently, the agent supports the following metric sources in your VPC:

- Grafana
- Grafana Loki
- Cloudwatch
- Kubernetes
- Azure AKS (via native Kubernetes)
- AWS EKS (via native Kubernetes)
- GKE (via native Kubernetes)
- New Relic
- Datadog
- Opensearch
- MongoDB
- Github
- Postgres
- Any SQL Database (via Sql Connection String)
- Bash Commands

Releasing soon (reach out to us if you need support for these or any other source):

- Azure

## Installation

## MCP Mode

The Doctor Droid VPC Agent can also run as an MCP (Model Context Protocol) server, allowing you to connect it directly to Cursor or other MCP-compatible clients.

### Docker Compose (MCP Mode)

1. Add your credentials in `credentials/secrets.yaml`
2. Run the MCP server:
   ```shell
   docker compose -f mcp.docker-compose.yaml up --build -d
   ```
3. Add it to your Cursor using the localhost setup with this `mcp.json` configuration:
   ```json
   {
     "mcpServers": {
       "droid-vpc-agent": {
         "url": "http://localhost:8000/playbooks/mcp"
       }
     }
   }
   ```

### Helm (MCP Mode)

For Helm deployment, the process is the same as the normal Helm deployment:

```shell
cd mcp_helm
./deploy_mcp_helm.sh
```

### Local Development (MCP Mode)

1. Create and activate a virtual environment:
   ```shell
   uv venv env
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```shell
   uv pip sync requirements.txt
   ```
3. Start the MCP server:
   ```shell
   sh start_mcp_server.sh
   ```

## Standard Agent Mode

To get started create an agent authentication token by visiting [site](https://playbooks.drdroid.io/agent-tokens)

## Env vars

| Env Var Name        | Description                                    | Required |
| ------------------- | ---------------------------------------------- | -------- |
| DRD_CLOUD_API_TOKEN | Authentication token for doctor droid platform | True     |

### Docker Compose

1. Create credentials/secret.yaml file with valid credentials. Secrets format for different connections can be
   referenced
   from: [credentials/credentials_template.yaml.](https://github.com/DrDroidLab/drd-vpc-agent/blob/main/credentials/credentials_template.yaml)

Command:

```shell
./deploy_docker.sh <API_TOKEN>
```

For any update the agent, re-run the command.

### Helm

1. Add the secrets for the integrations in helm/configmap.yaml file.
   Refer to the image below for a sample:
   <img width="934" alt="Screenshot 2024-12-20 at 14 02 43" src="https://github.com/user-attachments/assets/cadb2b0a-db0c-4128-bef7-fe2a6288b79b" />

Command:

```shell
cd helm
./deploy_helm.sh <API_TOKEN>
```

- The agent will be installed in the namespace 'drdroid' by default. This can be changed in the helm/deploy_helm.sh
  file.
- Agent updates the image automatically every day at 00:00 UTC.
- Agent will have read access to the cluster and will be able to fetch the metrics from the cluster.

## Support

Go through our [documentation](https://docs.drdroid.io?utm_param=github-py) to learn more.
Visit [Doctor Droid website](https://drdroid.io?utm_param=github-py) for more information.

For any queries, reach out at [support@drdroid.io](mailto:support@drdroid.io).

## Contributions

We welcome contributions to the Doctor Droid Python Proxy Agent. If you have any suggestions or improvements, please
feel free to open an issue or submit a pull request. We appreciate your help in making this project better!

### Maintainers:

- [Mohit Goyal](https://github.com/droid-mohit)
