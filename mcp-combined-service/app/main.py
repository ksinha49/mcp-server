"""
MCP Combined Server - Main Application

All-in-one MCP server supporting multiple providers with configurable enablement.

Supports:
- Streamable HTTP transport (MCP 2025-06-18)
- STDIO transport (Claude Desktop)
- Per-provider endpoints (/mcp/{provider})
- Combined endpoint with prefixed tools (/mcp)

Usage:
    # HTTP mode with all providers
    python -m app.main --transport http --port 8000

    # HTTP mode with specific providers
    ENABLED_PROVIDERS=outlook,sharepoint python -m app.main --transport http

    # STDIO mode (Claude Desktop)
    python -m app.main --transport stdio

Environment:
    ENABLED_PROVIDERS: Comma-separated list of providers to enable
                       (outlook, sharepoint, teams, azuredevops, snowflake)
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
from app.providers import registry
from app.sandbox import SandboxMode, SandboxManager, ExecutionContext
from app.providers.outlook import OutlookProvider, OUTLOOK_TOOLS
from app.providers.sharepoint import SharePointProvider, SHAREPOINT_TOOLS
from app.providers.teams import TeamsProvider, TEAMS_TOOLS
from app.providers.azuredevops import AzureDevOpsProvider, AZUREDEVOPS_TOOLS
from app.providers.snowflake import SnowflakeProvider, SNOWFLAKE_TOOLS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr if "--stdio" in sys.argv else sys.stdout)],
)
log = logging.getLogger(__name__)


def initialize_providers(user_token: Optional[str] = None):
    """Initialize all enabled providers."""
    settings = get_settings()
    enabled = settings.get_enabled_providers()

    if "outlook" in enabled:
        provider = OutlookProvider(
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            tenant_id=settings.microsoft_tenant_id,
            user_token=user_token,
        )
        registry.register("outlook", provider, OUTLOOK_TOOLS)
        log.info("Registered Outlook provider")

    if "sharepoint" in enabled:
        provider = SharePointProvider(
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            tenant_id=settings.microsoft_tenant_id,
            user_token=user_token,
        )
        registry.register("sharepoint", provider, SHAREPOINT_TOOLS)
        log.info("Registered SharePoint provider")

    if "teams" in enabled:
        provider = TeamsProvider(
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            tenant_id=settings.microsoft_tenant_id,
            user_token=user_token,
        )
        registry.register("teams", provider, TEAMS_TOOLS)
        log.info("Registered Teams provider")

    if "azuredevops" in enabled:
        provider = AzureDevOpsProvider(
            organization_url=settings.azdo_organization_url,
            pat=settings.azdo_pat,
            user_token=user_token,
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            tenant_id=settings.microsoft_tenant_id,
        )
        registry.register("azuredevops", provider, AZUREDEVOPS_TOOLS)
        log.info("Registered Azure DevOps provider")

    if "snowflake" in enabled:
        provider = SnowflakeProvider(
            account=settings.snowflake_account,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
            role=settings.snowflake_role,
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            private_key_path=settings.snowflake_private_key_path,
            private_key_passphrase=settings.snowflake_private_key_passphrase,
            oauth_access_token=user_token,
        )
        registry.register("snowflake", provider, SNOWFLAKE_TOOLS)
        log.info("Registered Snowflake provider")


def create_mcp_server(user_token: Optional[str] = None) -> Server:
    """
    Create MCP server instance with all enabled provider tools.

    Args:
        user_token: Optional OAuth token for delegated auth

    Returns:
        Configured MCP Server instance
    """
    settings = get_settings()
    enabled = settings.get_enabled_providers()

    # Initialize providers
    initialize_providers(user_token)

    # Create server
    server = Server("combined-mcp-server")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List tools from all enabled providers."""
        return registry.get_all_tools(enabled)

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a tool (format: provider_toolname)."""
        provider_name, tool_name = registry.find_provider_for_tool(name)

        if not provider_name or not tool_name:
            return [TextContent(type="text", text=f"Error: Unknown tool: {name}")]

        provider = registry.get_provider(provider_name)
        if not provider:
            return [TextContent(type="text", text=f"Error: Provider not found: {provider_name}")]

        try:
            result = await provider.execute_tool(tool_name, arguments)
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            log.exception("Tool execution failed: %s", e)
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_stdio():
    """Run server in STDIO mode for Claude Desktop."""
    log.info("Starting Combined MCP Server in STDIO mode")
    server = create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_http(host: str, port: int):
    """Run server in HTTP mode with Streamable HTTP transport."""
    from fastapi import FastAPI, Request, HTTPException
    import uvicorn

    app = FastAPI(title="Combined MCP Server", version="1.0.0")
    settings = get_settings()
    enabled = settings.get_enabled_providers()

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "combined-mcp-server",
            "enabled_providers": list(enabled),
        }

    @app.get("/.well-known/oauth-protected-resource.json")
    async def protected_resource_metadata():
        """MCP 2025-06-18 Protected Resource Metadata."""
        auth_servers = []
        scopes = []

        # Microsoft providers
        if any(p in enabled for p in ["outlook", "sharepoint", "teams", "azuredevops"]):
            auth_servers.append(f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/v2.0")
            if "outlook" in enabled:
                scopes.extend(["Mail.Read", "Mail.Send", "Calendars.ReadWrite", "Contacts.Read"])
            if "sharepoint" in enabled:
                scopes.extend(["Sites.Read.All", "Files.Read.All"])
            if "teams" in enabled:
                scopes.extend(["Team.ReadBasic.All", "Channel.ReadBasic.All", "Chat.Read"])
            if "azuredevops" in enabled:
                scopes.append("499b84ac-1321-427f-aa17-267ca6975798/user_impersonation")

        # Snowflake
        if "snowflake" in enabled:
            auth_servers.append(f"https://{settings.snowflake_account}.snowflakecomputing.com/oauth/token")
            scopes.append("session:role:PUBLIC")

        return {
            "resource": f"http://{host}:{port}",
            "authorization_servers": auth_servers,
            "bearer_methods_supported": ["header"],
            "scopes_supported": scopes,
        }

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """Combined MCP endpoint with prefixed tool names."""
        auth_header = request.headers.get("Authorization", "")
        user_token = None
        if auth_header.startswith("Bearer "):
            user_token = auth_header[7:]

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Invalid JSON")

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        server = create_mcp_server(user_token)

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

    @app.post("/mcp/{provider}")
    async def provider_endpoint(provider: str, request: Request):
        """Per-provider MCP endpoint (non-prefixed tool names)."""
        if provider not in enabled:
            raise HTTPException(404, f"Provider '{provider}' not enabled")

        auth_header = request.headers.get("Authorization", "")
        user_token = None
        if auth_header.startswith("Bearer "):
            user_token = auth_header[7:]

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Invalid JSON")

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        # Re-initialize specific provider
        initialize_providers(user_token)
        provider_obj = registry.get_provider(provider)

        if method == "tools/list":
            tools = registry._tools.get(provider, [])
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [t.model_dump() for t in tools]}}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = await provider_obj.execute_tool(tool_name, tool_args)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(result)}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

    # Code Execution Endpoints
    sandbox_manager: Optional[SandboxManager] = None

    if settings.code_execution_enabled:
        sandbox_mode = SandboxMode(settings.sandbox_mode)
        sandbox_manager = SandboxManager.create(
            sandbox_mode,
            deno_server_port=settings.deno_server_port,
            python_backend_port=port,
        )

        @app.on_event("startup")
        async def start_sandbox():
            if sandbox_manager:
                await sandbox_manager.start()
                log.info("Sandbox manager started (mode: %s)", settings.sandbox_mode)

        @app.on_event("shutdown")
        async def stop_sandbox():
            if sandbox_manager:
                await sandbox_manager.stop()
                log.info("Sandbox manager stopped")

        @app.get("/mcp/code/status")
        async def code_status():
            """Get code execution sandbox status."""
            if not sandbox_manager:
                return {"enabled": False}
            health = await sandbox_manager.health_check()
            return {"enabled": True, **health}

        @app.get("/mcp/code/tools")
        async def code_tools():
            """List tools available for code execution with TypeScript types."""
            tools = []
            for provider_name in enabled:
                provider = registry.get_provider(provider_name)
                if provider:
                    for tool in registry._tools.get(provider_name, []):
                        tools.append({
                            "provider": provider_name,
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema,
                        })
            return {"tools": tools, "total": len(tools)}

        @app.post("/mcp/code/validate")
        async def code_validate(request: Request):
            """Validate TypeScript code without executing."""
            if not sandbox_manager:
                raise HTTPException(503, "Code execution not enabled")

            try:
                body = await request.json()
            except Exception:
                raise HTTPException(400, "Invalid JSON")

            code = body.get("code")
            if not code:
                raise HTTPException(400, "Missing required field: code")

            result = await sandbox_manager.validate(code)
            return {
                "valid": result.valid,
                "errors": result.errors,
                "warnings": result.warnings,
            }

        @app.post("/mcp/code/execute")
        async def code_execute(request: Request):
            """Execute TypeScript code in sandboxed environment."""
            if not sandbox_manager:
                raise HTTPException(503, "Code execution not enabled")

            auth_header = request.headers.get("Authorization", "")
            user_token = None
            if auth_header.startswith("Bearer "):
                user_token = auth_header[7:]

            try:
                body = await request.json()
            except Exception:
                raise HTTPException(400, "Invalid JSON")

            code = body.get("code")
            if not code:
                raise HTTPException(400, "Missing required field: code")

            context = ExecutionContext(
                code=code,
                timeout_ms=body.get("timeout_ms", 60000),
                variables=body.get("variables", {}),
                auth_token=user_token,
            )

            result = await sandbox_manager.execute(context)
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "logs": result.logs,
                "execution_time_ms": result.execution_time_ms,
                "tools_called": [
                    {
                        "provider": tc.provider,
                        "tool": tc.tool,
                        "arguments": tc.arguments,
                        "duration_ms": tc.duration_ms,
                        "success": tc.success,
                        "error": tc.error,
                    }
                    for tc in result.tools_called
                ],
            }

    log.info("Starting Combined MCP Server at http://%s:%d", host, port)
    log.info("Enabled providers: %s", ", ".join(enabled))
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Combined MCP Server")
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
        default=8000,
        help="HTTP port (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio())
    else:
        asyncio.run(run_http(args.host, args.port))


if __name__ == "__main__":
    main()
