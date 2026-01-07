"""
Type definitions for MCP OAuth library.

Provides Pydantic models for OAuth tokens, state, and metadata
following MCP 2025-06-18 specification.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    """
    Decoded token information after validation.

    Contains claims extracted from a validated JWT token,
    used by MCP resource servers to authorize requests.
    """
    user_id: str = Field(..., description="User identifier from token")
    email: Optional[str] = Field(None, description="User email if present")
    name: Optional[str] = Field(None, description="User display name")
    scopes: List[str] = Field(default_factory=list, description="Granted OAuth scopes")
    audience: str = Field(..., description="Token audience (resource server)")
    issuer: str = Field(..., description="Token issuer (authorization server)")
    expires_at: int = Field(..., description="Token expiration Unix timestamp")
    issued_at: int = Field(..., description="Token issued Unix timestamp")
    raw_claims: Dict[str, Any] = Field(default_factory=dict, description="All token claims")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow().timestamp() >= self.expires_at

    @property
    def time_remaining(self) -> int:
        """Seconds until token expiration."""
        return max(0, self.expires_at - int(datetime.utcnow().timestamp()))


class TokenRecord(BaseModel):
    """
    Stored token record for a user integration.

    Represents encrypted token data stored in database
    for per-user delegated authentication.
    """
    user_id: str = Field(..., description="User identifier")
    provider: str = Field(..., description="OAuth provider (outlook, sharepoint, etc.)")
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: Optional[str] = Field(None, description="Encrypted refresh token")
    token_type: str = Field("Bearer", description="Token type")
    expires_at: int = Field(..., description="Expiration Unix timestamp")
    scope: Optional[str] = Field(None, description="Granted scopes")
    token_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow().timestamp() >= self.expires_at

    @property
    def needs_refresh(self, buffer_seconds: int = 300) -> bool:
        """Check if token needs refresh (within buffer of expiration)."""
        return datetime.utcnow().timestamp() >= (self.expires_at - buffer_seconds)


class OAuthState(BaseModel):
    """
    OAuth state stored during authorization flow.

    Contains all data needed to complete OAuth callback,
    including PKCE code_verifier and CSRF state parameter.
    """
    state: str = Field(..., description="CSRF protection state parameter")
    user_id: str = Field(..., description="User initiating OAuth")
    provider: str = Field(..., description="OAuth provider")
    redirect_uri: str = Field(..., description="Callback URL")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier")
    scopes: List[str] = Field(default_factory=list, description="Requested scopes")
    flow_data: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific flow data")
    created_at: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    expires_at: int = Field(..., description="State expiration timestamp")

    @property
    def is_expired(self) -> bool:
        """Check if state has expired."""
        return datetime.utcnow().timestamp() >= self.expires_at


class ProtectedResourceMetadata(BaseModel):
    """
    OAuth 2.0 Protected Resource Metadata (RFC 9728).

    Published at /.well-known/oauth-protected-resource.json
    to advertise authorization requirements.
    """
    resource: str = Field(..., description="Protected resource identifier (URL)")
    authorization_servers: List[str] = Field(
        ...,
        description="URLs of authorization servers that can issue tokens for this resource"
    )
    bearer_methods_supported: List[str] = Field(
        default=["header"],
        description="Token transmission methods supported"
    )
    resource_signing_alg_values_supported: List[str] = Field(
        default=["RS256"],
        description="JWS algorithms for signing"
    )
    scopes_supported: Optional[List[str]] = Field(
        None,
        description="OAuth scopes that can be used at this resource"
    )
    resource_documentation: Optional[str] = Field(
        None,
        description="URL of human-readable documentation"
    )


@dataclass
class AuthInitResult:
    """Result of initiating an OAuth authorization flow."""
    authorization_url: str
    state: str
    code_verifier: Optional[str] = None


@dataclass
class TokenResult:
    """Result of token exchange or refresh."""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None
