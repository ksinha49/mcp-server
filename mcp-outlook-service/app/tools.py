"""
Outlook MCP Tool Definitions

Defines MCP tools for Microsoft Outlook operations:
- Email: search, get, send
- Calendar: list events, create event
- Contacts: search
"""

from mcp.types import Tool

OUTLOOK_TOOLS = [
    # Email Tools
    Tool(
        name="search_emails",
        description="""Search emails in Outlook mailbox.

Supports filtering by:
- Folder (inbox, sent, drafts, etc.)
- Search query (searches subject, body, from)
- Date range
- Read/unread status
- Has attachments

Returns list of email summaries with id, subject, from, date, preview.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (searches subject, body, sender)",
                },
                "folder": {
                    "type": "string",
                    "description": "Folder to search (inbox, sent, drafts)",
                    "default": "inbox",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 25,
                },
                "from_date": {
                    "type": "string",
                    "description": "Filter emails after this date (ISO 8601)",
                },
                "to_date": {
                    "type": "string",
                    "description": "Filter emails before this date (ISO 8601)",
                },
                "is_read": {
                    "type": "boolean",
                    "description": "Filter by read status",
                },
                "has_attachments": {
                    "type": "boolean",
                    "description": "Filter by attachment presence",
                },
            },
        },
    ),
    Tool(
        name="get_email",
        description="""Get full email content by ID.

Returns complete email including:
- Subject, from, to, cc, bcc
- Full body content (HTML and text)
- Attachments list
- Headers
- Timestamps""",
        inputSchema={
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "Email ID to retrieve",
                },
                "include_attachments": {
                    "type": "boolean",
                    "description": "Include attachment content",
                    "default": False,
                },
            },
            "required": ["email_id"],
        },
    ),
    Tool(
        name="send_email",
        description="""Send a new email.

Supports:
- Single or multiple recipients (to, cc, bcc)
- HTML or plain text body
- Attachments (by URL or base64)
- Reply-to address
- Importance flag""",
        inputSchema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recipient email addresses",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject",
                },
                "body": {
                    "type": "string",
                    "description": "Email body content",
                },
                "body_type": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "description": "Body content type",
                    "default": "text",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CC recipients",
                },
                "bcc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "BCC recipients",
                },
                "importance": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "default": "normal",
                },
            },
            "required": ["to", "subject", "body"],
        },
    ),

    # Calendar Tools
    Tool(
        name="list_calendar_events",
        description="""List calendar events.

Returns events with:
- Subject, organizer, attendees
- Start and end times
- Location (physical or online meeting link)
- Description/body
- Recurrence info""",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start of date range (ISO 8601)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End of date range (ISO 8601)",
                },
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID (default: primary)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum events to return",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="create_calendar_event",
        description="""Create a new calendar event.

Supports:
- Single or recurring events
- Online meetings (Teams)
- Attendees with optional/required status
- Reminders
- Categories/tags""",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Event subject/title",
                },
                "start": {
                    "type": "string",
                    "description": "Start time (ISO 8601)",
                },
                "end": {
                    "type": "string",
                    "description": "End time (ISO 8601)",
                },
                "body": {
                    "type": "string",
                    "description": "Event description",
                },
                "location": {
                    "type": "string",
                    "description": "Event location",
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Attendee email addresses",
                },
                "is_online_meeting": {
                    "type": "boolean",
                    "description": "Create Teams meeting",
                    "default": False,
                },
                "reminder_minutes": {
                    "type": "integer",
                    "description": "Reminder before event (minutes)",
                    "default": 15,
                },
            },
            "required": ["subject", "start", "end"],
        },
    ),

    # Contacts Tools
    Tool(
        name="search_contacts",
        description="""Search contacts in Outlook.

Searches across:
- Display name
- Email addresses
- Company name
- Phone numbers

Returns contact details with all available information.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum contacts to return",
                    "default": 25,
                },
            },
            "required": ["query"],
        },
    ),
]
