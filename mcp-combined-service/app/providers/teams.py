"""
Teams Provider for Combined Service

Simplified Teams provider for combined deployment.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from mcp.types import Tool

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

TEAMS_TOOLS = [
    Tool(
        name="list_teams",
        description="List Teams the user is a member of.",
        inputSchema={
            "type": "object",
            "properties": {"max_results": {"type": "integer", "default": 50}},
        },
    ),
    Tool(
        name="list_channels",
        description="List channels in a Team.",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="send_channel_message",
        description="Send a message to a channel.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string"},
                "channel_id": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["team_id", "channel_id", "content"],
        },
    ),
    Tool(
        name="list_chats",
        description="List user's chats.",
        inputSchema={
            "type": "object",
            "properties": {"max_results": {"type": "integer", "default": 50}},
        },
    ),
    Tool(
        name="create_meeting",
        description="Create a new Teams meeting.",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["subject", "start", "end"],
        },
    ),
]


class TeamsProvider:
    """Teams provider implementation."""

    def __init__(self, client_id: str, client_secret: str, tenant_id: str, user_token: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_token = user_token
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        if self.user_token:
            return self.user_token
        if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
            return self._app_token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            })
            response.raise_for_status()
            data = response.json()
        self._app_token = data["access_token"]
        self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._app_token

    async def _graph_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Any:
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{GRAPH_API_BASE}{endpoint}",
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "list_teams": self._list_teams,
            "list_channels": self._list_channels,
            "send_channel_message": self._send_channel_message,
            "list_chats": self._list_chats,
            "create_meeting": self._create_meeting,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(**arguments)

    async def _list_teams(self, max_results: int = 50, **kwargs) -> List[Dict]:
        result = await self._graph_request("GET", "/me/joinedTeams", params={"$top": max_results})
        return [{"id": t["id"], "name": t.get("displayName"), "description": t.get("description")} for t in result.get("value", [])]

    async def _list_channels(self, team_id: str, **kwargs) -> List[Dict]:
        result = await self._graph_request("GET", f"/teams/{team_id}/channels")
        return [{"id": c["id"], "name": c.get("displayName")} for c in result.get("value", [])]

    async def _send_channel_message(self, team_id: str, channel_id: str, content: str, **kwargs) -> Dict:
        body = {"body": {"contentType": "text", "content": content}}
        result = await self._graph_request("POST", f"/teams/{team_id}/channels/{channel_id}/messages", json=body)
        return {"id": result["id"], "status": "sent"}

    async def _list_chats(self, max_results: int = 50, **kwargs) -> List[Dict]:
        result = await self._graph_request("GET", "/me/chats", params={"$top": max_results})
        return [{"id": c["id"], "topic": c.get("topic"), "chat_type": c.get("chatType")} for c in result.get("value", [])]

    async def _create_meeting(self, subject: str, start: str, end: str, attendees: Optional[List[str]] = None, **kwargs) -> Dict:
        event = {"subject": subject, "start": {"dateTime": start, "timeZone": "UTC"}, "end": {"dateTime": end, "timeZone": "UTC"}, "isOnlineMeeting": True, "onlineMeetingProvider": "teamsForBusiness"}
        if attendees:
            event["attendees"] = [{"emailAddress": {"address": a}, "type": "required"} for a in attendees]
        result = await self._graph_request("POST", "/me/events", json=event)
        return {"id": result["id"], "join_url": result.get("onlineMeeting", {}).get("joinUrl")}
