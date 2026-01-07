# MCP OAuth Library

Shared Python OAuth library for MCP (Model Context Protocol) servers. Provides MCP 2025-06-18 compliant authentication components including PKCE flows, token validation, and state management.

## Overview

This library provides reusable OAuth 2.1 components for all MCP servers in this repository:

- **PKCE Implementation** - RFC 7636 compliant code verifier/challenge generation
- **Token Validation** - JWT validation with audience binding (RFC 8707)
- **State Management** - Redis-backed OAuth state storage
- **Token Encryption** - Secure token storage with AES encryption

## Features

- OAuth 2.1 with mandatory PKCE (S256 only)
- JWT validation with configurable audience
- Redis-backed state management with TTL
- Fernet-based token encryption
- Async-first design
- Type hints throughout

## Requirements

- Python 3.11+
- Redis (for state management)

## Quick Start

```python
from mcp_oauth import PKCEFlow, TokenValidator, StateManager

# Generate PKCE challenge
pkce = PKCEFlow()
verifier, challenge = pkce.generate()

# Validate tokens
validator = TokenValidator(
    issuer="https://login.microsoftonline.com/{tenant}/v2.0",
    audience="your-client-id"
)
claims = await validator.validate(token)

# Manage OAuth state
state_manager = StateManager(redis_url="redis://localhost:6379")
await state_manager.store(state_key, state_data, ttl=600)
```

## Module Reference

| Module | Description |
|--------|-------------|
| `mcp_oauth.pkce` | PKCE code verifier and challenge generation |
| `mcp_oauth.token_validator` | JWT validation with audience binding |
| `mcp_oauth.state` | Redis-backed OAuth state management |
| `mcp_oauth.encryption` | Token encryption/decryption utilities |
| `mcp_oauth.exceptions` | Custom exception classes |
| `mcp_oauth.types` | Type definitions and models |

## Dependencies

- PyJWT >= 2.8.0
- cryptography >= 41.0.0
- redis >= 5.0.0
- pydantic >= 2.0.0
- httpx >= 0.25.0

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Detailed installation instructions
- [SECURITY.md](./SECURITY.md) - Security considerations and best practices

## License

MIT
