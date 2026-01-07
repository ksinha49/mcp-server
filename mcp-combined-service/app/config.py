"""
Configuration for Combined MCP Server
"""

from functools import lru_cache
from typing import List, Optional, Set

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings for combined server."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # Enabled providers (comma-separated)
    enabled_providers: str = Field(default="outlook,sharepoint,teams,azuredevops,snowflake")

    oauth_gateway_url: Optional[str] = Field(default=None)

    # Microsoft OAuth (for Outlook, SharePoint, Teams, Azure DevOps)
    microsoft_client_id: str = Field(default="")
    microsoft_client_secret: str = Field(default="")
    microsoft_tenant_id: str = Field(default="common")

    # Azure DevOps specific
    azdo_organization_url: str = Field(default="")
    azdo_pat: Optional[str] = Field(default=None)

    # Snowflake
    snowflake_account: str = Field(default="")
    snowflake_warehouse: str = Field(default="COMPUTE_WH")
    snowflake_database: Optional[str] = Field(default=None)
    snowflake_schema: Optional[str] = Field(default=None)
    snowflake_role: Optional[str] = Field(default=None)
    snowflake_user: Optional[str] = Field(default=None)
    snowflake_password: Optional[str] = Field(default=None)
    snowflake_private_key_path: Optional[str] = Field(default=None)
    snowflake_private_key_passphrase: Optional[str] = Field(default=None)
    snowflake_oauth_client_id: Optional[str] = Field(default=None)
    snowflake_oauth_client_secret: Optional[str] = Field(default=None)

    token_encryption_key: Optional[str] = Field(default=None)
    resource_uri: Optional[str] = Field(default=None)

    # Code Execution Settings
    code_execution_enabled: bool = Field(default=False)
    sandbox_mode: str = Field(default="deno")  # "deno" or "docker"
    deno_server_port: int = Field(default=8001)
    docker_pool_size: int = Field(default=5)
    docker_executor_image: str = Field(default="mcp-code-executor:latest")
    max_execution_time_ms: int = Field(default=60000)
    max_memory_mb: int = Field(default=128)
    rate_limit_per_minute: int = Field(default=30)

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_enabled_providers(self) -> Set[str]:
        """Get set of enabled provider names."""
        return set(p.strip().lower() for p in self.enabled_providers.split(",") if p.strip())


@lru_cache()
def get_settings() -> Settings:
    return Settings()
