# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise MCP (Model Context Protocol) Servers repository implementing MCP-compliant servers for AI clients. Follows MCP 2025-06-18 specification with OAuth 2.1 authentication.

**Services:**
- **Context7 MCP** (TypeScript) - Documentation server for up-to-date library docs
- **OAuth Gateway** (Python) - Centralized OAuth service for MCP servers
- **Outlook MCP** (Python) - Microsoft Outlook email, calendar, contacts
- **SharePoint MCP** (Python) - Microsoft SharePoint documents and sites
- **Teams MCP** (Python) - Microsoft Teams chat and channels
- **Azure DevOps MCP** (Python) - Azure DevOps projects and repos
- **Snowflake MCP** (Python) - Snowflake data warehouse queries

## Repository Structure

```
mcp-server/
├── mcp-oauth-lib/            # Shared Python OAuth library (PKCE, token validation)
├── mcp-oauth-gateway/        # Centralized OAuth service (FastAPI)
├── mcp-outlook-service/      # Outlook MCP Server
├── mcp-sharepoint-service/   # SharePoint MCP Server (template)
├── mcp-teams-service/        # Teams MCP Server (template)
├── mcp-azuredevops-service/  # Azure DevOps MCP Server (template)
├── mcp-snowflake-service/    # Snowflake MCP Server (template)
├── mcp-context-7-service/    # Context7 TypeScript MCP server
├── mcp-ecs-service-1/        # Sample Python ECS service
└── docs/                     # Architecture diagrams
```

## Build & Development Commands

### Shared OAuth Library (mcp-oauth-lib/)

```bash
cd mcp-oauth-lib
pip install -e .                 # Install in editable mode
pip install -e ".[dev]"          # With dev dependencies
pytest                           # Run tests
```

### OAuth Gateway (mcp-oauth-gateway/)

```bash
cd mcp-oauth-gateway
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib  # Install shared lib

# Run locally
uvicorn app.main:app --reload --port 8000

# Docker
docker build -t mcp-oauth-gateway:latest .
docker run -p 8000:8000 mcp-oauth-gateway:latest
```

### Outlook MCP Server (mcp-outlook-service/)

```bash
cd mcp-outlook-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

# STDIO mode (Claude Desktop)
python -m app.main --transport stdio

# HTTP mode
python -m app.main --transport http --port 8001

# Docker
docker build -t mcp-outlook-service:latest .
```

### Context7 Service (mcp-context-7-service/)

```bash
cd mcp-context-7-service
bun install && bun run build
node dist/index.js --transport http  # HTTP mode
node dist/index.js --transport stdio # STDIO mode
bun run lint && bun run format       # Lint & format
```

## Architecture

### MCP 2025-06-18 Compliance

All services follow [MCP 2025-06-18 specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization):

- **OAuth 2.1** with mandatory PKCE (S256)
- **Protected Resource Metadata** at `/.well-known/oauth-protected-resource.json`
- **Streamable HTTP transport** (primary) + SSE (backward compatibility)
- **Token audience binding** per RFC 8707

### OAuth Gateway Pattern

```
MCP Client → OAuth Gateway → Individual MCP Servers
                ↓
         Token Storage (encrypted)
```

**Gateway endpoints:**
- `/.well-known/oauth-protected-resource.json` - RFC 9728 metadata
- `/oauth/authorize` - Initiate OAuth flow
- `/oauth/callback/{provider}` - Handle callbacks
- `/oauth/token` - Token retrieval
- `/health` - Health check

### MCP Server Pattern

Each MCP server:
- Acts as OAuth 2.1 Resource Server (validates tokens only)
- Uses `mcp-oauth-lib` for token validation
- Supports both STDIO and HTTP transports
- Publishes own Protected Resource Metadata

## Key Files

### OAuth Library
- `mcp-oauth-lib/mcp_oauth/pkce.py` - PKCE implementation (RFC 7636)
- `mcp-oauth-lib/mcp_oauth/token_validator.py` - JWT validation with audience binding
- `mcp-oauth-lib/mcp_oauth/state.py` - Redis-backed OAuth state management

### OAuth Gateway
- `mcp-oauth-gateway/app/main.py` - FastAPI entry point
- `mcp-oauth-gateway/app/services/microsoft_auth.py` - Microsoft OAuth flows (MSAL)
- `mcp-oauth-gateway/app/routers/well_known.py` - Discovery endpoints

### Outlook Service
- `mcp-outlook-service/app/main.py` - MCP server entry
- `mcp-outlook-service/app/provider.py` - Microsoft Graph API client
- `mcp-outlook-service/app/tools.py` - MCP tool definitions

### Context7 Service
- `mcp-context-7-service/src/index.ts:108` - `createServerInstance()`
- `mcp-context-7-service/src/lib/api.ts` - Context7 API client

## Environment Variables

### OAuth Gateway
```
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=...
TOKEN_ENCRYPTION_KEY=...
```

### MCP Servers
```
OAUTH_GATEWAY_URL=https://mcp-oauth.internal.example.com
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=...
TOKEN_ENCRYPTION_KEY=...
```

## Tech Stack

**Python Services:**
- FastAPI, Uvicorn
- MSAL (Microsoft auth)
- Pydantic, Redis
- MCP SDK / FastMCP

**TypeScript Services:**
- Bun / Node.js
- @modelcontextprotocol/sdk
- Zod, Commander
