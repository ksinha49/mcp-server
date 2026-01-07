"""
Token Encryption Utilities

Provides AES-256-GCM encryption for secure token storage.
All tokens are encrypted before storage and decrypted on retrieval.

Security Features:
- AES-256-GCM authenticated encryption
- Random 96-bit IV per encryption
- Authentication tag to detect tampering
- Key derivation from environment variable
"""

import base64
import logging
import os
import secrets
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from mcp_oauth.exceptions import EncryptionError

log = logging.getLogger(__name__)

# Constants
IV_LENGTH = 12  # 96 bits for GCM
TAG_LENGTH = 16  # 128 bits authentication tag
KEY_LENGTH = 32  # 256 bits for AES-256


def derive_key(secret: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Derive an AES-256 key from a secret string using PBKDF2.

    Args:
        secret: Secret string (e.g., from environment variable)
        salt: Optional salt bytes. If not provided, generates new random salt.

    Returns:
        Tuple of (derived_key, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(secret.encode("utf-8"))
    return key, salt


def get_encryption_key() -> bytes:
    """
    Get the encryption key from environment variable.

    The key should be either:
    - A base64-encoded 32-byte key
    - A passphrase that will be derived using PBKDF2

    Returns:
        32-byte encryption key

    Raises:
        EncryptionError: If key is not configured or invalid
    """
    key_env = os.environ.get("TOKEN_ENCRYPTION_KEY")

    if not key_env:
        raise EncryptionError(
            "TOKEN_ENCRYPTION_KEY environment variable not set", operation="key_load"
        )

    # Try to decode as base64 first
    try:
        key = base64.b64decode(key_env)
        if len(key) == KEY_LENGTH:
            return key
    except Exception:
        pass

    # Treat as passphrase - derive key with fixed salt for consistency
    # In production, store the salt separately or use a proper key management system
    fixed_salt = b"mcp_oauth_token_encryption_salt_"[:16]
    key, _ = derive_key(key_env, fixed_salt)
    return key


def encrypt_token(plaintext: str, key: Optional[bytes] = None) -> str:
    """
    Encrypt a token string using AES-256-GCM.

    The output format is: base64(iv + ciphertext + tag)

    Args:
        plaintext: Token string to encrypt
        key: Optional encryption key. If not provided, uses TOKEN_ENCRYPTION_KEY env var.

    Returns:
        Base64-encoded encrypted token

    Raises:
        EncryptionError: If encryption fails
    """
    try:
        if key is None:
            key = get_encryption_key()

        # Generate random IV
        iv = secrets.token_bytes(IV_LENGTH)

        # Create cipher and encrypt
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

        # Combine IV + ciphertext (tag is appended by AESGCM)
        encrypted = iv + ciphertext

        # Base64 encode
        result = base64.b64encode(encrypted).decode("utf-8")

        log.debug("Encrypted token (length: %d -> %d)", len(plaintext), len(result))
        return result

    except EncryptionError:
        raise
    except Exception as e:
        log.error("Failed to encrypt token: %s", e)
        raise EncryptionError(f"Encryption failed: {e}", operation="encrypt") from e


def decrypt_token(encrypted: str, key: Optional[bytes] = None) -> str:
    """
    Decrypt an encrypted token string.

    Args:
        encrypted: Base64-encoded encrypted token (from encrypt_token)
        key: Optional encryption key. If not provided, uses TOKEN_ENCRYPTION_KEY env var.

    Returns:
        Decrypted token string

    Raises:
        EncryptionError: If decryption fails (invalid key, tampered data, etc.)
    """
    try:
        if key is None:
            key = get_encryption_key()

        # Base64 decode
        data = base64.b64decode(encrypted)

        # Extract IV and ciphertext
        iv = data[:IV_LENGTH]
        ciphertext = data[IV_LENGTH:]

        # Decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)

        result = plaintext.decode("utf-8")
        log.debug("Decrypted token (length: %d -> %d)", len(encrypted), len(result))
        return result

    except EncryptionError:
        raise
    except Exception as e:
        log.error("Failed to decrypt token: %s", e)
        raise EncryptionError(f"Decryption failed: {e}", operation="decrypt") from e


def try_decrypt_token(
    encrypted: str, key: Optional[bytes] = None, fallback: Optional[str] = None
) -> Optional[str]:
    """
    Try to decrypt a token, returning fallback value on failure.

    Useful for handling legacy unencrypted tokens during migration.

    Args:
        encrypted: Possibly encrypted token string
        key: Optional encryption key
        fallback: Value to return on failure (default: the original string)

    Returns:
        Decrypted token, or fallback/original on failure
    """
    try:
        return decrypt_token(encrypted, key)
    except EncryptionError:
        if fallback is not None:
            return fallback
        # Assume it might be plaintext (legacy token)
        log.warning("Failed to decrypt token - returning as plaintext (may be legacy)")
        return encrypted


def generate_encryption_key() -> str:
    """
    Generate a new random encryption key suitable for TOKEN_ENCRYPTION_KEY.

    Returns:
        Base64-encoded 32-byte key
    """
    key = secrets.token_bytes(KEY_LENGTH)
    return base64.b64encode(key).decode("utf-8")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted (base64 encoded with expected length).

    This is a heuristic check - it doesn't guarantee the value is properly encrypted.

    Args:
        value: String to check

    Returns:
        True if value appears to be encrypted
    """
    try:
        decoded = base64.b64decode(value)
        # Minimum length: IV (12) + tag (16) + at least 1 byte of data
        return len(decoded) >= IV_LENGTH + TAG_LENGTH + 1
    except Exception:
        return False


__all__ = [
    "encrypt_token",
    "decrypt_token",
    "try_decrypt_token",
    "get_encryption_key",
    "generate_encryption_key",
    "is_encrypted",
    "derive_key",
]
