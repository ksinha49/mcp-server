"""
Microsoft OAuth Service

Handles OAuth 2.1 authorization flows for Microsoft providers:
- Outlook (Email, Calendar, Contacts)
- SharePoint (Documents, Sites)
- Teams (Chat, Channels, Meetings)
- Azure DevOps (Projects, Repos, Work Items)

Uses MSAL (Microsoft Authentication Library) for token acquisition.

References:
- MSAL Python: https://github.com/AzureAD/microsoft-authentication-library-for-python
- Microsoft Graph API: https://docs.microsoft.com/en-us/graph/overview
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from msal import ConfidentialClientApplication

from app.config import Settings
from mcp_oauth import (
    get_oauth_state_manager,
    generate_pkce_pair,
    encrypt_token,
)
from mcp_oauth.types import AuthInitResult, TokenResult

log = logging.getLogger(__name__)


@dataclass
class MicrosoftTokenResult:
    """Result of Microsoft token acquisition."""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class MicrosoftAuthService:
    """
    Microsoft OAuth service using MSAL.

    Implements OAuth 2.1 authorization code flow with PKCE for
    Microsoft providers (Outlook, SharePoint, Teams, Azure DevOps).
    """

    def __init__(self, provider: str, settings: Settings):
        """
        Initialize Microsoft auth service.

        Args:
            provider: Provider name (outlook, sharepoint, teams, azuredevops)
            settings: Application settings
        """
        self.provider = provider
        self.settings = settings

        # Get credentials for this provider
        self.client_id, self.client_secret = settings.get_microsoft_credentials(provider)
        self.tenant_id = settings.microsoft_tenant_id

        if not self.client_id or not self.client_secret:
            raise ValueError(f"Microsoft OAuth credentials not configured for {provider}")

        # Create MSAL app
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self._msal_app: Optional[ConfidentialClientApplication] = None

    @property
    def msal_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL application instance."""
        if self._msal_app is None:
            self._msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )
        return self._msal_app

    async def initiate_auth(
        self,
        user_id: str,
        redirect_uri: str,
        scopes: List[str],
    ) -> AuthInitResult:
        """
        Initiate Microsoft OAuth authorization flow.

        Creates PKCE pair, stores state, and returns authorization URL.

        Args:
            user_id: User identifier
            redirect_uri: Callback URL after authorization
            scopes: OAuth scopes to request

        Returns:
            AuthInitResult with authorization URL and state
        """
        state_manager = get_oauth_state_manager()

        # Generate PKCE pair
        code_verifier, code_challenge = generate_pkce_pair()

        # Initiate auth code flow using MSAL
        # MSAL handles PKCE internally when we provide state
        flow = self.msal_app.initiate_auth_code_flow(
            scopes=scopes,
            redirect_uri=redirect_uri,
        )

        if "error" in flow:
            raise Exception(f"MSAL error: {flow.get('error_description', flow.get('error'))}")

        # Extract state from flow
        state = flow.get("state", "")

        # Store state with user context and flow data
        state_data = {
            "user_id": user_id,
            "provider": self.provider,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "scopes": scopes,
            "flow": flow,  # Store entire flow for callback
            "created_at": int(time.time()),
        }

        if not state_manager.store_state(state, state_data):
            raise Exception("Failed to store OAuth state")

        # Get authorization URL
        auth_url = flow.get("auth_uri", "")

        log.info(
            "Initiated Microsoft OAuth for user %s, provider %s",
            user_id[:8] + "...",
            self.provider,
        )

        return AuthInitResult(
            authorization_url=auth_url,
            state=state,
            code_verifier=code_verifier,
        )

    async def handle_callback(
        self,
        code: str,
        state: str,
        state_data: Dict[str, Any],
    ) -> TokenResult:
        """
        Handle OAuth callback and exchange code for tokens.

        Args:
            code: Authorization code from callback
            state: State parameter
            state_data: Stored state data

        Returns:
            TokenResult with tokens or error
        """
        user_id = state_data.get("user_id", "")
        flow = state_data.get("flow", {})

        try:
            # Complete auth code flow using MSAL
            result = self.msal_app.acquire_token_by_auth_code_flow(
                auth_code_flow=flow,
                auth_response={"code": code, "state": state},
            )

            if "error" in result:
                log.error(
                    "Token acquisition failed: %s - %s",
                    result.get("error"),
                    result.get("error_description"),
                )
                return TokenResult(
                    success=False,
                    error=result.get("error"),
                    error_description=result.get("error_description"),
                )

            if "access_token" not in result:
                return TokenResult(
                    success=False,
                    error="no_token",
                    error_description="No access token in response",
                )

            # Extract token information
            access_token = result["access_token"]
            refresh_token = result.get("refresh_token")
            expires_in = result.get("expires_in", 3600)
            scope = " ".join(result.get("scope", []))

            # TODO: Store encrypted tokens in database
            # For now, just log success
            log.info(
                "Token acquired for user %s, provider %s, expires_in=%d",
                user_id[:8] + "...",
                self.provider,
                expires_in,
            )

            # Encrypt tokens before storage (when database is implemented)
            # encrypted_access = encrypt_token(access_token)
            # encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

            return TokenResult(
                success=True,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                scope=scope,
            )

        except Exception as e:
            log.exception("Token exchange failed: %s", e)
            return TokenResult(
                success=False,
                error="token_exchange_error",
                error_description=str(e),
            )

    async def refresh_token(
        self,
        refresh_token: str,
        scopes: Optional[List[str]] = None,
    ) -> TokenResult:
        """
        Refresh an access token using refresh token.

        Args:
            refresh_token: Refresh token
            scopes: Optional scopes to request (defaults to original scopes)

        Returns:
            TokenResult with new tokens
        """
        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=scopes or self.settings.get_scopes(self.provider),
            )

            if "error" in result:
                return TokenResult(
                    success=False,
                    error=result.get("error"),
                    error_description=result.get("error_description"),
                )

            return TokenResult(
                success=True,
                access_token=result.get("access_token"),
                refresh_token=result.get("refresh_token"),
                expires_in=result.get("expires_in", 3600),
                scope=" ".join(result.get("scope", [])),
            )

        except Exception as e:
            log.exception("Token refresh failed: %s", e)
            return TokenResult(
                success=False,
                error="refresh_error",
                error_description=str(e),
            )
