"""
Exception classes for MCP OAuth library.

Provides a hierarchy of OAuth-related exceptions for
proper error handling in MCP servers.
"""


class OAuthError(Exception):
    """Base exception for all OAuth-related errors."""

    def __init__(self, message: str, error_code: str = "oauth_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class TokenValidationError(OAuthError):
    """Token validation failed."""

    def __init__(self, message: str, error_code: str = "invalid_token"):
        super().__init__(message, error_code)


class TokenExpiredError(TokenValidationError):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "token_expired")


class InvalidAudienceError(TokenValidationError):
    """Token audience does not match expected resource."""

    def __init__(self, expected: str, actual: str):
        message = f"Token audience mismatch: expected '{expected}', got '{actual}'"
        super().__init__(message, "invalid_audience")
        self.expected = expected
        self.actual = actual


class InvalidIssuerError(TokenValidationError):
    """Token issuer is not trusted."""

    def __init__(self, issuer: str):
        message = f"Token issuer not trusted: '{issuer}'"
        super().__init__(message, "invalid_issuer")
        self.issuer = issuer


class InsufficientScopeError(TokenValidationError):
    """Token does not have required scopes."""

    def __init__(self, required: list[str], granted: list[str]):
        missing = set(required) - set(granted)
        message = f"Insufficient scope: missing {missing}"
        super().__init__(message, "insufficient_scope")
        self.required = required
        self.granted = granted
        self.missing = list(missing)


class StateError(OAuthError):
    """OAuth state validation error."""

    def __init__(self, message: str = "Invalid or expired OAuth state"):
        super().__init__(message, "invalid_state")


class StateExpiredError(StateError):
    """OAuth state has expired."""

    def __init__(self):
        super().__init__("OAuth state has expired")


class StateNotFoundError(StateError):
    """OAuth state not found in storage."""

    def __init__(self, state: str):
        super().__init__(f"OAuth state not found: {state[:10]}...")
        self.state = state


class EncryptionError(OAuthError):
    """Token encryption/decryption error."""

    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(message, "encryption_error")
        self.operation = operation


class TokenExchangeError(OAuthError):
    """Token exchange with authorization server failed."""

    def __init__(self, message: str, oauth_error: str | None = None):
        super().__init__(message, "token_exchange_error")
        self.oauth_error = oauth_error


class RefreshTokenError(OAuthError):
    """Token refresh failed."""

    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message, "refresh_token_error")
        self.provider = provider


class ProviderError(OAuthError):
    """OAuth provider-specific error."""

    def __init__(self, message: str, provider: str, status_code: int | None = None):
        super().__init__(message, "provider_error")
        self.provider = provider
        self.status_code = status_code
