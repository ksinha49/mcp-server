"""
Repos Capability for Azure DevOps MCP Server

Handles repository operations:
- List repositories
- Get repository contents
- Search code
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ReposCapability:
    """Repos capability implementation."""

    def __init__(self, api_client):
        self.api = api_client

    async def list_repos(self, project: str) -> List[Dict]:
        """List Git repositories in a project."""
        result = await self.api.request(
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

    async def get_repo_contents(
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

        result = await self.api.request(
            "GET", f"{project}/_apis/git/repositories/{repo}/items",
            params=params
        )

        if result.get("isFolder"):
            children = await self.api.request(
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
            content = await self.api.request(
                "GET", f"{project}/_apis/git/repositories/{repo}/items",
                params={**params, "includeContent": True}
            )
            return {
                "path": path,
                "type": "file",
                "content": content.get("content", "")[:50000],
            }

    async def search_code(
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

        result = await self.api.search_request(
            "POST", "_apis/search/codeSearchResults",
            json=search_request
        )

        return [
            {
                "path": hit.get("path"),
                "repository": hit.get("repository", {}).get("name"),
                "project": hit.get("project", {}).get("name"),
                "matches": hit.get("matches", {}).get("content", [])[:3],
            }
            for hit in result.get("results", [])
        ]
