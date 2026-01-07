"""
SharePoint Provider for Combined Service

Simplified SharePoint provider for combined deployment.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from mcp.types import Tool

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

SHAREPOINT_TOOLS = [
    Tool(
        name="list_sites",
        description="List SharePoint sites the user has access to.",
        inputSchema={
            "type": "object",
            "properties": {
                "search": {"type": "string"},
                "max_results": {"type": "integer", "default": 25},
            },
        },
    ),
    Tool(
        name="get_site",
        description="Get details of a specific SharePoint site.",
        inputSchema={
            "type": "object",
            "properties": {"site_id": {"type": "string"}},
            "required": ["site_id"],
        },
    ),
    Tool(
        name="search_documents",
        description="Search for documents across SharePoint.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 25},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="list_folder_contents",
        description="List contents of a folder in a document library.",
        inputSchema={
            "type": "object",
            "properties": {
                "site_id": {"type": "string"},
                "folder_path": {"type": "string", "default": "/"},
            },
            "required": ["site_id"],
        },
    ),
]


class SharePointProvider:
    """SharePoint provider implementation."""

    def __init__(self, client_id: str, client_secret: str, tenant_id: str, user_token: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_token = user_token
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        if self.user_token:
            return self.user_token
        if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
            return self._app_token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            })
            response.raise_for_status()
            data = response.json()
        self._app_token = data["access_token"]
        self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._app_token

    async def _graph_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Any:
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{GRAPH_API_BASE}{endpoint}",
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "list_sites": self._list_sites,
            "get_site": self._get_site,
            "search_documents": self._search_documents,
            "list_folder_contents": self._list_folder_contents,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(**arguments)

    async def _list_sites(self, search: Optional[str] = None, max_results: int = 25, **kwargs) -> List[Dict]:
        query = search or "*"
        result = await self._graph_request("GET", f"/sites?search={query}", params={"$top": max_results})
        return [{"id": s["id"], "name": s.get("displayName"), "url": s.get("webUrl")} for s in result.get("value", [])]

    async def _get_site(self, site_id: str, **kwargs) -> Dict:
        site = await self._graph_request("GET", f"/sites/{site_id}")
        return {"id": site["id"], "name": site.get("displayName"), "url": site.get("webUrl"), "description": site.get("description")}

    async def _search_documents(self, query: str, max_results: int = 25, **kwargs) -> List[Dict]:
        search_request = {"requests": [{"entityTypes": ["driveItem"], "query": {"queryString": query}, "size": max_results}]}
        result = await self._graph_request("POST", "/search/query", json=search_request)
        docs = []
        for hc in result.get("value", []):
            for hit in hc.get("hitsContainers", [{}])[0].get("hits", []):
                r = hit.get("resource", {})
                docs.append({"id": r.get("id"), "name": r.get("name"), "web_url": r.get("webUrl")})
        return docs

    async def _list_folder_contents(self, site_id: str, folder_path: str = "/", **kwargs) -> List[Dict]:
        if folder_path == "/":
            endpoint = f"/sites/{site_id}/drive/root/children"
        else:
            endpoint = f"/sites/{site_id}/drive/root:{folder_path}:/children"
        result = await self._graph_request("GET", endpoint)
        return [{"id": i["id"], "name": i.get("name"), "type": "folder" if i.get("folder") else "file"} for i in result.get("value", [])]
