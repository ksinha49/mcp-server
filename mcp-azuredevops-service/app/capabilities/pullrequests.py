"""
Pull Requests Capability for Azure DevOps MCP Server

Handles pull request operations:
- List pull requests
- Get pull request details
- Create pull request
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class PullRequestsCapability:
    """Pull requests capability implementation."""

    def __init__(self, api_client):
        self.api = api_client

    async def list_pull_requests(
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

        result = await self.api.request(
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

    async def get_pull_request(
        self,
        project: str,
        repo: str,
        pull_request_id: int,
    ) -> Dict:
        """Get pull request details."""
        result = await self.api.request(
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

    async def create_pull_request(
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

        result = await self.api.request(
            "POST", f"{project}/_apis/git/repositories/{repo}/pullrequests",
            json=body
        )

        return {
            "id": result["pullRequestId"],
            "title": result.get("title"),
            "url": result.get("url"),
            "status": "created",
        }
