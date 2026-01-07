"""
Email Capability for Outlook MCP Server

Handles email operations:
- Search emails
- Get email by ID
- Send email
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class EmailCapability:
    """Email capability implementation."""

    def __init__(self, graph_client):
        """
        Initialize email capability.

        Args:
            graph_client: Microsoft Graph API client
        """
        self.graph = graph_client

    async def search_emails(
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
        result = await self.graph.request("GET", endpoint, params=params)

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

    async def get_email(
        self,
        email_id: str,
        include_attachments: bool = False,
    ) -> Dict:
        """Get full email by ID."""
        params = {"$select": "id,subject,from,toRecipients,ccRecipients,body,receivedDateTime,hasAttachments"}
        endpoint = f"/me/messages/{email_id}"
        msg = await self.graph.request("GET", endpoint, params=params)

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
            attachments = await self.graph.request("GET", f"{endpoint}/attachments")
            result["attachments"] = [
                {"name": a.get("name"), "size": a.get("size"), "content_type": a.get("contentType")}
                for a in attachments.get("value", [])
            ]

        return result

    async def send_email(
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

        await self.graph.request("POST", "/me/sendMail", json={"message": message})
        return {"status": "sent", "to": to, "subject": subject}
