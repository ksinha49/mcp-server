# MCP OAuth Gateway

Centralized OAuth 2.1 service for MCP (Model Context Protocol) servers. Handles authentication flows, token storage, and multi-provider OAuth coordination.

## Overview

The OAuth Gateway acts as a centralized authentication service for all MCP servers in this repository. It implements:

- **OAuth 2.1** with mandatory PKCE (S256)
- **Multi-Provider Support** - Microsoft, Snowflake, and extensible for others
- **Token Management** - Secure storage, refresh, and revocation
- **RFC 9728 Compliance** - Protected Resource Metadata discovery

## Features

- Centralized OAuth flow management
- Multi-provider authentication (Microsoft, Snowflake)
- PKCE enforcement for all flows
- Encrypted token storage
- Redis-backed session management
- PostgreSQL for persistent storage
- CORS configuration for web clients

## Port

**8000** (default)

## Architecture

```
MCP Client → OAuth Gateway → Identity Provider (Microsoft/Snowflake)
                ↓
         Token Storage (PostgreSQL + Encryption)
                ↓
         MCP Servers (validate tokens)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/oauth-protected-resource.json` | GET | Protected Resource Metadata |
| `/oauth/authorize` | POST | Initiate OAuth flow |
| `/oauth/callback/{provider}` | GET/POST | OAuth callback handler |
| `/oauth/token` | POST | Token retrieval |
| `/oauth/refresh` | POST | Token refresh |
| `/oauth/revoke` | POST | Token revocation |
| `/health` | GET | Health check |
| `/ping` | GET | Ping endpoint |

## Supported Providers

| Provider | Description |
|----------|-------------|
| Microsoft | Azure AD / Microsoft Entra ID |
| Snowflake | Snowflake OAuth |

## Quick Start

```bash
# Install dependencies
cd mcp-oauth-gateway
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib

# Set environment variables
export MICROSOFT_CLIENT_ID=your-client-id
export MICROSOFT_CLIENT_SECRET=your-client-secret
export MICROSOFT_TENANT_ID=your-tenant-id
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=postgresql://user:pass@localhost/mcp_oauth

# Run the server
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# Build
docker build -t mcp-oauth-gateway:latest .

# Run
docker run -p 8000:8000 \
  -e MICROSOFT_CLIENT_ID=... \
  -e MICROSOFT_CLIENT_SECRET=... \
  mcp-oauth-gateway:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MICROSOFT_CLIENT_ID` | Yes | Microsoft OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | Yes | Microsoft OAuth client secret |
| `MICROSOFT_TENANT_ID` | Yes | Microsoft tenant ID |
| `REDIS_URL` | Yes | Redis connection URL |
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `TOKEN_ENCRYPTION_KEY` | Yes | Base64-encoded 32-byte key |
| `GATEWAY_URL` | No | Public URL of this gateway |
| `FRONTEND_URL` | No | Frontend URL for redirects |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Detailed installation instructions
- [SECURITY.md](./SECURITY.md) - Security considerations and best practices

## Dependencies

- FastAPI >= 0.109.0
- uvicorn >= 0.27.0
- msal >= 1.26.0
- PyJWT >= 2.8.0
- redis >= 5.0.0
- sqlalchemy >= 2.0.0
- asyncpg >= 0.29.0
- pydantic >= 2.5.0
- httpx >= 0.26.0

## License

MIT
