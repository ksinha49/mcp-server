# Enterprise MCP Servers

## Overview
Enteprise MCP Servers repository implements Model Context Protocol (MCP)–compliant servers that enables AI clients to securely access Ameritas internal services, approved enterprise tools and data sources through a standardized interface. It provides session management, request routing, and pluggable resource modules to extend functionality on demand.

---

## Features
- **Secure Protocol Handling**: Adheres to the MCP specification for authentication, authorization, and request validation.
- **Extensible Tool Modules**: Add or remove resource handlers (e.g., document Q&A, database access, custom workflows) without changing core logic.
- **Scalable Deployment**: Compatible with container orchestration platforms and can be scaled horizontally behind a load balancer.
- **Observability**: Built-in metrics and structured logging for Prometheus and ELK integration.

---

## Architecture
### MCP Blueprint
![MCP Server Architecture](docs/MCP%20Blueprint.svg)

### MCP Client-Server Workflow
![MCP Client Server Workflow](docs/Server-Client%20workflow.png)

---

## AWS Deployment
This section outlines steps to deploy the MCP Server on AWS using container services and infrastructure as code.

### 1. Docker Image
1. Build and tag the image:
```bash
docker build -t alic-aio/mcp-server:latest .
```
2. Authenticate and push to ECR:
```bash
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com
docker tag alic-aio/mcp-server-<toolname>:latest <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/mcp-server-<toolname>:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/mcp-server-<toolname>:latest
```
### 2. Infrastructure
```bash
Resources:
  MCPCluster:
    Type: AWS::ECS::Cluster

  MCPTaskDef:
    Type: AWS::ECS::TaskDefinition
    Properties:
      RequiresCompatibilities: [FARGATE]
      Cpu: "512"
      Memory: "1024"
      NetworkMode: awsvpc
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      ContainerDefinitions:
          - Name: mcp-server
            Image: <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/mcp-server-<toolname>:latest
            PortMappings:
              - ContainerPort: 3000
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: /ecs/mcp-server
              awslogs-region: us-east-2
              awslogs-stream-prefix: ecs

  MCPService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref MCPCluster
      DesiredCount: 2
      LaunchType: FARGATE
      TaskDefinition: !Ref MCPTaskDef
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets: [subnet-abc123, subnet-def456]
          SecurityGroups: [sg-123abc]
      LoadBalancers:
        - ContainerName: mcp-server
          ContainerPort: 3000
          TargetGroupArn: !Ref MCPTargetGroup
```
Using AWS Fargate on Amazon ECS with an Application Load Balancer and IAM roles:

- **ECS Cluster:** Launch type FARGATE
- **Task Definition:** CPU 512, Memory 1GB
- **Service:** Desired count 2, attach to ALB
- **Load Balancer:** Route HTTP/HTTPS to container port 3000 by default. If you need the target group to use a different port (e.g., 8000), set the `PORT` environment variable in the task definition and update the target group to match.
- **IAM Roles:**
  - Task execution role (ECR pull, CloudWatch logs)
  - Task role (access to RDS, S3, Secrets Manager)

### 3. CloudFormation 

Use IaC to define resources. Example CloudFormation snippet for ECS Service:
```bash
Resources:
  MCPCluster:
    Type: AWS::ECS::Cluster

  MCPTaskDef:
    Type: AWS::ECS::TaskDefinition
    Properties:
      RequiresCompatibilities: [FARGATE]
      Cpu: "512"
      Memory: "1024"
      NetworkMode: awsvpc
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      ContainerDefinitions:
        - Name: mcp-server
          Image: <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/mcp-server-<toolname>:latest
          PortMappings:
            - ContainerPort: 8000
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: /ecs/mcp-server
              awslogs-region: us-east-1
              awslogs-stream-prefix: ecs

          # Optional: override the port the container listens on if your target group
          # uses a different port, such as 8000
          Environment:
            - Name: PORT
              Value: "8000"

  MCPService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref MCPCluster
      DesiredCount: 2
      LaunchType: FARGATE
      TaskDefinition: !Ref MCPTaskDef
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets: [subnet-abc123, subnet-def456]
          SecurityGroups: [sg-123abc]
      LoadBalancers:
        - ContainerName: mcp-server
          ContainerPort: 8000
          TargetGroupArn: !Ref MCPTargetGroup
```

### 4. CI/CD Pipeline

Automate build and deployment with AWS CodePipeline or GitHub Actions:

- Build Stage: Build Docker image, push to ECR

- Deploy Stage: Update ECS service with new image tag

## Installation

1. Clone the repository:
```bash
git clone git@github.com:ameritascorp/aio-mcp-server.git
```
2. Create a Python 3.10+ virtual environment and activate it:
```bash
python3.13 -m venv venv && source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
## Usage

- **Start the server** locally on port 8000:
```bash
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000
```
- **Configure clients** by adding the server entry in your mcp_config.json as shown in the examples/ folder.
- **Health check:** GET /health returns 200 OK if all modules are loaded.
