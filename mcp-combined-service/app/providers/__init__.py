"""
MCP Provider Registry

Central registry for all MCP providers in the combined service.
"""

from typing import Any, Dict, List, Optional, Set
from mcp.types import Tool


class ProviderRegistry:
    """Registry for managing multiple MCP providers."""

    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self._tools: Dict[str, List[Tool]] = {}

    def register(self, name: str, provider: Any, tools: List[Tool]):
        """Register a provider with its tools."""
        self._providers[name] = provider
        self._tools[name] = tools

    def get_provider(self, name: str) -> Optional[Any]:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_all_tools(self, enabled: Optional[Set[str]] = None) -> List[Tool]:
        """Get all tools from enabled providers."""
        all_tools = []
        for name, tools in self._tools.items():
            if enabled is None or name in enabled:
                # Prefix tool names with provider name for uniqueness
                for tool in tools:
                    prefixed_tool = Tool(
                        name=f"{name}_{tool.name}",
                        description=f"[{name.upper()}] {tool.description}",
                        inputSchema=tool.inputSchema,
                    )
                    all_tools.append(prefixed_tool)
        return all_tools

    def find_provider_for_tool(self, tool_name: str) -> tuple[Optional[str], Optional[str]]:
        """Find which provider owns a tool and return (provider_name, original_tool_name)."""
        for provider_name in self._providers:
            prefix = f"{provider_name}_"
            if tool_name.startswith(prefix):
                return provider_name, tool_name[len(prefix):]
        return None, None


# Global registry instance
registry = ProviderRegistry()
