import requests
from typing import Any, Dict

class AtlasApiClient:
    """Simple HTTP client for the Atlas API."""

    def __init__(self, base_url: str = "http://localhost:5000") -> None:
        self.base_url = base_url

    def get_graph(self, query_params: Dict[str, Any]) -> bytes:
        response = requests.post(f"{self.base_url}/graph", json=query_params)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if content_type != "image/png":
            raise ValueError("Unexpected content type")
        return response.content
