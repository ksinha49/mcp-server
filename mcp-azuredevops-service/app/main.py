"""
MCP Azure DevOps Server - Main Application

Implements MCP 2025-06-18 compliant server for Azure DevOps access.

Supports:
- Streamable HTTP transport (MCP 2025-06-18)
- SSE transport (backward compatibility)
- STDIO transport (Claude Desktop)

Usage:
    # HTTP mode (production)
    python -m app.main --transport http --port 8004

    # STDIO mode (Claude Desktop)
    python -m app.main --transport stdio

    # With OAuth gateway
    export OAUTH_GATEWAY_URL=https://mcp-oauth.example.com
    python -m app.main --transport http
"""

import argparse
import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.config import get_settings
from app.provider import AzureDevOpsProvider
from app.tools import AZUREDEVOPS_TOOLS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr if "--stdio" in sys.argv else sys.stdout)],
)
log = logging.getLogger(__name__)


def create_mcp_server(user_token: Optional[str] = None) -> Server:
    """
    Create MCP server instance with Azure DevOps tools.

    Args:
        user_token: Optional OAuth token for delegated auth

    Returns:
        Configured MCP Server instance
    """
    settings = get_settings()

    # Create server
    server = Server("azuredevops-mcp-server")

    # Create provider instance
    provider = AzureDevOpsProvider(
        organization_url=settings.azdo_organization_url,
        pat=settings.azdo_pat,
        user_token=user_token,
        client_id=settings.microsoft_client_id,
        client_secret=settings.microsoft_client_secret,
        tenant_id=settings.microsoft_tenant_id,
    )

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available Azure DevOps tools."""
        return AZUREDEVOPS_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute an Azure DevOps tool."""
        log.debug("Executing tool: %s with args: %s", name, list(arguments.keys()))

        try:
            result = await provider.execute_tool(name, arguments)
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            log.exception("Tool execution failed: %s", e)
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_stdio():
    """Run server in STDIO mode for Claude Desktop."""
    log.info("Starting Azure DevOps MCP Server in STDIO mode")
    server = create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_http(host: str, port: int):
    """
    Run server in HTTP mode with Streamable HTTP transport.

    Note: Full HTTP implementation requires FastAPI with custom transport.
    This is a simplified placeholder.
    """
    from fastapi import FastAPI, Request, HTTPException
    import uvicorn

    app = FastAPI(title="Azure DevOps MCP Server", version="1.0.0")
    settings = get_settings()

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "azuredevops-mcp-server"}

    @app.get("/.well-known/oauth-protected-resource.json")
    async def protected_resource_metadata():
        """MCP 2025-06-18 Protected Resource Metadata."""
        return {
            "resource": f"http://{host}:{port}",
            "authorization_servers": [
                f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/v2.0"
            ],
            "bearer_methods_supported": ["header"],
            "scopes_supported": [
                "499b84ac-1321-427f-aa17-267ca6975798/user_impersonation"
            ],
        }

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """
        Streamable HTTP MCP endpoint (MCP 2025-06-18).

        Note: Full implementation requires proper JSON-RPC handling.
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        user_token = None
        if auth_header.startswith("Bearer "):
            user_token = auth_header[7:]

        # Parse JSON-RPC request
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Invalid JSON")

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        server = create_mcp_server(user_token)

        # Handle MCP methods
        if method == "tools/list":
            tools = await server.list_tools()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [t.model_dump() for t in tools]}}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result = await server.call_tool(tool_name, tool_args)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [r.model_dump() for r in result]}}

        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

    log.info("Starting Azure DevOps MCP Server at http://%s:%d", host, port)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Azure DevOps MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8004,
        help="HTTP port (default: 8004)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio())
    else:
        asyncio.run(run_http(args.host, args.port))


if __name__ == "__main__":
    main()
