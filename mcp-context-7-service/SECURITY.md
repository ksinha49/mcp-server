# Security Guide - MCP Context7 Service

## Overview

This MCP server provides access to Context7 library documentation search. This document covers security considerations and best practices for this relatively low-risk service.

## Security Profile

This service has a **low security risk profile** because:

- Read-only access to public documentation
- No user data storage
- No authentication required by default
- No sensitive data processed

## Security Architecture

### Data Flow

```
MCP Client → Context7 Service → Context7 API (external)
                                    ↓
                           Public documentation data
```

### No Sensitive Data

This service:
- Does not store user data
- Does not process PII
- Does not require authentication
- Accesses only public documentation

## Authentication (Optional)

### API Key Authentication

If Context7 API requires authentication:

```bash
API_KEY=your-context7-api-key
```

### MCP Client Authentication

For production deployments, consider adding client authentication:

- Bearer token validation
- API key header
- mTLS (mutual TLS)

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → Context7 Service (private subnet)
                              ↓
                       Context7 API (external)
```

### TLS Requirements

- **Inbound**: TLS 1.2+ recommended for HTTP transport
- **Outbound**: TLS to Context7 API

### Firewall Rules

| Direction | Destination | Port | Purpose |
|-----------|-------------|------|---------|
| Outbound | Context7 API | 443 | Documentation API |
| Inbound | Load Balancer | 8006 | Service traffic |

## Input Validation

### MCP Tool Inputs

| Tool | Validation |
|------|------------|
| `searchLibraries` | Query sanitized, length limited |
| `fetchLibraryDocumentation` | Library ID format validated |

### Query Sanitization

- Search queries are length-limited
- Special characters handled safely
- No SQL/command injection possible (read-only API)

## Rate Limiting

### Recommended Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Library searches | 60 | per minute |
| Documentation fetches | 30 | per minute |

### External API Limits

Context7 API may have its own rate limits. Implement:
- Exponential backoff on 429 responses
- Request caching where appropriate

## Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| Search request | INFO | query (truncated), result count |
| Documentation fetch | INFO | library ID |
| API error | WARN | error code |
| Rate limit hit | WARN | operation count |

### No Sensitive Data in Logs

This service doesn't handle sensitive data, but still avoid logging:
- Full request bodies
- API keys
- User identifiers (if added)

## Dependency Security

### Key Dependencies

| Package | Purpose | Risk |
|---------|---------|------|
| @modelcontextprotocol/sdk | MCP protocol | Low |
| commander | CLI parsing | Low |
| zod | Validation | Low |

### Dependency Updates

```bash
# Check for vulnerabilities
npm audit
# or
bun audit

# Update dependencies
npm update
# or
bun update
```

### Security Scanning

Run security scans regularly:

```bash
# npm audit
npm audit

# Snyk (if available)
snyk test
```

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Status | Notes |
|------|--------|-------|
| Injection | N/A | Read-only API, no DB |
| Broken Auth | Low | Optional API key |
| Sensitive Data | N/A | No sensitive data |
| XXE | N/A | JSON only |
| Access Control | Low | Public data only |

### TypeScript Security

- Strict type checking enabled
- Zod validation for inputs
- No `any` types in critical paths

## Container Security

### Docker Best Practices

The Dockerfile implements:
- Non-root user (`appuser`)
- Multi-stage build (smaller image)
- No unnecessary packages
- Read-only filesystem compatible

### Runtime Security

```bash
# Run with read-only filesystem
docker run --read-only \
  --tmpfs /tmp \
  mcp-context7-service:latest
```

## Incident Response

### Service Unavailable

1. Check Context7 API status
2. Verify network connectivity
3. Check rate limits
4. Review error logs

### Suspected Abuse

1. Enable request logging
2. Identify source IPs
3. Implement rate limiting
4. Block abusive clients

## Compliance

### Data Handling

- No PII processed
- No data storage
- Pass-through to public API
- GDPR: No personal data concerns

## Security Checklist

### Pre-Production

- [ ] TLS enabled (HTTP transport)
- [ ] Rate limiting configured
- [ ] Health check endpoint verified
- [ ] Dependencies audited
- [ ] Container runs as non-root

### Ongoing

- [ ] Update dependencies (monthly)
- [ ] Review npm audit (weekly)
- [ ] Monitor error rates
- [ ] Update base images (monthly)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
