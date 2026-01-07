# Security Guide - MCP Outlook Service

## Overview

This MCP server provides access to sensitive email, calendar, and contact data. This document covers security considerations, best practices, and compliance requirements.

## Security Architecture

### Authentication Flow

```
1. MCP Client sends request with OAuth token
2. Service validates token via OAuth Gateway
3. Service uses delegated token to call Microsoft Graph
4. Response returned to MCP Client
```

### Token Delegation

This service uses **delegated permissions** - it acts on behalf of the authenticated user, not with application-level access. This limits the blast radius of any security incident.

## Microsoft Graph API Permissions

### Minimum Required Permissions

| Permission | Purpose | Risk Level |
|------------|---------|------------|
| `User.Read` | User profile | Low |
| `Mail.Read` | Read emails | Medium |
| `Mail.Send` | Send emails | High |
| `Calendars.Read` | Read calendar | Medium |
| `Calendars.ReadWrite` | Create events | Medium |
| `Contacts.Read` | Read contacts | Medium |

### Permission Best Practices

1. **Request minimum permissions** - Only enable permissions you need
2. **Use delegated, not application** - Act on behalf of users
3. **Review regularly** - Audit permissions quarterly
4. **Admin consent** - Require admin consent for sensitive permissions

## Data Security

### Data Handled

| Data Type | Sensitivity | Retention |
|-----------|-------------|-----------|
| Email content | High | Not stored |
| Email metadata | Medium | Not stored |
| Calendar events | Medium | Not stored |
| Contact information | Medium | Not stored |
| OAuth tokens | High | Encrypted |

### Data Handling Principles

- **No storage**: Email/calendar/contact data is never persisted
- **Pass-through**: Data flows from Graph API to MCP client
- **Token encryption**: OAuth tokens encrypted at rest
- **Memory only**: Sensitive data only in memory during request

## Token Security

### Token Validation

Every request validates:
- Token signature (via OAuth Gateway)
- Token expiration
- Audience claim (must match this service)
- Issuer (must be expected identity provider)

### Token Storage

If token caching is enabled:
- Tokens encrypted with AES-128 (Fernet)
- Short TTL matching token expiration
- Stored in memory or Redis (encrypted)

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → Outlook Service (private subnet)
                              ↓
                       OAuth Gateway (private subnet)
                              ↓
                       Microsoft Graph API (external)
```

### TLS Requirements

- **Inbound**: TLS 1.2+ required
- **Outbound to Graph**: TLS 1.2+ (Microsoft enforced)
- **Outbound to OAuth Gateway**: TLS 1.2+ recommended

### Firewall Rules

| Direction | Destination | Port | Purpose |
|-----------|-------------|------|---------|
| Outbound | graph.microsoft.com | 443 | Graph API |
| Outbound | login.microsoftonline.com | 443 | Token validation |
| Outbound | OAuth Gateway | 8000 | Token operations |
| Inbound | Load Balancer | 8001 | Service traffic |

## Input Validation

### MCP Tool Inputs

All tool inputs are validated:

| Tool | Validation |
|------|------------|
| `search_emails` | Query sanitized, max results limited |
| `get_email` | Email ID format validated |
| `send_email` | Recipients validated, content size limited |
| `list_calendar_events` | Date range validated |
| `create_calendar_event` | Required fields validated |
| `search_contacts` | Query sanitized |
| `get_contact` | Contact ID format validated |

### Query Injection Prevention

- Microsoft Graph queries use SDK with parameterization
- User input never directly interpolated into queries
- OData filter expressions sanitized

## Rate Limiting

### Microsoft Graph Limits

Microsoft Graph has built-in rate limits:
- Per-user throttling
- Per-tenant throttling
- Service-specific limits

### Recommended Application Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Email searches | 30 | per minute |
| Email sends | 10 | per minute |
| Calendar operations | 60 | per minute |

## Audit Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| Tool invocation | INFO | tool name, user |
| Email search | INFO | query (sanitized), result count |
| Email send | INFO | recipients (hashed), success/failure |
| Calendar access | INFO | date range, event count |
| Auth failure | WARN | reason, client info |
| Graph API error | ERROR | error code, operation |

### Sensitive Data in Logs

**Never log**:
- Email content or subjects
- Contact details (names, emails, phones)
- OAuth tokens
- Full error messages from Graph (may contain PII)

**Safe to log**:
- Request IDs
- Operation types
- Result counts
- Error codes (not messages)

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Mitigation |
|------|------------|
| Injection | SDK parameterization, input validation |
| Broken Auth | OAuth 2.1, token validation |
| Sensitive Data | No storage, encryption in transit |
| XXE | No XML processing |
| Access Control | Delegated permissions, user context |

### Email-Specific Risks

| Risk | Mitigation |
|------|------------|
| Email spoofing | Send only as authenticated user |
| Phishing via send | Rate limiting, audit logging |
| Data exfiltration | Delegated access only, no bulk export |

## Incident Response

### Compromised OAuth Token

1. Revoke token via OAuth Gateway
2. User re-authenticates
3. Audit recent activity via logs
4. Check for unauthorized email sends

### Unauthorized Email Access

1. Identify affected user(s)
2. Check audit logs for access patterns
3. Revoke active sessions
4. Notify affected users
5. Review permission grants

### Microsoft Graph API Breach (External)

1. Monitor Microsoft security advisories
2. Rotate client secrets
3. Force re-authentication for all users
4. Review access logs

## Compliance

### Supported Standards

- **OAuth 2.1**: Authentication standard
- **MCP 2025-06-18**: Protocol compliance
- **RFC 8707**: Token audience binding

### Data Protection

- GDPR: No PII storage, pass-through only
- HIPAA: Not recommended for PHI without additional controls
- SOC 2: Compatible with logging and access controls

## Security Checklist

### Pre-Production

- [ ] OAuth Gateway configured and secured
- [ ] TLS enabled for all endpoints
- [ ] Minimum Graph permissions granted
- [ ] Admin consent for sensitive permissions
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured

### Ongoing

- [ ] Review Azure AD permissions (quarterly)
- [ ] Rotate client secrets (quarterly)
- [ ] Review audit logs (weekly)
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
