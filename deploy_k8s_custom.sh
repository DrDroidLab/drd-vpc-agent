#!/bin/bash

# Deploy K8s (custom image) - Same as deploy_k8s.sh but accepts a custom image
# repository and tag (e.g. for a private registry mirror like JFrog Artifactory,
# a self-hosted GHCR path, or a pinned release version).
#
# Usage:
#   ./deploy_k8s_custom.sh <DRD_CLOUD_API_TOKEN> \
#       [--image-repository <repo>] [--image-tag <tag>] \
#       [--no-network-mapper] [--no-auto-update]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run a deployment script and capture its result
run_deployment() {
    local script_name=$1
    local script_path=$2
    local args=$3

    print_status $BLUE "Starting deployment: $script_name"

    if [ ! -f "$script_path" ]; then
        print_status $RED "ERROR: Script not found: $script_path"
        return 1
    fi

    if [ ! -x "$script_path" ]; then
        print_status $YELLOW "Making script executable: $script_path"
        chmod +x "$script_path"
    fi

    if eval "$script_path $args"; then
        print_status $GREEN "✓ SUCCESS: $script_name deployment completed"
        return 0
    else
        print_status $RED "✗ FAILED: $script_name deployment failed"
        return 1
    fi
}

# Function to update Helm values.yaml with configuration flags
update_helm_values() {
    local values_file="helm/values.yaml"

    # Create backup of original values.yaml
    if [ -f "$values_file" ]; then
        cp "$values_file" "${values_file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Update network mapper configuration
    if [ "$ENABLE_NETWORK_MAPPER" = false ]; then
        if grep -q "networkMapper:" "$values_file" && grep -q "enabled:" "$values_file"; then
            sed -i.bak '/networkMapper:/,/^[^[:space:]]/ s/enabled:.*/enabled: false/' "$values_file"
        else
            if grep -q "networkMapper:" "$values_file"; then
                sed -i.bak '/networkMapper:/a\  enabled: false' "$values_file"
            else
                echo -e "\nnetworkMapper:\n  enabled: false" >> "$values_file"
            fi
        fi
    else
        if grep -q "networkMapper:" "$values_file" && grep -q "enabled:" "$values_file"; then
            sed -i.bak '/networkMapper:/,/^[^[:space:]]/ s/enabled:.*/enabled: true/' "$values_file"
        else
            if grep -q "networkMapper:" "$values_file"; then
                sed -i.bak '/networkMapper:/a\  enabled: true' "$values_file"
            else
                echo -e "\nnetworkMapper:\n  enabled: true" >> "$values_file"
            fi
        fi
    fi

    # Update auto update configuration
    if [ "$ENABLE_AUTO_UPDATE" = false ]; then
        if grep -q "autoUpdate:" "$values_file" && grep -q "enabled:" "$values_file"; then
            sed -i.bak '/autoUpdate:/,/^[^[:space:]]/ s/enabled:.*/enabled: false/' "$values_file"
        else
            if grep -q "autoUpdate:" "$values_file"; then
                sed -i.bak '/autoUpdate:/a\  enabled: false' "$values_file"
            else
                echo -e "\nautoUpdate:\n  enabled: false" >> "$values_file"
            fi
        fi
    else
        if grep -q "autoUpdate:" "$values_file" && grep -q "enabled:" "$values_file"; then
            sed -i.bak '/autoUpdate:/,/^[^[:space:]]/ s/enabled:.*/enabled: true/' "$values_file"
        else
            if grep -q "autoUpdate:" "$values_file"; then
                sed -i.bak '/autoUpdate:/a\  enabled: true' "$values_file"
            else
                echo -e "\nautoUpdate:\n  enabled: true" >> "$values_file"
            fi
        fi
    fi

    rm -f "${values_file}.bak"

    print_status $GREEN "✓ Helm values updated successfully"
}

# Function to deploy VPC agent with custom image overrides
deploy_vpc_agent() {
    local namespace="drdroid"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    print_status $BLUE "Deploying VPC agent to namespace: $namespace"

    cd "$script_dir/helm"

    # Create the namespace if it doesn't exist
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -

    # Apply credentials secret
    kubectl apply -f credentials-secret.yaml -n "$namespace"

    # Build values.override.yaml: always sets the API token; optionally overrides
    # the image repository and/or tag for both celery-beat and celery-worker.
    {
        echo "global:"
        echo "  DRD_CLOUD_API_TOKEN: \"$DRD_CLOUD_API_TOKEN\""

        if [ -n "$IMAGE_REPOSITORY" ] || [ -n "$IMAGE_TAG" ]; then
            for chart in celery-beat celery-worker; do
                echo "${chart}:"
                echo "  image:"
                [ -n "$IMAGE_REPOSITORY" ] && echo "    repository: \"$IMAGE_REPOSITORY\""
                [ -n "$IMAGE_TAG" ]        && echo "    tag: \"$IMAGE_TAG\""
            done
        fi
    } > values.override.yaml

    if helm upgrade --install drd-vpc-agent . \
        -n "$namespace" \
        -f values.yaml \
        -f values.override.yaml; then
        print_status $GREEN "✓ SUCCESS: VPC Agent deployment completed"
        return 0
    else
        print_status $RED "✗ FAILED: VPC Agent deployment failed"
        return 1
    fi
}

# Parse command line arguments
parse_arguments() {
    DRD_CLOUD_API_TOKEN=""
    IMAGE_REPOSITORY=""
    IMAGE_TAG=""
    ENABLE_NETWORK_MAPPER=true
    ENABLE_AUTO_UPDATE=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --image-repository|--image-repo)
                IMAGE_REPOSITORY="$2"
                shift 2
                ;;
            --image-tag|--image-version)
                # Strip a leading `v` if present so users can pass either `1.0.0`
                # or `v1.0.0` (image tags published by CI have no `v` prefix).
                IMAGE_TAG="${2#v}"
                shift 2
                ;;
            --no-network-mapper)
                ENABLE_NETWORK_MAPPER=false
                shift
                ;;
            --no-auto-update)
                ENABLE_AUTO_UPDATE=false
                shift
                ;;
            --help|-h)
                echo "Usage: $0 <DRD_CLOUD_API_TOKEN> [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --image-repository <repo>  Override image repository for celery-beat and celery-worker"
                echo "                             (e.g. my-artifactory.jfrog.io/docker-local/drd-vpc-agent)"
                echo "  --image-tag <tag>          Override image tag (e.g. 1.0.0)"
                echo "  --no-network-mapper        Disable network mapper deployment (not recommended)"
                echo "  --no-auto-update           Disable automatic deployment updates (restart cronjob)"
                echo "  --help, -h                 Show this help message"
                echo ""
                echo "Aliases: --image-repo = --image-repository, --image-version = --image-tag"
                echo ""
                echo "Examples:"
                echo "  $0 your-api-token"
                echo "  $0 your-api-token --image-tag 1.0.0"
                echo "  $0 your-api-token \\"
                echo "      --image-repository my-artifactory.jfrog.io/docker-local/drd-vpc-agent \\"
                echo "      --image-tag 1.0.0"
                echo "  $0 your-api-token --image-tag 1.0.0 --no-network-mapper"
                exit 0
                ;;
            *)
                if [ -z "$DRD_CLOUD_API_TOKEN" ]; then
                    DRD_CLOUD_API_TOKEN="$1"
                else
                    print_status $RED "ERROR: Unknown argument: $1"
                    echo "Use --help for usage information"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [ -z "$DRD_CLOUD_API_TOKEN" ]; then
        print_status $RED "ERROR: DRD_CLOUD_API_TOKEN is required"
        echo "Usage: $0 <DRD_CLOUD_API_TOKEN> [OPTIONS]"
        echo "Use --help for more information"
        exit 1
    fi
}

# Main deployment function
main() {
    print_status $BLUE "=== DRD VPC Agent K8s Deployment (custom image) ==="

    parse_arguments "$@"

    print_status $BLUE "Checking prerequisites..."

    if ! command_exists kubectl; then
        print_status $RED "ERROR: kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! command_exists helm; then
        print_status $RED "ERROR: helm is not installed or not in PATH"
        exit 1
    fi

    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_status $RED "ERROR: Cannot connect to Kubernetes cluster"
        print_status $YELLOW "Please ensure your kubeconfig is properly configured"
        exit 1
    fi

    print_status $GREEN "✓ Prerequisites check passed"

    print_status $BLUE "Deployment Configuration:"
    print_status $BLUE "  - Image repository: ${IMAGE_REPOSITORY:-<chart default>}"
    print_status $BLUE "  - Image tag:        ${IMAGE_TAG:-<chart default>}"
    print_status $BLUE "  - Network Mapper:   $([ "$ENABLE_NETWORK_MAPPER" = true ] && echo "ENABLED" || echo "DISABLED")"
    print_status $BLUE "  - Auto Update:      $([ "$ENABLE_AUTO_UPDATE" = true ] && echo "ENABLED" || echo "DISABLED")"

    print_status $BLUE "Updating Helm values configuration..."
    update_helm_values

    deployment_success=true

    if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
        print_status $BLUE "Deploying network mapper components..."
        if ! run_deployment "Network Mapper" "network-mapper-helm/deploy-helm.sh"; then
            deployment_success=false
        fi

        print_status $YELLOW "Waiting for network mapper to be ready..."
        sleep 10
    else
        print_status $YELLOW "⚠️  Network mapper deployment is DISABLED"
        print_status $YELLOW "   This will limit service topology visibility and network insights"
    fi

    print_status $BLUE "Deploying VPC agent core components..."
    if ! deploy_vpc_agent; then
        deployment_success=false
    fi

    if [ "$deployment_success" = true ]; then
        print_status $GREEN "🎉 Deployment completed successfully!"
        print_status $BLUE "You can check the status of your deployment with:"
        echo "  kubectl get pods -n drdroid"
        if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
            echo "  kubectl get pods -n otterize-system"
        fi
        print_status $BLUE "Deployment Summary:"
        print_status $BLUE "  - VPC Agent: Deployed to 'drdroid' namespace"
        if [ -n "$IMAGE_REPOSITORY" ]; then
            print_status $BLUE "  - Image repository override: $IMAGE_REPOSITORY"
        fi
        if [ -n "$IMAGE_TAG" ]; then
            print_status $BLUE "  - Image tag override:        $IMAGE_TAG"
        fi
        if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
            print_status $BLUE "  - Network Mapper: Deployed to 'otterize-system' namespace"
        else
            print_status $YELLOW "  - Network Mapper: DISABLED (service topology will be limited)"
        fi
        if [ "$ENABLE_AUTO_UPDATE" = false ]; then
            print_status $YELLOW "  - Auto Update: DISABLED (manual updates required)"
        fi
        exit 0
    else
        print_status $RED "❌ Deployment failed. Please check the logs above for details."
        exit 1
    fi
}

main "$@"
