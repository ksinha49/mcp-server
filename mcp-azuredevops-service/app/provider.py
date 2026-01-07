"""
Azure DevOps MCP Provider

Implements Azure DevOps REST API operations:
- Project operations (list, get details)
- Work Item operations (search, get, create, update)
- Repository operations (list, get files, search)
- Pipeline operations (list, trigger, get runs)
- Pull Request operations (list, get, create)

Supports both PAT and OAuth authentication.
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)


class AzureDevOpsProvider:
    """
    Azure DevOps MCP Provider.

    Implements tool execution using Azure DevOps REST API.
    Supports both PAT and OAuth (AAD) authentication.
    """

    def __init__(
        self,
        organization_url: str,
        pat: Optional[str] = None,
        user_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Azure DevOps provider.

        Args:
            organization_url: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
            pat: Personal Access Token for authentication
            user_token: OAuth access token (takes precedence over PAT)
            client_id: Azure AD client ID (for app-only auth)
            client_secret: Azure AD client secret
            tenant_id: Azure AD tenant ID
        """
        self.organization_url = organization_url.rstrip("/")
        self.pat = pat
        self.user_token = user_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None

    async def _get_auth_header(self) -> str:
        """Get authentication header value."""
        if self.user_token:
            return f"Bearer {self.user_token}"

        if self.pat:
            encoded = base64.b64encode(f":{self.pat}".encode()).decode()
            return f"Basic {encoded}"

        # Try app-only OAuth
        if self.client_id and self.client_secret and self.tenant_id:
            if self._app_token and self._app_token_expires and datetime.utcnow() < self._app_token_expires:
                return f"Bearer {self._app_token}"

            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "499b84ac-1321-427f-aa17-267ca6975798/.default",  # Azure DevOps
                        "grant_type": "client_credentials",
                    },
                )
                response.raise_for_status()
                data = response.json()

            self._app_token = data["access_token"]
            self._app_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
            return f"Bearer {self._app_token}"

        raise ValueError("No authentication method configured")

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Any] = None,
        api_version: str = "7.1",
    ) -> Any:
        """Make a request to Azure DevOps REST API."""
        auth_header = await self._get_auth_header()
        url = f"{self.organization_url}/{endpoint}"

        # Add API version
        if params is None:
            params = {}
        params["api-version"] = api_version

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json() if response.content else None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        tool_handlers = {
            "list_projects": self._list_projects,
            "get_project": self._get_project,
            "search_work_items": self._search_work_items,
            "get_work_item": self._get_work_item,
            "create_work_item": self._create_work_item,
            "update_work_item": self._update_work_item,
            "list_repos": self._list_repos,
            "get_repo_contents": self._get_repo_contents,
            "search_code": self._search_code,
            "list_pipelines": self._list_pipelines,
            "get_pipeline_runs": self._get_pipeline_runs,
            "trigger_pipeline": self._trigger_pipeline,
            "list_pull_requests": self._list_pull_requests,
            "get_pull_request": self._get_pull_request,
            "create_pull_request": self._create_pull_request,
        }

        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return await handler(**arguments)

    async def _list_projects(self, max_results: int = 100) -> List[Dict]:
        """List projects in the organization."""
        result = await self._api_request(
            "GET", "_apis/projects",
            params={"$top": max_results}
        )

        return [
            {
                "id": proj["id"],
                "name": proj["name"],
                "description": proj.get("description", ""),
                "state": proj.get("state"),
                "visibility": proj.get("visibility"),
                "url": proj.get("url"),
            }
            for proj in result.get("value", [])
        ]

    async def _get_project(self, project: str) -> Dict:
        """Get project details."""
        result = await self._api_request(
            "GET", f"_apis/projects/{project}",
            params={"includeCapabilities": True}
        )

        return {
            "id": result["id"],
            "name": result["name"],
            "description": result.get("description", ""),
            "state": result.get("state"),
            "visibility": result.get("visibility"),
            "capabilities": result.get("capabilities", {}),
        }

    async def _search_work_items(
        self,
        project: str,
        query: Optional[str] = None,
        work_item_type: Optional[str] = None,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """Search work items using WIQL."""
        # Build WIQL query
        conditions = [f"[System.TeamProject] = '{project}'"]
        if work_item_type:
            conditions.append(f"[System.WorkItemType] = '{work_item_type}'")
        if state:
            conditions.append(f"[System.State] = '{state}'")
        if assigned_to:
            conditions.append(f"[System.AssignedTo] = '{assigned_to}'")
        if query:
            conditions.append(f"[System.Title] CONTAINS '{query}'")

        wiql = f"SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType], [System.AssignedTo] FROM WorkItems WHERE {' AND '.join(conditions)} ORDER BY [System.ChangedDate] DESC"

        result = await self._api_request(
            "POST", f"{project}/_apis/wit/wiql",
            json={"query": wiql},
            params={"$top": max_results}
        )

        # Get work item details
        work_item_ids = [wi["id"] for wi in result.get("workItems", [])[:max_results]]
        if not work_item_ids:
            return []

        items_result = await self._api_request(
            "GET", "_apis/wit/workitems",
            params={"ids": ",".join(map(str, work_item_ids))}
        )

        return [
            {
                "id": item["id"],
                "title": item.get("fields", {}).get("System.Title"),
                "type": item.get("fields", {}).get("System.WorkItemType"),
                "state": item.get("fields", {}).get("System.State"),
                "assigned_to": item.get("fields", {}).get("System.AssignedTo", {}).get("displayName"),
                "url": item.get("url"),
            }
            for item in items_result.get("value", [])
        ]

    async def _get_work_item(
        self,
        work_item_id: int,
        include_history: bool = False,
    ) -> Dict:
        """Get a work item by ID."""
        params = {"$expand": "all"}
        result = await self._api_request(
            "GET", f"_apis/wit/workitems/{work_item_id}",
            params=params
        )

        work_item = {
            "id": result["id"],
            "rev": result.get("rev"),
            "fields": result.get("fields", {}),
            "url": result.get("url"),
        }

        if include_history:
            history = await self._api_request(
                "GET", f"_apis/wit/workitems/{work_item_id}/updates"
            )
            work_item["history"] = [
                {
                    "rev": u.get("rev"),
                    "revised_by": u.get("revisedBy", {}).get("displayName"),
                    "revised_date": u.get("revisedDate"),
                    "fields": u.get("fields", {}),
                }
                for u in history.get("value", [])[-10:]  # Last 10 revisions
            ]

        return work_item

    async def _create_work_item(
        self,
        project: str,
        work_item_type: str,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Dict:
        """Create a new work item."""
        operations = [
            {"op": "add", "path": "/fields/System.Title", "value": title}
        ]

        if description:
            operations.append({"op": "add", "path": "/fields/System.Description", "value": description})
        if assigned_to:
            operations.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to})
        if area_path:
            operations.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})
        if iteration_path:
            operations.append({"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path})
        if priority:
            operations.append({"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority})

        result = await self._api_request(
            "POST", f"{project}/_apis/wit/workitems/${work_item_type}",
            json=operations
        )

        return {
            "id": result["id"],
            "title": result.get("fields", {}).get("System.Title"),
            "url": result.get("url"),
            "status": "created",
        }

    async def _update_work_item(
        self,
        work_item_id: int,
        fields: Dict[str, Any],
    ) -> Dict:
        """Update an existing work item."""
        operations = [
            {"op": "replace", "path": f"/fields/{key}", "value": value}
            for key, value in fields.items()
        ]

        result = await self._api_request(
            "PATCH", f"_apis/wit/workitems/{work_item_id}",
            json=operations
        )

        return {
            "id": result["id"],
            "rev": result.get("rev"),
            "status": "updated",
        }

    async def _list_repos(self, project: str) -> List[Dict]:
        """List Git repositories in a project."""
        result = await self._api_request(
            "GET", f"{project}/_apis/git/repositories"
        )

        return [
            {
                "id": repo["id"],
                "name": repo["name"],
                "url": repo.get("webUrl"),
                "default_branch": repo.get("defaultBranch", "").replace("refs/heads/", ""),
                "size": repo.get("size"),
            }
            for repo in result.get("value", [])
        ]

    async def _get_repo_contents(
        self,
        project: str,
        repo: str,
        path: str = "/",
        branch: str = "main",
    ) -> Dict:
        """Get contents of a file or directory."""
        params = {
            "path": path,
            "versionDescriptor.version": branch,
            "versionDescriptor.versionType": "branch",
        }

        result = await self._api_request(
            "GET", f"{project}/_apis/git/repositories/{repo}/items",
            params=params
        )

        # Check if it's a file or folder
        if result.get("isFolder"):
            children = await self._api_request(
                "GET", f"{project}/_apis/git/repositories/{repo}/items",
                params={**params, "recursionLevel": "OneLevel"}
            )
            return {
                "path": path,
                "type": "folder",
                "items": [
                    {
                        "path": item.get("path"),
                        "type": "folder" if item.get("isFolder") else "file",
                        "size": item.get("size"),
                    }
                    for item in children.get("value", [])
                ],
            }
        else:
            # Get file content
            content = await self._api_request(
                "GET", f"{project}/_apis/git/repositories/{repo}/items",
                params={**params, "includeContent": True}
            )
            return {
                "path": path,
                "type": "file",
                "content": content.get("content", "")[:50000],  # Limit size
            }

    async def _search_code(
        self,
        query: str,
        project: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict]:
        """Search code across repositories."""
        search_request = {
            "searchText": query,
            "$top": max_results,
        }
        if project:
            search_request["filters"] = {"Project": [project]}

        # Use search API
        url = f"{self.organization_url}/_apis/search/codeSearchResults"
        auth_header = await self._get_auth_header()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={"api-version": "7.1"},
                json=search_request,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

        return [
            {
                "path": hit.get("path"),
                "repository": hit.get("repository", {}).get("name"),
                "project": hit.get("project", {}).get("name"),
                "matches": hit.get("matches", {}).get("content", [])[:3],
            }
            for hit in result.get("results", [])
        ]

    async def _list_pipelines(
        self,
        project: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """List pipelines in a project."""
        result = await self._api_request(
            "GET", f"{project}/_apis/pipelines",
            params={"$top": max_results}
        )

        return [
            {
                "id": pipe["id"],
                "name": pipe["name"],
                "folder": pipe.get("folder"),
                "url": pipe.get("url"),
            }
            for pipe in result.get("value", [])
        ]

    async def _get_pipeline_runs(
        self,
        project: str,
        pipeline_id: int,
        max_results: int = 25,
    ) -> List[Dict]:
        """Get recent runs of a pipeline."""
        result = await self._api_request(
            "GET", f"{project}/_apis/pipelines/{pipeline_id}/runs",
            params={"$top": max_results}
        )

        return [
            {
                "id": run["id"],
                "name": run.get("name"),
                "state": run.get("state"),
                "result": run.get("result"),
                "created": run.get("createdDate"),
                "finished": run.get("finishedDate"),
            }
            for run in result.get("value", [])
        ]

    async def _trigger_pipeline(
        self,
        project: str,
        pipeline_id: int,
        branch: Optional[str] = None,
        variables: Optional[Dict] = None,
    ) -> Dict:
        """Trigger a pipeline run."""
        body: Dict[str, Any] = {}
        if branch:
            body["resources"] = {
                "repositories": {
                    "self": {"refName": f"refs/heads/{branch}"}
                }
            }
        if variables:
            body["variables"] = {
                k: {"value": v} for k, v in variables.items()
            }

        result = await self._api_request(
            "POST", f"{project}/_apis/pipelines/{pipeline_id}/runs",
            json=body
        )

        return {
            "id": result["id"],
            "state": result.get("state"),
            "url": result.get("url"),
            "status": "triggered",
        }

    async def _list_pull_requests(
        self,
        project: str,
        repo: str,
        status: str = "active",
        max_results: int = 25,
    ) -> List[Dict]:
        """List pull requests in a repository."""
        params = {"$top": max_results}
        if status != "all":
            params["searchCriteria.status"] = status

        result = await self._api_request(
            "GET", f"{project}/_apis/git/repositories/{repo}/pullrequests",
            params=params
        )

        return [
            {
                "id": pr["pullRequestId"],
                "title": pr.get("title"),
                "status": pr.get("status"),
                "source_branch": pr.get("sourceRefName", "").replace("refs/heads/", ""),
                "target_branch": pr.get("targetRefName", "").replace("refs/heads/", ""),
                "created_by": pr.get("createdBy", {}).get("displayName"),
                "created": pr.get("creationDate"),
            }
            for pr in result.get("value", [])
        ]

    async def _get_pull_request(
        self,
        project: str,
        repo: str,
        pull_request_id: int,
    ) -> Dict:
        """Get pull request details."""
        result = await self._api_request(
            "GET", f"{project}/_apis/git/repositories/{repo}/pullrequests/{pull_request_id}"
        )

        return {
            "id": result["pullRequestId"],
            "title": result.get("title"),
            "description": result.get("description"),
            "status": result.get("status"),
            "source_branch": result.get("sourceRefName", "").replace("refs/heads/", ""),
            "target_branch": result.get("targetRefName", "").replace("refs/heads/", ""),
            "created_by": result.get("createdBy", {}).get("displayName"),
            "created": result.get("creationDate"),
            "reviewers": [
                {
                    "name": r.get("displayName"),
                    "vote": r.get("vote"),
                }
                for r in result.get("reviewers", [])
            ],
            "merge_status": result.get("mergeStatus"),
        }

    async def _create_pull_request(
        self,
        project: str,
        repo: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new pull request."""
        body = {
            "sourceRefName": f"refs/heads/{source_branch}",
            "targetRefName": f"refs/heads/{target_branch}",
            "title": title,
        }

        if description:
            body["description"] = description

        if reviewers:
            body["reviewers"] = [{"id": r} for r in reviewers]

        result = await self._api_request(
            "POST", f"{project}/_apis/git/repositories/{repo}/pullrequests",
            json=body
        )

        return {
            "id": result["pullRequestId"],
            "title": result.get("title"),
            "url": result.get("url"),
            "status": "created",
        }
