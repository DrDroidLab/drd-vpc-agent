#!/bin/bash

# Script to deploy network-mapper with locally built images
# Usage: ./deploy-local.sh [release-name] [namespace]

RELEASE_NAME=${1:-network-mapper-local}
NAMESPACE=droid-network-mapper

echo "Deploying network-mapper with locally built images..."
echo "Release name: $RELEASE_NAME"
echo "Namespace: $NAMESPACE"

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy using the local values
helm upgrade --install "$RELEASE_NAME" . \
  --namespace "$NAMESPACE" \
  --values values-local.yaml \
  --wait

echo "Deployment completed!"
echo "Check status with: kubectl get pods -n $NAMESPACE"