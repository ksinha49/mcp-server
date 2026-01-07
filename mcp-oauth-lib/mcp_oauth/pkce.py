"""
OAuth 2.1 with PKCE (Proof Key for Code Exchange) Implementation

Implements RFC 7636 PKCE for OAuth 2.1 compliance, preventing authorization code
interception attacks in public clients and enhancing security for confidential clients.

Security Features:
- S256 (SHA-256) code challenge method (most secure)
- Cryptographically secure random code_verifier generation
- Automatic code_challenge generation from verifier
- Support for both confidential and public OAuth clients
- Compliant with OAuth 2.1 security best practices

References:
- RFC 7636: Proof Key for Code Exchange by OAuth Public Clients
- OAuth 2.1 Draft: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-10
- MCP 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
"""

import base64
import hashlib
import logging
import re
import secrets
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

log = logging.getLogger(__name__)

# PKCE configuration constants
PKCE_CODE_VERIFIER_LENGTH = 128  # RFC 7636 recommends 128 bytes for maximum entropy
PKCE_CODE_VERIFIER_MIN_LENGTH = 43  # RFC 7636 minimum
PKCE_CODE_VERIFIER_MAX_LENGTH = 128  # RFC 7636 maximum
PKCE_CODE_CHALLENGE_METHOD = "S256"  # SHA-256 (most secure, required by OAuth 2.1)


class PKCEError(Exception):
    """Base exception for PKCE-related errors."""

    pass


class PKCECodeVerifierError(PKCEError):
    """Error in code_verifier generation or validation."""

    pass


class PKCECodeChallengeError(PKCEError):
    """Error in code_challenge generation."""

    pass


def generate_code_verifier(length: int = PKCE_CODE_VERIFIER_LENGTH) -> str:
    """
    Generate a cryptographically secure code_verifier for PKCE.

    The code_verifier is a high-entropy cryptographic random string using the
    unreserved characters [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"

    Args:
        length: Length of the code_verifier (default: 128, min: 43, max: 128)

    Returns:
        URL-safe random string suitable for use as code_verifier

    Raises:
        PKCECodeVerifierError: If length is invalid

    Security Notes:
        - Uses secrets.token_urlsafe() for cryptographically secure randomness
        - Length of 128 provides maximum entropy (96 bytes of entropy)
        - Result is URL-safe base64 without padding (unreserved characters only)

    Example:
        >>> verifier = generate_code_verifier()
        >>> len(verifier)  # Approximately 128 characters
        128
    """
    # Validate length
    if not isinstance(length, int):
        raise PKCECodeVerifierError(
            f"Code verifier length must be an integer, got {type(length).__name__}"
        )

    if length < PKCE_CODE_VERIFIER_MIN_LENGTH:
        raise PKCECodeVerifierError(
            f"Code verifier length must be at least {PKCE_CODE_VERIFIER_MIN_LENGTH} characters "
            f"(RFC 7636 requirement), got {length}"
        )

    if length > PKCE_CODE_VERIFIER_MAX_LENGTH:
        raise PKCECodeVerifierError(
            f"Code verifier length must not exceed {PKCE_CODE_VERIFIER_MAX_LENGTH} characters "
            f"(RFC 7636 requirement), got {length}"
        )

    try:
        # Generate URL-safe random string
        # secrets.token_urlsafe generates base64-encoded random bytes
        # We need approximately length * 0.75 bytes to get 'length' base64 characters
        num_bytes = (length * 3) // 4

        # Generate the random string
        verifier = secrets.token_urlsafe(num_bytes)

        # Trim to exact length (token_urlsafe may return slightly longer strings)
        verifier = verifier[:length]

        # Ensure we have at least the minimum length
        while len(verifier) < length:
            verifier += secrets.token_urlsafe(num_bytes)[: length - len(verifier)]

        log.debug("Generated code_verifier with length %d", len(verifier))
        return verifier

    except Exception as e:
        log.error("Failed to generate code_verifier: %s", e)
        raise PKCECodeVerifierError(f"Failed to generate code_verifier: {e}") from e


def generate_code_challenge(
    code_verifier: str, method: str = PKCE_CODE_CHALLENGE_METHOD
) -> str:
    """
    Generate a code_challenge from a code_verifier using the specified method.

    OAuth 2.1 requires S256 (SHA-256) method for security. The "plain" method
    is deprecated and should not be used.

    Args:
        code_verifier: The code_verifier string (from generate_code_verifier)
        method: Challenge method - "S256" (SHA-256, recommended) or "plain" (deprecated)

    Returns:
        URL-safe base64-encoded code_challenge

    Raises:
        PKCECodeChallengeError: If code_verifier is invalid or method is unsupported

    Security Notes:
        - S256 method uses SHA-256 hash + base64url encoding
        - "plain" method is deprecated by OAuth 2.1 and NOT recommended
        - Challenge is URL-safe base64 without padding

    Example:
        >>> verifier = generate_code_verifier()
        >>> challenge = generate_code_challenge(verifier)
        >>> len(challenge)  # SHA-256 base64url output is 43 characters
        43
    """
    # Validate code_verifier
    if not code_verifier or not isinstance(code_verifier, str):
        raise PKCECodeChallengeError("code_verifier must be a non-empty string")

    verifier_len = len(code_verifier)
    if (
        verifier_len < PKCE_CODE_VERIFIER_MIN_LENGTH
        or verifier_len > PKCE_CODE_VERIFIER_MAX_LENGTH
    ):
        raise PKCECodeChallengeError(
            f"code_verifier length must be between {PKCE_CODE_VERIFIER_MIN_LENGTH} and "
            f"{PKCE_CODE_VERIFIER_MAX_LENGTH} characters (RFC 7636), got {verifier_len}"
        )

    try:
        if method == "S256":
            # S256: BASE64URL(SHA256(ASCII(code_verifier)))
            # This is the REQUIRED method for OAuth 2.1
            verifier_bytes = code_verifier.encode("ascii")
            sha256_hash = hashlib.sha256(verifier_bytes).digest()

            # Base64url encode (URL-safe base64 without padding)
            challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")

            log.debug("Generated code_challenge using S256 method")
            return challenge

        elif method == "plain":
            # Plain method: code_challenge = code_verifier
            # DEPRECATED: OAuth 2.1 prohibits this method
            log.warning(
                "SECURITY WARNING: Using 'plain' PKCE method - DEPRECATED by OAuth 2.1"
            )
            return code_verifier

        else:
            raise PKCECodeChallengeError(
                f"Unsupported code_challenge_method: '{method}'. "
                f"Supported methods: 'S256' (recommended), 'plain' (deprecated)"
            )

    except PKCECodeChallengeError:
        raise
    except Exception as e:
        log.error("Failed to generate code_challenge: %s", e)
        raise PKCECodeChallengeError(f"Failed to generate code_challenge: {e}") from e


def generate_pkce_pair(
    verifier_length: int = PKCE_CODE_VERIFIER_LENGTH,
    challenge_method: str = PKCE_CODE_CHALLENGE_METHOD,
) -> Tuple[str, str]:
    """
    Generate a complete PKCE pair (code_verifier, code_challenge).

    Convenience function that combines generate_code_verifier() and
    generate_code_challenge() for OAuth 2.1 authorization flows.

    Args:
        verifier_length: Length of code_verifier (default: 128)
        challenge_method: Method for code_challenge (default: "S256")

    Returns:
        Tuple of (code_verifier, code_challenge)

    Raises:
        PKCEError: If PKCE pair generation fails

    Security Notes:
        - OAuth 2.1 requires S256 method (default)
        - code_verifier must be stored securely and sent during token exchange
        - code_challenge is sent with authorization request

    Example:
        >>> verifier, challenge = generate_pkce_pair()
        >>> len(verifier), len(challenge)
        (128, 43)
    """
    try:
        # Generate code_verifier
        code_verifier = generate_code_verifier(length=verifier_length)

        # Generate code_challenge
        code_challenge = generate_code_challenge(code_verifier, method=challenge_method)

        log.debug(
            "Generated PKCE pair: verifier_length=%d, challenge_length=%d, method=%s",
            len(code_verifier),
            len(code_challenge),
            challenge_method,
        )

        return code_verifier, code_challenge

    except (PKCECodeVerifierError, PKCECodeChallengeError) as e:
        log.error("Failed to generate PKCE pair: %s", e)
        raise PKCEError(f"Failed to generate PKCE pair: {e}") from e


def build_authorization_url_with_pkce(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str,
    challenge_method: str = PKCE_CODE_CHALLENGE_METHOD,
    extra_params: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build an OAuth 2.1 authorization URL with PKCE parameters.

    Constructs a complete authorization URL with all required OAuth 2.1 parameters
    including PKCE code_challenge and code_challenge_method.

    Args:
        authorization_endpoint: OAuth provider's authorization URL
        client_id: OAuth client identifier
        redirect_uri: Callback URL for OAuth redirect
        scope: Space-separated list of requested scopes
        state: CSRF protection state parameter
        code_challenge: PKCE code_challenge (from generate_code_challenge)
        challenge_method: PKCE method (default: "S256")
        extra_params: Optional additional query parameters

    Returns:
        Complete authorization URL with query parameters

    Security Notes:
        - state parameter provides CSRF protection (must be validated in callback)
        - code_challenge prevents authorization code interception attacks
        - code_challenge_method MUST be S256 for OAuth 2.1 compliance

    Example:
        >>> verifier, challenge = generate_pkce_pair()
        >>> url = build_authorization_url_with_pkce(
        ...     "https://oauth.provider.com/authorize",
        ...     "my_client_id",
        ...     "https://myapp.com/callback",
        ...     "openid profile",
        ...     "random_state_123",
        ...     challenge
        ... )
        >>> "code_challenge=" in url and "code_challenge_method=S256" in url
        True
    """
    # Parse the authorization endpoint to preserve existing query parameters
    parsed = urlparse(authorization_endpoint)
    existing_params = parse_qs(parsed.query) if parsed.query else {}

    # Build query parameters
    params = {
        "client_id": client_id,
        "response_type": "code",  # OAuth 2.1 authorization code flow
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": challenge_method,
    }

    # Add extra parameters if provided
    if extra_params:
        params.update(extra_params)

    # Merge with existing parameters (new params take precedence)
    for key, value in existing_params.items():
        if key not in params:
            # Use first value from parse_qs (which returns lists)
            params[key] = value[0] if isinstance(value, list) and value else value

    # Build query string
    query_string = urlencode(params)

    # Reconstruct URL
    url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            parsed.fragment,
        )
    )

    log.debug(
        "Built authorization URL with PKCE: endpoint=%s, client_id=%s",
        authorization_endpoint,
        client_id,
    )

    return url


def build_token_request_with_pkce(
    code: str,
    code_verifier: str,
    client_id: str,
    redirect_uri: str,
    client_secret: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build token exchange request parameters with PKCE code_verifier.

    Creates the request body for exchanging an authorization code for an access token,
    including the PKCE code_verifier for verification.

    Args:
        code: Authorization code from OAuth callback
        code_verifier: PKCE code_verifier (generated during authorization)
        client_id: OAuth client identifier
        redirect_uri: Callback URL (must match authorization request)
        client_secret: Optional client secret (for confidential clients)

    Returns:
        Dictionary of token request parameters

    Security Notes:
        - code_verifier MUST match the original verifier used to generate code_challenge
        - client_secret is optional for public clients (PKCE provides security)
        - code_verifier is sent in request body, NOT in URL
        - OAuth 2.1 requires PKCE even for confidential clients

    Example:
        >>> verifier, challenge = generate_pkce_pair()
        >>> # ... complete authorization flow, receive code ...
        >>> token_params = build_token_request_with_pkce(
        ...     code="auth_code_xyz",
        ...     code_verifier=verifier,
        ...     client_id="my_client",
        ...     redirect_uri="https://myapp.com/callback"
        ... )
        >>> token_params["grant_type"]
        'authorization_code'
        >>> "code_verifier" in token_params
        True
    """
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,  # PKCE verification parameter
    }

    # Add client_secret if provided (for confidential clients)
    # OAuth 2.1 requires PKCE even for confidential clients (defense in depth)
    if client_secret:
        params["client_secret"] = client_secret
        log.debug("Token request includes client_secret (confidential client with PKCE)")
    else:
        log.debug("Token request uses PKCE only (public client)")

    return params


def validate_code_verifier(code_verifier: str) -> bool:
    """
    Validate a code_verifier string according to RFC 7636 requirements.

    Checks that the code_verifier:
    - Is a string
    - Has correct length (43-128 characters)
    - Contains only unreserved characters [A-Za-z0-9._~-]

    Args:
        code_verifier: The code_verifier to validate

    Returns:
        True if valid, False otherwise

    Security Notes:
        - This performs format validation only
        - Does NOT verify that verifier matches challenge (server does that)
        - Use during development/debugging to catch invalid verifiers early

    Example:
        >>> verifier = generate_code_verifier()
        >>> validate_code_verifier(verifier)
        True
        >>> validate_code_verifier("too_short")
        False
    """
    if not isinstance(code_verifier, str):
        log.warning(
            "Code verifier validation failed: not a string (type=%s)",
            type(code_verifier).__name__,
        )
        return False

    verifier_len = len(code_verifier)
    if (
        verifier_len < PKCE_CODE_VERIFIER_MIN_LENGTH
        or verifier_len > PKCE_CODE_VERIFIER_MAX_LENGTH
    ):
        log.warning(
            "Code verifier validation failed: invalid length %d (must be %d-%d)",
            verifier_len,
            PKCE_CODE_VERIFIER_MIN_LENGTH,
            PKCE_CODE_VERIFIER_MAX_LENGTH,
        )
        return False

    # RFC 7636: unreserved characters = [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
    unreserved_pattern = re.compile(r"^[A-Za-z0-9._~-]+$")
    if not unreserved_pattern.match(code_verifier):
        log.warning(
            "Code verifier validation failed: contains invalid characters (must be [A-Za-z0-9._~-])"
        )
        return False

    log.debug("Code verifier validation passed: length=%d", verifier_len)
    return True


def verify_code_challenge(code_challenge: str, code_verifier: str) -> bool:
    """
    Verify that a code_challenge matches a code_verifier.

    This is used server-side during token exchange to verify PKCE.

    Args:
        code_challenge: The code_challenge from the authorization request
        code_verifier: The code_verifier from the token request

    Returns:
        True if the code_verifier produces the given code_challenge

    Example:
        >>> verifier, challenge = generate_pkce_pair()
        >>> verify_code_challenge(challenge, verifier)
        True
    """
    try:
        expected_challenge = generate_code_challenge(code_verifier, method="S256")
        return secrets.compare_digest(code_challenge, expected_challenge)
    except PKCECodeChallengeError:
        return False


# Export main functions
__all__ = [
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_pkce_pair",
    "build_authorization_url_with_pkce",
    "build_token_request_with_pkce",
    "validate_code_verifier",
    "verify_code_challenge",
    "PKCEError",
    "PKCECodeVerifierError",
    "PKCECodeChallengeError",
    "PKCE_CODE_VERIFIER_LENGTH",
    "PKCE_CODE_VERIFIER_MIN_LENGTH",
    "PKCE_CODE_VERIFIER_MAX_LENGTH",
    "PKCE_CODE_CHALLENGE_METHOD",
]
