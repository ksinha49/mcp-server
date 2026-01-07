"""
Outlook Provider for Combined Service

Re-exports from mcp-outlook-service for combined deployment.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from mcp.types import Tool

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

OUTLOOK_TOOLS = [
    Tool(
        name="search_emails",
        description="Search emails in mailbox by query, folder, date range, etc.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "folder": {"type": "string", "default": "inbox"},
                "max_results": {"type": "integer", "default": 25},
            },
        },
    ),
    Tool(
        name="get_email",
        description="Get full email by ID with optional attachments.",
        inputSchema={
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "Email ID"},
                "include_attachments": {"type": "boolean", "default": False},
            },
            "required": ["email_id"],
        },
    ),
    Tool(
        name="send_email",
        description="Send a new email.",
        inputSchema={
            "type": "object",
            "properties": {
                "to": {"type": "array", "items": {"type": "string"}},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "body_type": {"type": "string", "enum": ["text", "html"], "default": "text"},
            },
            "required": ["to", "subject", "body"],
        },
    ),
    Tool(
        name="list_calendar_events",
        description="List calendar events within a date range.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "max_results": {"type": "integer", "default": 50},
            },
        },
    ),
    Tool(
        name="create_calendar_event",
        description="Create a new calendar event.",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
                "is_online_meeting": {"type": "boolean", "default": False},
            },
            "required": ["subject", "start", "end"],
        },
    ),
    Tool(
        name="search_contacts",
        description="Search contacts by name or email.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 25},
            },
            "required": ["query"],
        },
    ),
]


class OutlookProvider:
    """Outlook provider implementation."""

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
            "search_emails": self._search_emails,
            "get_email": self._get_email,
            "send_email": self._send_email,
            "list_calendar_events": self._list_calendar_events,
            "create_calendar_event": self._create_calendar_event,
            "search_contacts": self._search_contacts,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(**arguments)

    async def _search_emails(self, query: Optional[str] = None, folder: str = "inbox", max_results: int = 25, **kwargs) -> List[Dict]:
        params = {"$top": max_results, "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead", "$orderby": "receivedDateTime desc"}
        if query:
            params["$search"] = f'"{query}"'
        result = await self._graph_request("GET", f"/me/mailFolders/{folder}/messages", params=params)
        return [{"id": m["id"], "subject": m.get("subject"), "from": m.get("from", {}).get("emailAddress", {}).get("address"), "received": m.get("receivedDateTime")} for m in result.get("value", [])]

    async def _get_email(self, email_id: str, include_attachments: bool = False, **kwargs) -> Dict:
        msg = await self._graph_request("GET", f"/me/messages/{email_id}")
        return {"id": msg["id"], "subject": msg.get("subject"), "body": msg.get("body", {}).get("content")}

    async def _send_email(self, to: List[str], subject: str, body: str, body_type: str = "text", **kwargs) -> Dict:
        message = {"subject": subject, "body": {"contentType": "HTML" if body_type == "html" else "Text", "content": body}, "toRecipients": [{"emailAddress": {"address": addr}} for addr in to]}
        await self._graph_request("POST", "/me/sendMail", json={"message": message})
        return {"status": "sent"}

    async def _list_calendar_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None, max_results: int = 50, **kwargs) -> List[Dict]:
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        params = {"startDateTime": start_date, "endDateTime": end_date, "$top": max_results}
        result = await self._graph_request("GET", "/me/calendar/calendarView", params=params)
        return [{"id": e["id"], "subject": e.get("subject"), "start": e.get("start", {}).get("dateTime")} for e in result.get("value", [])]

    async def _create_calendar_event(self, subject: str, start: str, end: str, attendees: Optional[List[str]] = None, is_online_meeting: bool = False, **kwargs) -> Dict:
        event = {"subject": subject, "start": {"dateTime": start, "timeZone": "UTC"}, "end": {"dateTime": end, "timeZone": "UTC"}}
        if attendees:
            event["attendees"] = [{"emailAddress": {"address": a}, "type": "required"} for a in attendees]
        if is_online_meeting:
            event["isOnlineMeeting"] = True
        result = await self._graph_request("POST", "/me/calendar/events", json=event)
        return {"id": result["id"], "subject": result.get("subject")}

    async def _search_contacts(self, query: str, max_results: int = 25, **kwargs) -> List[Dict]:
        params = {"$search": f'"{query}"', "$top": max_results}
        result = await self._graph_request("GET", "/me/contacts", params=params)
        return [{"id": c["id"], "name": c.get("displayName"), "email": c.get("emailAddresses", [{}])[0].get("address") if c.get("emailAddresses") else None} for c in result.get("value", [])]
