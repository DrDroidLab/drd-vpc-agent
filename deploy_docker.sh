#!/bin/bash

# Check if the token is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <DRD_CLOUD_API_TOKEN>"
  exit 1
fi

DRD_CLOUD_API_TOKEN=$1

echo "🔽 Bringing down Docker Compose stack..."
docker-compose -f agent.docker-compose.yaml down

echo "📦 Stashing local changes (if any)..."
git stash

echo "⬇️ Pulling latest changes from origin/main..."
git pull origin main

echo "📤 Reapplying stashed changes (if any)..."
git stash pop

echo "🗑️ Removing old Docker container (if exists)..."
docker rm -f drd_agent 2>/dev/null || echo "No existing container to remove."

echo "🗑️ Removing old Docker image (if exists)..."
docker rmi drd_agent 2>/dev/null || echo "No existing image to remove."

echo "📝 Capturing current commit hash..."
COMMIT_HASH=$(git rev-parse HEAD)

echo "🚀 Starting Docker Compose with new deployment... with commit hash: $COMMIT_HASH"
DRD_CLOUD_API_TOKEN="$DRD_CLOUD_API_TOKEN" COMMIT_HASH="$COMMIT_HASH" IS_KUBERNETES="False" docker-compose -f agent.docker-compose.yaml up -d

echo "✅ Deployment complete."