# Installation Guide - MCP Combined Service

## Prerequisites

- Python 3.11 or higher
- Access to services you want to enable
- OAuth Gateway configured (for Microsoft providers)

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-combined-service
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e ../mcp-oauth-lib
```

### 4. Configure Environment Variables

Create `.env` file based on which providers you want to enable:

#### Full Configuration (All Providers)

```bash
# Enabled Providers
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG

# Microsoft OAuth (for Outlook, SharePoint, Teams)
OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Azure DevOps
AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org
AZURE_DEVOPS_PAT=your-pat-token

# Snowflake
SNOWFLAKE_ACCOUNT=your-account.region
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your-database
```

#### Microsoft 365 Only

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams

OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key
```

#### Data Focus (Snowflake + SharePoint)

```bash
ENABLED_PROVIDERS=sharepoint,snowflake

# Microsoft (for SharePoint)
OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Snowflake
SNOWFLAKE_ACCOUNT=your-account.region
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
```

### 5. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
python -m app.main --transport stdio
```

#### HTTP Mode (for production)

```bash
python -m app.main --transport http --port 8000
```

### 6. Verify Installation

```bash
# HTTP mode only
curl http://localhost:8000/health
```

Expected response showing enabled providers:
```json
{
  "status": "healthy",
  "service": "mcp-combined-service",
  "enabled_providers": ["outlook", "sharepoint", "teams", "azuredevops", "snowflake"]
}
```

## Claude Desktop Integration

### 1. Locate Config File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add MCP Server Configuration

```json
{
  "mcpServers": {
    "enterprise": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-combined-service",
      "env": {
        "ENABLED_PROVIDERS": "outlook,sharepoint,teams",
        "OAUTH_GATEWAY_URL": "https://your-oauth-gateway.com",
        "MICROSOFT_CLIENT_ID": "your-client-id",
        "MICROSOFT_CLIENT_SECRET": "your-client-secret",
        "MICROSOFT_TENANT_ID": "your-tenant-id",
        "TOKEN_ENCRYPTION_KEY": "your-encryption-key"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

## Docker Deployment

### Build Image

```bash
docker build -t mcp-combined-service:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-combined-service \
  -p 8000:8000 \
  -e ENABLED_PROVIDERS=outlook,sharepoint,teams \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  -e MICROSOFT_CLIENT_SECRET=your-client-secret \
  -e MICROSOFT_TENANT_ID=your-tenant-id \
  -e TOKEN_ENCRYPTION_KEY=your-key \
  mcp-combined-service:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  combined-service:
    build: ./mcp-combined-service
    ports:
      - "8000:8000"
    environment:
      - ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
      - OAUTH_GATEWAY_URL=http://oauth-gateway:8000
      - MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID}
      - MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET}
      - MICROSOFT_TENANT_ID=${MICROSOFT_TENANT_ID}
      - TOKEN_ENCRYPTION_KEY=${TOKEN_ENCRYPTION_KEY}
      - AZURE_DEVOPS_ORGANIZATION_URL=${AZURE_DEVOPS_ORGANIZATION_URL}
      - AZURE_DEVOPS_PAT=${AZURE_DEVOPS_PAT}
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
    depends_on:
      - oauth-gateway
```

## AWS ECS Deployment

### Task Definition

See `environments/prod/ecs-task-definition.json` for the complete ECS task definition.

### Required AWS Resources

1. **Secrets Manager**:
   - `/mcp/prod/combined/microsoft_client_secret`
   - `/mcp/prod/combined/token_encryption_key`
   - `/mcp/prod/combined/azuredevops_pat`
   - `/mcp/prod/combined/snowflake_password`

2. **SSM Parameters**:
   - `/mcp/prod/combined/enabled_providers`
   - `/mcp/prod/combined/microsoft_client_id`
   - `/mcp/prod/combined/microsoft_tenant_id`
   - `/mcp/prod/combined/azuredevops_organization_url`
   - `/mcp/prod/combined/snowflake_account`
   - `/mcp/prod/combined/snowflake_user`

### Deploy Command

```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-combined-service \
  --force-new-deployment
```

## Provider-Specific Setup

### Microsoft Providers (Outlook, SharePoint, Teams)

See individual service documentation:
- [mcp-outlook-service/INSTALLATION.md](../mcp-outlook-service/INSTALLATION.md)
- [mcp-sharepoint-service/INSTALLATION.md](../mcp-sharepoint-service/INSTALLATION.md)
- [mcp-teams-service/INSTALLATION.md](../mcp-teams-service/INSTALLATION.md)

### Azure DevOps

See [mcp-azuredevops-service/INSTALLATION.md](../mcp-azuredevops-service/INSTALLATION.md)

### Snowflake

See [mcp-snowflake-service/INSTALLATION.md](../mcp-snowflake-service/INSTALLATION.md)

## Troubleshooting

### Provider Not Available

If a provider's tools don't appear:

1. Check `ENABLED_PROVIDERS` includes the provider
2. Verify provider-specific environment variables are set
3. Check logs for initialization errors

```bash
# Check which providers loaded
curl http://localhost:8000/health
```

### Mixed Authentication Issues

Different providers may need different authentication:
- Microsoft providers: OAuth via gateway
- Azure DevOps: PAT or OAuth
- Snowflake: Password, key-pair, or OAuth

Ensure each provider's credentials are configured correctly.

### Performance Considerations

Running all providers increases:
- Memory usage
- Startup time
- Dependency footprint

For production, consider enabling only the providers you need.

## Health Check

```bash
# HTTP mode
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "service": "mcp-combined-service",
  "enabled_providers": ["outlook", "sharepoint", "teams"]
}
```
