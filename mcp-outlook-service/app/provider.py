"""
Outlook MCP Provider

Implements Microsoft Graph API operations for Outlook:
- Email operations (search, get, send)
- Calendar operations (list, create)
- Contact operations (search)

Uses Microsoft Graph SDK with OAuth 2.1 authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

# Microsoft Graph API base URL
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class OutlookProvider:
    """
    Microsoft Outlook MCP Provider.

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
        Initialize Outlook provider.

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
            "search_emails": self._search_emails,
            "get_email": self._get_email,
            "send_email": self._send_email,
            "list_calendar_events": self._list_calendar_events,
            "create_calendar_event": self._create_calendar_event,
            "search_contacts": self._search_contacts,
        }

        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return await handler(**arguments)

    async def _search_emails(
        self,
        query: Optional[str] = None,
        folder: str = "inbox",
        max_results: int = 25,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        is_read: Optional[bool] = None,
        has_attachments: Optional[bool] = None,
    ) -> List[Dict]:
        """Search emails in mailbox."""
        # Build OData filter
        filters = []
        if is_read is not None:
            filters.append(f"isRead eq {str(is_read).lower()}")
        if has_attachments is not None:
            filters.append(f"hasAttachments eq {str(has_attachments).lower()}")
        if from_date:
            filters.append(f"receivedDateTime ge {from_date}")
        if to_date:
            filters.append(f"receivedDateTime le {to_date}")

        params = {
            "$top": max_results,
            "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments",
            "$orderby": "receivedDateTime desc",
        }

        if filters:
            params["$filter"] = " and ".join(filters)
        if query:
            params["$search"] = f'"{query}"'

        # Map folder name to Graph API path
        folder_map = {
            "inbox": "inbox",
            "sent": "sentItems",
            "drafts": "drafts",
            "deleted": "deletedItems",
            "archive": "archive",
        }
        folder_path = folder_map.get(folder.lower(), folder)

        endpoint = f"/me/mailFolders/{folder_path}/messages"
        result = await self._graph_request("GET", endpoint, params=params)

        return [
            {
                "id": msg["id"],
                "subject": msg.get("subject", "(no subject)"),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
                "received": msg.get("receivedDateTime"),
                "preview": msg.get("bodyPreview", "")[:200],
                "is_read": msg.get("isRead", False),
                "has_attachments": msg.get("hasAttachments", False),
            }
            for msg in result.get("value", [])
        ]

    async def _get_email(
        self,
        email_id: str,
        include_attachments: bool = False,
    ) -> Dict:
        """Get full email by ID."""
        params = {"$select": "id,subject,from,toRecipients,ccRecipients,body,receivedDateTime,hasAttachments"}
        endpoint = f"/me/messages/{email_id}"
        msg = await self._graph_request("GET", endpoint, params=params)

        result = {
            "id": msg["id"],
            "subject": msg.get("subject"),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
            "to": [r.get("emailAddress", {}).get("address") for r in msg.get("toRecipients", [])],
            "cc": [r.get("emailAddress", {}).get("address") for r in msg.get("ccRecipients", [])],
            "body": msg.get("body", {}).get("content"),
            "body_type": msg.get("body", {}).get("contentType"),
            "received": msg.get("receivedDateTime"),
        }

        if include_attachments and msg.get("hasAttachments"):
            attachments = await self._graph_request("GET", f"{endpoint}/attachments")
            result["attachments"] = [
                {"name": a.get("name"), "size": a.get("size"), "content_type": a.get("contentType")}
                for a in attachments.get("value", [])
            ]

        return result

    async def _send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = "text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        importance: str = "normal",
    ) -> Dict:
        """Send a new email."""
        message = {
            "subject": subject,
            "body": {
                "contentType": "HTML" if body_type == "html" else "Text",
                "content": body,
            },
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            "importance": importance,
        }

        if cc:
            message["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]
        if bcc:
            message["bccRecipients"] = [{"emailAddress": {"address": addr}} for addr in bcc]

        await self._graph_request("POST", "/me/sendMail", json={"message": message})
        return {"status": "sent", "to": to, "subject": subject}

    async def _list_calendar_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_id: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """List calendar events."""
        # Default to next 7 days
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

        params = {
            "startDateTime": start_date,
            "endDateTime": end_date,
            "$top": max_results,
            "$select": "id,subject,organizer,start,end,location,isOnlineMeeting,onlineMeetingUrl",
            "$orderby": "start/dateTime",
        }

        endpoint = "/me/calendar/calendarView"
        if calendar_id:
            endpoint = f"/me/calendars/{calendar_id}/calendarView"

        result = await self._graph_request("GET", endpoint, params=params)

        return [
            {
                "id": event["id"],
                "subject": event.get("subject"),
                "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address"),
                "start": event.get("start", {}).get("dateTime"),
                "end": event.get("end", {}).get("dateTime"),
                "location": event.get("location", {}).get("displayName"),
                "is_online": event.get("isOnlineMeeting", False),
                "meeting_url": event.get("onlineMeetingUrl"),
            }
            for event in result.get("value", [])
        ]

    async def _create_calendar_event(
        self,
        subject: str,
        start: str,
        end: str,
        body: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        is_online_meeting: bool = False,
        reminder_minutes: int = 15,
    ) -> Dict:
        """Create a calendar event."""
        event = {
            "subject": subject,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "reminderMinutesBeforeStart": reminder_minutes,
        }

        if body:
            event["body"] = {"contentType": "Text", "content": body}
        if location:
            event["location"] = {"displayName": location}
        if attendees:
            event["attendees"] = [
                {"emailAddress": {"address": addr}, "type": "required"}
                for addr in attendees
            ]
        if is_online_meeting:
            event["isOnlineMeeting"] = True
            event["onlineMeetingProvider"] = "teamsForBusiness"

        result = await self._graph_request("POST", "/me/calendar/events", json=event)

        return {
            "id": result["id"],
            "subject": result.get("subject"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "meeting_url": result.get("onlineMeetingUrl"),
        }

    async def _search_contacts(
        self,
        query: str,
        max_results: int = 25,
    ) -> List[Dict]:
        """Search contacts."""
        params = {
            "$search": f'"{query}"',
            "$top": max_results,
            "$select": "id,displayName,emailAddresses,businessPhones,companyName,jobTitle",
        }

        result = await self._graph_request("GET", "/me/contacts", params=params)

        return [
            {
                "id": contact["id"],
                "name": contact.get("displayName"),
                "email": contact.get("emailAddresses", [{}])[0].get("address") if contact.get("emailAddresses") else None,
                "phone": contact.get("businessPhones", [None])[0],
                "company": contact.get("companyName"),
                "title": contact.get("jobTitle"),
            }
            for contact in result.get("value", [])
        ]
