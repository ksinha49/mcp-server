"""
Azure DevOps MCP Tool Definitions

Defines MCP tools for Azure DevOps operations:
- Projects: list, get details
- Work Items: search, get, create, update
- Repos: list, get files, search code
- Pipelines: list, trigger, get status
- Pull Requests: list, get, create
"""

from mcp.types import Tool

AZUREDEVOPS_TOOLS = [
    # Project Tools
    Tool(
        name="list_projects",
        description="""List Azure DevOps projects in the organization.

Returns project information including:
- Project ID and name
- Description
- State (active, deleted)
- Visibility""",
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum projects to return",
                    "default": 100,
                },
            },
        },
    ),
    Tool(
        name="get_project",
        description="""Get details of a specific project.

Returns full project information including repos and team info.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name or ID",
                },
            },
            "required": ["project"],
        },
    ),

    # Work Item Tools
    Tool(
        name="search_work_items",
        description="""Search work items using WIQL or text search.

Returns matching work items with fields.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "query": {
                    "type": "string",
                    "description": "Search text or WIQL query",
                },
                "work_item_type": {
                    "type": "string",
                    "description": "Filter by type (Bug, Task, User Story, etc.)",
                },
                "state": {
                    "type": "string",
                    "description": "Filter by state (New, Active, Closed, etc.)",
                },
                "assigned_to": {
                    "type": "string",
                    "description": "Filter by assignee",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 50,
                },
            },
            "required": ["project"],
        },
    ),
    Tool(
        name="get_work_item",
        description="""Get a work item by ID.

Returns full work item with all fields and history.""",
        inputSchema={
            "type": "object",
            "properties": {
                "work_item_id": {
                    "type": "integer",
                    "description": "Work item ID",
                },
                "include_history": {
                    "type": "boolean",
                    "description": "Include revision history",
                    "default": False,
                },
            },
            "required": ["work_item_id"],
        },
    ),
    Tool(
        name="create_work_item",
        description="""Create a new work item.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "work_item_type": {
                    "type": "string",
                    "description": "Work item type (Bug, Task, User Story, etc.)",
                },
                "title": {
                    "type": "string",
                    "description": "Work item title",
                },
                "description": {
                    "type": "string",
                    "description": "Work item description (HTML)",
                },
                "assigned_to": {
                    "type": "string",
                    "description": "Assignee email or display name",
                },
                "area_path": {
                    "type": "string",
                    "description": "Area path",
                },
                "iteration_path": {
                    "type": "string",
                    "description": "Iteration/sprint path",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority (1-4)",
                },
            },
            "required": ["project", "work_item_type", "title"],
        },
    ),
    Tool(
        name="update_work_item",
        description="""Update an existing work item.""",
        inputSchema={
            "type": "object",
            "properties": {
                "work_item_id": {
                    "type": "integer",
                    "description": "Work item ID",
                },
                "fields": {
                    "type": "object",
                    "description": "Fields to update (key-value pairs)",
                },
            },
            "required": ["work_item_id", "fields"],
        },
    ),

    # Repository Tools
    Tool(
        name="list_repos",
        description="""List Git repositories in a project.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
            },
            "required": ["project"],
        },
    ),
    Tool(
        name="get_repo_contents",
        description="""Get contents of a file or directory from a repository.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "path": {
                    "type": "string",
                    "description": "File or folder path",
                    "default": "/",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name",
                    "default": "main",
                },
            },
            "required": ["project", "repo"],
        },
    ),
    Tool(
        name="search_code",
        description="""Search code across repositories.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name (optional for org-wide search)",
                },
                "query": {
                    "type": "string",
                    "description": "Search query",
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

    # Pipeline Tools
    Tool(
        name="list_pipelines",
        description="""List build/release pipelines in a project.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 50,
                },
            },
            "required": ["project"],
        },
    ),
    Tool(
        name="get_pipeline_runs",
        description="""Get recent runs of a pipeline.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "pipeline_id": {
                    "type": "integer",
                    "description": "Pipeline ID",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 25,
                },
            },
            "required": ["project", "pipeline_id"],
        },
    ),
    Tool(
        name="trigger_pipeline",
        description="""Trigger a pipeline run.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "pipeline_id": {
                    "type": "integer",
                    "description": "Pipeline ID",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to build",
                },
                "variables": {
                    "type": "object",
                    "description": "Pipeline variables to override",
                },
            },
            "required": ["project", "pipeline_id"],
        },
    ),

    # Pull Request Tools
    Tool(
        name="list_pull_requests",
        description="""List pull requests in a repository.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "completed", "abandoned", "all"],
                    "description": "PR status filter",
                    "default": "active",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 25,
                },
            },
            "required": ["project", "repo"],
        },
    ),
    Tool(
        name="get_pull_request",
        description="""Get pull request details.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "pull_request_id": {
                    "type": "integer",
                    "description": "Pull request ID",
                },
            },
            "required": ["project", "repo", "pull_request_id"],
        },
    ),
    Tool(
        name="create_pull_request",
        description="""Create a new pull request.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "source_branch": {
                    "type": "string",
                    "description": "Source branch",
                },
                "target_branch": {
                    "type": "string",
                    "description": "Target branch",
                },
                "title": {
                    "type": "string",
                    "description": "PR title",
                },
                "description": {
                    "type": "string",
                    "description": "PR description",
                },
                "reviewers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Reviewer emails or IDs",
                },
            },
            "required": ["project", "repo", "source_branch", "target_branch", "title"],
        },
    ),
]
