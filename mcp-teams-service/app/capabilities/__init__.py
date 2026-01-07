"""
Teams Capabilities

Provides individual capability modules for Teams operations:
- teams: Team listing and details
- channels: Channel operations and messaging
- chats: Chat operations
- meetings: Meeting management
"""

from app.capabilities.teams import TeamsCapability
from app.capabilities.channels import ChannelsCapability
from app.capabilities.chats import ChatsCapability
from app.capabilities.meetings import MeetingsCapability

__all__ = ["TeamsCapability", "ChannelsCapability", "ChatsCapability", "MeetingsCapability"]
