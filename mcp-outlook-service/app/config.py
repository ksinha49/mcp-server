"""
Configuration for Outlook MCP Server

Loads settings from environment variables.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    log_level: str = Field(default="INFO")

    # OAuth Gateway
    oauth_gateway_url: Optional[str] = Field(
        default=None,
        description="URL of the MCP OAuth Gateway",
    )

    # Microsoft credentials (can be overridden by OAuth gateway)
    microsoft_client_id: str = Field(default="")
    microsoft_client_secret: str = Field(default="")
    microsoft_tenant_id: str = Field(default="common")

    # Token encryption (for storing delegated tokens)
    token_encryption_key: Optional[str] = Field(default=None)

    # Resource server identity
    resource_uri: Optional[str] = Field(
        default=None,
        description="URI of this MCP server for audience validation",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
