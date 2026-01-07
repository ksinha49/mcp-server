# Installation Guide - MCP Snowflake Service

## Prerequisites

- Python 3.11 or higher
- Snowflake account with appropriate permissions
- Network access to Snowflake (direct or via proxy)

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-snowflake-service
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

#### Option A: Password Authentication

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account.region.cloud
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=your-role

# Server Configuration
HOST=0.0.0.0
PORT=8005
LOG_LEVEL=DEBUG
```

#### Option B: Key-Pair Authentication (Recommended)

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account.region.cloud
SNOWFLAKE_USER=your-username
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/rsa_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=optional-passphrase
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your-database

# Server Configuration
HOST=0.0.0.0
PORT=8005
LOG_LEVEL=DEBUG
```

### 5. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
python -m app.main --transport stdio
```

#### HTTP Mode (for production)

```bash
python -m app.main --transport http --port 8005
```

### 6. Verify Installation

```bash
# HTTP mode only
curl http://localhost:8005/health
```

## Snowflake Account Setup

### Finding Your Account Identifier

Your account identifier format depends on your Snowflake deployment:

| Type | Format | Example |
|------|--------|---------|
| Standard | `account.region` | `xy12345.us-east-1` |
| AWS PrivateLink | `account.region.privatelink` | `xy12345.us-east-1.privatelink` |
| Azure | `account.region.azure` | `xy12345.east-us-2.azure` |
| GCP | `account.region.gcp` | `xy12345.us-central1.gcp` |

### Creating a Service User

```sql
-- Create role for MCP service
CREATE ROLE mcp_service_role;

-- Grant necessary privileges
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE mcp_service_role;
GRANT USAGE ON DATABASE your_database TO ROLE mcp_service_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE your_database TO ROLE mcp_service_role;
GRANT SELECT ON ALL TABLES IN DATABASE your_database TO ROLE mcp_service_role;

-- Create service user
CREATE USER mcp_service_user
  PASSWORD = 'strong-password-here'
  DEFAULT_ROLE = mcp_service_role
  DEFAULT_WAREHOUSE = COMPUTE_WH;

-- Grant role to user
GRANT ROLE mcp_service_role TO USER mcp_service_user;
```

### Setting Up Key-Pair Authentication

#### 1. Generate Key Pair

```bash
# Generate private key (with passphrase)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

#### 2. Assign Public Key to User

```sql
ALTER USER mcp_service_user SET RSA_PUBLIC_KEY='MIIBIjANBgkqh...';
```

Note: Copy the public key content without the header/footer lines.

## Claude Desktop Integration

### 1. Locate Config File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add MCP Server Configuration

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "python",
      "args": ["-m", "app.main", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-snowflake-service",
      "env": {
        "SNOWFLAKE_ACCOUNT": "xy12345.us-east-1",
        "SNOWFLAKE_USER": "mcp_service_user",
        "SNOWFLAKE_PASSWORD": "your-password",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_DATABASE": "ANALYTICS"
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
docker build -t mcp-snowflake-service:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-snowflake-service \
  -p 8005:8005 \
  -e SNOWFLAKE_ACCOUNT=xy12345.us-east-1 \
  -e SNOWFLAKE_USER=mcp_service_user \
  -e SNOWFLAKE_PASSWORD=your-password \
  -e SNOWFLAKE_WAREHOUSE=COMPUTE_WH \
  mcp-snowflake-service:latest
```

### With Key-Pair Authentication

```bash
docker run -d \
  --name mcp-snowflake-service \
  -p 8005:8005 \
  -v /path/to/keys:/keys:ro \
  -e SNOWFLAKE_ACCOUNT=xy12345.us-east-1 \
  -e SNOWFLAKE_USER=mcp_service_user \
  -e SNOWFLAKE_PRIVATE_KEY_PATH=/keys/rsa_key.p8 \
  mcp-snowflake-service:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  snowflake-service:
    build: ./mcp-snowflake-service
    ports:
      - "8005:8005"
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}
      - SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}
```

## AWS ECS Deployment

### Task Definition

See `environments/prod/ecs-task-definition.json` for the complete ECS task definition.

### Required AWS Resources

1. **Secrets Manager**:
   - `/mcp/prod/snowflake/password` (or private key)
   - `/mcp/prod/snowflake/private_key_passphrase`

2. **SSM Parameters**:
   - `/mcp/prod/snowflake/account`
   - `/mcp/prod/snowflake/user`
   - `/mcp/prod/snowflake/warehouse`
   - `/mcp/prod/snowflake/database`

### Deploy Command

```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-snowflake-service \
  --force-new-deployment
```

## Troubleshooting

### Connection Errors

```bash
# Test basic connectivity
python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    account='your-account.region',
    user='your-user',
    password='your-password'
)
print('Connected!')
conn.close()
"
```

### Authentication Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Incorrect username or password` | Wrong credentials | Verify username/password |
| `User temporarily locked` | Too many failed attempts | Wait or contact admin |
| `JWT token is invalid` | Key-pair issue | Regenerate and reassign public key |

### Network Issues

If behind a corporate firewall:

```bash
# Set proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### Permission Errors

If you see `Insufficient privileges`:

```sql
-- Check grants
SHOW GRANTS TO USER mcp_service_user;

-- Verify role grants
SHOW GRANTS TO ROLE mcp_service_role;
```

## Health Check

```bash
# HTTP mode
curl http://localhost:8005/health

# Expected response
{"status": "healthy", "service": "mcp-snowflake-service"}
```
