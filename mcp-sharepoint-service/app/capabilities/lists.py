"""
Lists Capability for SharePoint MCP Server

Handles SharePoint list operations:
- Get list items
- Create list items
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ListsCapability:
    """Lists capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def get_list_items(
        self,
        site_id: str,
        list_id: str,
        filter: Optional[str] = None,
        select: Optional[List[str]] = None,
        max_results: int = 100,
    ) -> List[Dict]:
        """Get items from a SharePoint list."""
        endpoint = f"/sites/{site_id}/lists/{list_id}/items"
        params = {
            "$top": max_results,
            "$expand": "fields",
        }

        if filter:
            params["$filter"] = filter
        if select:
            params["$expand"] = f"fields($select={','.join(select)})"

        result = await self.graph.request("GET", endpoint, params=params)

        return [
            {
                "id": item["id"],
                "created": item.get("createdDateTime"),
                "modified": item.get("lastModifiedDateTime"),
                "fields": item.get("fields", {}),
            }
            for item in result.get("value", [])
        ]

    async def create_list_item(
        self,
        site_id: str,
        list_id: str,
        fields: Dict[str, Any],
    ) -> Dict:
        """Create a new item in a SharePoint list."""
        endpoint = f"/sites/{site_id}/lists/{list_id}/items"

        result = await self.graph.request("POST", endpoint, json={"fields": fields})

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "fields": result.get("fields", {}),
        }
