"""
OAuth State Management with Redis Backend

Provides secure, distributed storage for OAuth state parameters during authentication flows.

Security Features:
- CSRF protection via state parameter validation
- Automatic cleanup with TTL (15 minutes default)
- Thread-safe operations in multi-process environments
- Fallback to in-memory storage if Redis unavailable (dev only)

References:
- MCP 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- OAuth 2.1: State parameter for CSRF protection
"""

import json
import logging
import secrets
import time
from typing import Any, Dict, Optional

from mcp_oauth.exceptions import StateError, StateExpiredError, StateNotFoundError

log = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    from redis.exceptions import RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    log.warning(
        "Redis not available - OAuth state will use in-memory storage (NOT PRODUCTION SAFE)"
    )


class OAuthStateManager:
    """
    Manages OAuth state parameters with Redis backend.

    OAuth state is used for CSRF protection and storing temporary auth flow data.
    Each state:
    - Has a unique random ID (32 bytes, URL-safe)
    - Expires after 15 minutes (900 seconds) by default
    - Contains user_id, provider, redirect_uri, PKCE verifier, and flow data
    """

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 900):
        """
        Initialize OAuth state manager.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            ttl_seconds: Time-to-live for state entries (default: 900 = 15 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self._in_memory_fallback: Dict[str, Dict[str, Any]] = {}

        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                log.info(
                    "OAuth state manager initialized with Redis backend at %s",
                    redis_url.split("@")[-1] if "@" in redis_url else redis_url,
                )
            except Exception as e:
                log.error("Failed to connect to Redis for OAuth state: %s", e)
                log.warning(
                    "Falling back to in-memory OAuth state storage (NOT PRODUCTION SAFE)"
                )
                self.redis_client = None
        else:
            if not REDIS_AVAILABLE:
                log.warning(
                    "Redis library not installed - using in-memory OAuth state (NOT PRODUCTION SAFE)"
                )
            else:
                log.warning(
                    "No Redis URL provided - using in-memory OAuth state (NOT PRODUCTION SAFE)"
                )

    def _make_key(self, state: str) -> str:
        """Generate Redis key for OAuth state."""
        return f"mcp:oauth:state:{state}"

    def generate_state(self) -> str:
        """
        Generate a cryptographically secure random state parameter.

        Returns:
            URL-safe random string (64 characters)
        """
        return secrets.token_urlsafe(32)

    def store_state(self, state: str, data: Dict[str, Any]) -> bool:
        """
        Store OAuth state data.

        Args:
            state: Unique state parameter
            data: State data (user_id, provider, redirect_uri, code_verifier, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.redis_client:
                # Store in Redis with TTL
                key = self._make_key(state)
                value = json.dumps(data)
                self.redis_client.setex(key, self.ttl_seconds, value)
                log.debug(
                    "Stored OAuth state %s... in Redis with %ds TTL",
                    state[:10],
                    self.ttl_seconds,
                )
                return True
            else:
                # Fallback to in-memory (development only)
                self._in_memory_fallback[state] = {
                    **data,
                    "_expires_at": time.time() + self.ttl_seconds,
                }
                log.debug(
                    "Stored OAuth state %s... in memory (NOT PRODUCTION SAFE)",
                    state[:10],
                )
                return True
        except Exception as e:
            log.error("Failed to store OAuth state: %s", e)
            return False

    def get_state(self, state: str, delete_after: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth state data.

        Args:
            state: Unique state parameter
            delete_after: If True, delete state after retrieval (single-use)

        Returns:
            State data if found and not expired, None otherwise
        """
        try:
            if self.redis_client:
                # Retrieve from Redis
                key = self._make_key(state)
                value = self.redis_client.get(key)
                if value:
                    data = json.loads(value)
                    if delete_after:
                        self.redis_client.delete(key)
                        log.debug(
                            "Retrieved and deleted OAuth state %s... from Redis",
                            state[:10],
                        )
                    else:
                        log.debug(
                            "Retrieved OAuth state %s... from Redis", state[:10]
                        )
                    return data
                log.debug(
                    "OAuth state %s... not found in Redis (expired or invalid)",
                    state[:10],
                )
                return None
            else:
                # Fallback to in-memory
                if state in self._in_memory_fallback:
                    entry = self._in_memory_fallback[state]
                    # Check expiration
                    if time.time() < entry.get("_expires_at", 0):
                        # Remove internal fields
                        data = {k: v for k, v in entry.items() if not k.startswith("_")}
                        if delete_after:
                            del self._in_memory_fallback[state]
                            log.debug(
                                "Retrieved and deleted OAuth state %s... from memory",
                                state[:10],
                            )
                        else:
                            log.debug(
                                "Retrieved OAuth state %s... from memory", state[:10]
                            )
                        return data
                    else:
                        # Expired - remove it
                        del self._in_memory_fallback[state]
                        log.debug("OAuth state %s... expired (in-memory)", state[:10])
                return None
        except Exception as e:
            log.error("Failed to retrieve OAuth state: %s", e)
            return None

    def get_state_or_raise(self, state: str, delete_after: bool = True) -> Dict[str, Any]:
        """
        Retrieve OAuth state data or raise exception.

        Args:
            state: Unique state parameter
            delete_after: If True, delete state after retrieval (default: True for single-use)

        Returns:
            State data

        Raises:
            StateNotFoundError: If state not found
            StateExpiredError: If state has expired
        """
        data = self.get_state(state, delete_after=delete_after)
        if data is None:
            raise StateNotFoundError(state)
        return data

    def delete_state(self, state: str) -> bool:
        """
        Delete OAuth state data (cleanup after successful authentication).

        Args:
            state: Unique state parameter

        Returns:
            True if deleted, False if not found or error
        """
        try:
            if self.redis_client:
                key = self._make_key(state)
                deleted = self.redis_client.delete(key)
                if deleted:
                    log.debug("Deleted OAuth state %s... from Redis", state[:10])
                    return True
                log.debug("OAuth state %s... not found for deletion", state[:10])
                return False
            else:
                # Fallback to in-memory
                if state in self._in_memory_fallback:
                    del self._in_memory_fallback[state]
                    log.debug("Deleted OAuth state %s... from memory", state[:10])
                    return True
                return False
        except Exception as e:
            log.error("Failed to delete OAuth state: %s", e)
            return False

    def cleanup_expired(self) -> int:
        """
        Clean up expired state entries (in-memory only, Redis handles automatically via TTL).

        Returns:
            Number of entries cleaned up
        """
        if self.redis_client:
            # Redis handles cleanup automatically via TTL
            return 0

        # Clean up expired in-memory entries
        now = time.time()
        expired_keys = [
            k
            for k, v in self._in_memory_fallback.items()
            if now >= v.get("_expires_at", 0)
        ]

        for key in expired_keys:
            del self._in_memory_fallback[key]

        if expired_keys:
            log.debug("Cleaned up %d expired OAuth state entries", len(expired_keys))

        return len(expired_keys)

    def count_active_states(self) -> int:
        """
        Count active OAuth state entries (for monitoring/debugging).

        Returns:
            Number of active state entries
        """
        try:
            if self.redis_client:
                # Count keys matching pattern
                keys = self.redis_client.keys("mcp:oauth:state:*")
                return len(keys)
            else:
                # Count non-expired in-memory entries
                now = time.time()
                active = sum(
                    1
                    for v in self._in_memory_fallback.values()
                    if now < v.get("_expires_at", 0)
                )
                return active
        except Exception as e:
            log.error("Failed to count OAuth states: %s", e)
            return -1


# Global instance
_oauth_state_manager: Optional[OAuthStateManager] = None


def init_oauth_state_manager(
    redis_url: Optional[str] = None, ttl_seconds: int = 900
) -> OAuthStateManager:
    """
    Initialize the global OAuth state manager.

    Args:
        redis_url: Redis connection URL
        ttl_seconds: TTL for state entries (default: 15 minutes)

    Returns:
        OAuthStateManager instance
    """
    global _oauth_state_manager
    _oauth_state_manager = OAuthStateManager(redis_url, ttl_seconds)
    return _oauth_state_manager


def get_oauth_state_manager() -> OAuthStateManager:
    """
    Get the global OAuth state manager instance.

    Returns:
        OAuthStateManager instance

    Raises:
        RuntimeError: If manager not initialized
    """
    if _oauth_state_manager is None:
        raise RuntimeError(
            "OAuth state manager not initialized. Call init_oauth_state_manager() first."
        )
    return _oauth_state_manager


# Export main classes and functions
__all__ = [
    "OAuthStateManager",
    "init_oauth_state_manager",
    "get_oauth_state_manager",
]
