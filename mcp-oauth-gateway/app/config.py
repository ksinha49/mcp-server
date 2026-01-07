"""
Configuration for MCP OAuth Gateway

Loads settings from environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Gateway identity
    gateway_url: str = Field(
        default="http://localhost:8000",
        description="Public URL of this gateway",
    )

    # Frontend
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for OAuth redirects",
    )

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Redis for state management
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for OAuth state storage",
    )

    # Database for token storage
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL URL for token storage",
    )

    # Token encryption
    token_encryption_key: str = Field(
        default="",
        description="Base64-encoded 32-byte key for token encryption",
    )

    # OAuth state TTL
    oauth_state_ttl_seconds: int = Field(
        default=900,
        description="OAuth state TTL in seconds (default: 15 minutes)",
    )

    # Microsoft OAuth (common for all Microsoft providers)
    microsoft_client_id: str = Field(
        default="",
        description="Microsoft OAuth client ID",
    )
    microsoft_client_secret: str = Field(
        default="",
        description="Microsoft OAuth client secret",
    )
    microsoft_tenant_id: str = Field(
        default="common",
        description="Microsoft tenant ID (or 'common' for multi-tenant)",
    )

    # Per-provider client IDs (optional overrides)
    outlook_client_id: Optional[str] = Field(default=None)
    outlook_client_secret: Optional[str] = Field(default=None)
    sharepoint_client_id: Optional[str] = Field(default=None)
    sharepoint_client_secret: Optional[str] = Field(default=None)
    teams_client_id: Optional[str] = Field(default=None)
    teams_client_secret: Optional[str] = Field(default=None)
    azuredevops_client_id: Optional[str] = Field(default=None)
    azuredevops_client_secret: Optional[str] = Field(default=None)

    # Snowflake OAuth
    snowflake_oauth_client_id: Optional[str] = Field(default=None)
    snowflake_oauth_client_secret: Optional[str] = Field(default=None)
    snowflake_oauth_authorization_endpoint: Optional[str] = Field(default=None)
    snowflake_oauth_token_endpoint: Optional[str] = Field(default=None)

    # Scopes for each provider
    outlook_scopes: str = Field(
        default="openid profile email offline_access Mail.Read Mail.Send Calendars.ReadWrite Contacts.Read",
        description="Default Outlook OAuth scopes",
    )
    sharepoint_scopes: str = Field(
        default="openid profile email offline_access Sites.Read.All Files.ReadWrite.All",
        description="Default SharePoint OAuth scopes",
    )
    teams_scopes: str = Field(
        default="openid profile email offline_access Team.ReadBasic.All Channel.ReadBasic.All Chat.Read ChannelMessage.Read.All",
        description="Default Teams OAuth scopes",
    )
    azuredevops_scopes: str = Field(
        default="openid profile email offline_access 499b84ac-1321-427f-aa17-267ca6975798/.default",
        description="Default Azure DevOps OAuth scopes",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_microsoft_credentials(self, provider: str) -> tuple[str, str]:
        """Get client ID and secret for a Microsoft provider."""
        # Check provider-specific override first
        overrides = {
            "outlook": (self.outlook_client_id, self.outlook_client_secret),
            "sharepoint": (self.sharepoint_client_id, self.sharepoint_client_secret),
            "teams": (self.teams_client_id, self.teams_client_secret),
            "azuredevops": (self.azuredevops_client_id, self.azuredevops_client_secret),
        }

        client_id, client_secret = overrides.get(provider, (None, None))

        # Fall back to common Microsoft credentials
        if not client_id:
            client_id = self.microsoft_client_id
        if not client_secret:
            client_secret = self.microsoft_client_secret

        return client_id, client_secret

    def get_scopes(self, provider: str) -> List[str]:
        """Get OAuth scopes for a provider."""
        scope_map = {
            "outlook": self.outlook_scopes,
            "sharepoint": self.sharepoint_scopes,
            "teams": self.teams_scopes,
            "azuredevops": self.azuredevops_scopes,
        }
        scope_str = scope_map.get(provider, "openid profile email offline_access")
        return scope_str.split()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Supported OAuth providers
MICROSOFT_PROVIDERS = {"outlook", "sharepoint", "teams", "azuredevops"}
ALL_PROVIDERS = MICROSOFT_PROVIDERS | {"snowflake"}
