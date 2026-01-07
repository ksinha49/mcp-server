"""
SharePoint MCP Tool Definitions

Defines MCP tools for Microsoft SharePoint operations:
- Sites: list, get details
- Documents: search, get, upload, download
- Lists: get items, create items
"""

from mcp.types import Tool

SHAREPOINT_TOOLS = [
    # Site Tools
    Tool(
        name="list_sites",
        description="""List SharePoint sites the user has access to.

Returns site information including:
- Site ID and name
- URL
- Description
- Created/modified dates""",
        inputSchema={
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search query to filter sites",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum sites to return",
                    "default": 25,
                },
            },
        },
    ),
    Tool(
        name="get_site",
        description="""Get details of a specific SharePoint site.

Returns full site information including lists and document libraries.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID or site path (e.g., 'contoso.sharepoint.com:/sites/team')",
                },
            },
            "required": ["site_id"],
        },
    ),

    # Document Tools
    Tool(
        name="search_documents",
        description="""Search for documents across SharePoint.

Searches document content, metadata, and file names.
Returns matching documents with preview and metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "site_id": {
                    "type": "string",
                    "description": "Limit search to specific site",
                },
                "file_type": {
                    "type": "string",
                    "description": "Filter by file extension (e.g., 'docx', 'pdf')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 25,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_document",
        description="""Get document metadata and optionally content.

Returns document properties, permissions, and version history.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID containing the document",
                },
                "item_id": {
                    "type": "string",
                    "description": "Document/item ID",
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include document content (text extraction)",
                    "default": False,
                },
            },
            "required": ["site_id", "item_id"],
        },
    ),
    Tool(
        name="list_folder_contents",
        description="""List contents of a folder in a document library.

Returns files and subfolders with metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID",
                },
                "drive_id": {
                    "type": "string",
                    "description": "Drive/library ID (optional, uses default document library)",
                },
                "folder_path": {
                    "type": "string",
                    "description": "Folder path (e.g., '/General/Reports')",
                    "default": "/",
                },
                "max_results": {
                    "type": "integer",
                    "default": 50,
                },
            },
            "required": ["site_id"],
        },
    ),
    Tool(
        name="upload_document",
        description="""Upload a document to SharePoint.

Supports creating new files or updating existing ones.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID",
                },
                "folder_path": {
                    "type": "string",
                    "description": "Target folder path",
                },
                "file_name": {
                    "type": "string",
                    "description": "File name",
                },
                "content": {
                    "type": "string",
                    "description": "File content (text or base64 encoded)",
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type",
                    "default": "text/plain",
                },
            },
            "required": ["site_id", "folder_path", "file_name", "content"],
        },
    ),

    # List Tools
    Tool(
        name="get_list_items",
        description="""Get items from a SharePoint list.

Returns list items with all columns and metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID",
                },
                "list_id": {
                    "type": "string",
                    "description": "List ID or name",
                },
                "filter": {
                    "type": "string",
                    "description": "OData filter expression",
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to return",
                },
                "max_results": {
                    "type": "integer",
                    "default": 100,
                },
            },
            "required": ["site_id", "list_id"],
        },
    ),
    Tool(
        name="create_list_item",
        description="""Create a new item in a SharePoint list.""",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "Site ID",
                },
                "list_id": {
                    "type": "string",
                    "description": "List ID or name",
                },
                "fields": {
                    "type": "object",
                    "description": "Field values for the new item",
                },
            },
            "required": ["site_id", "list_id", "fields"],
        },
    ),
]
