# Security Guide - MCP OAuth Gateway

## Overview

The OAuth Gateway is the central authentication service for all MCP servers. This document covers security architecture, best practices, and compliance requirements.

## Security Architecture

### Authentication Flow

```
1. Client initiates OAuth with PKCE
2. Gateway validates request and generates state
3. User authenticates with identity provider
4. Gateway receives authorization code
5. Gateway exchanges code for tokens (with PKCE verification)
6. Tokens encrypted and stored
7. Client receives session token
```

### Token Security

| Token Type | Storage | Encryption | TTL |
|------------|---------|------------|-----|
| Access Token | PostgreSQL | AES-128 (Fernet) | Provider-dependent |
| Refresh Token | PostgreSQL | AES-128 (Fernet) | Provider-dependent |
| State Token | Redis | None (random value) | 10 minutes |
| Session Token | Redis | HMAC-signed | 24 hours |

## Security Features

### OAuth 2.1 Compliance

- **Mandatory PKCE**: All flows require PKCE with S256
- **No Implicit Flow**: Only authorization code flow supported
- **Token Binding**: Tokens bound to client via audience claim
- **Short-lived Tokens**: Access tokens have limited lifetime

### PKCE Enforcement

```python
# All authorization requests must include:
{
    "code_challenge": "base64url(sha256(verifier))",
    "code_challenge_method": "S256"
}
```

### Token Encryption

All tokens are encrypted at rest using Fernet (AES-128-CBC with HMAC-SHA256):

```python
# Token storage flow
encrypted_token = fernet.encrypt(token.encode())
# Stored in PostgreSQL with user/provider association
```

### State Management

- Cryptographically random state tokens
- Redis storage with 10-minute TTL
- Single-use validation (deleted after verification)
- CSRF protection for all OAuth flows

## Configuration Security

### Required Secrets

| Secret | Purpose | Storage |
|--------|---------|---------|
| `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth | Secrets Manager |
| `SNOWFLAKE_OAUTH_CLIENT_SECRET` | Snowflake OAuth | Secrets Manager |
| `TOKEN_ENCRYPTION_KEY` | Token at-rest encryption | Secrets Manager |
| `DATABASE_URL` | Database credentials | Secrets Manager |

### Secret Generation

```bash
# Generate TOKEN_ENCRYPTION_KEY
python -c "import secrets; import base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"

# Generate strong database password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Environment Variable Security

**DO NOT** store secrets in:
- Source code
- Docker images
- Environment files committed to git
- Logs

**DO** store secrets in:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Environment variables injected at runtime

## Network Security

### Recommended Architecture

```
Internet → WAF → ALB → OAuth Gateway (private subnet)
                           ↓
                     PostgreSQL (private subnet)
                           ↓
                     Redis (private subnet)
```

### TLS Configuration

- **Minimum TLS Version**: 1.2
- **Recommended**: TLS 1.3
- **Certificate**: Use ACM or Let's Encrypt

### CORS Configuration

```python
# Production CORS settings
allowed_origins = [
    "https://your-frontend.example.com"
]
# Never use "*" in production
```

### Rate Limiting

Implement rate limiting at ALB or WAF level:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/oauth/authorize` | 10 | per minute per IP |
| `/oauth/token` | 20 | per minute per IP |
| `/oauth/refresh` | 30 | per minute per IP |

## Database Security

### PostgreSQL

1. **Network Isolation**: Deploy in private subnet
2. **Encryption**: Enable encryption at rest
3. **Authentication**: Use IAM authentication when possible
4. **Connections**: Use SSL/TLS for all connections

```python
# Connection string with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Redis

1. **Network Isolation**: Deploy in private subnet
2. **Authentication**: Enable AUTH
3. **Encryption**: Use TLS (rediss://)
4. **No Persistence**: Disable RDB/AOF for sensitive data

```python
# Redis URL with TLS and auth
REDIS_URL=rediss://:password@redis.example.com:6379
```

## Audit Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| OAuth flow initiated | INFO | client_id, provider, state |
| OAuth callback received | INFO | provider, success/failure |
| Token issued | INFO | user_id, provider, scopes |
| Token refresh | INFO | user_id, provider |
| Token revocation | INFO | user_id, provider |
| Authentication failure | WARN | reason, client_id |
| Invalid state | WARN | attempted state value |

### Log Security

- Never log tokens, secrets, or passwords
- Mask sensitive fields in logs
- Send logs to centralized logging (CloudWatch, Splunk)
- Enable log encryption at rest

## Vulnerability Mitigations

### OWASP Top 10

| Vulnerability | Mitigation |
|---------------|------------|
| Injection | Parameterized queries (SQLAlchemy) |
| Broken Authentication | OAuth 2.1 with PKCE |
| Sensitive Data Exposure | Token encryption, TLS |
| XXE | No XML processing |
| Broken Access Control | Token validation, audience binding |
| Security Misconfiguration | Secure defaults, no debug in prod |
| XSS | JSON-only responses |
| Insecure Deserialization | Pydantic validation |
| Components with Vulnerabilities | Regular dependency updates |
| Insufficient Logging | Comprehensive audit logging |

### Additional Protections

- **CSRF**: State parameter validation
- **Clickjacking**: X-Frame-Options: DENY
- **MIME Sniffing**: X-Content-Type-Options: nosniff
- **Referrer Leakage**: Referrer-Policy: strict-origin-when-cross-origin

## Incident Response

### Compromised Client Secret

1. Immediately rotate in Azure AD / Snowflake
2. Update Secrets Manager
3. Deploy new configuration
4. Revoke all existing tokens for that provider
5. Audit logs for unauthorized access

### Compromised Token Encryption Key

1. Generate new encryption key
2. Update Secrets Manager
3. Invalidate all stored tokens (users must re-authenticate)
4. Deploy with new key
5. Audit for unauthorized token access

### Database Breach

1. Rotate all credentials
2. Enable enhanced monitoring
3. Tokens are encrypted, but rotate encryption key
4. Notify affected users
5. Review access logs

## Compliance

### Supported Standards

- OAuth 2.1 (draft specification)
- RFC 7636 (PKCE)
- RFC 8707 (Resource Indicators)
- RFC 9728 (OAuth Protected Resource Metadata)
- RFC 6749 (OAuth 2.0)

### Data Protection

- Tokens encrypted at rest
- TLS for data in transit
- Minimal data retention
- No PII stored beyond necessary OAuth data

## Security Checklist

### Pre-Production

- [ ] All secrets in Secrets Manager
- [ ] TLS enabled for all endpoints
- [ ] Database encryption enabled
- [ ] Redis authentication enabled
- [ ] CORS restricted to known origins
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Network isolation configured
- [ ] WAF rules configured

### Ongoing

- [ ] Regular dependency updates
- [ ] Secret rotation (quarterly)
- [ ] Security audit (annually)
- [ ] Penetration testing (annually)
- [ ] Log review (weekly)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
