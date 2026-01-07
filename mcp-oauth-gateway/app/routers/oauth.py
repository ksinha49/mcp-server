"""
OAuth Authorization Endpoints

Implements OAuth 2.1 authorization flows for MCP servers:
- Authorization initiation with PKCE
- Callback handling and token exchange
- Token retrieval for authenticated users
- Token refresh
- Token revocation

References:
- MCP 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- OAuth 2.1: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1
- RFC 7636: PKCE
"""

import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from app.config import get_settings, MICROSOFT_PROVIDERS, ALL_PROVIDERS
from app.services.microsoft_auth import MicrosoftAuthService
from mcp_oauth import get_oauth_state_manager
from mcp_oauth.exceptions import StateNotFoundError

log = logging.getLogger(__name__)

router = APIRouter()


class AuthorizeRequest(BaseModel):
    """Request body for /authorize endpoint."""
    provider: str
    user_id: str
    redirect_uri: Optional[str] = None
    scopes: Optional[str] = None


class TokenResponse(BaseModel):
    """Response for token endpoints."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class ErrorResponse(BaseModel):
    """OAuth error response."""
    error: str
    error_description: Optional[str] = None


@router.post("/authorize")
async def initiate_authorization(request: AuthorizeRequest):
    """
    Initiate OAuth authorization flow.

    This endpoint starts the OAuth flow by:
    1. Generating PKCE code_verifier and code_challenge
    2. Storing state with user context
    3. Returning authorization URL for the provider

    Args:
        provider: OAuth provider (outlook, sharepoint, teams, azuredevops, snowflake)
        user_id: User identifier for the authorization
        redirect_uri: Optional override for callback URL
        scopes: Optional override for OAuth scopes

    Returns:
        JSON with authorization_url to redirect user to
    """
    settings = get_settings()

    # Validate provider
    if request.provider not in ALL_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {request.provider}. Supported: {', '.join(ALL_PROVIDERS)}",
        )

    # Determine callback URL
    callback_url = request.redirect_uri or f"{settings.gateway_url}/oauth/callback/{request.provider}"

    try:
        if request.provider in MICROSOFT_PROVIDERS:
            # Use Microsoft auth service
            auth_service = MicrosoftAuthService(
                provider=request.provider,
                settings=settings,
            )

            # Get scopes
            scopes = request.scopes.split() if request.scopes else settings.get_scopes(request.provider)

            # Initiate auth flow
            result = await auth_service.initiate_auth(
                user_id=request.user_id,
                redirect_uri=callback_url,
                scopes=scopes,
            )

            return {
                "authorization_url": result.authorization_url,
                "state": result.state,
                "provider": request.provider,
            }

        elif request.provider == "snowflake":
            # Snowflake auth (to be implemented)
            raise HTTPException(
                status_code=501,
                detail="Snowflake OAuth not yet implemented",
            )

    except Exception as e:
        log.exception("Failed to initiate authorization for %s: %s", request.provider, e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate authorization: {e}",
        )


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """
    OAuth callback handler.

    This endpoint handles the callback from the OAuth provider after
    user authorization. It:
    1. Validates the state parameter
    2. Exchanges the authorization code for tokens
    3. Stores tokens securely
    4. Redirects to frontend with success/error status

    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: State parameter for CSRF validation
        error: OAuth error code (if authorization failed)
        error_description: Human-readable error description

    Returns:
        Redirect to frontend with result
    """
    settings = get_settings()

    # Handle OAuth errors from provider
    if error:
        log.warning("OAuth error from %s: %s - %s", provider, error, error_description)
        redirect_url = f"{settings.frontend_url}/integrations/callback?provider={provider}&error={error}"
        if error_description:
            redirect_url += f"&error_description={error_description}"
        return RedirectResponse(url=redirect_url)

    # Validate required parameters
    if not code or not state:
        log.warning("Missing code or state in OAuth callback")
        return RedirectResponse(
            url=f"{settings.frontend_url}/integrations/callback?provider={provider}&error=missing_parameters"
        )

    try:
        # Retrieve and validate state
        state_manager = get_oauth_state_manager()
        state_data = state_manager.get_state_or_raise(state, delete_after=True)

        # Verify provider matches
        if state_data.get("provider") != provider:
            raise HTTPException(status_code=400, detail="Provider mismatch in state")

        user_id = state_data.get("user_id")

        if provider in MICROSOFT_PROVIDERS:
            # Exchange code for tokens
            auth_service = MicrosoftAuthService(
                provider=provider,
                settings=settings,
            )

            result = await auth_service.handle_callback(
                code=code,
                state=state,
                state_data=state_data,
            )

            if result.success:
                log.info("OAuth callback successful for user %s, provider %s", user_id[:8] + "...", provider)
                return RedirectResponse(
                    url=f"{settings.frontend_url}/integrations/callback?provider={provider}&success=true"
                )
            else:
                log.error("Token exchange failed: %s", result.error)
                return RedirectResponse(
                    url=f"{settings.frontend_url}/integrations/callback?provider={provider}&error=token_exchange_failed"
                )

        elif provider == "snowflake":
            # Snowflake callback (to be implemented)
            raise HTTPException(status_code=501, detail="Snowflake OAuth not yet implemented")

    except StateNotFoundError:
        log.warning("Invalid or expired OAuth state")
        return RedirectResponse(
            url=f"{settings.frontend_url}/integrations/callback?provider={provider}&error=invalid_state"
        )
    except Exception as e:
        log.exception("OAuth callback error: %s", e)
        return RedirectResponse(
            url=f"{settings.frontend_url}/integrations/callback?provider={provider}&error=callback_failed"
        )


@router.get("/status/{provider}")
async def get_auth_status(
    provider: str,
    user_id: str = Query(..., description="User ID to check status for"),
):
    """
    Get authentication status for a user and provider.

    Returns:
        JSON with authentication status
    """
    settings = get_settings()

    if provider not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # TODO: Check token storage for user
    # For now, return placeholder
    return {
        "provider": provider,
        "user_id": user_id,
        "authenticated": False,
        "expires_at": None,
    }


@router.post("/refresh")
async def refresh_token(
    provider: str = Query(...),
    user_id: str = Query(...),
):
    """
    Refresh an access token.

    Uses the stored refresh token to obtain a new access token.

    Returns:
        New token information
    """
    settings = get_settings()

    if provider not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # TODO: Implement token refresh
    raise HTTPException(status_code=501, detail="Token refresh not yet implemented")


@router.delete("/revoke")
async def revoke_token(
    provider: str = Query(...),
    user_id: str = Query(...),
):
    """
    Revoke OAuth tokens for a user and provider.

    This removes the stored tokens and optionally revokes them
    with the OAuth provider.

    Returns:
        Success status
    """
    settings = get_settings()

    if provider not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # TODO: Implement token revocation
    raise HTTPException(status_code=501, detail="Token revocation not yet implemented")
