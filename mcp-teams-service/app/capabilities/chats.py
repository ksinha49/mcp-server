"""
Chats Capability for Teams MCP Server

Handles chat operations:
- List chats
- Get chat messages
- Send chat messages
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ChatsCapability:
    """Chats capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def list_chats(self, max_results: int = 50) -> List[Dict]:
        """List user's chats."""
        params = {
            "$top": max_results,
            "$expand": "members",
        }

        result = await self.graph.request("GET", "/me/chats", params=params)

        return [
            {
                "id": chat["id"],
                "topic": chat.get("topic", ""),
                "chat_type": chat.get("chatType"),
                "created": chat.get("createdDateTime"),
                "last_updated": chat.get("lastUpdatedDateTime"),
                "members": [
                    m.get("displayName")
                    for m in chat.get("members", [])
                ][:5],
            }
            for chat in result.get("value", [])
        ]

    async def get_chat_messages(
        self,
        chat_id: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """Get messages from a chat."""
        result = await self.graph.request(
            "GET", f"/me/chats/{chat_id}/messages",
            params={"$top": max_results}
        )

        return [
            {
                "id": msg["id"],
                "created": msg.get("createdDateTime"),
                "from": msg.get("from", {}).get("user", {}).get("displayName"),
                "content": msg.get("body", {}).get("content", "")[:500],
                "content_type": msg.get("body", {}).get("contentType"),
            }
            for msg in result.get("value", [])
        ]

    async def send_chat_message(
        self,
        chat_id: str,
        content: str,
        content_type: str = "text",
    ) -> Dict:
        """Send a message in a chat."""
        body = {
            "body": {
                "contentType": "html" if content_type == "html" else "text",
                "content": content,
            }
        }

        result = await self.graph.request(
            "POST", f"/me/chats/{chat_id}/messages",
            json=body
        )

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "status": "sent",
        }
