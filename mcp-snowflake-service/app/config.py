"""
Configuration for Snowflake MCP Server
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8005)
    log_level: str = Field(default="INFO")

    oauth_gateway_url: Optional[str] = Field(default=None)

    # Snowflake connection settings
    snowflake_account: str = Field(default="")
    snowflake_warehouse: str = Field(default="COMPUTE_WH")
    snowflake_database: Optional[str] = Field(default=None)
    snowflake_schema: Optional[str] = Field(default=None)
    snowflake_role: Optional[str] = Field(default=None)

    # Auth: OAuth (preferred)
    snowflake_oauth_client_id: Optional[str] = Field(default=None)
    snowflake_oauth_client_secret: Optional[str] = Field(default=None)
    snowflake_oauth_token_endpoint: Optional[str] = Field(default=None)

    # Auth: Key-pair (fallback)
    snowflake_user: Optional[str] = Field(default=None)
    snowflake_private_key_path: Optional[str] = Field(default=None)
    snowflake_private_key_passphrase: Optional[str] = Field(default=None)

    # Auth: Username/password (development only)
    snowflake_password: Optional[str] = Field(default=None)

    token_encryption_key: Optional[str] = Field(default=None)
    resource_uri: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
