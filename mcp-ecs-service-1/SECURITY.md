# Security Guide - MCP ECS Service 1 (Sample)

## Overview

This is a sample service demonstrating ECS deployment patterns. This document covers security best practices that should be applied when using this as a template for production services.

## Security Profile

This sample service has **minimal security requirements** as it:

- Exposes only a simple hello endpoint
- Stores no data
- Requires no authentication
- Has no secrets

**Note**: When building production services based on this template, apply the security practices below.

## Container Security

### Base Image

The Dockerfile uses `python:3.11-slim`:
- Minimal attack surface
- Regular security updates from Python
- No unnecessary packages

### Non-Root User

For production, add a non-root user:

```dockerfile
# Add to Dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### Read-Only Filesystem

Enable read-only filesystem where possible:

```json
// In ECS task definition
"readonlyRootFilesystem": true,
"mountPoints": [
  {
    "sourceVolume": "tmp",
    "containerPath": "/tmp",
    "readOnly": false
  }
]
```

## Network Security

### Security Group Configuration

Restrict inbound traffic:

```json
{
  "IpProtocol": "tcp",
  "FromPort": 80,
  "ToPort": 80,
  "SourceSecurityGroupId": "sg-alb-only"
}
```

### Private Subnets

Deploy in private subnets with NAT gateway for outbound traffic:

```
Internet → ALB (public) → ECS Tasks (private)
```

### TLS Termination

Terminate TLS at the load balancer:

```
Client → ALB (HTTPS/443) → ECS (HTTP/80)
```

## AWS Security

### IAM Task Role

Create minimal IAM task role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/mcp-ecs-service-1:*"
    }
  ]
}
```

### Execution Role

Separate execution role for ECS agent:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Secrets Management

For production services with secrets:

```json
// In task definition
"secrets": [
  {
    "name": "DATABASE_URL",
    "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
  }
]
```

## Logging

### CloudWatch Logs

Configure log group with retention:

```bash
aws logs create-log-group \
  --log-group-name /ecs/mcp-ecs-service-1

aws logs put-retention-policy \
  --log-group-name /ecs/mcp-ecs-service-1 \
  --retention-in-days 30
```

### Log Encryption

Enable encryption for sensitive logs:

```bash
aws logs associate-kms-key \
  --log-group-name /ecs/mcp-ecs-service-1 \
  --kms-key-id arn:aws:kms:region:account:key/id
```

## Vulnerability Scanning

### ECR Image Scanning

Enable automatic scanning:

```bash
aws ecr put-image-scanning-configuration \
  --repository-name mcp-ecs-service-1 \
  --image-scanning-configuration scanOnPush=true
```

### Dependency Scanning

Scan Python dependencies:

```bash
pip install safety
safety check -r requirements.txt
```

## Production Checklist

### Container

- [ ] Non-root user configured
- [ ] Read-only filesystem enabled
- [ ] Health check defined
- [ ] Resource limits set

### Network

- [ ] Private subnet deployment
- [ ] Security group restricts access
- [ ] TLS at load balancer
- [ ] VPC flow logs enabled

### AWS

- [ ] Minimal IAM task role
- [ ] Secrets in Secrets Manager
- [ ] CloudWatch logs configured
- [ ] ECR image scanning enabled

### Monitoring

- [ ] Health check alarms
- [ ] Error rate monitoring
- [ ] Resource utilization alerts

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
