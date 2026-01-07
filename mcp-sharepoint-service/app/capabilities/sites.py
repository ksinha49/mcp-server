"""
Sites Capability for SharePoint MCP Server

Handles site operations:
- List sites
- Get site details
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class SitesCapability:
    """Sites capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def list_sites(
        self,
        search: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict]:
        """List SharePoint sites the user has access to."""
        params = {
            "$top": max_results,
            "$select": "id,displayName,name,webUrl,description,createdDateTime,lastModifiedDateTime",
        }

        query = search or "*"
        result = await self.graph.request("GET", f"/sites?search={query}", params=params)

        return [
            {
                "id": site["id"],
                "name": site.get("displayName") or site.get("name"),
                "url": site.get("webUrl"),
                "description": site.get("description", ""),
                "created": site.get("createdDateTime"),
                "modified": site.get("lastModifiedDateTime"),
            }
            for site in result.get("value", [])
        ]

    async def get_site(self, site_id: str) -> Dict:
        """Get details of a specific SharePoint site."""
        endpoint = f"/sites/{site_id}"
        site = await self.graph.request("GET", endpoint)

        # Get lists and drives
        lists_result = await self.graph.request("GET", f"{endpoint}/lists", params={"$top": 50})
        drives_result = await self.graph.request("GET", f"{endpoint}/drives", params={"$top": 50})

        return {
            "id": site["id"],
            "name": site.get("displayName") or site.get("name"),
            "url": site.get("webUrl"),
            "description": site.get("description", ""),
            "created": site.get("createdDateTime"),
            "modified": site.get("lastModifiedDateTime"),
            "lists": [
                {
                    "id": lst["id"],
                    "name": lst.get("displayName"),
                    "description": lst.get("description", ""),
                    "template": lst.get("list", {}).get("template"),
                }
                for lst in lists_result.get("value", [])
            ],
            "drives": [
                {
                    "id": drv["id"],
                    "name": drv.get("name"),
                    "description": drv.get("description", ""),
                    "web_url": drv.get("webUrl"),
                }
                for drv in drives_result.get("value", [])
            ],
        }
