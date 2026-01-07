"""
Contacts Capability for Outlook MCP Server

Handles contact operations:
- Search contacts
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ContactsCapability:
    """Contacts capability implementation."""

    def __init__(self, graph_client):
        """
        Initialize contacts capability.

        Args:
            graph_client: Microsoft Graph API client
        """
        self.graph = graph_client

    async def search_contacts(
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

        result = await self.graph.request("GET", "/me/contacts", params=params)

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
