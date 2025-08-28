#!/bin/bash

# Script to deploy network-mapper with locally built images
# Usage: ./deploy-local.sh [release-name] [namespace]

RELEASE_NAME=network-mapper
NAMESPACE=otterize-system

echo "Deploying network-mapper with locally built images..."
echo "Release name: $RELEASE_NAME"
echo "Namespace: $NAMESPACE"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the network-mapper-helm directory
cd "$SCRIPT_DIR"

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy using the local values
helm upgrade --install "$RELEASE_NAME" . \
  --namespace "$NAMESPACE" \
  --values values-local.yaml \
  --wait

echo "Deployment completed!"
echo "Check status with: kubectl get pods -n $NAMESPACE"