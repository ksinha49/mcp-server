# MCP Azure DevOps Service

MCP (Model Context Protocol) server for Azure DevOps integration. Provides AI clients with access to projects, repositories, pipelines, and pull requests via the Azure DevOps REST API.

## Overview

This service implements the MCP 2025-06-18 specification to expose Azure DevOps functionality to AI clients like Claude Desktop. It supports both STDIO transport (for local use) and HTTP transport (for production deployments).

## Features

- **Project Management** - List and access projects
- **Repository Operations** - List repositories, browse code
- **Pipeline Management** - List and view pipelines
- **Pull Request Tracking** - List and view pull requests
- **OAuth 2.1** - Secure authentication via OAuth Gateway
- **PAT Support** - Personal Access Token alternative
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Port

**8004** (HTTP transport)

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects in organization |
| `get_project` | Get project details by ID |
| `list_repositories` | List repositories in a project |
| `get_repository` | Get repository details |
| `list_pipelines` | List build/release pipelines |
| `get_pipeline` | Get pipeline details |
| `list_pull_requests` | List pull requests |
| `get_pull_request` | Get pull request details |

## Quick Start

### STDIO Mode (Claude Desktop)

```bash
cd mcp-azuredevops-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

python -m app.main --transport stdio
```

### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8004
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "azuredevops": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-azuredevops-service",
      "env": {
        "AZURE_DEVOPS_ORGANIZATION_URL": "https://dev.azure.com/your-org",
        "AZURE_DEVOPS_PAT": "your-pat-token"
      }
    }
  }
}
```

## Docker

```bash
# Build
docker build -t mcp-azuredevops-service:latest .

# Run (HTTP mode)
docker run -p 8004:8004 \
  -e AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org \
  -e AZURE_DEVOPS_PAT=your-pat-token \
  mcp-azuredevops-service:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_DEVOPS_ORGANIZATION_URL` | Yes | Azure DevOps organization URL |
| `AZURE_DEVOPS_PAT` | Yes* | Personal Access Token |
| `OAUTH_GATEWAY_URL` | Yes* | URL of OAuth Gateway (if using OAuth) |
| `MICROSOFT_CLIENT_ID` | No | Microsoft OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | No | Microsoft OAuth client secret |
| `MICROSOFT_TENANT_ID` | No | Microsoft tenant ID |
| `TOKEN_ENCRYPTION_KEY` | No | Token encryption key |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8004) |

*Either `AZURE_DEVOPS_PAT` or OAuth configuration required

## Authentication Methods

### Personal Access Token (Recommended for Development)

```bash
AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org
AZURE_DEVOPS_PAT=your-pat-token
```

### OAuth 2.1 (Recommended for Production)

```bash
AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org
OAUTH_GATEWAY_URL=https://your-oauth-gateway.com
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
```

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
- azure-devops >= 7.1.0b1
- msrest >= 0.7.1
- httpx >= 0.26.0
- pydantic >= 2.5.0
- PyJWT >= 2.8.0

## License

MIT
