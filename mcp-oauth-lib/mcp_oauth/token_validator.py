"""
JWT Token Validator with Audience Binding

Validates OAuth 2.1 access tokens for MCP resource servers following
MCP 2025-06-18 specification requirements.

Features:
- JWT signature verification
- Expiration validation
- Audience binding (RFC 8707) to prevent token reuse across servers
- Issuer validation
- Scope checking

References:
- MCP 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- RFC 8707: Resource Indicators for OAuth 2.0
- RFC 9068: JWT Profile for OAuth 2.0 Access Tokens
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError

from mcp_oauth.types import TokenInfo
from mcp_oauth.exceptions import (
    TokenValidationError,
    TokenExpiredError,
    InvalidAudienceError,
    InvalidIssuerError,
    InsufficientScopeError,
)

log = logging.getLogger(__name__)


class TokenValidator:
    """
    Validates OAuth 2.1 access tokens for MCP resource servers.

    Implements token validation per MCP 2025-06-18 specification:
    - Validates JWT signature using authorization server's JWKS
    - Checks token expiration
    - Validates audience claim matches the resource server (RFC 8707)
    - Validates issuer is trusted
    - Checks required scopes

    Usage:
        validator = TokenValidator(
            resource_uri="https://mcp.example.com",
            trusted_issuers=["https://login.microsoftonline.com/{tenant}/v2.0"]
        )
        token_info = await validator.validate_token(token, required_scopes=["Mail.Read"])
    """

    def __init__(
        self,
        resource_uri: str,
        trusted_issuers: List[str],
        jwks_cache_ttl: int = 3600,
        clock_skew_seconds: int = 30,
    ):
        """
        Initialize the token validator.

        Args:
            resource_uri: URI of this resource server (used for audience validation)
            trusted_issuers: List of trusted token issuer URIs
            jwks_cache_ttl: TTL for JWKS cache in seconds (default: 1 hour)
            clock_skew_seconds: Allowed clock skew for expiration checks (default: 30s)
        """
        self.resource_uri = resource_uri
        self.trusted_issuers = set(trusted_issuers)
        self.jwks_cache_ttl = jwks_cache_ttl
        self.clock_skew_seconds = clock_skew_seconds

        # JWKS clients cache (per issuer)
        self._jwks_clients: Dict[str, PyJWKClient] = {}

    def _get_jwks_client(self, issuer: str) -> PyJWKClient:
        """Get or create JWKS client for an issuer."""
        if issuer not in self._jwks_clients:
            # Construct JWKS URI from issuer
            # Standard location: {issuer}/.well-known/jwks.json
            # For Azure AD: {issuer}/discovery/v2.0/keys
            if "microsoftonline.com" in issuer:
                jwks_uri = f"{issuer}/discovery/v2.0/keys"
            else:
                jwks_uri = f"{issuer.rstrip('/')}/.well-known/jwks.json"

            self._jwks_clients[issuer] = PyJWKClient(
                jwks_uri,
                cache_keys=True,
                lifespan=self.jwks_cache_ttl,
            )
            log.debug("Created JWKS client for issuer %s", issuer)

        return self._jwks_clients[issuer]

    async def validate_token(
        self,
        token: str,
        required_scopes: Optional[List[str]] = None,
        audience: Optional[str] = None,
    ) -> TokenInfo:
        """
        Validate an access token.

        Args:
            token: JWT access token string
            required_scopes: List of scopes that must be present (optional)
            audience: Override audience to validate (default: self.resource_uri)

        Returns:
            TokenInfo with decoded claims

        Raises:
            TokenValidationError: If token is invalid
            TokenExpiredError: If token has expired
            InvalidAudienceError: If audience doesn't match
            InvalidIssuerError: If issuer is not trusted
            InsufficientScopeError: If required scopes are missing
        """
        expected_audience = audience or self.resource_uri

        try:
            # Decode header to get key ID and issuer hint
            unverified = jwt.decode(
                token, options={"verify_signature": False, "verify_exp": False}
            )
            issuer = unverified.get("iss", "")

            # Validate issuer is trusted
            if issuer not in self.trusted_issuers:
                raise InvalidIssuerError(issuer)

            # Get signing key from JWKS
            jwks_client = self._get_jwks_client(issuer)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=expected_audience,
                issuer=issuer,
                leeway=self.clock_skew_seconds,
                options={
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "require": ["exp", "iss"],
                },
            )

            # Check expiration with clock skew
            exp = claims.get("exp", 0)
            now = time.time()
            if now > exp + self.clock_skew_seconds:
                raise TokenExpiredError(
                    f"Token expired at {exp}, current time {int(now)}"
                )

            # Extract scopes (may be in 'scope' or 'scp' claim)
            scope_claim = claims.get("scope") or claims.get("scp") or ""
            if isinstance(scope_claim, list):
                granted_scopes = scope_claim
            else:
                granted_scopes = scope_claim.split() if scope_claim else []

            # Validate required scopes
            if required_scopes:
                missing = set(required_scopes) - set(granted_scopes)
                if missing:
                    raise InsufficientScopeError(required_scopes, granted_scopes)

            # Build TokenInfo
            token_info = TokenInfo(
                user_id=claims.get("sub") or claims.get("oid") or "",
                email=claims.get("email") or claims.get("preferred_username"),
                name=claims.get("name"),
                scopes=granted_scopes,
                audience=expected_audience,
                issuer=issuer,
                expires_at=exp,
                issued_at=claims.get("iat", 0),
                raw_claims=claims,
            )

            log.debug(
                "Token validated: user=%s, scopes=%s, exp=%d",
                token_info.user_id[:10] + "..." if token_info.user_id else "unknown",
                len(token_info.scopes),
                token_info.expires_at,
            )

            return token_info

        except jwt.ExpiredSignatureError as e:
            log.warning("Token expired: %s", e)
            raise TokenExpiredError(str(e)) from e

        except jwt.InvalidAudienceError as e:
            log.warning("Invalid token audience: %s", e)
            # Extract actual audience from token for error message
            try:
                unverified = jwt.decode(
                    token, options={"verify_signature": False, "verify_exp": False}
                )
                actual_aud = unverified.get("aud", "unknown")
            except Exception:
                actual_aud = "unknown"
            raise InvalidAudienceError(expected_audience, str(actual_aud)) from e

        except InvalidIssuerError:
            raise

        except InsufficientScopeError:
            raise

        except PyJWKClientError as e:
            log.error("Failed to fetch JWKS: %s", e)
            raise TokenValidationError(f"Failed to validate token signature: {e}") from e

        except jwt.InvalidTokenError as e:
            log.warning("Invalid token: %s", e)
            raise TokenValidationError(str(e)) from e

        except Exception as e:
            log.error("Unexpected error validating token: %s", e)
            raise TokenValidationError(f"Token validation failed: {e}") from e

    def validate_token_sync(
        self,
        token: str,
        required_scopes: Optional[List[str]] = None,
        audience: Optional[str] = None,
    ) -> TokenInfo:
        """
        Synchronous version of validate_token.

        For use in sync contexts. Note: JWKS fetching is blocking.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.validate_token(token, required_scopes, audience)
        )


def create_microsoft_validator(
    resource_uri: str, tenant_id: str
) -> TokenValidator:
    """
    Create a TokenValidator configured for Microsoft Azure AD / Entra ID.

    Args:
        resource_uri: URI of this MCP resource server
        tenant_id: Azure AD tenant ID (GUID or domain)

    Returns:
        TokenValidator configured for Microsoft tokens
    """
    # Microsoft v2.0 token issuer
    issuers = [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        f"https://sts.windows.net/{tenant_id}/",
    ]
    return TokenValidator(resource_uri=resource_uri, trusted_issuers=issuers)


def create_generic_validator(
    resource_uri: str, issuer: str
) -> TokenValidator:
    """
    Create a TokenValidator for a generic OIDC provider.

    Args:
        resource_uri: URI of this MCP resource server
        issuer: Token issuer URI (authorization server)

    Returns:
        TokenValidator configured for the given issuer
    """
    return TokenValidator(resource_uri=resource_uri, trusted_issuers=[issuer])


__all__ = [
    "TokenValidator",
    "create_microsoft_validator",
    "create_generic_validator",
]
