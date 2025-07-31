"""
Simple test to verify Django MCP server setup is working.
"""
import pytest
import os
import django
from django.test import Client
from django.conf import settings

# Set up Django before importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent.settings')
os.environ.setdefault('DRD_AGENT_MODE', 'mcp')
os.environ.setdefault('DRD_CLOUD_API_TOKEN', 'mcp-mode')
os.environ.setdefault('DJANGO_DEBUG', 'True')

django.setup()

@pytest.mark.django_db
class TestDjangoMCPSetup:
    """Test basic Django MCP server setup."""
    
    def test_django_setup(self):
        """Test that Django is properly configured."""
        from django.conf import settings
        import os
        assert settings.DEBUG is True
        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'agent.settings'
    
    def test_mcp_endpoint_exists(self):
        """Test that the MCP endpoint is accessible."""
        client = Client()
        
        # Test GET request to MCP endpoint (should return server info)
        response = client.get('/playbooks/mcp')
        assert response.status_code == 200
        
        # Should return JSON with server info
        data = response.json()
        assert 'name' in data
        assert data['name'] == 'drdroid-mcp-server'
    
    def test_mcp_endpoint_initialize(self):
        """Test MCP initialize method."""
        client = Client()
        
        # Test initialize request
        response = client.post(
            '/playbooks/mcp',
            data='{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-06-18"}, "id": "test-1"}',
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('jsonrpc') == '2.0'
        assert 'result' in data
        assert data['result']['protocolVersion'] == '2025-06-18' 