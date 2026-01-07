"""
Azure DevOps Capabilities

Provides individual capability modules for Azure DevOps operations:
- projects: Project operations
- workitems: Work item management
- repos: Repository operations
- pipelines: Pipeline operations
- pullrequests: Pull request management
"""

from app.capabilities.projects import ProjectsCapability
from app.capabilities.workitems import WorkItemsCapability
from app.capabilities.repos import ReposCapability
from app.capabilities.pipelines import PipelinesCapability
from app.capabilities.pullrequests import PullRequestsCapability

__all__ = [
    "ProjectsCapability",
    "WorkItemsCapability",
    "ReposCapability",
    "PipelinesCapability",
    "PullRequestsCapability",
]
