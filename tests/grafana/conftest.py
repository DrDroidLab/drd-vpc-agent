import os
from typing import List, Optional

import pytest
import yaml
import django
from django.conf import settings
from django.test import Client
from django.core.management import execute_from_command_line

# Set required environment variables before Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent.settings')
os.environ.setdefault('DRD_AGENT_MODE', 'mcp')
os.environ.setdefault('DRD_CLOUD_API_TOKEN', 'mcp-mode')
os.environ.setdefault('DJANGO_DEBUG', 'True')

# Configure Django settings for tests
django.setup()

# Import evaluation utilities (optional)
try:
    from tests.grafana.utils import GrafanaResponseEvaluator
except ImportError:
    GrafanaResponseEvaluator = None


@pytest.fixture(scope="session")
def grafana_config():
    """
    Loads the Grafana configuration from credentials/secrets.yaml file.
    """
    config_path = "credentials/secrets.yaml"
    if not os.path.exists(config_path):
        pytest.skip(f"Config file not found at {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Look for grafana connector configuration
    grafana_config = None
    for connector in config.get("connectors", []):
        if connector.get("connector_name") == "grafana":
            grafana_config = connector
            break
    
    if not grafana_config:
        pytest.skip("Grafana connector not found in secrets.yaml")
    
    return grafana_config


@pytest.fixture(scope="session")
def django_db_setup():
    """Setup Django database for testing"""
    from django.core.management import call_command
    call_command('migrate', verbosity=0, interactive=False)


@pytest.fixture(scope="module")
def client():
    """A Django test client for the app."""
    return Client()


@pytest.fixture(scope="session")
def openai_api_key():
    """Fixture to get the OpenAI API key."""
    # Try to get from environment first
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Fallback to credentials file
    config_path = "credentials/secrets.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                for connector in config.get("connectors", []):
                    if connector.get("connector_name") == "openai":
                        api_key = connector.get("configuration", {}).get("api_key")
                        if api_key:
                            return api_key
        except yaml.YAMLError:
            pass  # Ignore malformed config

    return None


@pytest.fixture(scope="module")
def evaluator(openai_api_key):
    """Fixture to create a GrafanaResponseEvaluator instance for testing."""
    if GrafanaResponseEvaluator is None:
        pytest.skip("langevals not available - install with: pip install 'langevals[openai]'")

    if not openai_api_key:
        pytest.skip("OpenAI API key required for evaluation")

    # Use gpt-4o-mini for cost-effective testing
    return GrafanaResponseEvaluator(model="gpt-4o-mini")


@pytest.fixture(scope="module")
def mcp_client(openai_api_key, client):
    """Fixture to create an OpenAIMCPClient instance for testing."""
    if not openai_api_key:
        pytest.skip("OpenAI API key not available")

    from tests.grafana.clients.openai import OpenAIMCPClient

    mcp_client_instance = OpenAIMCPClient(
        test_client=client,
        openai_api_key=openai_api_key,
    )
    yield mcp_client_instance
    mcp_client_instance.close()


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Setup environment for testing."""
    # Set Django to MCP mode
    os.environ["DRD_AGENT_MODE"] = "mcp"
    os.environ["DRD_CLOUD_API_TOKEN"] = "mcp-mode"
    os.environ["DJANGO_DEBUG"] = "True"
    
    # Try to set OpenAI API key from config if not already set
    if not os.environ.get("OPENAI_API_KEY"):
        config_path = "credentials/secrets.yaml"
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    for connector in config.get("connectors", []):
                        if connector.get("connector_name") == "openai":
                            api_key = connector.get("configuration", {}).get("api_key")
                            if api_key:
                                os.environ["OPENAI_API_KEY"] = api_key
                                break
            except yaml.YAMLError:
                pass

    yield


# Custom pytest markers for pass rate functionality
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "flaky: mark test as potentially flaky")
    config.addinivalue_line("markers", "pass_rate: specify minimum pass rate for test")


def assert_response_quality(
    prompt: str,
    response: str,
    evaluator,
    min_pass_rate: float = 0.8,
    specific_checks: Optional[List[str]] = None,
    required_checks: Optional[List[str]] = None,
):
    """
    Assert response quality using LLM evaluation.

    Args:
        prompt: The input prompt
        response: The generated response
        evaluator: Response evaluator instance
        min_pass_rate: Minimum pass rate required
        specific_checks: List of specific checks to run
        required_checks: List of required checks that must pass
    """
    if evaluator is None:
        pytest.skip("LLM evaluator not available")

    from tests.grafana.utils import assert_evaluation_passes, evaluate_response_quality

    results = evaluate_response_quality(
        prompt=prompt, 
        response=response, 
        evaluator=evaluator, 
        specific_checks=specific_checks
    )

    assert_evaluation_passes(
        evaluation_results=results, 
        min_pass_rate=min_pass_rate, 
        required_checks=required_checks
    )
