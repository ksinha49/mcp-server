"""
Pipelines Capability for Azure DevOps MCP Server

Handles pipeline operations:
- List pipelines
- Get pipeline runs
- Trigger pipeline
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class PipelinesCapability:
    """Pipelines capability implementation."""

    def __init__(self, api_client):
        self.api = api_client

    async def list_pipelines(
        self,
        project: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """List pipelines in a project."""
        result = await self.api.request(
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

    async def get_pipeline_runs(
        self,
        project: str,
        pipeline_id: int,
        max_results: int = 25,
    ) -> List[Dict]:
        """Get recent runs of a pipeline."""
        result = await self.api.request(
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

    async def trigger_pipeline(
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

        result = await self.api.request(
            "POST", f"{project}/_apis/pipelines/{pipeline_id}/runs",
            json=body
        )

        return {
            "id": result["id"],
            "state": result.get("state"),
            "url": result.get("url"),
            "status": "triggered",
        }
