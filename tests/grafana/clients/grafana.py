import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GrafanaMCPClient:
    """
    Client for interacting with the Grafana MCP server for testing purposes.
    Wraps the Django test client and provides MCP protocol methods.
    """

    def __init__(self, test_client: Any, api_key: str = "test-key"):
        """
        Initialize the Grafana MCP client.

        Args:
            test_client: Django test client instance
            api_key: API key for MCP server (for testing)
        """
        self.test_client = test_client
        self.api_key = api_key
        self.session_initialized = False
        self.mcp_url = "/playbooks/mcp"
        self._initialize_session()

    def _initialize_session(self):
        """Initialize the MCP session."""
        try:
            response = self.test_client.post(
                self.mcp_url,
                data=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18", 
                            "capabilities": {}, 
                            "clientInfo": {
                                "name": "test-client", 
                                "version": "1.0.0"
                            }
                        },
                        "id": "init-1",
                    }
                ),
                content_type="application/json",
            )

            if response.status_code == 200:
                self.session_initialized = True
                logger.info("MCP session initialized successfully")
            else:
                logger.error(f"Failed to initialize MCP session: {response.status_code}")

        except Exception as e:
            logger.error(f"Error initializing MCP session: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        try:
            response = self.test_client.post(
                self.mcp_url, 
                data=json.dumps({
                    "jsonrpc": "2.0", 
                    "method": "tools/list", 
                    "params": {}, 
                    "id": "tools-list"
                }), 
                content_type="application/json"
            )

            if response.status_code != 200:
                logger.error(f"Failed to list tools: HTTP {response.status_code}")
                return []

            # Django test client uses json() method instead of get_json()
            response_data = response.json()

            if "error" in response_data:
                logger.error(f"MCP error listing tools: {response_data['error']}")
                return []

            if "result" in response_data and "tools" in response_data["result"]:
                return response_data["result"]["tools"]

            return []

        except Exception as e:
            logger.error(f"Exception listing tools: {e}")
            return []

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on the MCP server.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool

        Returns:
            Tool execution result
        """
        try:
            response = self.test_client.post(
                self.mcp_url,
                data=json.dumps(
                    {
                        "jsonrpc": "2.0", 
                        "method": "tools/call", 
                        "params": {
                            "name": tool_name, 
                            "arguments": parameters
                        }, 
                        "id": f"tool-{tool_name}"
                    }
                ),
                content_type="application/json",
            )

            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}

            # Django test client uses json() method instead of get_json()
            response_data = response.json()

            if "error" in response_data:
                return {"error": response_data["error"].get("message", "Unknown MCP error")}

            if "result" in response_data:
                result = response_data["result"]

                # Extract content from MCP result format
                if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                    content_item = result["content"][0]
                    if "text" in content_item:
                        try:
                            # Try to parse JSON content
                            return json.loads(content_item["text"])
                        except json.JSONDecodeError:
                            # Return as plain text if not JSON
                            return {"content": content_item["text"]}

                # Return raw result if content format is unexpected
                return result

            return {"error": "No result in response"}

        except Exception as e:
            logger.error(f"Exception executing tool {tool_name}: {e}")
            return {"error": str(e)}

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Grafana via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_fetch_datasources", {})

    def fetch_dashboards(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Fetch dashboards via MCP server."""
        params = {}
        if limit is not None:
            params["limit"] = limit
        return self.execute_tool("mcp_droid-vpc-agent_grafana_fetch_all_dashboards", params)

    def get_dashboard_config(self, dashboard_uid: str) -> Dict[str, Any]:
        """Get dashboard configuration via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_get_dashboard_config", {"dashboard_uid": dashboard_uid})

    def execute_dashboard_panels(self, dashboard_uid: str, template_variables: str = "{}") -> Dict[str, Any]:
        """Execute all dashboard panels via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_execute_all_dashboard_panels", {
            "dashboard_uid": dashboard_uid,
            "template_variables": template_variables
        })

    def query_datasource(self, datasource_uid: str, query_expression: str, query_type: str = "prometheus") -> Dict[str, Any]:
        """Execute datasource query via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_datasource_query_execution", {
            "datasource_uid": datasource_uid,
            "query_expression": query_expression,
            "query_type": query_type
        })

    def fetch_datasources(self) -> Dict[str, Any]:
        """Fetch datasources via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_fetch_datasources", {})

    def fetch_folders(self) -> Dict[str, Any]:
        """Fetch folders via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_fetch_folders", {})

    def fetch_dashboard_variables(self, dashboard_uid: str) -> Dict[str, Any]:
        """Fetch dashboard variables via MCP server."""
        return self.execute_tool("mcp_droid-vpc-agent_grafana_fetch_dashboard_variables", {"dashboard_uid": dashboard_uid})

    def close_session(self):
        """Close the MCP session."""
        self.session_initialized = False
        logger.info("MCP session closed")
