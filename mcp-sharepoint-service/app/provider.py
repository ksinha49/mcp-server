"""
SharePoint MCP Provider

Implements Microsoft Graph API operations for SharePoint:
- Site operations (list, get details)
- Document operations (search, get, upload, list folder)
- List operations (get items, create items)

Uses Microsoft Graph SDK with OAuth 2.1 authentication.
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

# Microsoft Graph API base URL
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class SharePointProvider:
    """
    Microsoft SharePoint MCP Provider.

    Implements tool execution using Microsoft Graph API.
    Supports both app-only and delegated (user) authentication.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        user_token: Optional[str] = None,
    ):
        """
        Initialize SharePoint provider.

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            user_token: Optional user access token for delegated auth
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_token = user_token
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Get access token (user token or app token)."""
        if self.user_token:
            return self.user_token

        # Use app-only token
        if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
            return self._app_token

        # Acquire new app token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            data = response.json()

        self._app_token = data["access_token"]
        self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._app_token

    async def _graph_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        content: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        """Make a request to Microsoft Graph API."""
        token = await self._get_token()
        url = f"{GRAPH_API_BASE}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        elif json is not None:
            headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                content=content,
                headers=headers,
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool_handlers = {
            "list_sites": self._list_sites,
            "get_site": self._get_site,
            "search_documents": self._search_documents,
            "get_document": self._get_document,
            "list_folder_contents": self._list_folder_contents,
            "upload_document": self._upload_document,
            "get_list_items": self._get_list_items,
            "create_list_item": self._create_list_item,
        }

        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return await handler(**arguments)

    async def _list_sites(
        self,
        search: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict]:
        """List SharePoint sites the user has access to."""
        params = {
            "$top": max_results,
            "$select": "id,displayName,name,webUrl,description,createdDateTime,lastModifiedDateTime",
        }

        if search:
            # Use search endpoint
            endpoint = f"/sites?search={search}"
            result = await self._graph_request("GET", endpoint, params=params)
        else:
            # List all sites (requires admin consent for Sites.Read.All)
            result = await self._graph_request("GET", "/sites?search=*", params=params)

        return [
            {
                "id": site["id"],
                "name": site.get("displayName") or site.get("name"),
                "url": site.get("webUrl"),
                "description": site.get("description", ""),
                "created": site.get("createdDateTime"),
                "modified": site.get("lastModifiedDateTime"),
            }
            for site in result.get("value", [])
        ]

    async def _get_site(self, site_id: str) -> Dict:
        """Get details of a specific SharePoint site."""
        endpoint = f"/sites/{site_id}"
        site = await self._graph_request("GET", endpoint)

        # Get lists and drives
        lists_result = await self._graph_request("GET", f"{endpoint}/lists", params={"$top": 50})
        drives_result = await self._graph_request("GET", f"{endpoint}/drives", params={"$top": 50})

        return {
            "id": site["id"],
            "name": site.get("displayName") or site.get("name"),
            "url": site.get("webUrl"),
            "description": site.get("description", ""),
            "created": site.get("createdDateTime"),
            "modified": site.get("lastModifiedDateTime"),
            "lists": [
                {
                    "id": lst["id"],
                    "name": lst.get("displayName"),
                    "description": lst.get("description", ""),
                    "template": lst.get("list", {}).get("template"),
                }
                for lst in lists_result.get("value", [])
            ],
            "drives": [
                {
                    "id": drv["id"],
                    "name": drv.get("name"),
                    "description": drv.get("description", ""),
                    "web_url": drv.get("webUrl"),
                }
                for drv in drives_result.get("value", [])
            ],
        }

    async def _search_documents(
        self,
        query: str,
        site_id: Optional[str] = None,
        file_type: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict]:
        """Search for documents across SharePoint."""
        # Build search query
        search_query = query
        if file_type:
            search_query += f" filetype:{file_type}"

        # Use Microsoft Search API
        search_request = {
            "requests": [
                {
                    "entityTypes": ["driveItem"],
                    "query": {"queryString": search_query},
                    "from": 0,
                    "size": max_results,
                }
            ]
        }

        if site_id:
            search_request["requests"][0]["sharePointOneDriveOptions"] = {
                "includeContent": "privateContent",
            }

        result = await self._graph_request("POST", "/search/query", json=search_request)

        documents = []
        for hit_container in result.get("value", []):
            for hit in hit_container.get("hitsContainers", [{}])[0].get("hits", []):
                resource = hit.get("resource", {})
                documents.append({
                    "id": resource.get("id"),
                    "name": resource.get("name"),
                    "web_url": resource.get("webUrl"),
                    "size": resource.get("size"),
                    "created": resource.get("createdDateTime"),
                    "modified": resource.get("lastModifiedDateTime"),
                    "created_by": resource.get("createdBy", {}).get("user", {}).get("displayName"),
                    "summary": hit.get("summary", ""),
                })

        return documents

    async def _get_document(
        self,
        site_id: str,
        item_id: str,
        include_content: bool = False,
    ) -> Dict:
        """Get document metadata and optionally content."""
        endpoint = f"/sites/{site_id}/drive/items/{item_id}"
        item = await self._graph_request("GET", endpoint)

        result = {
            "id": item["id"],
            "name": item.get("name"),
            "web_url": item.get("webUrl"),
            "size": item.get("size"),
            "mime_type": item.get("file", {}).get("mimeType"),
            "created": item.get("createdDateTime"),
            "modified": item.get("lastModifiedDateTime"),
            "created_by": item.get("createdBy", {}).get("user", {}).get("displayName"),
            "modified_by": item.get("lastModifiedBy", {}).get("user", {}).get("displayName"),
        }

        # Get version history
        try:
            versions = await self._graph_request("GET", f"{endpoint}/versions", params={"$top": 10})
            result["versions"] = [
                {
                    "id": v.get("id"),
                    "modified": v.get("lastModifiedDateTime"),
                    "modified_by": v.get("lastModifiedBy", {}).get("user", {}).get("displayName"),
                }
                for v in versions.get("value", [])
            ]
        except Exception:
            result["versions"] = []

        if include_content and item.get("file"):
            # Download content for text-based files
            mime_type = item.get("file", {}).get("mimeType", "")
            if mime_type.startswith("text/") or mime_type in [
                "application/json",
                "application/xml",
                "application/javascript",
            ]:
                try:
                    token = await self._get_token()
                    async with httpx.AsyncClient() as client:
                        download_url = f"{GRAPH_API_BASE}{endpoint}/content"
                        response = await client.get(
                            download_url,
                            headers={"Authorization": f"Bearer {token}"},
                            follow_redirects=True,
                        )
                        response.raise_for_status()
                        result["content"] = response.text[:50000]  # Limit content size
                except Exception as e:
                    result["content_error"] = str(e)

        return result

    async def _list_folder_contents(
        self,
        site_id: str,
        drive_id: Optional[str] = None,
        folder_path: str = "/",
        max_results: int = 50,
    ) -> List[Dict]:
        """List contents of a folder in a document library."""
        if drive_id:
            if folder_path == "/":
                endpoint = f"/sites/{site_id}/drives/{drive_id}/root/children"
            else:
                endpoint = f"/sites/{site_id}/drives/{drive_id}/root:{folder_path}:/children"
        else:
            if folder_path == "/":
                endpoint = f"/sites/{site_id}/drive/root/children"
            else:
                endpoint = f"/sites/{site_id}/drive/root:{folder_path}:/children"

        params = {
            "$top": max_results,
            "$select": "id,name,size,file,folder,webUrl,createdDateTime,lastModifiedDateTime",
        }

        result = await self._graph_request("GET", endpoint, params=params)

        return [
            {
                "id": item["id"],
                "name": item.get("name"),
                "type": "folder" if item.get("folder") else "file",
                "size": item.get("size"),
                "web_url": item.get("webUrl"),
                "mime_type": item.get("file", {}).get("mimeType") if item.get("file") else None,
                "child_count": item.get("folder", {}).get("childCount") if item.get("folder") else None,
                "created": item.get("createdDateTime"),
                "modified": item.get("lastModifiedDateTime"),
            }
            for item in result.get("value", [])
        ]

    async def _upload_document(
        self,
        site_id: str,
        folder_path: str,
        file_name: str,
        content: str,
        content_type: str = "text/plain",
    ) -> Dict:
        """Upload a document to SharePoint."""
        # Decode base64 if needed
        try:
            file_content = base64.b64decode(content)
        except Exception:
            file_content = content.encode("utf-8")

        # Build upload path
        path = f"{folder_path.rstrip('/')}/{file_name}"
        endpoint = f"/sites/{site_id}/drive/root:{path}:/content"

        result = await self._graph_request(
            "PUT",
            endpoint,
            content=file_content,
            content_type=content_type,
        )

        return {
            "id": result["id"],
            "name": result.get("name"),
            "web_url": result.get("webUrl"),
            "size": result.get("size"),
            "created": result.get("createdDateTime"),
        }

    async def _get_list_items(
        self,
        site_id: str,
        list_id: str,
        filter: Optional[str] = None,
        select: Optional[List[str]] = None,
        max_results: int = 100,
    ) -> List[Dict]:
        """Get items from a SharePoint list."""
        endpoint = f"/sites/{site_id}/lists/{list_id}/items"
        params = {
            "$top": max_results,
            "$expand": "fields",
        }

        if filter:
            params["$filter"] = filter
        if select:
            params["$expand"] = f"fields($select={','.join(select)})"

        result = await self._graph_request("GET", endpoint, params=params)

        return [
            {
                "id": item["id"],
                "created": item.get("createdDateTime"),
                "modified": item.get("lastModifiedDateTime"),
                "fields": item.get("fields", {}),
            }
            for item in result.get("value", [])
        ]

    async def _create_list_item(
        self,
        site_id: str,
        list_id: str,
        fields: Dict[str, Any],
    ) -> Dict:
        """Create a new item in a SharePoint list."""
        endpoint = f"/sites/{site_id}/lists/{list_id}/items"

        result = await self._graph_request("POST", endpoint, json={"fields": fields})

        return {
            "id": result["id"],
            "created": result.get("createdDateTime"),
            "fields": result.get("fields", {}),
        }
