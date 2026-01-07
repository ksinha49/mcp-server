# Security Guide - MCP Azure DevOps Service

## Overview

This MCP server provides access to Azure DevOps projects, repositories, pipelines, and pull requests. This document covers security considerations, best practices, and compliance requirements for handling source code and CI/CD data.

## Security Architecture

### Authentication Methods

#### Personal Access Token (PAT)

```
MCP Client → Service → Azure DevOps REST API
                ↓
           PAT Authentication
```

#### OAuth 2.1

```
MCP Client → Service → OAuth Gateway → Azure AD
                           ↓
                    Token Validation
                           ↓
                    Azure DevOps REST API
```

### Recommended Authentication

| Environment | Method | Reason |
|-------------|--------|--------|
| Development | PAT | Simple setup, easy rotation |
| Production | OAuth | Better audit trail, user delegation |

## Personal Access Token Security

### PAT Scopes (Principle of Least Privilege)

| Scope | Access Level | Purpose |
|-------|--------------|---------|
| Code | Read | Repository access |
| Build | Read | Pipeline information |
| Release | Read | Release pipelines |
| Project and Team | Read | Project listing |
| Pull Request Threads | Read | PR access |

### PAT Best Practices

1. **Minimum scopes**: Only grant necessary permissions
2. **Short expiration**: 90 days maximum
3. **Regular rotation**: Rotate before expiration
4. **Secure storage**: Use secrets manager, never commit to code
5. **One per service**: Don't share PATs between applications

### PAT Storage

**Secure options**:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Environment variables (runtime injection only)

**Insecure practices** (avoid):
- Committing to source control
- Hardcoding in application
- Storing in plain text files
- Sharing via email/chat

## Data Security

### Data Handled

| Data Type | Sensitivity | Retention |
|-----------|-------------|-----------|
| Source code | High | Not stored |
| Pipeline definitions | Medium | Not stored |
| Pull request content | Medium | Not stored |
| Project metadata | Low | Not stored |
| Build logs | Medium | Not stored |
| PAT tokens | Critical | Encrypted |

### Source Code Access

This service can access:
- Repository contents
- File contents
- Commit history
- Branch information

**Important**: Source code may contain sensitive information including:
- API keys (anti-pattern but common)
- Configuration secrets
- Intellectual property
- Security vulnerabilities

### Data Handling Principles

- **No storage**: Source code is never persisted
- **Pass-through**: Data flows from Azure DevOps to MCP client
- **Token encryption**: PATs and OAuth tokens encrypted at rest
- **Read-only default**: No write operations unless explicitly enabled

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → Azure DevOps Service (private subnet)
                              ↓
                       Azure DevOps (external)
```

### TLS Requirements

- **Inbound**: TLS 1.2+ required
- **Outbound to Azure DevOps**: TLS 1.2+ (Microsoft enforced)

### Firewall Rules

| Direction | Destination | Port | Purpose |
|-----------|-------------|------|---------|
| Outbound | dev.azure.com | 443 | Azure DevOps API |
| Outbound | login.microsoftonline.com | 443 | OAuth (if used) |
| Outbound | OAuth Gateway | 8000 | Token operations |
| Inbound | Load Balancer | 8004 | Service traffic |

## Input Validation

### MCP Tool Inputs

| Tool | Validation |
|------|------------|
| `list_projects` | Max results limited |
| `get_project` | Project ID/name validated |
| `list_repositories` | Project ID validated |
| `get_repository` | Repository ID validated |
| `list_pipelines` | Project ID validated |
| `get_pipeline` | Pipeline ID validated |
| `list_pull_requests` | Repository ID validated |
| `get_pull_request` | PR ID validated |

### Query Injection Prevention

- All inputs sanitized before API calls
- API parameters use SDK methods (not string interpolation)
- Special characters escaped

## Rate Limiting

### Azure DevOps Limits

Azure DevOps enforces rate limits:
- Global: 30,000 requests per hour per user
- Surge protection for high-frequency requests

### Recommended Application Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Project listings | 30 | per minute |
| Repository access | 60 | per minute |
| Pipeline queries | 30 | per minute |
| PR operations | 30 | per minute |

## Audit Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| Project access | INFO | project ID, user |
| Repository access | INFO | repo ID, operation |
| Pipeline query | INFO | pipeline ID |
| PR access | INFO | PR ID |
| Auth failure | WARN | reason, attempted org |
| Rate limit hit | WARN | operation, count |

### Sensitive Data in Logs

**Never log**:
- PAT tokens
- Source code content
- File contents
- OAuth tokens

**Safe to log**:
- Project/repo IDs
- Operation types
- Request counts
- Error codes

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Mitigation |
|------|------------|
| Injection | SDK parameterization |
| Broken Auth | PAT/OAuth validation |
| Sensitive Data | No storage, TLS |
| Security Misconfiguration | Minimum PAT scopes |
| Components with Vulnerabilities | Regular updates |

### DevOps-Specific Risks

| Risk | Mitigation |
|------|------------|
| Source code exposure | Read-only access, audit logging |
| Pipeline secrets | No secret access via API |
| Credential harvesting | PAT scope limitations |
| Insider threat | Audit logging, least privilege |

## Incident Response

### Compromised PAT

1. **Immediately revoke** the PAT in Azure DevOps
2. Create new PAT with same scopes
3. Update secrets manager
4. Deploy with new PAT
5. Review Azure DevOps audit logs for unauthorized access

### Suspected Data Exfiltration

1. Review audit logs for bulk repository access
2. Identify affected repositories
3. Check access patterns
4. Revoke PAT/tokens
5. Notify security team

### OAuth Token Compromise

1. Revoke token via OAuth Gateway
2. Force user re-authentication
3. Audit recent repository access
4. Review Azure DevOps audit logs

## Compliance

### Supported Standards

- **OAuth 2.1**: Authentication standard (optional)
- **MCP 2025-06-18**: Protocol compliance
- **Azure DevOps Security**: Organization-level policies respected

### Access Control Alignment

This service respects Azure DevOps:
- Organization permissions
- Project permissions
- Repository permissions
- Branch policies

### Audit Trail

Azure DevOps maintains comprehensive audit logs:
- Access events
- Permission changes
- Repository operations

## Security Checklist

### Pre-Production

- [ ] PAT with minimum required scopes
- [ ] PAT stored in secrets manager
- [ ] TLS enabled for all endpoints
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured

### PAT Management

- [ ] PAT expiration set (≤90 days)
- [ ] Rotation procedure documented
- [ ] Rotation alerts configured
- [ ] Emergency revocation process defined

### Ongoing

- [ ] Rotate PAT before expiration
- [ ] Review access patterns (weekly)
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
