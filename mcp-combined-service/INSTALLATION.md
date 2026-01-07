# Installation Guide - MCP Combined Service

## Prerequisites

- Python 3.11 or higher
- Access to services you want to enable
- OAuth Gateway configured (for Microsoft providers)

### For Code Execution (Optional)

- **Deno sandbox**: Deno >= 1.40
- **Docker sandbox**: Docker >= 24.0

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

### 4. Install Deno (For Code Execution)

```bash
# macOS / Linux
curl -fsSL https://deno.land/install.sh | sh

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# Verify installation
deno --version
```

### 5. Configure Environment Variables

Create `.env` file based on which providers you want to enable:

#### Full Configuration (All Providers + Code Execution)

```bash
# Enabled Providers
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG

# Code Execution
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=deno
DENO_SERVER_PORT=8001
MAX_EXECUTION_TIME_MS=60000
MAX_MEMORY_MB=128
RATE_LIMIT_PER_MINUTE=30

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

#### Microsoft 365 Only (Standard Mode)

```bash
ENABLED_PROVIDERS=outlook,sharepoint,teams

OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key
```

#### Data Focus with Code Execution

```bash
ENABLED_PROVIDERS=sharepoint,snowflake

# Enable code execution for data processing
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=deno

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

### 6. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
python -m app.main --transport stdio
```

#### HTTP Mode (Standard)

```bash
python -m app.main --transport http --port 8000
```

#### HTTP Mode with Code Execution

```bash
CODE_EXECUTION_ENABLED=true SANDBOX_MODE=deno python -m app.main --transport http --port 8000
```

### 7. Verify Installation

```bash
# Health check (HTTP mode only)
curl http://localhost:8000/health

# Expected response showing enabled providers
{
  "status": "healthy",
  "service": "mcp-combined-service",
  "enabled_providers": ["outlook", "sharepoint", "teams", "azuredevops", "snowflake"]
}

# If code execution is enabled
curl http://localhost:8000/mcp/code/status

# Expected response
{
  "enabled": true,
  "status": "healthy",
  "mode": "deno",
  "providers": ["outlook", "sharepoint", "teams", "azuredevops", "snowflake"]
}
```

## Code Execution Setup

### Deno Sandbox (Recommended for Development)

1. Install Deno (see step 4 above)
2. Set environment variables:

```bash
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=deno
DENO_SERVER_PORT=8001
```

3. Start the server - Deno executor starts automatically

### Docker Sandbox (Recommended for Production)

1. Build the executor image:

```bash
docker build -t mcp-code-executor:latest -f docker/executor/Dockerfile .
```

2. Set environment variables:

```bash
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=docker
DOCKER_POOL_SIZE=5
DOCKER_EXECUTOR_IMAGE=mcp-code-executor:latest
```

3. Start the server - Docker containers are pre-warmed automatically

### Testing Code Execution

```bash
# Validate code syntax
curl -X POST http://localhost:8000/mcp/code/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "const x = await tools.outlook.search_emails({});"}'

# Execute code
curl -X POST http://localhost:8000/mcp/code/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const result = await tools.snowflake.list_databases({});\nreturn result;",
    "timeout_ms": 10000
  }'
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

### Run Container (Standard Mode)

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

### Run Container (With Deno Code Execution)

```bash
docker run -d \
  --name mcp-combined-service \
  -p 8000:8000 \
  -p 8001:8001 \
  -e ENABLED_PROVIDERS=outlook,sharepoint,snowflake \
  -e CODE_EXECUTION_ENABLED=true \
  -e SANDBOX_MODE=deno \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  -e MICROSOFT_CLIENT_SECRET=your-client-secret \
  -e MICROSOFT_TENANT_ID=your-tenant-id \
  -e TOKEN_ENCRYPTION_KEY=your-key \
  mcp-combined-service:latest
```

### Run Container (With Docker Sandbox)

```bash
docker run -d \
  --name mcp-combined-service \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e ENABLED_PROVIDERS=outlook,sharepoint,snowflake \
  -e CODE_EXECUTION_ENABLED=true \
  -e SANDBOX_MODE=docker \
  -e DOCKER_POOL_SIZE=5 \
  mcp-combined-service:latest
```

### Docker Compose (Full Stack with Sandbox Pool)

```bash
cd docker
docker-compose -f docker-compose.sandbox.yml up -d
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  combined-service:
    build: ./mcp-combined-service
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
      - CODE_EXECUTION_ENABLED=true
      - SANDBOX_MODE=deno
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
   - `/mcp/prod/combined/code_execution_enabled`
   - `/mcp/prod/combined/sandbox_mode`
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

### Code Execution Not Working

1. Verify `CODE_EXECUTION_ENABLED=true`
2. Check sandbox mode is set correctly
3. For Deno: ensure Deno is installed and in PATH
4. For Docker: ensure Docker daemon is running

```bash
# Check sandbox status
curl http://localhost:8000/mcp/code/status

# For Deno mode, verify Deno is available
deno --version

# For Docker mode, verify Docker is running
docker ps
```

### Code Validation Failing

Static analysis blocks dangerous patterns:

```bash
# These patterns are blocked:
# - eval(), Function(), new Function()
# - import() (dynamic imports)
# - Deno.*, globalThis, __proto__
# - require(), process.*

# Test validation
curl -X POST http://localhost:8000/mcp/code/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "const x = 1 + 1; return x;"}'
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

With code execution enabled:
- Deno sandbox: ~50-100MB additional memory
- Docker sandbox: ~128MB per container * pool size

## Health Checks

### Standard Health Check

```bash
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "service": "mcp-combined-service",
  "enabled_providers": ["outlook", "sharepoint", "teams"]
}
```

### Code Execution Health Check

```bash
curl http://localhost:8000/mcp/code/status

# Expected response (Deno mode)
{
  "enabled": true,
  "status": "healthy",
  "mode": "deno",
  "port": 8001,
  "providers": ["outlook", "sharepoint", "snowflake"]
}

# Expected response (Docker mode)
{
  "enabled": true,
  "status": "healthy",
  "mode": "docker",
  "pool_size": 5,
  "active_containers": 5,
  "available": 4,
  "in_use": 1
}
```
