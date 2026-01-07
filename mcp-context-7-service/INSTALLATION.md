# Installation Guide - MCP Context7 Service

## Prerequisites

- Node.js 18+ or Bun 1.0+
- npm, yarn, or bun package manager

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-context-7-service
```

### 2. Install Dependencies

Using Bun (recommended):
```bash
bun install
```

Using npm:
```bash
npm install
```

Using yarn:
```bash
yarn install
```

### 3. Build the Project

```bash
bun run build
# or
npm run build
```

### 4. Start the Server

#### STDIO Mode (for Claude Desktop)

```bash
node dist/index.js --transport stdio
```

#### HTTP Mode (for production)

```bash
node dist/index.js --transport http --port 8006
```

#### SSE Mode (backward compatibility)

```bash
node dist/index.js --transport sse --port 8006
```

### 5. Verify Installation

```bash
# HTTP mode only
curl http://localhost:8006/health
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
    "context7": {
      "command": "node",
      "args": ["dist/index.js", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-context-7-service"
    }
  }
}
```

### Alternative: Using npx (if published)

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@your-org/mcp-context7-service"]
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

## Docker Deployment

### Build Image

```bash
docker build -t mcp-context7-service:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-context7-service \
  -p 8006:8006 \
  mcp-context7-service:latest
```

### With Environment Variables

```bash
docker run -d \
  --name mcp-context7-service \
  -p 8006:8006 \
  -e API_KEY=your-optional-api-key \
  mcp-context7-service:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  context7-service:
    build: ./mcp-context-7-service
    ports:
      - "8006:8006"
    environment:
      - PORT=8006
      - TRANSPORT=http
```

## AWS ECS Deployment

### Task Definition

See `environments/prod/ecs-task-definition.json` for the complete ECS task definition.

### Required AWS Resources

1. **SSM Parameters** (optional):
   - `/mcp/prod/context7/api_key`

### Deploy Command

```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-context7-service \
  --force-new-deployment
```

## Development Commands

### Install Dependencies

```bash
bun install
```

### Build TypeScript

```bash
bun run build
```

### Run in Development (watch mode)

```bash
bun run dev
```

### Lint Code

```bash
bun run lint
```

### Format Code

```bash
bun run format
```

### Check Types

```bash
bun run typecheck
```

## Transport Modes

### STDIO Transport

Best for local development and Claude Desktop integration:
- Input/output via stdin/stdout
- No network configuration needed
- Process management by parent application

### HTTP Transport (Streamable HTTP)

Best for production deployments:
- Standard HTTP POST requests
- Supports streaming responses
- Load balancer compatible
- Health checks supported

### SSE Transport

For backward compatibility:
- Server-Sent Events
- Long-running connections
- Real-time updates

## Troubleshooting

### Build Errors

```bash
# Clean and rebuild
rm -rf dist node_modules
bun install
bun run build
```

### Node Version Issues

Ensure you're using Node.js 18+:
```bash
node --version
# Should be v18.0.0 or higher
```

### TypeScript Errors

```bash
# Check TypeScript configuration
bun run typecheck

# View detailed errors
npx tsc --noEmit
```

### STDIO Mode Issues

- Ensure no other output is written to stdout
- Check stderr for error messages
- Verify the process can read from stdin

### HTTP Mode Issues

```bash
# Check if port is in use
lsof -i :8006

# Test endpoint
curl -v http://localhost:8006/health
```

## Health Check

```bash
# HTTP mode
curl http://localhost:8006/health

# Expected response
{"status": "ok"}
```

## Performance Tuning

### Node.js Options

```bash
# Increase memory limit if needed
node --max-old-space-size=4096 dist/index.js --transport http --port 8006
```

### Container Resources

In ECS/Docker, allocate appropriate resources:
- CPU: 256-512 units
- Memory: 512MB-1GB
