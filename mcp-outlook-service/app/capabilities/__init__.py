"""
Outlook Capabilities

Provides individual capability modules for Outlook operations:
- email: Email search, get, send
- calendar: Calendar events management
- contacts: Contact search and management
"""

from app.capabilities.email import EmailCapability
from app.capabilities.calendar import CalendarCapability
from app.capabilities.contacts import ContactsCapability

__all__ = ["EmailCapability", "CalendarCapability", "ContactsCapability"]
