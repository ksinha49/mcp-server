# MCP SharePoint Service

MCP (Model Context Protocol) server for Microsoft SharePoint integration. Provides AI clients with access to SharePoint sites, documents, and lists via the Microsoft Graph API.

## Overview

This service implements the MCP 2025-06-18 specification to expose Microsoft SharePoint functionality to AI clients like Claude Desktop. It supports both STDIO transport (for local use) and HTTP transport (for production deployments).

## Features

- **Site Management** - List and access SharePoint sites
- **Document Operations** - Search, upload, download documents
- **List Management** - Access and manage SharePoint lists
- **OAuth 2.1** - Secure authentication via OAuth Gateway
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Port

**8002** (HTTP transport)

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_sites` | List accessible SharePoint sites |
| `get_site` | Get site details by ID |
| `search_documents` | Search documents across sites |
| `get_document` | Get document metadata and content |
| `upload_document` | Upload a document to a library |
| `download_document` | Download document content |
| `list_items` | Get items from a SharePoint list |
| `create_item` | Create new item in a list |

## Quick Start

### STDIO Mode (Claude Desktop)

```bash
cd mcp-sharepoint-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

python -m app.main --transport stdio
```

### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8002
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-sharepoint-service",
      "env": {
        "OAUTH_GATEWAY_URL": "https://your-oauth-gateway.com",
        "MICROSOFT_CLIENT_ID": "your-client-id"
      }
    }
  }
}
```

## Docker

```bash
# Build
docker build -t mcp-sharepoint-service:latest .

# Run (HTTP mode)
docker run -p 8002:8002 \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  mcp-sharepoint-service:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OAUTH_GATEWAY_URL` | Yes | URL of the OAuth Gateway |
| `MICROSOFT_CLIENT_ID` | Yes | Microsoft OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | Yes | Microsoft OAuth client secret |
| `MICROSOFT_TENANT_ID` | Yes | Microsoft tenant ID |
| `TOKEN_ENCRYPTION_KEY` | Yes | Token encryption key |
| `RESOURCE_URI` | No | Server URI for audience validation |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8002) |

## API Endpoints (HTTP Mode)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/.well-known/oauth-protected-resource.json` | GET | OAuth metadata |
| `/mcp` | POST | MCP message endpoint |

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Detailed installation instructions
- [SECURITY.md](./SECURITY.md) - Security considerations and best practices

## Dependencies

- mcp >= 1.0.0
- fastmcp >= 2.0.0
- FastAPI >= 0.109.0
- uvicorn >= 0.27.0
- msgraph-sdk >= 1.0.0
- azure-identity >= 1.15.0
- httpx >= 0.26.0
- pydantic >= 2.5.0
- PyJWT >= 2.8.0

## License

MIT
