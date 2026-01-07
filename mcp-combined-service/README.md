# MCP Combined Service

All-in-one MCP (Model Context Protocol) server combining all five enterprise providers: Outlook, SharePoint, Teams, Azure DevOps, and Snowflake. Provides a unified interface to multiple Microsoft 365 and data services.

## Overview

This service implements the MCP 2025-06-18 specification to expose multiple enterprise service providers through a single MCP server. It supports dynamic provider enablement, allowing you to configure which providers are active based on your needs.

## Features

- **All-in-One** - Single deployment for all providers
- **Dynamic Providers** - Enable/disable providers via configuration
- **Unified Endpoint** - Combined `/mcp` endpoint with prefixed tool names
- **Per-Provider Endpoints** - Dedicated `/mcp/{provider}` endpoints
- **OAuth 2.1** - Secure authentication via OAuth Gateway
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Port

**8000** (HTTP transport)

## Supported Providers

| Provider | Tools Prefix | Description |
|----------|--------------|-------------|
| `outlook` | `outlook_*` | Email, calendar, contacts |
| `sharepoint` | `sharepoint_*` | Documents, sites, lists |
| `teams` | `teams_*` | Chat, channels, meetings |
| `azuredevops` | `azuredevops_*` | Projects, repos, pipelines |
| `snowflake` | `snowflake_*` | Data warehouse queries |

## MCP Tools

Combined endpoint tools are prefixed with provider name:

| Provider | Tools |
|----------|-------|
| Outlook | `outlook_search_emails`, `outlook_get_email`, `outlook_send_email`, `outlook_list_calendar_events`, `outlook_create_calendar_event`, `outlook_search_contacts`, `outlook_get_contact` |
| SharePoint | `sharepoint_list_sites`, `sharepoint_get_site`, `sharepoint_search_documents`, `sharepoint_get_document`, `sharepoint_upload_document`, `sharepoint_download_document`, `sharepoint_list_items`, `sharepoint_create_item` |
| Teams | `teams_list_teams`, `teams_get_team`, `teams_list_channels`, `teams_list_messages`, `teams_send_message`, `teams_list_chat_messages`, `teams_send_chat_message`, `teams_get_meeting` |
| Azure DevOps | `azuredevops_list_projects`, `azuredevops_get_project`, `azuredevops_list_repositories`, `azuredevops_get_repository`, `azuredevops_list_pipelines`, `azuredevops_get_pipeline`, `azuredevops_list_pull_requests`, `azuredevops_get_pull_request` |
| Snowflake | `snowflake_query`, `snowflake_list_databases`, `snowflake_list_schemas`, `snowflake_list_tables`, `snowflake_describe_table`, `snowflake_list_views`, `snowflake_execute_stored_procedure` |

## Quick Start

### STDIO Mode (Claude Desktop)

```bash
cd mcp-combined-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

# Enable specific providers
export ENABLED_PROVIDERS=outlook,sharepoint,teams

python -m app.main --transport stdio
```

### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8000
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "enterprise": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-combined-service",
      "env": {
        "ENABLED_PROVIDERS": "outlook,sharepoint,teams,azuredevops,snowflake",
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
docker build -t mcp-combined-service:latest .

# Run (HTTP mode)
docker run -p 8000:8000 \
  -e ENABLED_PROVIDERS=outlook,sharepoint,teams \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  mcp-combined-service:latest
```

## Environment Variables

### Provider Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLED_PROVIDERS` | No | all | Comma-separated list of providers |

### Microsoft OAuth (Required for Microsoft providers)

| Variable | Required | Description |
|----------|----------|-------------|
| `OAUTH_GATEWAY_URL` | Yes | URL of the OAuth Gateway |
| `MICROSOFT_CLIENT_ID` | Yes | Microsoft OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | Yes | Microsoft OAuth client secret |
| `MICROSOFT_TENANT_ID` | Yes | Microsoft tenant ID |
| `TOKEN_ENCRYPTION_KEY` | Yes | Token encryption key |

### Azure DevOps (if enabled)

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_DEVOPS_ORGANIZATION_URL` | Yes | Azure DevOps organization URL |
| `AZURE_DEVOPS_PAT` | Yes* | Personal Access Token |

### Snowflake (if enabled)

| Variable | Required | Description |
|----------|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | Snowflake account identifier |
| `SNOWFLAKE_USER` | Yes | Username |
| `SNOWFLAKE_PASSWORD` | Yes* | Password (or key-pair auth) |
| `SNOWFLAKE_WAREHOUSE` | No | Warehouse name |
| `SNOWFLAKE_DATABASE` | No | Default database |

### Server Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## API Endpoints (HTTP Mode)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with enabled providers |
| `/.well-known/oauth-protected-resource.json` | GET | OAuth metadata |
| `/mcp` | POST | Combined endpoint (prefixed tools) |
| `/mcp/outlook` | POST | Outlook-only endpoint |
| `/mcp/sharepoint` | POST | SharePoint-only endpoint |
| `/mcp/teams` | POST | Teams-only endpoint |
| `/mcp/azuredevops` | POST | Azure DevOps-only endpoint |
| `/mcp/snowflake` | POST | Snowflake-only endpoint |

## Provider Configuration Examples

### Microsoft 365 Only

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams
```

### Data Focus

```bash
ENABLED_PROVIDERS=snowflake,sharepoint
```

### Development Focus

```bash
ENABLED_PROVIDERS=azuredevops
```

### All Providers

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
# Or simply omit the variable for all providers
```

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Detailed installation instructions
- [SECURITY.md](./SECURITY.md) - Security considerations and best practices

## Dependencies

Combines dependencies from all providers:
- mcp >= 1.0.0
- fastmcp >= 2.0.0
- FastAPI >= 0.109.0
- uvicorn >= 0.27.0
- msgraph-sdk >= 1.0.0
- azure-identity >= 1.15.0
- azure-devops >= 7.1.0b1
- snowflake-connector-python >= 3.6.0
- httpx >= 0.26.0
- pydantic >= 2.5.0
- PyJWT >= 2.8.0

## License

MIT
