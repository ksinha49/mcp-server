"""
Azure DevOps Provider for Combined Service

Simplified Azure DevOps provider for combined deployment.
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from mcp.types import Tool

log = logging.getLogger(__name__)

AZUREDEVOPS_TOOLS = [
    Tool(
        name="list_projects",
        description="List Azure DevOps projects in the organization.",
        inputSchema={
            "type": "object",
            "properties": {"max_results": {"type": "integer", "default": 100}},
        },
    ),
    Tool(
        name="search_work_items",
        description="Search work items using text search.",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 50},
            },
            "required": ["project"],
        },
    ),
    Tool(
        name="get_work_item",
        description="Get a work item by ID.",
        inputSchema={
            "type": "object",
            "properties": {"work_item_id": {"type": "integer"}},
            "required": ["work_item_id"],
        },
    ),
    Tool(
        name="list_repos",
        description="List Git repositories in a project.",
        inputSchema={
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "required": ["project"],
        },
    ),
    Tool(
        name="list_pipelines",
        description="List pipelines in a project.",
        inputSchema={
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "required": ["project"],
        },
    ),
    Tool(
        name="list_pull_requests",
        description="List pull requests in a repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "repo": {"type": "string"},
                "status": {"type": "string", "default": "active"},
            },
            "required": ["project", "repo"],
        },
    ),
]


class AzureDevOpsProvider:
    """Azure DevOps provider implementation."""

    def __init__(self, organization_url: str, pat: Optional[str] = None, user_token: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None, tenant_id: Optional[str] = None):
        self.organization_url = organization_url.rstrip("/")
        self.pat = pat
        self.user_token = user_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_auth_header(self) -> str:
        if self.user_token:
            return f"Bearer {self.user_token}"
        if self.pat:
            encoded = base64.b64encode(f":{self.pat}".encode()).decode()
            return f"Basic {encoded}"
        if self.client_id and self.client_secret and self.tenant_id:
            if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
                return f"Bearer {self._app_token}"
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "499b84ac-1321-427f-aa17-267ca6975798/.default",
                    "grant_type": "client_credentials",
                })
                response.raise_for_status()
                data = response.json()
            self._app_token = data["access_token"]
            self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
            return f"Bearer {self._app_token}"
        raise ValueError("No authentication method configured")

    async def _api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Any] = None) -> Any:
        auth_header = await self._get_auth_header()
        if params is None:
            params = {}
        params["api-version"] = "7.1"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.organization_url}/{endpoint}",
                params=params,
                json=json,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "list_projects": self._list_projects,
            "search_work_items": self._search_work_items,
            "get_work_item": self._get_work_item,
            "list_repos": self._list_repos,
            "list_pipelines": self._list_pipelines,
            "list_pull_requests": self._list_pull_requests,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(**arguments)

    async def _list_projects(self, max_results: int = 100, **kwargs) -> List[Dict]:
        result = await self._api_request("GET", "_apis/projects", params={"$top": max_results})
        return [{"id": p["id"], "name": p["name"], "state": p.get("state")} for p in result.get("value", [])]

    async def _search_work_items(self, project: str, query: Optional[str] = None, max_results: int = 50, **kwargs) -> List[Dict]:
        wiql = f"SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.TeamProject] = '{project}'"
        if query:
            wiql += f" AND [System.Title] CONTAINS '{query}'"
        result = await self._api_request("POST", f"{project}/_apis/wit/wiql", json={"query": wiql}, params={"$top": max_results})
        ids = [w["id"] for w in result.get("workItems", [])[:max_results]]
        if not ids:
            return []
        items = await self._api_request("GET", "_apis/wit/workitems", params={"ids": ",".join(map(str, ids))})
        return [{"id": i["id"], "title": i.get("fields", {}).get("System.Title"), "state": i.get("fields", {}).get("System.State")} for i in items.get("value", [])]

    async def _get_work_item(self, work_item_id: int, **kwargs) -> Dict:
        result = await self._api_request("GET", f"_apis/wit/workitems/{work_item_id}")
        return {"id": result["id"], "fields": result.get("fields", {})}

    async def _list_repos(self, project: str, **kwargs) -> List[Dict]:
        result = await self._api_request("GET", f"{project}/_apis/git/repositories")
        return [{"id": r["id"], "name": r["name"], "url": r.get("webUrl")} for r in result.get("value", [])]

    async def _list_pipelines(self, project: str, **kwargs) -> List[Dict]:
        result = await self._api_request("GET", f"{project}/_apis/pipelines")
        return [{"id": p["id"], "name": p["name"]} for p in result.get("value", [])]

    async def _list_pull_requests(self, project: str, repo: str, status: str = "active", **kwargs) -> List[Dict]:
        params = {}
        if status != "all":
            params["searchCriteria.status"] = status
        result = await self._api_request("GET", f"{project}/_apis/git/repositories/{repo}/pullrequests", params=params)
        return [{"id": pr["pullRequestId"], "title": pr.get("title"), "status": pr.get("status")} for pr in result.get("value", [])]
