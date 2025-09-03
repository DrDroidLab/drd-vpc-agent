#!/bin/bash

set -e

NAMESPACE="drdroid"

# Check if the DRD_CLOUD_API_TOKEN is passed as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <DRD_CLOUD_API_TOKEN>"
  exit 1
fi

DRD_CLOUD_API_TOKEN=$1

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the helm directory
cd "$SCRIPT_DIR"

# Create the namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f configmap.yaml -n $NAMESPACE

# Create a values.override.yaml file to override the global API token
cat <<EOF > values.override.yaml
global:
  DRD_CLOUD_API_TOKEN: "$DRD_CLOUD_API_TOKEN"
EOF

# Run the Helm upgrade/install command with the override file
helm upgrade --install drd-vpc-agent . \
  -n $NAMESPACE \
  -f values.yaml \
  -f values.override.yaml
