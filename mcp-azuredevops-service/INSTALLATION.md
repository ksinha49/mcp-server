# Installation Guide - MCP Azure DevOps Service

## Prerequisites

- Python 3.11 or higher
- Azure DevOps organization access
- Personal Access Token (PAT) or OAuth configuration

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-azuredevops-service
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

#### Option A: Personal Access Token (Recommended for Development)

```bash
# Azure DevOps Configuration
AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-organization
AZURE_DEVOPS_PAT=your-personal-access-token

# Server Configuration
HOST=0.0.0.0
PORT=8004
LOG_LEVEL=DEBUG
```

#### Option B: OAuth Configuration

```bash
# Azure DevOps Configuration
AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-organization

# OAuth Configuration
OAUTH_GATEWAY_URL=http://localhost:8000
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Server Configuration
HOST=0.0.0.0
PORT=8004
LOG_LEVEL=DEBUG
```

### 5. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
python -m app.main --transport stdio
```

#### HTTP Mode (for production)

```bash
python -m app.main --transport http --port 8004
```

### 6. Verify Installation

```bash
# HTTP mode only
curl http://localhost:8004/health
```

## Creating a Personal Access Token

### 1. Navigate to Azure DevOps

1. Go to `https://dev.azure.com/your-organization`
2. Click on User Settings (gear icon) → Personal access tokens

### 2. Create New Token

1. Click "New Token"
2. Name your token (e.g., "MCP Azure DevOps Service")
3. Set expiration (recommend: 90 days)
4. Select scopes:

| Scope | Access | Purpose |
|-------|--------|---------|
| Code | Read | Repository access |
| Build | Read | Pipeline builds |
| Release | Read | Release pipelines |
| Project and Team | Read | Project listing |
| Pull Request Threads | Read | PR access |

5. Click "Create" and copy the token immediately

### 3. Store Token Securely

- Never commit PATs to source control
- Use environment variables or secrets management
- Rotate tokens regularly

## Claude Desktop Integration

### 1. Locate Config File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add MCP Server Configuration

```json
{
  "mcpServers": {
    "azuredevops": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-azuredevops-service",
      "env": {
        "AZURE_DEVOPS_ORGANIZATION_URL": "https://dev.azure.com/your-org",
        "AZURE_DEVOPS_PAT": "your-pat-token"
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
docker build -t mcp-azuredevops-service:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-azuredevops-service \
  -p 8004:8004 \
  -e AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org \
  -e AZURE_DEVOPS_PAT=your-pat-token \
  mcp-azuredevops-service:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  azuredevops-service:
    build: ./mcp-azuredevops-service
    ports:
      - "8004:8004"
    environment:
      - AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-org
      - AZURE_DEVOPS_PAT=${AZURE_DEVOPS_PAT}
```

## AWS ECS Deployment

### Task Definition

See `environments/prod/ecs-task-definition.json` for the complete ECS task definition.

### Required AWS Resources

1. **Secrets Manager**:
   - `/mcp/prod/azuredevops/pat`
   - `/mcp/prod/azuredevops/token_encryption_key` (if using OAuth)

2. **SSM Parameters**:
   - `/mcp/prod/azuredevops/organization_url`

### Deploy Command

```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-azuredevops-service \
  --force-new-deployment
```

## Troubleshooting

### Authentication Errors

```bash
# Test PAT authentication
curl -u :your-pat-token \
  "https://dev.azure.com/your-org/_apis/projects?api-version=7.0"
```

### Organization URL Issues

Ensure the URL format is correct:
- Correct: `https://dev.azure.com/your-organization`
- Incorrect: `https://your-organization.visualstudio.com` (legacy)

### Permission Errors

If you see `Access Denied`:
1. Verify PAT has required scopes
2. Check organization membership
3. Verify project permissions

### Connection Issues

```bash
# Test connectivity
curl -I https://dev.azure.com/your-org

# Check DNS resolution
nslookup dev.azure.com
```

## Health Check

```bash
# HTTP mode
curl http://localhost:8004/health

# Expected response
{"status": "healthy", "service": "mcp-azuredevops-service"}
```
