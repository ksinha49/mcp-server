# Installation Guide - MCP SharePoint Service

## Prerequisites

- Python 3.11 or higher
- Access to MCP OAuth Gateway
- Microsoft Azure AD app registration with SharePoint permissions

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-sharepoint-service
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

Create `.env` file:

```bash
# OAuth Configuration
OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Server Configuration
HOST=0.0.0.0
PORT=8002
LOG_LEVEL=DEBUG

# Optional
RESOURCE_URI=http://localhost:8002
```

### 5. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
python -m app.main --transport stdio
```

#### HTTP Mode (for production)

```bash
python -m app.main --transport http --port 8002
```

### 6. Verify Installation

```bash
# HTTP mode only
curl http://localhost:8002/health
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
    "sharepoint": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-sharepoint-service",
      "env": {
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
docker build -t mcp-sharepoint-service:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-sharepoint-service \
  -p 8002:8002 \
  -e OAUTH_GATEWAY_URL=https://oauth-gateway.example.com \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  -e MICROSOFT_CLIENT_SECRET=your-client-secret \
  -e MICROSOFT_TENANT_ID=your-tenant-id \
  -e TOKEN_ENCRYPTION_KEY=your-key \
  mcp-sharepoint-service:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  sharepoint-service:
    build: ./mcp-sharepoint-service
    ports:
      - "8002:8002"
    environment:
      - OAUTH_GATEWAY_URL=http://oauth-gateway:8000
      - MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID}
      - MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET}
      - MICROSOFT_TENANT_ID=${MICROSOFT_TENANT_ID}
      - TOKEN_ENCRYPTION_KEY=${TOKEN_ENCRYPTION_KEY}
    depends_on:
      - oauth-gateway
```

## AWS ECS Deployment

### Task Definition

See `environments/prod/ecs-task-definition.json` for the complete ECS task definition.

### Required AWS Resources

1. **Secrets Manager**:
   - `/mcp/prod/sharepoint/microsoft_client_secret`
   - `/mcp/prod/sharepoint/token_encryption_key`

2. **SSM Parameters**:
   - `/mcp/prod/sharepoint/microsoft_client_id`
   - `/mcp/prod/sharepoint/microsoft_tenant_id`
   - `/mcp/prod/oauth-gateway/url`

### Deploy Command

```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-sharepoint-service \
  --force-new-deployment
```

## Microsoft Azure AD Setup

### Required API Permissions

| Permission | Type | Description |
|------------|------|-------------|
| `User.Read` | Delegated | Sign in and read user profile |
| `Sites.Read.All` | Delegated | Read items in all site collections |
| `Sites.ReadWrite.All` | Delegated | Edit items in all site collections |
| `Files.Read.All` | Delegated | Read files user can access |
| `Files.ReadWrite.All` | Delegated | Read/write files user can access |

### Configure Redirect URI

Add the following redirect URI to your Azure AD app:
```
https://your-oauth-gateway.com/oauth/callback/microsoft
```

## Troubleshooting

### OAuth Errors

```bash
# Verify OAuth Gateway is accessible
curl https://your-oauth-gateway.com/health

# Check token encryption key format
python -c "import base64; key='your-key'; print(len(base64.urlsafe_b64decode(key)))"
# Should output: 32
```

### SharePoint Access Errors

Common issues:
- **Access Denied**: User lacks permissions on the target site
- **Site Not Found**: Site URL or ID is incorrect
- **Throttling**: Too many requests, implement backoff

### Permission Errors

If you see `Insufficient privileges`:
1. Verify API permissions in Azure AD
2. Ensure admin consent is granted for `Sites.Read.All` or `Sites.ReadWrite.All`
3. Re-authenticate to get new tokens with updated scopes

## Health Check

```bash
# HTTP mode
curl http://localhost:8002/health

# Expected response
{"status": "healthy", "service": "mcp-sharepoint-service"}
```
