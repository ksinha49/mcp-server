"""
Calendar Capability for Outlook MCP Server

Handles calendar operations:
- List calendar events
- Create calendar event
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class CalendarCapability:
    """Calendar capability implementation."""

    def __init__(self, graph_client):
        """
        Initialize calendar capability.

        Args:
            graph_client: Microsoft Graph API client
        """
        self.graph = graph_client

    async def list_calendar_events(
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

        result = await self.graph.request("GET", endpoint, params=params)

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

    async def create_calendar_event(
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

        result = await self.graph.request("POST", "/me/calendar/events", json=event)

        return {
            "id": result["id"],
            "subject": result.get("subject"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "meeting_url": result.get("onlineMeetingUrl"),
        }
