# Security Guide - MCP Combined Service

## Overview

This MCP server combines access to multiple enterprise services including Microsoft 365 (Outlook, SharePoint, Teams), Azure DevOps, and Snowflake. This document covers security considerations when running multiple providers in a single service.

## Security Architecture

### Multi-Provider Authentication

```
MCP Client → Combined Service → Provider-specific auth
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
             Microsoft OAuth   Azure DevOps PAT   Snowflake Auth
                    ↓               ↓               ↓
              Graph API      DevOps REST API   Snowflake API
```

### Authentication per Provider

| Provider | Auth Method | Credential Storage |
|----------|-------------|-------------------|
| Outlook | OAuth via Gateway | Encrypted tokens |
| SharePoint | OAuth via Gateway | Encrypted tokens |
| Teams | OAuth via Gateway | Encrypted tokens |
| Azure DevOps | PAT or OAuth | Secrets Manager |
| Snowflake | Password/Key-pair | Secrets Manager |

## Security Considerations

### Combined Attack Surface

Running multiple providers increases:
- Number of credentials to manage
- Potential impact of a breach
- Complexity of security monitoring

### Credential Isolation

Each provider's credentials should be:
- Stored separately in Secrets Manager
- Accessed with minimum necessary IAM permissions
- Rotated independently

### Blast Radius

A compromise of one provider's credentials should not affect others:
- Separate secrets per provider
- No shared authentication tokens
- Independent session management

## Data Security

### Combined Data Access

This service can access:

| Provider | Data Types |
|----------|------------|
| Outlook | Email, Calendar, Contacts |
| SharePoint | Documents, Sites, Lists |
| Teams | Chats, Channels, Meetings |
| Azure DevOps | Code, Pipelines, PRs |
| Snowflake | Database queries |

### Data Handling Principles

- **No cross-provider data mixing**: Data from one provider not used with another
- **No persistent storage**: All data is pass-through
- **Provider isolation**: Each provider operates independently

## Credential Management

### Required Secrets by Provider

#### Microsoft Providers (Outlook, SharePoint, Teams)
| Secret | Purpose |
|--------|---------|
| `MICROSOFT_CLIENT_SECRET` | OAuth authentication |
| `TOKEN_ENCRYPTION_KEY` | Token at-rest encryption |

#### Azure DevOps
| Secret | Purpose |
|--------|---------|
| `AZURE_DEVOPS_PAT` | API authentication |

#### Snowflake
| Secret | Purpose |
|--------|---------|
| `SNOWFLAKE_PASSWORD` | Database authentication |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Key-pair auth (if used) |

### Secrets Rotation Schedule

| Provider | Credential | Rotation Frequency |
|----------|------------|-------------------|
| Microsoft | Client Secret | 90 days |
| Microsoft | Encryption Key | Quarterly |
| Azure DevOps | PAT | 90 days |
| Snowflake | Password | 90 days |
| Snowflake | Key-pair | Quarterly |

## Network Security

### Outbound Connections

| Provider | Destination |
|----------|-------------|
| Microsoft | graph.microsoft.com |
| Microsoft | login.microsoftonline.com |
| Azure DevOps | dev.azure.com |
| Snowflake | *.snowflakecomputing.com |

### Firewall Configuration

Allow outbound to all provider APIs:

```
Outbound: 443 → graph.microsoft.com
Outbound: 443 → login.microsoftonline.com
Outbound: 443 → dev.azure.com
Outbound: 443 → *.snowflakecomputing.com
```

## Provider Enablement Security

### Principle of Least Privilege

Enable only required providers:

```bash
# Good: Enable only what's needed
ENABLED_PROVIDERS=outlook,sharepoint

# Avoid: Enabling unused providers
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
```

### Runtime Provider Restrictions

Disabled providers:
- Are not initialized
- Cannot be accessed via any endpoint
- Have credentials not loaded into memory

## Audit Logging

### Cross-Provider Audit Trail

| Event | Level | Data |
|-------|-------|------|
| Service startup | INFO | enabled providers |
| Provider access | INFO | provider, user, operation |
| Cross-provider request | INFO | source provider, target |
| Auth failure | WARN | provider, reason |

### Provider-Specific Logging

Each provider maintains its own audit trail. See:
- [mcp-outlook-service/SECURITY.md](../mcp-outlook-service/SECURITY.md)
- [mcp-sharepoint-service/SECURITY.md](../mcp-sharepoint-service/SECURITY.md)
- [mcp-teams-service/SECURITY.md](../mcp-teams-service/SECURITY.md)
- [mcp-azuredevops-service/SECURITY.md](../mcp-azuredevops-service/SECURITY.md)
- [mcp-snowflake-service/SECURITY.md](../mcp-snowflake-service/SECURITY.md)

## Incident Response

### Multi-Provider Breach

If the combined service is compromised:

1. **Immediate actions**:
   - Disable the service
   - Revoke ALL provider credentials
   - Rotate ALL secrets

2. **Per-provider assessment**:
   - Review Microsoft audit logs (Azure AD, Graph)
   - Review Azure DevOps audit logs
   - Review Snowflake query history

3. **Scope determination**:
   - Which providers were accessed?
   - What data was potentially exposed?
   - What operations were performed?

### Single Provider Credential Compromise

If one provider's credentials are compromised:

1. Rotate only that provider's credentials
2. Other providers remain unaffected
3. Review that provider's audit logs
4. No need to rotate other credentials

## Vulnerability Mitigations

### Combined Service Risks

| Risk | Mitigation |
|------|------------|
| Single point of failure | Health checks, auto-restart |
| Increased attack surface | Enable only needed providers |
| Complex credential management | Secrets Manager per provider |
| Cross-provider data leak | Provider isolation |

### Provider-Specific Mitigations

See individual provider security documentation for:
- SQL injection (Snowflake)
- Email spoofing (Outlook)
- Document access (SharePoint)
- Message integrity (Teams)
- Code exposure (Azure DevOps)

## Compliance

### Combined Compliance Considerations

Running multiple providers may affect:
- Data residency (different provider data centers)
- Audit requirements (multiple audit trails)
- Access controls (different permission models)

### Per-Provider Compliance

| Provider | Key Compliance Features |
|----------|------------------------|
| Microsoft | Azure AD policies, DLP |
| Azure DevOps | Organization policies |
| Snowflake | Row access, masking |

## Security Checklist

### Pre-Production

- [ ] Enable only required providers
- [ ] Each provider's credentials in separate secrets
- [ ] OAuth Gateway secured (for Microsoft)
- [ ] TLS enabled for all endpoints
- [ ] Per-provider audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured

### Credential Management

- [ ] All secrets in Secrets Manager
- [ ] Rotation schedule documented
- [ ] Rotation alerts configured
- [ ] Emergency revocation procedure per provider

### Ongoing

- [ ] Review all provider access patterns (weekly)
- [ ] Rotate credentials per schedule
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
