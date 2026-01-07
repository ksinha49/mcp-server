"""
Well-Known Discovery Endpoints

Implements OAuth 2.0 discovery endpoints per MCP 2025-06-18 specification:
- Protected Resource Metadata (RFC 9728)
- Authorization Server Metadata (RFC 8414)

References:
- RFC 9728: OAuth 2.0 Protected Resource Metadata
- RFC 8414: OAuth 2.0 Authorization Server Metadata
- MCP 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings, ALL_PROVIDERS

router = APIRouter()


@router.get("/.well-known/oauth-protected-resource.json")
async def protected_resource_metadata():
    """
    OAuth 2.0 Protected Resource Metadata (RFC 9728).

    MCP servers MUST implement this endpoint to advertise their
    authorization requirements to clients.

    Returns:
        JSON metadata describing the protected resource
    """
    settings = get_settings()

    # Build authorization servers list
    authorization_servers = []
    if settings.microsoft_client_id:
        authorization_servers.append(
            f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/v2.0"
        )
    if settings.snowflake_oauth_authorization_endpoint:
        # Extract base URL from Snowflake authorization endpoint
        auth_server = settings.snowflake_oauth_authorization_endpoint.rsplit("/", 1)[0]
        authorization_servers.append(auth_server)

    # Build supported scopes
    scopes_supported = set()
    for provider in ALL_PROVIDERS:
        scopes = settings.get_scopes(provider) if hasattr(settings, 'get_scopes') else []
        scopes_supported.update(scopes)

    metadata = {
        "resource": settings.gateway_url,
        "authorization_servers": authorization_servers,
        "bearer_methods_supported": ["header"],
        "resource_signing_alg_values_supported": ["RS256"],
        "scopes_supported": sorted(scopes_supported),
        "resource_documentation": f"{settings.gateway_url}/docs",
    }

    return JSONResponse(
        content=metadata,
        headers={"Cache-Control": "max-age=3600"},
    )


@router.get("/.well-known/openid-configuration")
async def openid_configuration():
    """
    OpenID Connect Discovery (RFC 8414).

    Provides authorization server metadata for OAuth clients.
    This gateway acts as an authorization server that delegates
    to upstream providers (Microsoft, Snowflake).

    Returns:
        JSON metadata describing the authorization server
    """
    settings = get_settings()

    metadata = {
        "issuer": settings.gateway_url,
        "authorization_endpoint": f"{settings.gateway_url}/oauth/authorize",
        "token_endpoint": f"{settings.gateway_url}/oauth/token",
        "revocation_endpoint": f"{settings.gateway_url}/oauth/revoke",
        "jwks_uri": f"{settings.gateway_url}/.well-known/jwks.json",
        "registration_endpoint": f"{settings.gateway_url}/oauth/register",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": [
            "authorization_code",
            "refresh_token",
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none",  # For public clients with PKCE
        ],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["openid", "profile", "email", "offline_access"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "email", "name"],
    }

    return JSONResponse(
        content=metadata,
        headers={"Cache-Control": "max-age=3600"},
    )


@router.get("/.well-known/jwks.json")
async def jwks():
    """
    JSON Web Key Set (JWKS) endpoint.

    Note: This gateway delegates token issuance to upstream providers,
    so this endpoint returns an empty JWKS. Clients should use the
    JWKS from the upstream authorization server (e.g., Microsoft).

    Returns:
        Empty JWKS (tokens are issued by upstream providers)
    """
    return JSONResponse(
        content={"keys": []},
        headers={"Cache-Control": "max-age=3600"},
    )
