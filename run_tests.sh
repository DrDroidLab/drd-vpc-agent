#!/bin/bash

# Test runner script for Django MCP server
# This script sets up environment variables and runs the tests

# Check if OpenAI API key is provided as argument
if [ $# -eq 0 ]; then
    echo "Usage: ./run_tests.sh <OPENAI_API_KEY> [test_path] [test_name]"
    echo "Example: ./run_tests.sh sk-1234567890abcdef tests/grafana/"
    echo "Example: ./run_tests.sh sk-1234567890abcdef tests/test_django_setup.py"
    echo "Example: ./run_tests.sh sk-1234567890abcdef tests/grafana/tools/test_ai_tools.py test_openai_client_initialization"
    echo "Example: ./run_tests.sh sk-1234567890abcdef  # runs all tests"
    exit 1
fi

OPENAI_API_KEY=$1
TEST_PATH=${2:-"tests/"}  # Default to all tests if no path specified
TEST_NAME=${3:-""}  # Optional test name to run specific test

echo "🚀 Setting up environment for Django MCP server tests..."

# Set required Django environment variables
export DRD_AGENT_MODE=mcp
export DRD_CLOUD_API_TOKEN=mcp-mode
export DJANGO_DEBUG=True
export DJANGO_SETTINGS_MODULE=agent.settings

# Set OpenAI API key
export OPENAI_API_KEY=$OPENAI_API_KEY

echo "✅ Environment variables set"
echo "🔑 OpenAI API Key: ${OPENAI_API_KEY:0:8}..." # Show only first 8 characters for security
echo "📂 Test path: $TEST_PATH"
if [ ! -z "$TEST_NAME" ]; then
    echo "🎯 Test name: $TEST_NAME"
fi
echo ""

# Activate virtual environment and run tests
echo "🧪 Activating virtual environment and running tests..."
source .venv/bin/activate

if [ ! -z "$TEST_NAME" ]; then
    uv run pytest $TEST_PATH -k "$TEST_NAME" -v
else
    uv run pytest $TEST_PATH -v
fi

# Show exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests completed successfully!"
else
    echo ""
    echo "❌ Some tests failed. Check the output above for details."
    exit 1
fi 