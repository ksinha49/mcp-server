"""
Documents Capability for SharePoint MCP Server

Handles document operations:
- Search documents
- Get document metadata/content
- List folder contents
- Upload documents
"""

import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class DocumentsCapability:
    """Documents capability implementation."""

    def __init__(self, graph_client):
        self.graph = graph_client

    async def search_documents(
        self,
        query: str,
        site_id: Optional[str] = None,
        file_type: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict]:
        """Search for documents across SharePoint."""
        search_query = query
        if file_type:
            search_query += f" filetype:{file_type}"

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

        result = await self.graph.request("POST", "/search/query", json=search_request)

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

    async def get_document(
        self,
        site_id: str,
        item_id: str,
        include_content: bool = False,
    ) -> Dict:
        """Get document metadata and optionally content."""
        endpoint = f"/sites/{site_id}/drive/items/{item_id}"
        item = await self.graph.request("GET", endpoint)

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
            versions = await self.graph.request("GET", f"{endpoint}/versions", params={"$top": 10})
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

        return result

    async def list_folder_contents(
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

        result = await self.graph.request("GET", endpoint, params=params)

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

    async def upload_document(
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

        path = f"{folder_path.rstrip('/')}/{file_name}"
        endpoint = f"/sites/{site_id}/drive/root:{path}:/content"

        result = await self.graph.request(
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
