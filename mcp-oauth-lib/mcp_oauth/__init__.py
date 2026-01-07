"""
MCP OAuth Library

Shared OAuth utilities for MCP servers following MCP 2025-06-18 specification.

This library provides:
- PKCE (RFC 7636) implementation for OAuth 2.1 compliance
- OAuth state management with Redis backend
- JWT token validation with audience binding (RFC 8707)
- AES-256-GCM encryption for token storage

References:
- MCP Authorization: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- RFC 7636: Proof Key for Code Exchange
- RFC 8707: Resource Indicators for OAuth 2.0
- RFC 9728: OAuth 2.0 Protected Resource Metadata
"""

from mcp_oauth.pkce import (
    generate_code_verifier,
    generate_code_challenge,
    generate_pkce_pair,
    build_authorization_url_with_pkce,
    build_token_request_with_pkce,
    validate_code_verifier,
    PKCEError,
    PKCECodeVerifierError,
    PKCECodeChallengeError,
    PKCE_CODE_VERIFIER_LENGTH,
    PKCE_CODE_CHALLENGE_METHOD,
)

from mcp_oauth.types import (
    TokenInfo,
    TokenRecord,
    OAuthState,
    ProtectedResourceMetadata,
)

from mcp_oauth.exceptions import (
    OAuthError,
    TokenValidationError,
    TokenExpiredError,
    InvalidAudienceError,
    StateError,
    EncryptionError,
)

__version__ = "1.0.0"

__all__ = [
    # PKCE
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_pkce_pair",
    "build_authorization_url_with_pkce",
    "build_token_request_with_pkce",
    "validate_code_verifier",
    "PKCEError",
    "PKCECodeVerifierError",
    "PKCECodeChallengeError",
    "PKCE_CODE_VERIFIER_LENGTH",
    "PKCE_CODE_CHALLENGE_METHOD",
    # Types
    "TokenInfo",
    "TokenRecord",
    "OAuthState",
    "ProtectedResourceMetadata",
    # Exceptions
    "OAuthError",
    "TokenValidationError",
    "TokenExpiredError",
    "InvalidAudienceError",
    "StateError",
    "EncryptionError",
]
