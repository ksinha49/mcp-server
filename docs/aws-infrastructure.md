# AWS Infrastructure Setup for MCP Servers

This document describes the AWS infrastructure requirements for deploying MCP servers to ECS Fargate.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ECS Fargate Cluster                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ OAuth GW    │  │ Outlook MCP │  │ Teams MCP   │         │   │
│  │  │ Port: 8000  │  │ Port: 8001  │  │ Port: 8003  │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │SharePoint   │  │ Azure DevOps│  │ Snowflake   │         │   │
│  │  │ Port: 8002  │  │ Port: 8004  │  │ Port: 8005  │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  │  ┌─────────────┐                                            │   │
│  │  │ Context7    │                                            │   │
│  │  │ Port: 8006  │                                            │   │
│  │  └─────────────┘                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌───────────────────────────┼──────────────────────────────────┐  │
│  │            Configuration Sources                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                    │  │
│  │  │ SSM Parameter   │  │ Secrets Manager │                    │  │
│  │  │ Store           │  │                 │                    │  │
│  │  │ (Non-sensitive) │  │ (Sensitive)     │                    │  │
│  │  └─────────────────┘  └─────────────────┘                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Port Allocation

| Service | Port | Description |
|---------|------|-------------|
| mcp-oauth-gateway | 8000 | Centralized OAuth service |
| mcp-outlook-service | 8001 | Microsoft Outlook MCP |
| mcp-sharepoint-service | 8002 | Microsoft SharePoint MCP |
| mcp-teams-service | 8003 | Microsoft Teams MCP |
| mcp-azuredevops-service | 8004 | Azure DevOps MCP |
| mcp-snowflake-service | 8005 | Snowflake MCP |
| mcp-context-7-service | 8006 | Context7 Documentation MCP |

## IAM Roles

### Task Execution Role

This role is used by ECS to pull container images and retrieve secrets.

**Role Name:** `mcp-ecs-task-execution-role`

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Required Policies:**

1. **AmazonECSTaskExecutionRolePolicy** (AWS Managed)

2. **MCP SSM Parameter Store Access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SSMParameterAccess",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters",
        "ssm:GetParameter"
      ],
      "Resource": [
        "arn:aws:ssm:us-east-2:ACCOUNT_ID:parameter/mcp/prod/*"
      ]
    }
  ]
}
```

3. **MCP Secrets Manager Access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-2:ACCOUNT_ID:secret:mcp/prod/*"
      ]
    }
  ]
}
```

4. **KMS Decrypt (if using customer-managed KMS keys):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KMSDecrypt",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": [
        "arn:aws:kms:us-east-2:ACCOUNT_ID:key/KEY_ID"
      ]
    }
  ]
}
```

### Task Roles (per service)

Each service has its own task role for runtime permissions (if needed).

| Service | Role Name |
|---------|-----------|
| OAuth Gateway | `mcp-oauth-gateway-task-role` |
| Outlook | `mcp-outlook-task-role` |
| SharePoint | `mcp-sharepoint-task-role` |
| Teams | `mcp-teams-task-role` |
| Azure DevOps | `mcp-azuredevops-task-role` |
| Snowflake | `mcp-snowflake-task-role` |
| Combined | `mcp-combined-task-role` |
| Context7 | `mcp-context7-task-role` |

## SSM Parameter Store Parameters

Create these parameters in SSM Parameter Store (Standard tier, String type):

### Microsoft Common Parameters
```bash
# Create Microsoft Tenant ID
aws ssm put-parameter \
  --name "/mcp/prod/microsoft/tenant_id" \
  --value "YOUR_TENANT_ID" \
  --type "String" \
  --region us-east-2

# Or use SecureString for additional protection
aws ssm put-parameter \
  --name "/mcp/prod/microsoft/tenant_id" \
  --value "YOUR_TENANT_ID" \
  --type "SecureString" \
  --region us-east-2
```

### Azure DevOps Parameters
```bash
aws ssm put-parameter \
  --name "/mcp/prod/azuredevops/organization_url" \
  --value "https://dev.azure.com/YOUR_ORG" \
  --type "String" \
  --region us-east-2
```

### Snowflake Parameters
```bash
aws ssm put-parameter \
  --name "/mcp/prod/snowflake/account" \
  --value "YOUR_ACCOUNT.region" \
  --type "String" \
  --region us-east-2

aws ssm put-parameter \
  --name "/mcp/prod/snowflake/warehouse" \
  --value "COMPUTE_WH" \
  --type "String" \
  --region us-east-2

aws ssm put-parameter \
  --name "/mcp/prod/snowflake/database" \
  --value "YOUR_DATABASE" \
  --type "String" \
  --region us-east-2

aws ssm put-parameter \
  --name "/mcp/prod/snowflake/schema" \
  --value "PUBLIC" \
  --type "String" \
  --region us-east-2
```

### OAuth Gateway Parameters
```bash
aws ssm put-parameter \
  --name "/mcp/prod/oauth-gateway/microsoft_tenant_id" \
  --value "YOUR_TENANT_ID" \
  --type "String" \
  --region us-east-2
```

### Complete Parameter List

| Parameter Path | Description | Type |
|---------------|-------------|------|
| `/mcp/prod/microsoft/tenant_id` | Microsoft Entra tenant ID | String |
| `/mcp/prod/azuredevops/organization_url` | Azure DevOps org URL | String |
| `/mcp/prod/snowflake/account` | Snowflake account identifier | String |
| `/mcp/prod/snowflake/warehouse` | Default warehouse | String |
| `/mcp/prod/snowflake/database` | Default database | String |
| `/mcp/prod/snowflake/schema` | Default schema | String |
| `/mcp/prod/oauth-gateway/microsoft_tenant_id` | Tenant ID for OAuth gateway | String |

## Secrets Manager Secrets

Create these secrets in AWS Secrets Manager:

### Microsoft OAuth Secrets
```bash
# Microsoft Client ID
aws secretsmanager create-secret \
  --name "mcp/prod/microsoft/client_id" \
  --secret-string "YOUR_CLIENT_ID" \
  --region us-east-2

# Microsoft Client Secret
aws secretsmanager create-secret \
  --name "mcp/prod/microsoft/client_secret" \
  --secret-string "YOUR_CLIENT_SECRET" \
  --region us-east-2
```

### OAuth Gateway Secrets
```bash
# Redis URL
aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/redis_url" \
  --secret-string "redis://host:6379" \
  --region us-east-2

# Database URL
aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/database_url" \
  --secret-string "postgresql://user:pass@host:5432/db" \
  --region us-east-2

# OAuth Gateway Microsoft credentials
aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/microsoft_client_id" \
  --secret-string "YOUR_CLIENT_ID" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/microsoft_client_secret" \
  --secret-string "YOUR_CLIENT_SECRET" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/snowflake_oauth_client_id" \
  --secret-string "YOUR_SNOWFLAKE_OAUTH_CLIENT_ID" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/oauth-gateway/snowflake_oauth_client_secret" \
  --secret-string "YOUR_SNOWFLAKE_OAUTH_CLIENT_SECRET" \
  --region us-east-2
```

### Azure DevOps Secrets
```bash
aws secretsmanager create-secret \
  --name "mcp/prod/azuredevops/pat" \
  --secret-string "YOUR_PAT_TOKEN" \
  --region us-east-2
```

### Snowflake Secrets
```bash
aws secretsmanager create-secret \
  --name "mcp/prod/snowflake/user" \
  --secret-string "YOUR_USERNAME" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/snowflake/password" \
  --secret-string "YOUR_PASSWORD" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/snowflake/oauth_client_id" \
  --secret-string "YOUR_OAUTH_CLIENT_ID" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mcp/prod/snowflake/oauth_client_secret" \
  --secret-string "YOUR_OAUTH_CLIENT_SECRET" \
  --region us-east-2
```

### Common Secrets
```bash
# Token Encryption Key (32-byte key for AES-256)
aws secretsmanager create-secret \
  --name "mcp/prod/common/token_encryption_key" \
  --secret-string "$(openssl rand -base64 32)" \
  --region us-east-2
```

### Context7 Secrets
```bash
aws secretsmanager create-secret \
  --name "mcp/context7/api_key" \
  --secret-string "YOUR_CONTEXT7_API_KEY" \
  --region us-east-2
```

### Complete Secrets List

| Secret Path | Description |
|-------------|-------------|
| `mcp/prod/microsoft/client_id` | Microsoft OAuth client ID |
| `mcp/prod/microsoft/client_secret` | Microsoft OAuth client secret |
| `mcp/prod/oauth-gateway/redis_url` | Redis connection URL |
| `mcp/prod/oauth-gateway/database_url` | PostgreSQL connection URL |
| `mcp/prod/oauth-gateway/microsoft_client_id` | OAuth Gateway MS client ID |
| `mcp/prod/oauth-gateway/microsoft_client_secret` | OAuth Gateway MS client secret |
| `mcp/prod/oauth-gateway/snowflake_oauth_client_id` | Snowflake OAuth client ID |
| `mcp/prod/oauth-gateway/snowflake_oauth_client_secret` | Snowflake OAuth client secret |
| `mcp/prod/azuredevops/pat` | Azure DevOps Personal Access Token |
| `mcp/prod/snowflake/user` | Snowflake username |
| `mcp/prod/snowflake/password` | Snowflake password |
| `mcp/prod/snowflake/oauth_client_id` | Snowflake OAuth client ID |
| `mcp/prod/snowflake/oauth_client_secret` | Snowflake OAuth client secret |
| `mcp/prod/common/token_encryption_key` | AES-256 encryption key |
| `mcp/context7/api_key` | Context7 API key |

## CloudWatch Log Groups

Create these log groups before deployment:

```bash
aws logs create-log-group --log-group-name /ecs/mcp-oauth-gateway --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-outlook-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-sharepoint-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-teams-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-azuredevops-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-snowflake-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-combined-service --region us-east-2
aws logs create-log-group --log-group-name /ecs/mcp-context7-service --region us-east-2
```

Set retention policy (optional):
```bash
aws logs put-retention-policy \
  --log-group-name /ecs/mcp-oauth-gateway \
  --retention-in-days 30 \
  --region us-east-2
```

## VPC and Networking

### Required Security Group Rules

**Inbound:**
| Port | Source | Description |
|------|--------|-------------|
| 8000-8006 | ALB Security Group | Service traffic |

**Outbound:**
| Port | Destination | Description |
|------|-------------|-------------|
| 443 | 0.0.0.0/0 | HTTPS to Microsoft APIs, Snowflake |
| 443 | VPC Endpoints | SSM, Secrets Manager access |

### VPC Endpoints (Recommended)

For enhanced security, create interface VPC endpoints:

- `com.amazonaws.us-east-2.ssm` - SSM Parameter Store
- `com.amazonaws.us-east-2.secretsmanager` - Secrets Manager
- `com.amazonaws.us-east-2.ecr.api` - ECR API
- `com.amazonaws.us-east-2.ecr.dkr` - ECR Docker
- `com.amazonaws.us-east-2.logs` - CloudWatch Logs

## Deployment Commands

### Register Task Definition
```bash
aws ecs register-task-definition \
  --cli-input-json file://environments/prod/ecs-task-definition.json \
  --region us-east-2
```

### Create/Update Service
```bash
aws ecs create-service \
  --cluster mcp-cluster \
  --service-name mcp-oauth-gateway \
  --task-definition mcp-oauth-gateway-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region us-east-2
```

### Force New Deployment (to pick up secret changes)
```bash
aws ecs update-service \
  --cluster mcp-cluster \
  --service mcp-oauth-gateway \
  --force-new-deployment \
  --region us-east-2
```

## Important Notes

1. **Secret Rotation**: Secrets Manager secrets can be rotated. After rotation, you must force a new deployment for containers to pick up new values.

2. **Parameter Store vs Secrets Manager**:
   - Use SSM Parameter Store for non-sensitive configuration (free for standard parameters)
   - Use Secrets Manager for credentials and sensitive data (supports automatic rotation)

3. **KMS Keys**: Consider using customer-managed KMS keys for encryption if you need:
   - Cross-account access
   - Custom key policies
   - Key rotation control

4. **Naming Convention**: All parameters follow the pattern `/mcp/{environment}/{service}/{parameter}`

5. **Region**: All resources are deployed in `us-east-2`. Update ARNs if using a different region.
