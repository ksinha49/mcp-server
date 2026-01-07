"""
SharePoint Capabilities

Provides individual capability modules for SharePoint operations:
- sites: Site listing and details
- documents: Document search, get, upload
- lists: SharePoint list operations
"""

from app.capabilities.sites import SitesCapability
from app.capabilities.documents import DocumentsCapability
from app.capabilities.lists import ListsCapability

__all__ = ["SitesCapability", "DocumentsCapability", "ListsCapability"]
