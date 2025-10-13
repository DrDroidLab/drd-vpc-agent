# Doctor Droid Python Proxy Agent

The present repository contains the source code of the Doctor Droid Python Proxy Agent version 1.0.0.
Read more [here](https://github.com/DrDroidLab/drd-vpc-agent).
![VPC Agent](https://github.com/user-attachments/assets/a17b8904-7811-4597-b4cc-bae34f02cb48)

## Documentation

The Agent runs inside your VPC and acts as a reverse proxy to connect with your metric sources and send
metrics and related data to doctor droid cloud platform. The agent is designed to be lightweight and easy to deploy
with only egress tcp calls to Doctor Droid Cloud Platform.

Currently, the agent supports the following metric sources in your VPC:

* Grafana
* Grafana Loki
* Cloudwatch
* Kubernetes
* Azure AKS (via native Kubernetes)
* AWS EKS (via native Kubernetes)
* GKE (via native Kubernetes)
* New Relic
* Datadog
* Opensearch
* MongoDB
* Github
* Postgres
* Any SQL Database (via Sql Connection String)
* Bash Commands

Releasing soon (reach out to us if you need support for these or any other source):

* Azure

## Env vars

| Env Var Name        | Description                                    | Required | 
|---------------------|------------------------------------------------|----------|
| DRD_CLOUD_API_TOKEN | Authentication token for doctor droid platform | True     |

## Installation

To get started create an agent authentication token by visiting [site](https://playbooks.drdroid.io/agent-tokens)

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

#### Basic Deployment

```shell
./deploy_k8s.sh <API_TOKEN>
```

#### Advanced Deployment Options

The deployment script supports several CLI flags for enhanced control:

```shell
# Show help and available options
./deploy_k8s.sh --help

# Deploy without network mapper (not recommended)
./deploy_k8s.sh <API_TOKEN> --no-network-mapper

# Deploy with auto-updation of agent disabled
./deploy_k8s.sh <API_TOKEN> --no-auto-update

# Deploy with both network mapper and auto-updation of agent disabled
./deploy_k8s.sh <API_TOKEN> --no-network-mapper --no-auto-update
```

#### Configuration Flags

| Flag | Description | Default | Impact |
|------|-------------|---------|---------|
| `--no-network-mapper` | Disable network mapper deployment | **Enabled** | ⚠️ **Limits service topology visibility** |
| `--no-auto-update` | Disable auto-updation feature for agent | **Enabled** | 🔒 **Read-only mode for enhanced security** |

#### Why we recommend deploying the Network Mapper?

The **Network Mapper** is a critical component that provides:

- **Service Topology Visibility**: Maps the complete network topology of your Kubernetes cluster
- **Network Insights**: Discovers service-to-service communication patterns
- **Dependency Mapping**: Identifies which services depend on each other

**⚠️ Important**: Deploying the network mapper will significantly improve the agent's ability to provide comprehensive insights about your infrastructure. It's strongly recommended to keep it enabled unless you have specific security or resource constraints.

#### Why we recommend the write access?
The write access is only obtained on the deployments and replicasets within the cluster. It allows the agent to auto-update itself on a daily basis, thus bringing enhanced features and bug fixes without intervention of the developer. 

If you don't give the write access, then execute the following commands each time you want to update the agent with latest features and fixes.
```shell
kubectl rollout restart deployment drd-vpc-agent-celery-beat -n drdroid
kubectl rollout restart deployment drd-vpc-agent-celery-worker -n drdroid
```

#### ArgoCD Integration

The configuration flags are also available in `helm/values.yaml` for ArgoCD users:

```yaml
# Network Mapper Configuration
networkMapper:
  enabled: true  # Set to false to disable

# Write Access Configuration  
writeAccess:
  enabled: true  # Set to false for read-only mode
```

#### Deployment Details
* The agent will be installed in the namespace 'drdroid' by default
* Network mapper components are deployed to 'otterize-system' namespace (when enabled)
* Agent updates the image automatically every day at 00:00 UTC
* Agent will have read access to the cluster and will be able to fetch the metrics from the cluster
* Write access can be controlled via CLI flags or Helm values for enhanced security

## Pod Log Collection

The project includes a Python script to collect logs from all pods in the drdroid namespace for troubleshooting and analysis purposes.

### Basic Usage

```bash
# Collect logs from the last 15 minutes (default)
python utils/collect_pod_logs.py

# Collect logs from the last 30 minutes
python utils/collect_pod_logs.py --minutes 30

# Collect from a different namespace
python utils/collect_pod_logs.py --namespace my-namespace

# Save logs to a custom directory
python utils/collect_pod_logs.py --output-dir /path/to/logs
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--minutes` | `-m` | Number of minutes of logs to collect | 15 |
| `--namespace` | `-n` | Kubernetes namespace to collect from | drdroid |
| `--output-dir` | `-o` | Output directory for log files | pod_logs |

### Output

The script creates:
- Individual log files for each pod with standardized naming: `logs_{namespace}_{pod_name}_{timestamp}_past_{minutes}min.txt`
- A summary report: `collection_summary_{timestamp}.txt`

### Prerequisites

- `kubectl` must be installed and configured
- Access to the target Kubernetes cluster
- Appropriate permissions to list pods and collect logs

## Support

Go through our [documentation](https://docs.drdroid.io?utm_param=github-py) to learn more.
Visit [Doctor Droid website](https://drdroid.io?utm_param=github-py) for more information.

For any queries, reach out at [support@drdroid.io](mailto:support@drdroid.io).

## Contributions
We welcome contributions to the Doctor Droid Python Proxy Agent. If you have any suggestions or improvements, please
feel free to open an issue or submit a pull request. We appreciate your help in making this project better!

### Maintainers:
* [Mohit Goyal](https://github.com/droid-mohit)

