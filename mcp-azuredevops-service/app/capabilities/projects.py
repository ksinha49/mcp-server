"""
Projects Capability for Azure DevOps MCP Server

Handles project operations:
- List projects
- Get project details
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ProjectsCapability:
    """Projects capability implementation."""

    def __init__(self, api_client):
        self.api = api_client

    async def list_projects(self, max_results: int = 100) -> List[Dict]:
        """List projects in the organization."""
        result = await self.api.request(
            "GET", "_apis/projects",
            params={"$top": max_results}
        )

        return [
            {
                "id": proj["id"],
                "name": proj["name"],
                "description": proj.get("description", ""),
                "state": proj.get("state"),
                "visibility": proj.get("visibility"),
                "url": proj.get("url"),
            }
            for proj in result.get("value", [])
        ]

    async def get_project(self, project: str) -> Dict:
        """Get project details."""
        result = await self.api.request(
            "GET", f"_apis/projects/{project}",
            params={"includeCapabilities": True}
        )

        return {
            "id": result["id"],
            "name": result["name"],
            "description": result.get("description", ""),
            "state": result.get("state"),
            "visibility": result.get("visibility"),
            "capabilities": result.get("capabilities", {}),
        }
