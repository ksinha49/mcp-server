"""
Admin Endpoints

Administrative endpoints for managing OAuth integrations.
These endpoints should be protected with admin authentication
in production deployments.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings, ALL_PROVIDERS

log = logging.getLogger(__name__)

router = APIRouter()


class IntegrationStatus(BaseModel):
    """Status of a user's integration."""
    user_id: str
    provider: str
    authenticated: bool
    expires_at: int | None = None
    scopes: List[str] = []


class AdminStats(BaseModel):
    """Gateway statistics."""
    active_states: int
    total_integrations: int
    providers_configured: List[str]


@router.get("/stats")
async def get_stats():
    """
    Get gateway statistics.

    Returns:
        AdminStats with current gateway state
    """
    from mcp_oauth import get_oauth_state_manager

    try:
        state_manager = get_oauth_state_manager()
        active_states = state_manager.count_active_states()
    except RuntimeError:
        active_states = 0

    settings = get_settings()

    # Determine which providers are configured
    configured_providers = []
    if settings.microsoft_client_id:
        configured_providers.extend(["outlook", "sharepoint", "teams", "azuredevops"])
    if settings.snowflake_oauth_client_id:
        configured_providers.append("snowflake")

    return AdminStats(
        active_states=active_states,
        total_integrations=0,  # TODO: Query from database
        providers_configured=configured_providers,
    )


@router.get("/integrations/{user_id}")
async def get_user_integrations(user_id: str):
    """
    Get all integrations for a user.

    Args:
        user_id: User identifier

    Returns:
        List of integration statuses
    """
    # TODO: Query database for user's integrations
    integrations = []

    for provider in ALL_PROVIDERS:
        integrations.append(
            IntegrationStatus(
                user_id=user_id,
                provider=provider,
                authenticated=False,
            )
        )

    return integrations


@router.delete("/integrations/{user_id}/{provider}")
async def revoke_user_integration(user_id: str, provider: str):
    """
    Revoke a user's integration with a provider.

    This is an admin endpoint that allows revoking any user's tokens.

    Args:
        user_id: User identifier
        provider: OAuth provider

    Returns:
        Success status
    """
    if provider not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # TODO: Remove tokens from database
    log.info("Admin revoked integration: user=%s, provider=%s", user_id[:8] + "...", provider)

    return {"status": "revoked", "user_id": user_id, "provider": provider}


@router.delete("/integrations/{provider}/all")
async def revoke_all_provider_integrations(provider: str):
    """
    Revoke all user integrations for a provider.

    WARNING: This is a destructive operation that removes all tokens
    for a provider across all users.

    Args:
        provider: OAuth provider

    Returns:
        Number of integrations revoked
    """
    if provider not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # TODO: Remove all tokens for provider from database
    log.warning("Admin revoked ALL integrations for provider: %s", provider)

    return {"status": "revoked_all", "provider": provider, "count": 0}
