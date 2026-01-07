"""
Work Items Capability for Azure DevOps MCP Server

Handles work item operations:
- Search work items
- Get work item by ID
- Create work item
- Update work item
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class WorkItemsCapability:
    """Work items capability implementation."""

    def __init__(self, api_client):
        self.api = api_client

    async def search_work_items(
        self,
        project: str,
        query: Optional[str] = None,
        work_item_type: Optional[str] = None,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """Search work items using WIQL."""
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

        result = await self.api.request(
            "POST", f"{project}/_apis/wit/wiql",
            json={"query": wiql},
            params={"$top": max_results}
        )

        work_item_ids = [wi["id"] for wi in result.get("workItems", [])[:max_results]]
        if not work_item_ids:
            return []

        items_result = await self.api.request(
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

    async def get_work_item(
        self,
        work_item_id: int,
        include_history: bool = False,
    ) -> Dict:
        """Get a work item by ID."""
        result = await self.api.request(
            "GET", f"_apis/wit/workitems/{work_item_id}",
            params={"$expand": "all"}
        )

        work_item = {
            "id": result["id"],
            "rev": result.get("rev"),
            "fields": result.get("fields", {}),
            "url": result.get("url"),
        }

        if include_history:
            history = await self.api.request(
                "GET", f"_apis/wit/workitems/{work_item_id}/updates"
            )
            work_item["history"] = [
                {
                    "rev": u.get("rev"),
                    "revised_by": u.get("revisedBy", {}).get("displayName"),
                    "revised_date": u.get("revisedDate"),
                    "fields": u.get("fields", {}),
                }
                for u in history.get("value", [])[-10:]
            ]

        return work_item

    async def create_work_item(
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

        result = await self.api.request(
            "POST", f"{project}/_apis/wit/workitems/${work_item_type}",
            json=operations
        )

        return {
            "id": result["id"],
            "title": result.get("fields", {}).get("System.Title"),
            "url": result.get("url"),
            "status": "created",
        }

    async def update_work_item(
        self,
        work_item_id: int,
        fields: Dict[str, Any],
    ) -> Dict:
        """Update an existing work item."""
        operations = [
            {"op": "replace", "path": f"/fields/{key}", "value": value}
            for key, value in fields.items()
        ]

        result = await self.api.request(
            "PATCH", f"_apis/wit/workitems/{work_item_id}",
            json=operations
        )

        return {
            "id": result["id"],
            "rev": result.get("rev"),
            "status": "updated",
        }
