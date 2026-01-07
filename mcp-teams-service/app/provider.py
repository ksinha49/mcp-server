"""
Teams MCP Provider

Implements Microsoft Graph API operations for Teams:
- Team operations (list, get details)
- Channel operations (list, messages, send)
- Chat operations (list, messages, send)
- Meeting operations (list, create)

Uses Microsoft Graph SDK with OAuth 2.1 authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

# Microsoft Graph API base URL
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class TeamsProvider:
    """
    Microsoft Teams MCP Provider.

    Implements tool execution using Microsoft Graph API.
    Supports both app-only and delegated (user) authentication.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        user_token: Optional[str] = None,
    ):
        """
        Initialize Teams provider.

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            user_token: Optional user access token for delegated auth
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_token = user_token
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Get access token (user token or app token)."""
        if self.user_token:
            return self.user_token

        # Use app-only token
        if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
            return self._app_token

        # Acquire new app token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            data = response.json()

        self._app_token = data["access_token"]
        self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._app_token

    async def _graph_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Any:
        """Make a request to Microsoft Graph API."""
        token = await self._get_token()
        url = f"{GRAPH_API_BASE}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool_handlers = {
            "list_teams": self._list_teams,
            "get_team": self._get_team,
            "list_channels": self._list_channels,
            "get_channel_messages": self._get_channel_messages,
            "send_channel_message": self._send_channel_message,
            "list_chats": self._list_chats,
            "get_chat_messages": self._get_chat_messages,
            "send_chat_message": self._send_chat_message,
            "list_meetings": self._list_meetings,
            "create_meeting": self._create_meeting,
        }

        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return await handler(**arguments)

    async def _list_teams(self, max_results: int = 50) -> List[Dict]:
        """List Teams the user is a member of."""
        params = {
            "$top": max_results,
            "$select": "id,displayName,description,visibility",
        }

        result = await self._graph_request("GET", "/me/joinedTeams", params=params)

        return [
            {
                "id": team["id"],
                "name": team.get("displayName"),
                "description": team.get("description", ""),
                "visibility": team.get("visibility"),
            }
            for team in result.get("value", [])
        ]

    async def _get_team(self, team_id: str) -> Dict:
        """Get details of a specific Team."""
        team = await self._graph_request("GET", f"/teams/{team_id}")

        # Get channels
        channels_result = await self._graph_request(
            "GET", f"/teams/{team_id}/channels",
            params={"$top": 50}
        )

        # Get members
        members_result = await self._graph_request(
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

    async def _list_channels(self, team_id: str) -> List[Dict]:
        """List channels in a Team."""
        result = await self._graph_request(
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

    async def _get_channel_messages(
        self,
        team_id: str,
        channel_id: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """Get messages from a channel."""
        result = await self._graph_request(
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

    async def _send_channel_message(
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

        result = await self._graph_request(
            "POST", f"/teams/{team_id}/channels/{channel_id}/messages",
            json=body
        )

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "status": "sent",
        }

    async def _list_chats(self, max_results: int = 50) -> List[Dict]:
        """List user's chats."""
        params = {
            "$top": max_results,
            "$expand": "members",
        }

        result = await self._graph_request("GET", "/me/chats", params=params)

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

    async def _get_chat_messages(
        self,
        chat_id: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """Get messages from a chat."""
        result = await self._graph_request(
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

    async def _send_chat_message(
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

        result = await self._graph_request(
            "POST", f"/me/chats/{chat_id}/messages",
            json=body
        )

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "status": "sent",
        }

    async def _list_meetings(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """List user's scheduled meetings."""
        # Default to next 7 days
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

        # Use calendar view to get meetings
        params = {
            "startDateTime": start_date,
            "endDateTime": end_date,
            "$top": max_results,
            "$filter": "isOnlineMeeting eq true",
            "$select": "id,subject,organizer,start,end,onlineMeeting,location",
        }

        result = await self._graph_request("GET", "/me/calendar/calendarView", params=params)

        return [
            {
                "id": event["id"],
                "subject": event.get("subject"),
                "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address"),
                "start": event.get("start", {}).get("dateTime"),
                "end": event.get("end", {}).get("dateTime"),
                "join_url": event.get("onlineMeeting", {}).get("joinUrl"),
                "location": event.get("location", {}).get("displayName"),
            }
            for event in result.get("value", [])
        ]

    async def _create_meeting(
        self,
        subject: str,
        start: str,
        end: str,
        attendees: Optional[List[str]] = None,
        content: Optional[str] = None,
    ) -> Dict:
        """Create a new Teams meeting."""
        event = {
            "subject": subject,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness",
        }

        if content:
            event["body"] = {"contentType": "HTML", "content": content}

        if attendees:
            event["attendees"] = [
                {"emailAddress": {"address": addr}, "type": "required"}
                for addr in attendees
            ]

        result = await self._graph_request("POST", "/me/events", json=event)

        return {
            "id": result["id"],
            "subject": result.get("subject"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "join_url": result.get("onlineMeeting", {}).get("joinUrl"),
            "status": "created",
        }
