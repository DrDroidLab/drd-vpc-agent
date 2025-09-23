#!/bin/bash

# Deploy K8s - Main deployment script for DRD VPC Agent and Network Mapper
# Usage: ./deploy_k8s.sh <DRD_CLOUD_API_TOKEN> [--no-network-mapper] [--no-write-access]

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
    
    # Run the script and capture exit code
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
    
    # Update values.yaml with the configuration flags
    # This ensures that ArgoCD users can also control these settings
    
    # Update network mapper configuration
    if [ "$ENABLE_NETWORK_MAPPER" = false ]; then
        # Update or add network mapper disable flag
        if grep -q "networkMapper:" "$values_file" && grep -q "enabled:" "$values_file"; then
            # Update existing enabled value
            sed -i.bak '/networkMapper:/,/^[^[:space:]]/ s/enabled:.*/enabled: false/' "$values_file"
        else
            # Add new networkMapper section
            if grep -q "networkMapper:" "$values_file"; then
                # Section exists but no enabled field, add it
                sed -i.bak '/networkMapper:/a\  enabled: false' "$values_file"
            else
                # Section doesn't exist, add it
                echo -e "\nnetworkMapper:\n  enabled: false" >> "$values_file"
            fi
        fi
    else
        # Ensure network mapper is enabled (default)
        if grep -q "networkMapper:" "$values_file" && grep -q "enabled:" "$values_file"; then
            # Update existing enabled value
            sed -i.bak '/networkMapper:/,/^[^[:space:]]/ s/enabled:.*/enabled: true/' "$values_file"
        else
            # Add new networkMapper section
            if grep -q "networkMapper:" "$values_file"; then
                # Section exists but no enabled field, add it
                sed -i.bak '/networkMapper:/a\  enabled: true' "$values_file"
            else
                # Section doesn't exist, add it
                echo -e "\nnetworkMapper:\n  enabled: true" >> "$values_file"
            fi
        fi
    fi
    
    # Update write access configuration
    if [ "$ENABLE_WRITE_ACCESS" = false ]; then
        # Update or add write access disable flag
        if grep -q "writeAccess:" "$values_file" && grep -q "enabled:" "$values_file"; then
            # Update existing enabled value
            sed -i.bak '/writeAccess:/,/^[^[:space:]]/ s/enabled:.*/enabled: false/' "$values_file"
        else
            # Add new writeAccess section
            if grep -q "writeAccess:" "$values_file"; then
                # Section exists but no enabled field, add it
                sed -i.bak '/writeAccess:/a\  enabled: false' "$values_file"
            else
                # Section doesn't exist, add it
                echo -e "\nwriteAccess:\n  enabled: false" >> "$values_file"
            fi
        fi
    else
        # Ensure write access is enabled (default)
        if grep -q "writeAccess:" "$values_file" && grep -q "enabled:" "$values_file"; then
            # Update existing enabled value
            sed -i.bak '/writeAccess:/,/^[^[:space:]]/ s/enabled:.*/enabled: true/' "$values_file"
        else
            # Add new writeAccess section
            if grep -q "writeAccess:" "$values_file"; then
                # Section exists but no enabled field, add it
                sed -i.bak '/writeAccess:/a\  enabled: true' "$values_file"
            else
                # Section doesn't exist, add it
                echo -e "\nwriteAccess:\n  enabled: true" >> "$values_file"
            fi
        fi
    fi
    
    # Clean up backup files
    rm -f "${values_file}.bak"
    
    print_status $GREEN "✓ Helm values updated successfully"
}

# Function to deploy VPC agent directly (replacing deploy_helm.sh functionality)
deploy_vpc_agent() {
    local namespace="drdroid"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    print_status $BLUE "Deploying VPC agent to namespace: $namespace"
    
    # Change to the helm directory
    cd "$script_dir/helm"
    
    # Create the namespace if it doesn't exist
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configmap
    kubectl apply -f configmap.yaml -n "$namespace"
    
    # Create a values.override.yaml file to override the global API token
    cat <<EOF > values.override.yaml
global:
  DRD_CLOUD_API_TOKEN: "$DRD_CLOUD_API_TOKEN"
EOF
    
    # Run the Helm upgrade/install command with the override file
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
    ENABLE_NETWORK_MAPPER=true
    ENABLE_WRITE_ACCESS=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-network-mapper)
                ENABLE_NETWORK_MAPPER=false
                shift
                ;;
            --no-write-access)
                ENABLE_WRITE_ACCESS=false
                shift
                ;;
            --help|-h)
                echo "Usage: $0 <DRD_CLOUD_API_TOKEN> [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --no-network-mapper    Disable network mapper deployment (not recommended)"
                echo "  --no-write-access      Disable write access to cluster (read-only mode)"
                echo "  --help, -h             Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0 your-api-token"
                echo "  $0 your-api-token --no-network-mapper"
                echo "  $0 your-api-token --no-write-access"
                echo "  $0 your-api-token --no-network-mapper --no-write-access"
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
    
    # Check if DRD_CLOUD_API_TOKEN is provided
    if [ -z "$DRD_CLOUD_API_TOKEN" ]; then
        print_status $RED "ERROR: DRD_CLOUD_API_TOKEN is required"
        echo "Usage: $0 <DRD_CLOUD_API_TOKEN> [OPTIONS]"
        echo "Use --help for more information"
        exit 1
    fi
}

# Main deployment function
main() {
    print_status $BLUE "=== DRD VPC Agent K8s Deployment ==="
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Check prerequisites
    print_status $BLUE "Checking prerequisites..."
    
    if ! command_exists kubectl; then
        print_status $RED "ERROR: kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! command_exists helm; then
        print_status $RED "ERROR: helm is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to Kubernetes cluster
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_status $RED "ERROR: Cannot connect to Kubernetes cluster"
        print_status $YELLOW "Please ensure your kubeconfig is properly configured"
        exit 1
    fi
    
    print_status $GREEN "✓ Prerequisites check passed"
    
    # Display deployment configuration
    print_status $BLUE "Deployment Configuration:"
    print_status $BLUE "  - Network Mapper: $([ "$ENABLE_NETWORK_MAPPER" = true ] && echo "ENABLED" || echo "DISABLED")"
    print_status $BLUE "  - Write Access: $([ "$ENABLE_WRITE_ACCESS" = true ] && echo "ENABLED" || echo "DISABLED (Read-only)")"
    
    # Update values.yaml with the configuration flags
    print_status $BLUE "Updating Helm values configuration..."
    update_helm_values
    
    # Initialize deployment status
    deployment_success=true
    
    # Deploy network mapper if enabled
    if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
        print_status $BLUE "Deploying network mapper components..."
        if ! run_deployment "Network Mapper" "network-mapper-helm/deploy-helm.sh"; then
            deployment_success=false
        fi
        
        # Wait for network mapper to be ready before deploying VPC agent
        print_status $YELLOW "Waiting for network mapper to be ready..."
        sleep 10
    else
        print_status $YELLOW "⚠️  Network mapper deployment is DISABLED"
        print_status $YELLOW "   This will limit service topology visibility and network insights"
    fi
    
    # Deploy VPC agent core components
    print_status $BLUE "Deploying VPC agent core components..."
    if ! deploy_vpc_agent; then
        deployment_success=false
    fi
    
    # Final result
    if [ "$deployment_success" = true ]; then
        print_status $GREEN "🎉 Deployment completed successfully!"
        print_status $BLUE "You can check the status of your deployment with:"
        echo "  kubectl get pods -n drdroid"
        if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
            echo "  kubectl get pods -n otterize-system"
        fi
        print_status $BLUE "Deployment Summary:"
        print_status $BLUE "  - VPC Agent: Deployed to 'drdroid' namespace"
        if [ "$ENABLE_NETWORK_MAPPER" = true ]; then
            print_status $BLUE "  - Network Mapper: Deployed to 'otterize-system' namespace"
        else
            print_status $YELLOW "  - Network Mapper: DISABLED (service topology will be limited)"
        fi
        if [ "$ENABLE_WRITE_ACCESS" = false ]; then
            print_status $YELLOW "  - Write Access: DISABLED (read-only mode)"
        fi
        exit 0
    else
        print_status $RED "❌ Deployment failed. Please check the logs above for details."
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 