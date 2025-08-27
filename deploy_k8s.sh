#!/bin/bash

# Deploy K8s - Main deployment script for DRD VPC Agent and Network Mapper
# Usage: ./deploy_k8s.sh <DRD_CLOUD_API_TOKEN>

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

# Main deployment function
main() {
    print_status $BLUE "=== DRD VPC Agent K8s Deployment ==="
    
    # Check if DRD_CLOUD_API_TOKEN is provided
    if [ -z "$1" ]; then
        print_status $RED "ERROR: DRD_CLOUD_API_TOKEN is required"
        echo "Usage: $0 <DRD_CLOUD_API_TOKEN>"
        exit 1
    fi
    
    DRD_CLOUD_API_TOKEN=$1
    
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
    
    # Initialize deployment status
    deployment_success=true
    
    # Deploy core components
    print_status $BLUE "Deploying core components..."
    if ! run_deployment "Core Components" "helm/deploy_helm.sh" "$DRD_CLOUD_API_TOKEN"; then
        deployment_success=false
    fi
    
    # Deploy additional components
    print_status $BLUE "Deploying additional components..."
    if ! run_deployment "Additional Components" "network-mapper-helm/deploy-helm.sh"; then
        deployment_success=false
    fi
    
    # Final result
    if [ "$deployment_success" = true ]; then
        print_status $GREEN "🎉 Deployment completed successfully!"
        print_status $BLUE "You can check the status of your deployment with:"
        echo "  kubectl get pods -n drdroid"
        echo "  kubectl get pods -n otterize-system"
        exit 0
    else
        print_status $RED "❌ Deployment failed. Please check the logs above for details."
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 