#!/bin/bash

export DRD_AGENT_MODE=mcp
export DRD_CLOUD_API_TOKEN=mcp-mode
export DJANGO_DEBUG=True

uv run python3 manage.py runserver 0.0.0.0:8000