"""
Teams MCP Tool Definitions

Defines MCP tools for Microsoft Teams operations:
- Teams: list, get details
- Channels: list, get, post messages
- Chats: list, get, send messages
- Meetings: list, create, get details
"""

from mcp.types import Tool

TEAMS_TOOLS = [
    # Team Tools
    Tool(
        name="list_teams",
        description="""List Teams the user is a member of.

Returns team information including:
- Team ID and display name
- Description
- Visibility (public/private)""",
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum teams to return",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="get_team",
        description="""Get details of a specific Team.

Returns full team information including channels and members.""",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {
                    "type": "string",
                    "description": "Team ID",
                },
            },
            "required": ["team_id"],
        },
    ),

    # Channel Tools
    Tool(
        name="list_channels",
        description="""List channels in a Team.

Returns channel information including:
- Channel ID and name
- Description
- Membership type""",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {
                    "type": "string",
                    "description": "Team ID",
                },
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_channel_messages",
        description="""Get messages from a channel.

Returns recent messages with sender info and content.""",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {
                    "type": "string",
                    "description": "Team ID",
                },
                "channel_id": {
                    "type": "string",
                    "description": "Channel ID",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum messages to return",
                    "default": 50,
                },
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="send_channel_message",
        description="""Send a message to a channel.""",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {
                    "type": "string",
                    "description": "Team ID",
                },
                "channel_id": {
                    "type": "string",
                    "description": "Channel ID",
                },
                "content": {
                    "type": "string",
                    "description": "Message content (plain text or HTML)",
                },
                "content_type": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "description": "Content type",
                    "default": "text",
                },
            },
            "required": ["team_id", "channel_id", "content"],
        },
    ),

    # Chat Tools
    Tool(
        name="list_chats",
        description="""List user's chats.

Returns chat information including participants and last message preview.""",
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum chats to return",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="get_chat_messages",
        description="""Get messages from a chat.

Returns recent messages with sender info and content.""",
        inputSchema={
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum messages to return",
                    "default": 50,
                },
            },
            "required": ["chat_id"],
        },
    ),
    Tool(
        name="send_chat_message",
        description="""Send a message in a chat.""",
        inputSchema={
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID",
                },
                "content": {
                    "type": "string",
                    "description": "Message content",
                },
                "content_type": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "description": "Content type",
                    "default": "text",
                },
            },
            "required": ["chat_id", "content"],
        },
    ),

    # Meeting Tools
    Tool(
        name="list_meetings",
        description="""List user's scheduled meetings.

Returns meeting information including subject, time, and join URL.""",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date (ISO 8601)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (ISO 8601)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum meetings to return",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="create_meeting",
        description="""Create a new Teams meeting.

Creates an online meeting and returns the join information.""",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Meeting subject",
                },
                "start": {
                    "type": "string",
                    "description": "Start time (ISO 8601)",
                },
                "end": {
                    "type": "string",
                    "description": "End time (ISO 8601)",
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses",
                },
                "content": {
                    "type": "string",
                    "description": "Meeting body/agenda",
                },
            },
            "required": ["subject", "start", "end"],
        },
    ),
]
