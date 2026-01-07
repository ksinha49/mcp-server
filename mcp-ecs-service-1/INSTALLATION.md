# Installation Guide - MCP ECS Service 1 (Sample)

## Prerequisites

- Python 3.11 or higher
- Docker (for containerization)
- AWS CLI (for ECS deployment)

## Local Development Setup

### 1. Clone and Navigate

```bash
cd mcp-ecs-service-1
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
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload --port 80
```

### 5. Verify Installation

```bash
curl http://localhost:80/
curl http://localhost:80/health
```

## Docker Deployment

### Build Image

```bash
docker build -t mcp-ecs-service-1:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-ecs-service-1 \
  -p 80:80 \
  mcp-ecs-service-1:latest
```

### Test Container

```bash
curl http://localhost:80/
curl http://localhost:80/health
```

## AWS ECS Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. ECR repository created
3. ECS cluster available
4. VPC and subnets configured

### Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-2.amazonaws.com

# Tag image
docker tag mcp-ecs-service-1:latest \
  <account-id>.dkr.ecr.us-east-2.amazonaws.com/mcp-ecs-service-1:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-2.amazonaws.com/mcp-ecs-service-1:latest
```

### Register Task Definition

```bash
aws ecs register-task-definition \
  --cli-input-json file://environments/prod/ecs-task-definition.json
```

### Create or Update Service

```bash
# Create new service
aws ecs create-service \
  --cluster mcp-cluster \
  --service-name mcp-ecs-service-1 \
  --task-definition mcp-ecs-service-1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

# Or update existing service
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-ecs-service-1 \
  --force-new-deployment
```

## Task Definition

The ECS task definition is located at `environments/prod/ecs-task-definition.json`.

Key configuration:
- **CPU**: 256 units
- **Memory**: 512 MB
- **Network Mode**: awsvpc
- **Launch Type**: FARGATE

## Using as Template

To use this service as a template for a new ECS service:

1. Copy the directory structure
2. Update `app/main.py` with your application logic
3. Update `requirements.txt` with your dependencies
4. Modify `Dockerfile` if needed
5. Update `ecs-task-definition.json` with:
   - Service name
   - Container name
   - Resource requirements
   - Environment variables
   - Secrets references

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs mcp-ecs-service-1

# Run interactively
docker run -it --rm mcp-ecs-service-1:latest /bin/sh
```

### ECS Task Fails

```bash
# Check task status
aws ecs describe-tasks \
  --cluster mcp-cluster \
  --tasks <task-id>

# Check CloudWatch logs
aws logs get-log-events \
  --log-group-name /ecs/mcp-ecs-service-1 \
  --log-stream-name <stream-name>
```

### Port Already in Use

```bash
# Find process using port 80
lsof -i :80

# Use alternative port
uvicorn app.main:app --reload --port 8080
```
