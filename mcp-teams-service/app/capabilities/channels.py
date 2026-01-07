"""
Channels Capability for Teams MCP Server

Handles channel operations:
- List channels
- Get channel messages
- Send channel messages
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ChannelsCapability:
    """Channels capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def list_channels(self, team_id: str) -> List[Dict]:
        """List channels in a Team."""
        result = await self.graph.request(
            "GET", f"/teams/{team_id}/channels",
            params={"$top": 100}
        )

        return [
            {
                "id": ch["id"],
                "name": ch.get("displayName"),
                "description": ch.get("description", ""),
                "membership_type": ch.get("membershipType"),
                "web_url": ch.get("webUrl"),
            }
            for ch in result.get("value", [])
        ]

    async def get_channel_messages(
        self,
        team_id: str,
        channel_id: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """Get messages from a channel."""
        result = await self.graph.request(
            "GET", f"/teams/{team_id}/channels/{channel_id}/messages",
            params={"$top": max_results}
        )

        return [
            {
                "id": msg["id"],
                "created": msg.get("createdDateTime"),
                "from": msg.get("from", {}).get("user", {}).get("displayName"),
                "content": msg.get("body", {}).get("content", "")[:500],
                "content_type": msg.get("body", {}).get("contentType"),
                "importance": msg.get("importance"),
                "reply_count": len(msg.get("replies", [])),
            }
            for msg in result.get("value", [])
        ]

    async def send_channel_message(
        self,
        team_id: str,
        channel_id: str,
        content: str,
        content_type: str = "text",
    ) -> Dict:
        """Send a message to a channel."""
        body = {
            "body": {
                "contentType": "html" if content_type == "html" else "text",
                "content": content,
            }
        }

        result = await self.graph.request(
            "POST", f"/teams/{team_id}/channels/{channel_id}/messages",
            json=body
        )

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "status": "sent",
        }
