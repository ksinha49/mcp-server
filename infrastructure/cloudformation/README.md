# MCP Infrastructure - CloudFormation

This directory contains CloudFormation templates for deploying the MCP (Model Context Protocol) infrastructure on AWS ECS/Fargate following **Ameritas naming standards**.

## Naming Convention

All resources follow the Ameritas CloudFormation Resource Naming Standards:

| Component | Pattern | Example |
|-----------|---------|---------|
| Company | `alic` | - |
| App Name | `mcp` | - |
| Environment | `d`, `t`, `m`, `p` | d=dev, t=test, m=model/staging, p=production |
| Resource Name | `{app}-{env}-{purpose}-{type}` | `mcp-p-ecs-task-execution-iamrole` |

### Environment Codes

| Code | Environment |
|------|-------------|
| `d` | Development |
| `t` | Test |
| `m` | Model (UAT/Staging) |
| `p` | Production |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AWS Account (MCP Provider)                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    VPC Endpoint Service (PrivateLink)           │ │
│  └─────────────────────────────┬──────────────────────────────────┘ │
│                                │                                     │
│  ┌─────────────────────────────┴──────────────────────────────────┐ │
│  │              Network Load Balancer (Internal)                   │ │
│  │  :8000 → OAuth/Combined  :8001-8006 → Individual Services      │ │
│  └─────────────────────────────┬──────────────────────────────────┘ │
│                                │                                     │
│  ┌─────────────────────────────┴──────────────────────────────────┐ │
│  │                     ECS Cluster (Fargate)                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │
│  │  │OAuth GW  │ │Combined  │ │Outlook   │ │SharePoint│ ...       │ │
│  │  │:8000     │ │:8000     │ │:8001     │ │:8002     │          │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              AWS Cloud Map (Service Discovery)                  │ │
│  │              mcp.{env}.internal                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
infrastructure/cloudformation/
├── templates/
│   ├── parent-stack.yaml           # Master nested stack (deploy all at once)
│   ├── iam-stack.yaml              # IAM roles and policies
│   ├── security-groups-stack.yaml  # Security groups
│   ├── cloud-map-stack.yaml        # Service discovery namespace
│   ├── ecs-cluster-stack.yaml      # ECS cluster and log groups
│   ├── nlb-stack.yaml              # NLB + PrivateLink endpoint service
│   ├── mcp-services-stack.yaml     # All MCP ECS services
│   ├── autoscaling-stack.yaml      # Auto-scaling policies
│   └── monitoring-stack.yaml       # CloudWatch Alarms, SNS, Dashboard
├── parameters/
│   ├── prod.json                   # Production (p) parameters
│   └── staging.json                # Staging/Model (m) parameters
├── scripts/
│   ├── deploy.sh                   # Main deployment script
│   └── validate.sh                 # Template validation script
└── README.md                       # This file
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **VPC** with private subnets (preferably in multiple AZs)
3. **ECR Repositories** created for each service
4. **Secrets Manager** secrets created:
   - `mcp/{env}/microsoft/client_id`
   - `mcp/{env}/microsoft/client_secret`
   - `mcp/{env}/database/url`
   - `mcp/{env}/redis/url`
   - `mcp/{env}/encryption/token_key`
   - `mcp/{env}/snowflake/password`
   - `mcp/{env}/azuredevops/pat`
5. **SSM Parameters** created:
   - `/mcp/{env}/microsoft/tenant_id`
   - `/mcp/{env}/snowflake/account`
   - `/mcp/{env}/snowflake/user`
   - `/mcp/{env}/snowflake/warehouse`
   - `/mcp/{env}/snowflake/database`
   - `/mcp/{env}/azuredevops/org`

## Quick Start

### 1. Validate Templates

```bash
./scripts/validate.sh
```

### 2. Deploy All Stacks (in order)

```bash
# Set environment variables
export ENVIRONMENT=p              # d=dev, t=test, m=model, p=prod
export AWS_REGION=us-east-2
export VPC_ID=vpc-xxxxxxxxx
export PRIVATE_SUBNET_IDS="subnet-xxx,subnet-yyy,subnet-zzz"
export ECR_REPOSITORY_URI=123456789012.dkr.ecr.us-east-2.amazonaws.com

# Deploy all stacks to production
./scripts/deploy.sh -e p
```

### 3. Deploy Individual Stacks

```bash
# Deploy specific stack to production (p)
./scripts/deploy.sh -e p -s iam
./scripts/deploy.sh -e p -s security-groups
./scripts/deploy.sh -e p -s cloud-map
./scripts/deploy.sh -e p -s ecs-cluster
./scripts/deploy.sh -e p -s nlb
./scripts/deploy.sh -e p -s mcp-services
./scripts/deploy.sh -e p -s autoscaling

# Deploy to model/staging environment (m)
./scripts/deploy.sh -e m -s iam
```

## Stack Deployment Order

### Option A: Deploy Using Parent Stack (Recommended)

Deploy all infrastructure with a single command using the nested parent stack:

```bash
# Upload templates to S3 first
aws s3 sync templates/ s3://alic-aio-mcp-cloudformation-templates/cloudformation/templates/

# Deploy parent stack
aws cloudformation create-stack \
  --stack-name mcp-infrastructure-p \
  --template-body file://templates/parent-stack.yaml \
  --parameters file://parameters/prod-cli.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### Option B: Deploy Individual Stacks

Stacks must be deployed in this order due to cross-stack dependencies:

1. **iam-stack** - IAM roles (no dependencies)
2. **security-groups-stack** - Security groups (requires VPC)
3. **cloud-map-stack** - Service discovery (requires VPC)
4. **ecs-cluster-stack** - ECS cluster (no dependencies)
5. **nlb-stack** - Network Load Balancer (requires VPC, subnets)
6. **mcp-services-stack** - ECS services (requires all above)
7. **autoscaling-stack** - Auto-scaling (requires ECS services)
8. **monitoring-stack** - CloudWatch Alarms, SNS Topics, Dashboard (requires ECS services)

## Stack Details

### iam-stack.yaml

Creates IAM roles following naming pattern `{app}-{env}-{purpose}-iamrole`:
- `mcp-{env}-ecs-task-execution-iamrole` (shared)
- Individual task roles for each service
- `mcp-{env}-autoscaling-iamrole`

### security-groups-stack.yaml

Creates security groups with naming pattern `{app}-{env}-{purpose}-sg`:
- `mcp-{env}-alb-sg` (public-facing, ports 80/443)
- `mcp-{env}-nlb-sg` (internal, ports 8000-8006)
- `mcp-{env}-ecs-services-sg` (allows ALB/NLB traffic)
- `mcp-{env}-vpce-sg` (VPC endpoints)
- `mcp-{env}-database-sg` (PostgreSQL)
- `mcp-{env}-redis-sg` (Redis)

### cloud-map-stack.yaml

Creates AWS Cloud Map namespace:
- Namespace: `mcp.{env}.internal` (e.g., `mcp.p.internal`)
- Services: oauth-gateway, combined, outlook, sharepoint, teams, azuredevops, snowflake, context7

### ecs-cluster-stack.yaml

Creates:
- ECS Cluster: `mcp-{env}-cluster`
- CloudWatch Log Groups: `/ecs/mcp-{env}-{service}`

### nlb-stack.yaml

Creates:
- Internal NLB: `mcp-{env}-nlb`
- Target groups: `mcp-{env}-{service}-tg`
- Listeners for each port
- VPC Endpoint Service for PrivateLink

### mcp-services-stack.yaml

Creates ECS services and task definitions:
- Service name pattern: `mcp-{env}-{service}-ecsservice`
- Task definition pattern: `mcp-{env}-{service}-taskdef`

| Service | Port | Service Name | Task Definition |
|---------|------|--------------|-----------------|
| OAuth Gateway | 8000 | mcp-{env}-oauthgateway-ecsservice | mcp-{env}-oauthgateway-taskdef |
| Combined | 8000 | mcp-{env}-combined-ecsservice | mcp-{env}-combined-taskdef |
| Outlook | 8001 | mcp-{env}-outlook-ecsservice | mcp-{env}-outlook-taskdef |
| SharePoint | 8002 | mcp-{env}-sharepoint-ecsservice | mcp-{env}-sharepoint-taskdef |
| Teams | 8003 | mcp-{env}-teams-ecsservice | mcp-{env}-teams-taskdef |
| Azure DevOps | 8004 | mcp-{env}-azuredevops-ecsservice | mcp-{env}-azuredevops-taskdef |
| Snowflake | 8005 | mcp-{env}-snowflake-ecsservice | mcp-{env}-snowflake-taskdef |
| Context7 | 8006 | mcp-{env}-context7-ecsservice | mcp-{env}-context7-taskdef |

### autoscaling-stack.yaml

Creates auto-scaling policies:
- Target tracking on CPU utilization (default: 70%)
- Target tracking on Memory utilization (default: 80%)
- Scale-in cooldown: 300 seconds
- Scale-out cooldown: 60 seconds

### monitoring-stack.yaml

Creates comprehensive monitoring infrastructure:

**SNS Topics:**
- `{AWSAccountName}-monitoring-critical-alerts-topic` - Critical alerts (task count drops)
- `{AWSAccountName}-monitoring-warning-alerts-topic` - Warning alerts (CPU/Memory thresholds)

**CloudWatch Alarms (per service):**
- `mcp-{env}-{service}-cpu-alarm` - CPU utilization exceeds threshold (default: 85%)
- `mcp-{env}-{service}-memory-alarm` - Memory utilization exceeds threshold (default: 85%)
- `mcp-{env}-{service}-taskcount-alarm` - Running task count below minimum

**Composite Alarms:**
- `mcp-{env}-critical-services-composite-alarm` - Aggregated alarm for OAuth Gateway and Combined Service

**CloudWatch Dashboard:**
- `mcp-{env}-services-dashboard` - Real-time metrics visualization for all services

### parent-stack.yaml

Master nested stack that orchestrates all infrastructure:
- Deploys all nested stacks in correct dependency order
- Passes cross-stack references automatically
- Single deployment for entire infrastructure
- Supports rollback of all stacks together

**Deployment Layers:**
1. IAM Stack (Layer 1)
2. Security Groups Stack (Layer 2)
3. ECS Cluster Stack (Layer 3)
4. Cloud Map Stack (Layer 4)
5. NLB Stack (Layer 5)
6. MCP Services Stack (Layer 6)
7. Auto-Scaling Stack (Layer 7)
8. Monitoring Stack (Layer 8)

## Mandatory Tags

All resources include these mandatory tags per Ameritas standards:

| Tag Key | Description | Example Value |
|---------|-------------|---------------|
| Name | Resource name | mcp-p-ecs-services-sg |
| Environment | Environment code | p |
| Application | Application name | mcp |
| Owner | Owner email | aio-support@ameritas.com |
| CostCenter | Cost center | aio |
| DataClassification | Data classification | confidential |
| CreatedBy | Creation method | CloudFormation |

## Cross-Account Integration (PrivateLink)

To enable LiteLLM integration from another AWS account:

1. Get the consumer account ID
2. Set `LiteLLMAccountId` parameter when deploying nlb-stack
3. After deployment, get the Endpoint Service Name from stack outputs
4. In the consumer account, create a VPC Endpoint using the service name
5. Accept the endpoint connection in the provider account

```bash
# Get endpoint service name
aws cloudformation describe-stacks \
  --stack-name mcp-nlb-p \
  --query 'Stacks[0].Outputs[?OutputKey==`EndpointServiceName`].OutputValue' \
  --output text
```

## Cleanup

To delete all stacks:

```bash
./scripts/deploy.sh -e p -d
```

Or manually delete in reverse order:

```bash
aws cloudformation delete-stack --stack-name mcp-autoscaling-p
aws cloudformation delete-stack --stack-name mcp-mcp-services-p
aws cloudformation delete-stack --stack-name mcp-nlb-p
aws cloudformation delete-stack --stack-name mcp-ecs-cluster-p
aws cloudformation delete-stack --stack-name mcp-cloud-map-p
aws cloudformation delete-stack --stack-name mcp-security-groups-p
aws cloudformation delete-stack --stack-name mcp-iam-p
```

## Troubleshooting

### Stack Creation Failed

1. Check CloudFormation events for error details:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name <stack-name> \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
   ```

2. Common issues:
   - IAM permissions missing
   - VPC/subnet not found
   - Secrets/parameters not created
   - Resource name conflicts

### Services Not Starting

1. Check ECS service events:
   ```bash
   aws ecs describe-services \
     --cluster mcp-p-cluster \
     --services mcp-p-combined-ecsservice
   ```

2. Check CloudWatch logs:
   ```bash
   aws logs tail /ecs/mcp-p-combined --follow
   ```

### PrivateLink Connection Issues

1. Verify endpoint service permissions
2. Check security group rules
3. Verify NLB target health
4. Confirm endpoint connection is accepted

## Service Ports Reference

| Service | Port | Target Group |
|---------|------|--------------|
| OAuth Gateway | 8000 | mcp-{env}-oauth-tg |
| Combined | 8000 | mcp-{env}-combined-tg |
| Outlook | 8001 | mcp-{env}-outlook-tg |
| SharePoint | 8002 | mcp-{env}-sharepoint-tg |
| Teams | 8003 | mcp-{env}-teams-tg |
| Azure DevOps | 8004 | mcp-{env}-azuredevops-tg |
| Snowflake | 8005 | mcp-{env}-snowflake-tg |
| Context7 | 8006 | mcp-{env}-context7-tg |

## Resource Naming Examples (Production)

| Resource Type | Name |
|---------------|------|
| IAM Role | mcp-p-ecs-task-execution-iamrole |
| IAM Policy | mcp-p-secretsmanager-readonly-iampolicy |
| Security Group | mcp-p-ecs-services-sg |
| ECS Cluster | mcp-p-cluster |
| ECS Service | mcp-p-oauthgateway-ecsservice |
| Task Definition | mcp-p-oauthgateway-taskdef |
| NLB | mcp-p-nlb |
| Target Group | mcp-p-outlook-tg |
| Log Group | /ecs/mcp-p-oauthgateway |
| Cloud Map Namespace | mcp.p.internal |
| SNS Topic | alic-aio-mcp-monitoring-critical-alerts-topic |
| CloudWatch Alarm | mcp-p-oauthgateway-cpu-alarm |
| CloudWatch Dashboard | mcp-p-services-dashboard |
| Composite Alarm | mcp-p-critical-services-composite-alarm |
