# Security Guide - MCP OAuth Library

## Overview

This library implements OAuth 2.1 security patterns for MCP servers. This document covers security considerations, best practices, and configuration guidance.

## Security Features

### PKCE (RFC 7636)

- **S256 Only**: Only SHA-256 challenge method is supported (plain method is rejected)
- **Cryptographic Randomness**: Uses `secrets.token_urlsafe()` for verifier generation
- **Minimum Length**: 43-character minimum verifier length per RFC specification

```python
from mcp_oauth import PKCEFlow

pkce = PKCEFlow()
verifier, challenge = pkce.generate()
# verifier: 43+ character cryptographically random string
# challenge: Base64URL-encoded SHA-256 hash
```

### Token Validation

- **Signature Verification**: Validates JWT signatures using provider's JWKS
- **Audience Binding**: Enforces RFC 8707 audience claim validation
- **Issuer Validation**: Verifies token issuer matches expected identity provider
- **Expiration Checks**: Rejects expired tokens automatically
- **Clock Skew Tolerance**: Configurable leeway for clock drift (default: 30 seconds)

### Token Encryption

- **AES-128 Encryption**: Uses Fernet (AES-128-CBC with HMAC-SHA256)
- **Key Derivation**: Supports base64-encoded 32-byte keys
- **At-Rest Encryption**: Tokens are encrypted before storage

## Security Best Practices

### Token Encryption Key

Generate a secure encryption key:

```bash
python -c "import secrets; import base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Store securely using:
- AWS Secrets Manager
- HashiCorp Vault
- Environment variables (development only)

### Redis Security

For production Redis deployments:

1. **Enable Authentication**
   ```
   REDIS_URL=redis://:password@localhost:6379
   ```

2. **Use TLS**
   ```
   REDIS_URL=rediss://localhost:6379
   ```

3. **Network Isolation**: Deploy Redis in private subnet

4. **Key Expiration**: All state keys have TTL to prevent accumulation

### State Management

- **Cryptographic State Tokens**: Use `secrets.token_urlsafe(32)` for state parameters
- **Short TTL**: State tokens expire after 10 minutes (configurable)
- **Single Use**: State tokens are deleted after successful validation

## Vulnerability Mitigations

### OAuth Security Threats

| Threat | Mitigation |
|--------|------------|
| Authorization Code Interception | PKCE with S256 |
| Token Theft | Short-lived tokens, encryption at rest |
| CSRF | Cryptographic state parameter |
| Token Replay | Audience binding, issuer validation |
| Timing Attacks | Constant-time comparison for secrets |

### Input Validation

- All inputs are validated using Pydantic models
- Token claims are type-checked before use
- URLs are validated against expected patterns

## Secrets Management

### Required Secrets

| Secret | Purpose | Rotation |
|--------|---------|----------|
| `TOKEN_ENCRYPTION_KEY` | Token at-rest encryption | Quarterly |
| `REDIS_PASSWORD` | Redis authentication | Quarterly |

### Secret Rotation

1. Generate new key
2. Update in secrets manager
3. Deploy with new key (tokens encrypted with old key remain valid during transition if using key versioning)

## Audit Logging

Enable audit logging for security events:

```python
import logging
logging.getLogger("mcp_oauth").setLevel(logging.INFO)
```

Logged events:
- Token validation failures
- State validation failures
- PKCE verification failures

## Incident Response

### Compromised Token Encryption Key

1. Rotate `TOKEN_ENCRYPTION_KEY` immediately
2. Invalidate all stored tokens
3. Force re-authentication for all users

### Redis Breach

1. Flush Redis database
2. Rotate Redis password
3. Force re-authentication for all users

## Compliance

This library supports compliance with:
- OAuth 2.1 specification
- RFC 7636 (PKCE)
- RFC 8707 (Resource Indicators)
- RFC 9728 (Protected Resource Metadata)

## Reporting Security Issues

Report security vulnerabilities to the security team. Do not open public issues for security concerns.
