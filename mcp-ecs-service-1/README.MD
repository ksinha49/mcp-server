# MCP ECS Service 1 (Sample)

Sample Python service demonstrating AWS ECS Fargate deployment patterns for MCP services. This serves as a reference implementation for containerized service deployment.

## Overview

This is a minimal FastAPI service that demonstrates:

- Docker containerization patterns
- ECS Fargate task definition structure
- Health check endpoints
- AWS deployment workflow

## Purpose

This service is intended as a **reference template** for deploying Python services to AWS ECS. It is not a production MCP server but rather a starting point for understanding the deployment architecture.

## Port

**80** (default)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Simple hello world response |
| `/health` | GET | Health check |

## Directory Structure

```
mcp-ecs-service-1/
├── app/
│   └── main.py           # FastAPI application
├── environments/
│   └── prod/
│       ├── ecs-task-definition.json  # ECS task definition
│       └── github.properties         # Deployment properties
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── README.MD             # This file
├── INSTALLATION.md       # Installation guide
└── SECURITY.md           # Security considerations
```

## Quick Start

### Local Development

```bash
cd mcp-ecs-service-1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 80
```

### Docker

```bash
# Build
docker build -t mcp-ecs-service-1:latest .

# Run
docker run -p 80:80 mcp-ecs-service-1:latest
```

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Detailed installation instructions
- [SECURITY.md](./SECURITY.md) - Security considerations and best practices

## Dependencies

- fastapi
- uvicorn[standard]

## License

MIT
