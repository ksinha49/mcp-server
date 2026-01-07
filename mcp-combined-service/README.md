# MCP Combined Service

All-in-one MCP (Model Context Protocol) server combining all five enterprise providers: Outlook, SharePoint, Teams, Azure DevOps, and Snowflake. Provides a unified interface to multiple Microsoft 365 and data services with optional **Code Execution** capabilities for advanced agent workflows.

## Overview

This service implements the MCP 2025-06-18 specification to expose multiple enterprise service providers through a single MCP server. It supports:
- Dynamic provider enablement
- Standard MCP tool calls
- **Code Execution mode** - Agents write TypeScript code that runs in a sandbox with access to all tools

## Features

- **All-in-One** - Single deployment for all providers
- **Dynamic Providers** - Enable/disable providers via configuration
- **Unified Endpoint** - Combined `/mcp` endpoint with prefixed tool names
- **Per-Provider Endpoints** - Dedicated `/mcp/{provider}` endpoints
- **Code Execution** - TypeScript sandbox for agent-generated code (98%+ context reduction)
- **Dual Sandbox** - Deno (development) or Docker (production) isolation
- **OAuth 2.1** - Secure authentication via OAuth Gateway
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Ports

| Port | Service |
|------|---------|
| 8000 | Main HTTP transport |
| 8001 | Deno code executor (when enabled) |

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
| Outlook | `outlook_search_emails`, `outlook_get_email`, `outlook_send_email`, `outlook_list_calendar_events`, `outlook_create_calendar_event`, `outlook_search_contacts` |
| SharePoint | `sharepoint_list_sites`, `sharepoint_get_site`, `sharepoint_search_documents`, `sharepoint_list_folder_contents` |
| Teams | `teams_list_teams`, `teams_list_channels`, `teams_send_channel_message`, `teams_list_chats`, `teams_create_meeting` |
| Azure DevOps | `azuredevops_list_projects`, `azuredevops_search_work_items`, `azuredevops_get_work_item`, `azuredevops_list_repos`, `azuredevops_list_pipelines`, `azuredevops_list_pull_requests` |
| Snowflake | `snowflake_list_databases`, `snowflake_list_schemas`, `snowflake_list_tables`, `snowflake_describe_table`, `snowflake_execute_query`, `snowflake_preview_table` |

## Quick Start

### Standard MCP Mode

#### STDIO Mode (Claude Desktop)

```bash
cd mcp-combined-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

# Enable specific providers
export ENABLED_PROVIDERS=outlook,sharepoint,teams

python -m app.main --transport stdio
```

#### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8000
```

### Code Execution Mode

Enable the code execution layer for advanced agent workflows:

```bash
# With Deno sandbox (development)
export CODE_EXECUTION_ENABLED=true
export SANDBOX_MODE=deno
python -m app.main --transport http --port 8000

# With Docker sandbox (production)
export CODE_EXECUTION_ENABLED=true
export SANDBOX_MODE=docker
python -m app.main --transport http --port 8000
```

#### Execute Code Example

```bash
curl -X POST http://localhost:8000/mcp/code/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const emails = await tools.outlook.search_emails({query: \"urgent\"});\nconst filtered = emails.filter(e => e.subject.includes(\"meeting\"));\nreturn { count: filtered.length, subjects: filtered.map(e => e.subject) };",
    "timeout_ms": 30000
  }'
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

### Standard Mode

```bash
# Build
docker build -t mcp-combined-service:latest .

# Run (HTTP mode)
docker run -p 8000:8000 \
  -e ENABLED_PROVIDERS=outlook,sharepoint,teams \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  mcp-combined-service:latest
```

### With Code Execution

```bash
# Run with Deno sandbox
docker run -p 8000:8000 -p 8001:8001 \
  -e ENABLED_PROVIDERS=outlook,sharepoint,snowflake \
  -e CODE_EXECUTION_ENABLED=true \
  -e SANDBOX_MODE=deno \
  mcp-combined-service:latest

# Run with Docker sandbox (requires Docker-in-Docker or socket mount)
docker run -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e ENABLED_PROVIDERS=outlook,sharepoint,snowflake \
  -e CODE_EXECUTION_ENABLED=true \
  -e SANDBOX_MODE=docker \
  mcp-combined-service:latest
```

### Docker Compose with Sandbox Pool

```bash
cd docker
docker-compose -f docker-compose.sandbox.yml up -d
```

## Environment Variables

### Provider Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLED_PROVIDERS` | No | all | Comma-separated list of providers |

### Code Execution Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODE_EXECUTION_ENABLED` | No | false | Enable code execution layer |
| `SANDBOX_MODE` | No | deno | Sandbox type: `deno` or `docker` |
| `DENO_SERVER_PORT` | No | 8001 | Deno executor port |
| `DOCKER_POOL_SIZE` | No | 5 | Pre-warmed Docker containers |
| `DOCKER_EXECUTOR_IMAGE` | No | mcp-code-executor:latest | Docker executor image |
| `MAX_EXECUTION_TIME_MS` | No | 60000 | Max code execution time |
| `MAX_MEMORY_MB` | No | 128 | Memory limit per execution |
| `RATE_LIMIT_PER_MINUTE` | No | 30 | Rate limit per user |

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

### Standard MCP Endpoints

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

### Code Execution Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp/code/status` | GET | Sandbox health status |
| `/mcp/code/tools` | GET | List tools with TypeScript schemas |
| `/mcp/code/validate` | POST | Validate code without executing |
| `/mcp/code/execute` | POST | Execute TypeScript code in sandbox |

## Code Execution Pattern

The code execution layer implements the pattern described in [Anthropic's "Code Execution with MCP"](https://www.anthropic.com/engineering/code-execution-with-mcp):

### Benefits

- **98%+ context reduction** - Only return filtered/processed results to the model
- **Batch operations** - Execute multiple tool calls in a single sandbox session
- **Data processing** - Filter, transform, aggregate data before returning
- **Progressive discovery** - Tools loaded on-demand, not all upfront

### Example: Complex Data Processing

```typescript
// Agent-generated code executed in sandbox
const [emails, events] = await Promise.all([
  tools.outlook.search_emails({ query: 'project-x', max_results: 100 }),
  tools.outlook.list_calendar_events({ start_date: '2024-01-01' })
]);

// Process data in sandbox (not in model context)
const urgentEmails = emails.filter(e => e.subject.includes('urgent'));
const eventsByDay = stdlib.transform.groupBy(events, e => e.start.split('T')[0]);

// Return only summary to model
return {
  urgentCount: urgentEmails.length,
  topSenders: stdlib.transform.unique(urgentEmails.map(e => e.from)).slice(0, 5),
  busiestDays: Object.entries(eventsByDay)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 3)
    .map(([day, evts]) => ({ day, count: evts.length }))
};
```

### Sandbox Comparison

| Feature | Deno | Docker |
|---------|------|--------|
| Startup Time | ~50ms | ~100ms (pre-warmed) |
| Isolation | V8 isolates | Container namespaces |
| Security | Permission flags | cgroups + seccomp |
| Best For | Development | Production |

## Provider Configuration Examples

### Microsoft 365 Only

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams
```

### Data Focus with Code Execution

```bash
ENABLED_PROVIDERS=snowflake,sharepoint
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=deno
```

### Development Focus

```bash
ENABLED_PROVIDERS=azuredevops
```

### All Providers with Docker Sandbox

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=docker
DOCKER_POOL_SIZE=10
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

For code execution:
- Deno >= 1.40 (for Deno sandbox)
- Docker >= 24.0 (for Docker sandbox)

## License

MIT
