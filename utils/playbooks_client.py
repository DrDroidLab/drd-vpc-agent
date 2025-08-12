from typing import Dict, Any
import requests
from requests.exceptions import RequestException
from drdroid_debug_toolkit.core.protos.base_pb2 import SourceModelType
from drdroid_debug_toolkit.core.protos.assets.asset_pb2 import AccountConnectorAssets
from utils.proto_utils import dict_to_proto
from agent.settings import DRD_CLOUD_API_TOKEN, DRD_CLOUD_API_HOST


class PrototypeClient:
    """
    Client for interacting with the DrDroid Platform.
    
    This client provides methods to interact with various DrDroid Platform APIs
    in a clean and type-safe manner.
    """

    def __init__(self):
        """
        Initialize the client.
        """
        if not DRD_CLOUD_API_TOKEN and not DRD_CLOUD_API_HOST:
            raise ValueError("DRD_CLOUD_API_TOKEN and DRD_CLOUD_API_HOST must be set")

        self.auth_token = DRD_CLOUD_API_TOKEN
        self.base_url = DRD_CLOUD_API_HOST

    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers for API requests."""
        return {
            'content-type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}',
        }

    def get_connector_assets(
        self,
        connector_type: str,
        connector_id: str,
        asset_type: SourceModelType,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Retrieve connector assets based on specified parameters.

        Args:
            connector_type (str): Type of the connector (e.g., 'CLOUDWATCH')
            connector_id (str): ID of the connector

        Returns:
            Dict[str, Any]: Response data from the API

        Raises:
            Exception: If the API request fails
        """
        payload = {
            "connector_type": connector_type,
            "connector_id": connector_id,
            "type": asset_type,
        }

        if filters:
            payload["filters"] = filters

        try:
            response = requests.post(
                f"{self.base_url}/connectors/proxy/assets/models/get",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return self.post_process_assets(response.json())

        except RequestException as e:
            raise Exception(f"Failed to get connector assets: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Failed to get connector assets: {str(e)}") from e
    
    def post_process_assets(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process the assets to ensure they are in the correct format.
        """
        return dict_to_proto(assets['assets'][0], AccountConnectorAssets)
