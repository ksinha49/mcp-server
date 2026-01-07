"""
Teams Capability for Teams MCP Server

Handles team operations:
- List teams
- Get team details
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class TeamsCapability:
    """Teams capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def list_teams(self, max_results: int = 50) -> List[Dict]:
        """List Teams the user is a member of."""
        params = {
            "$top": max_results,
            "$select": "id,displayName,description,visibility",
        }

        result = await self.graph.request("GET", "/me/joinedTeams", params=params)

        return [
            {
                "id": team["id"],
                "name": team.get("displayName"),
                "description": team.get("description", ""),
                "visibility": team.get("visibility"),
            }
            for team in result.get("value", [])
        ]

    async def get_team(self, team_id: str) -> Dict:
        """Get details of a specific Team."""
        team = await self.graph.request("GET", f"/teams/{team_id}")

        # Get channels
        channels_result = await self.graph.request(
            "GET", f"/teams/{team_id}/channels",
            params={"$top": 50}
        )

        # Get members
        members_result = await self.graph.request(
            "GET", f"/teams/{team_id}/members",
            params={"$top": 100}
        )

        return {
            "id": team["id"],
            "name": team.get("displayName"),
            "description": team.get("description", ""),
            "visibility": team.get("visibility"),
            "is_archived": team.get("isArchived", False),
            "channels": [
                {
                    "id": ch["id"],
                    "name": ch.get("displayName"),
                    "description": ch.get("description", ""),
                    "membership_type": ch.get("membershipType"),
                }
                for ch in channels_result.get("value", [])
            ],
            "member_count": len(members_result.get("value", [])),
        }
