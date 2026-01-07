"""
Configuration for Teams MCP Server
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8003)
    log_level: str = Field(default="INFO")

    oauth_gateway_url: Optional[str] = Field(default=None)
    microsoft_client_id: str = Field(default="")
    microsoft_client_secret: str = Field(default="")
    microsoft_tenant_id: str = Field(default="common")
    token_encryption_key: Optional[str] = Field(default=None)
    resource_uri: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
