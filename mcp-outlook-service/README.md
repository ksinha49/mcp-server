# MCP Outlook Service

MCP (Model Context Protocol) server for Microsoft Outlook integration. Provides AI clients with access to email, calendar, and contacts via the Microsoft Graph API.

## Overview

This service implements the MCP 2025-06-18 specification to expose Microsoft Outlook functionality to AI clients like Claude Desktop. It supports both STDIO transport (for local use) and HTTP transport (for production deployments).

## Features

- **Email Management** - Search, read, and send emails
- **Calendar Operations** - List and create calendar events
- **Contact Management** - Search and retrieve contacts
- **OAuth 2.1** - Secure authentication via OAuth Gateway
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Port

**8001** (HTTP transport)

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_emails` | Search emails with query filters |
| `get_email` | Get full email content by ID |
| `send_email` | Send a new email |
| `list_calendar_events` | List calendar events in date range |
| `create_calendar_event` | Create a new calendar event |
| `search_contacts` | Search contacts by name or email |
| `get_contact` | Get contact details by ID |

## Quick Start

### STDIO Mode (Claude Desktop)

```bash
cd mcp-outlook-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

python -m app.main --transport stdio
```

### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8001
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "outlook": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-outlook-service",
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
docker build -t mcp-outlook-service:latest .

# Run (HTTP mode)
docker run -p 8001:8001 \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  mcp-outlook-service:latest
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
| `PORT` | No | Server port (default: 8001) |

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
