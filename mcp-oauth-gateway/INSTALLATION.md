# Installation Guide - MCP OAuth Gateway

## Prerequisites

- Python 3.11 or higher
- Redis server
- PostgreSQL database
- Microsoft Azure AD app registration (for Microsoft provider)

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-oauth-gateway
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

### 4. Set Up Redis

```bash
# Docker (recommended for development)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# or install locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt-get install redis-server
```

### 5. Set Up PostgreSQL

```bash
# Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=mcp \
  -e POSTGRES_PASSWORD=mcp_password \
  -e POSTGRES_DB=mcp_oauth \
  --name postgres \
  postgres:15-alpine

# Create database
psql -h localhost -U mcp -d postgres -c "CREATE DATABASE mcp_oauth;"
```

### 6. Configure Environment Variables

Create `.env` file:

```bash
# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG
GATEWAY_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Database
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://mcp:mcp_password@localhost:5432/mcp_oauth

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id

# Snowflake OAuth (optional)
SNOWFLAKE_OAUTH_CLIENT_ID=your-snowflake-client-id
SNOWFLAKE_OAUTH_CLIENT_SECRET=your-snowflake-client-secret

# Security
TOKEN_ENCRYPTION_KEY=your-base64-encoded-32-byte-key
```

Generate encryption key:

```bash
python -c "import secrets; import base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

### 7. Run Database Migrations

```bash
alembic upgrade head
```

### 8. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 9. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Protected Resource Metadata
curl http://localhost:8000/.well-known/oauth-protected-resource.json
```

## Docker Deployment

### Build Image

```bash
docker build -t mcp-oauth-gateway:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-oauth-gateway \
  -p 8000:8000 \
  -e MICROSOFT_CLIENT_ID=your-client-id \
  -e MICROSOFT_CLIENT_SECRET=your-client-secret \
  -e MICROSOFT_TENANT_ID=your-tenant-id \
  -e REDIS_URL=redis://redis:6379 \
  -e DATABASE_URL=postgresql://user:pass@postgres:5432/mcp_oauth \
  -e TOKEN_ENCRYPTION_KEY=your-key \
  mcp-oauth-gateway:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  oauth-gateway:
    build: ./mcp-oauth-gateway
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://mcp:password@postgres:5432/mcp_oauth
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: mcp
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mcp_oauth
    ports:
      - "5432:5432"
```

## AWS ECS Deployment

See the ECS task definition at:
`environments/prod/ecs-task-definition.json`

### Required AWS Resources

1. **Secrets Manager** secrets:
   - `/mcp/prod/oauth-gateway/microsoft_client_secret`
   - `/mcp/prod/oauth-gateway/token_encryption_key`
   - `/mcp/prod/oauth-gateway/database_url`

2. **SSM Parameters**:
   - `/mcp/prod/oauth-gateway/microsoft_client_id`
   - `/mcp/prod/oauth-gateway/microsoft_tenant_id`

3. **Infrastructure**:
   - ECS Cluster
   - Application Load Balancer
   - VPC with private subnets
   - ElastiCache Redis
   - RDS PostgreSQL

## Microsoft Azure AD Setup

### 1. Create App Registration

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Click "New registration"
3. Configure:
   - Name: `MCP OAuth Gateway`
   - Supported account types: Choose based on your needs
   - Redirect URI: `https://your-domain.com/oauth/callback/microsoft`

### 2. Configure API Permissions

Add required permissions:
- `User.Read` - Sign in and read user profile
- `Mail.Read` - Read user mail (for Outlook)
- `Calendars.Read` - Read user calendars
- `Sites.Read.All` - Read SharePoint sites (if using SharePoint)

### 3. Create Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Set expiration and create
4. Copy the secret value immediately

### 4. Note Configuration Values

- **Client ID**: Found on Overview page
- **Tenant ID**: Found on Overview page
- **Client Secret**: Created in step 3

## Troubleshooting

### Connection Refused (Redis)

```bash
# Check Redis is running
docker ps | grep redis
# or
redis-cli ping
```

### Database Connection Error

```bash
# Test PostgreSQL connection
psql -h localhost -U mcp -d mcp_oauth -c "SELECT 1"
```

### Token Encryption Errors

Ensure `TOKEN_ENCRYPTION_KEY` is exactly 32 bytes base64-encoded:

```bash
python -c "import base64; key='your-key'; print(len(base64.urlsafe_b64decode(key)))"
# Should print: 32
```

### CORS Issues

Set `FRONTEND_URL` to match your frontend's origin exactly.
