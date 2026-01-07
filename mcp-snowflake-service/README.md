# MCP Snowflake Service

MCP (Model Context Protocol) server for Snowflake Data Cloud integration. Provides AI clients with access to query data warehouses, explore schemas, and execute SQL via the Snowflake Connector.

## Overview

This service implements the MCP 2025-06-18 specification to expose Snowflake functionality to AI clients like Claude Desktop. It supports both STDIO transport (for local use) and HTTP transport (for production deployments).

## Features

- **SQL Query Execution** - Execute queries against Snowflake
- **Schema Discovery** - List databases, schemas, tables, views
- **Table Inspection** - Describe table structures
- **Stored Procedures** - Execute stored procedures
- **Multiple Auth Methods** - Password, key-pair, OAuth
- **Dual Transport** - STDIO and HTTP support
- **MCP Compliant** - Follows MCP 2025-06-18 specification

## Port

**8005** (HTTP transport)

## MCP Tools

| Tool | Description |
|------|-------------|
| `query` | Execute SQL query and return results |
| `list_databases` | List available databases |
| `list_schemas` | List schemas in a database |
| `list_tables` | List tables in a schema |
| `describe_table` | Get table structure (columns, types) |
| `list_views` | List views in a schema |
| `execute_stored_procedure` | Execute a stored procedure |

## Quick Start

### STDIO Mode (Claude Desktop)

```bash
cd mcp-snowflake-service
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

python -m app.main --transport stdio
```

### HTTP Mode (Production)

```bash
python -m app.main --transport http --port 8005
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-snowflake-service",
      "env": {
        "SNOWFLAKE_ACCOUNT": "your-account.region",
        "SNOWFLAKE_USER": "your-username",
        "SNOWFLAKE_PASSWORD": "your-password",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_DATABASE": "your-database"
      }
    }
  }
}
```

## Docker

```bash
# Build
docker build -t mcp-snowflake-service:latest .

# Run (HTTP mode)
docker run -p 8005:8005 \
  -e SNOWFLAKE_ACCOUNT=your-account.region \
  -e SNOWFLAKE_USER=your-username \
  -e SNOWFLAKE_PASSWORD=your-password \
  mcp-snowflake-service:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | Snowflake account identifier |
| `SNOWFLAKE_USER` | Yes | Username |
| `SNOWFLAKE_PASSWORD` | Yes* | Password (if using password auth) |
| `SNOWFLAKE_WAREHOUSE` | No | Warehouse name (default: COMPUTE_WH) |
| `SNOWFLAKE_DATABASE` | No | Default database |
| `SNOWFLAKE_SCHEMA` | No | Default schema |
| `SNOWFLAKE_ROLE` | No | Role to use |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | No | Path to private key (key-pair auth) |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | No | Private key passphrase |
| `SNOWFLAKE_OAUTH_CLIENT_ID` | No | OAuth client ID |
| `SNOWFLAKE_OAUTH_CLIENT_SECRET` | No | OAuth client secret |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8005) |

*Required for password authentication

## Authentication Methods

### Password Authentication (Simplest)

```bash
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
```

### Key-Pair Authentication (Recommended for Production)

```bash
SNOWFLAKE_USER=your-username
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/private_key.pem
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=optional-passphrase
```

### OAuth (Enterprise)

```bash
SNOWFLAKE_OAUTH_CLIENT_ID=your-client-id
SNOWFLAKE_OAUTH_CLIENT_SECRET=your-client-secret
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
- snowflake-connector-python >= 3.6.0
- httpx >= 0.26.0
- pydantic >= 2.5.0
- PyJWT >= 2.8.0
- cryptography >= 41.0.0

## License

MIT
