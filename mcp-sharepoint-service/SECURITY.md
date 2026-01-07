# Security Guide - MCP SharePoint Service

## Overview

This MCP server provides access to SharePoint sites, documents, and lists. This document covers security considerations, best practices, and compliance requirements for handling potentially sensitive organizational data.

## Security Architecture

### Authentication Flow

```
1. MCP Client sends request with OAuth token
2. Service validates token via OAuth Gateway
3. Service uses delegated token to call Microsoft Graph
4. Response returned to MCP Client
```

### Token Delegation

This service uses **delegated permissions** - it acts on behalf of the authenticated user. Users can only access SharePoint content they have permissions to access in the native SharePoint interface.

## Microsoft Graph API Permissions

### Minimum Required Permissions

| Permission | Purpose | Risk Level |
|------------|---------|------------|
| `User.Read` | User profile | Low |
| `Sites.Read.All` | Read sites | Medium |
| `Sites.ReadWrite.All` | Write to sites | High |
| `Files.Read.All` | Read documents | Medium |
| `Files.ReadWrite.All` | Write documents | High |

### Permission Recommendations

1. **Start with read-only**: Begin with `Sites.Read.All` and `Files.Read.All`
2. **Add write when needed**: Only add write permissions for specific use cases
3. **Audit access**: Monitor which sites/documents are being accessed
4. **User consent**: Consider whether user or admin consent is appropriate

## Data Security

### Data Handled

| Data Type | Sensitivity | Retention |
|-----------|-------------|-----------|
| Document content | Variable (High) | Not stored |
| Document metadata | Medium | Not stored |
| Site information | Low | Not stored |
| List items | Variable | Not stored |
| OAuth tokens | High | Encrypted |

### Document Classification

SharePoint documents may contain:
- Confidential business data
- Personal information (PII)
- Financial records
- Legal documents
- Intellectual property

**Important**: This service does not classify or filter documents. Users must ensure compliance with data handling policies.

### Data Handling Principles

- **No storage**: Document content is never persisted
- **Pass-through**: Data flows from Graph API to MCP client
- **Token encryption**: OAuth tokens encrypted at rest
- **Streaming**: Large files streamed to minimize memory exposure

## Token Security

### Token Validation

Every request validates:
- Token signature (via OAuth Gateway)
- Token expiration
- Audience claim (must match this service)
- Issuer (must be expected identity provider)

### SharePoint-Specific Considerations

- Site permissions are enforced by SharePoint, not this service
- User access is limited to sites they have native access to
- Document-level permissions are respected

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → SharePoint Service (private subnet)
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
| Inbound | Load Balancer | 8002 | Service traffic |

## Input Validation

### MCP Tool Inputs

| Tool | Validation |
|------|------------|
| `list_sites` | Max results limited |
| `get_site` | Site ID format validated |
| `search_documents` | Query sanitized, results limited |
| `get_document` | Document ID format validated |
| `upload_document` | File size limited, type validated |
| `download_document` | Document ID format validated |
| `list_items` | List ID validated, pagination enforced |
| `create_item` | Field types validated |

### File Upload Security

- File size limits enforced (configurable, default 100MB)
- File type validation (optional allowlist)
- Malware scanning recommended at infrastructure level
- Filename sanitization

## Rate Limiting

### Microsoft Graph Limits

Microsoft Graph enforces rate limits:
- Per-user throttling
- Per-tenant throttling
- SharePoint-specific limits (more restrictive)

### Recommended Application Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Site listings | 30 | per minute |
| Document searches | 20 | per minute |
| Document downloads | 50 | per minute |
| Document uploads | 10 | per minute |

## Audit Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| Site access | INFO | site ID, user |
| Document search | INFO | query (sanitized), result count |
| Document download | INFO | document ID (hashed), size |
| Document upload | INFO | target site, filename, size |
| List access | INFO | list ID, item count |
| Auth failure | WARN | reason, client info |
| Permission denied | WARN | operation, site/document ID |

### Sensitive Data in Logs

**Never log**:
- Document content
- Document names (may be sensitive)
- Full file paths
- OAuth tokens

**Safe to log**:
- Document IDs (hashed if needed)
- Site IDs
- Operation types
- File sizes
- Error codes

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Mitigation |
|------|------------|
| Injection | SDK parameterization, input validation |
| Broken Auth | OAuth 2.1, token validation |
| Sensitive Data | No storage, encryption in transit |
| XXE | No XML processing (JSON only) |
| Access Control | SharePoint permissions enforced |
| File Upload | Size limits, type validation |

### Document-Specific Risks

| Risk | Mitigation |
|------|------------|
| Data exfiltration | Delegated access, audit logging |
| Malware upload | Infrastructure-level scanning |
| Unauthorized sharing | SharePoint permissions |
| Sensitive document access | User-level permissions |

## Incident Response

### Unauthorized Document Access

1. Identify affected documents via logs
2. Check user's SharePoint permissions
3. Review OAuth token grants
4. Revoke tokens if compromised
5. Audit document access patterns

### Document Exfiltration Suspected

1. Review audit logs for bulk downloads
2. Identify affected user accounts
3. Disable service access for affected users
4. Coordinate with security team
5. Check SharePoint audit logs

### Compromised OAuth Token

1. Revoke token via OAuth Gateway
2. Force user re-authentication
3. Audit recent document access
4. Check for unauthorized uploads/downloads

## Compliance

### Supported Standards

- **OAuth 2.1**: Authentication standard
- **MCP 2025-06-18**: Protocol compliance
- **RFC 8707**: Token audience binding

### Data Protection Considerations

- **GDPR**: No PII storage; consider data residency for EU documents
- **HIPAA**: Not recommended for PHI without additional controls
- **SOC 2**: Compatible with proper logging and access controls
- **DLP**: Consider Microsoft DLP policies for document classification

## Security Checklist

### Pre-Production

- [ ] OAuth Gateway configured and secured
- [ ] TLS enabled for all endpoints
- [ ] Minimum Graph permissions granted
- [ ] Admin consent for required permissions
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured
- [ ] File upload limits set

### Ongoing

- [ ] Review SharePoint access patterns (weekly)
- [ ] Review Azure AD permissions (quarterly)
- [ ] Rotate client secrets (quarterly)
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
