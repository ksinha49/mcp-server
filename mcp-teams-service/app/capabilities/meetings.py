"""
Meetings Capability for Teams MCP Server

Handles meeting operations:
- List meetings
- Create meetings
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class MeetingsCapability:
    """Meetings capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def list_meetings(
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

        result = await self.graph.request("GET", "/me/calendar/calendarView", params=params)

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

    async def create_meeting(
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

        result = await self.graph.request("POST", "/me/events", json=event)

        return {
            "id": result["id"],
            "subject": result.get("subject"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "join_url": result.get("onlineMeeting", {}).get("joinUrl"),
            "status": "created",
        }
