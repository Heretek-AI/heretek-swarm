"""
Encryption utilities for API key encryption in configuration service.

Uses Fernet symmetric encryption to safely store API keys in the database.
"""

from __future__ import annotations

import base64
from typing import Any

import structlog

try:
    from cryptography.fernet import Fernet

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None

logger = structlog.get_logger("config.encryption")


class ApiKeyEncryptor:
    """
    Handles encryption and decryption of API keys.

    Uses Fernet symmetric encryption. The encryption key should be a
    32-byte URL-safe base64-encoded key. Generate with: Fernet.generate_key()
    """

    def __init__(self, encryption_key: str | None = None) -> None:
        """
        Initialize the encryptor.

        Args:
            encryption_key: The encryption key. If not provided, encryption
                is disabled (keys stored as-is).
        """
        self._fernet: Fernet | None = None
        self._encryption_key = encryption_key
        if self._encryption_key:
            self._initialize_encryption()
        else:
            logger.warning("CONFIG_ENCRYPTION_KEY not set - API keys will not be encrypted")

    def _initialize_encryption(self) -> None:
        """Initialize Fernet encryption."""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("cryptography package not installed - encryption disabled")
            return

        try:
            if len(self._encryption_key) == 44 and self._encryption_key.endswith("="):
                key = self._encryption_key.encode()
            else:
                key = base64.urlsafe_b64encode(self._encryption_key.encode().ljust(32))

            self._fernet = Fernet(key)
            logger.info("API key encryption initialized")
        except Exception as e:
            logger.error("Failed to initialize encryption", error=str(e))
            self._fernet = None

    @property
    def is_available(self) -> bool:
        """Check if encryption is available."""
        return self._fernet is not None

    def encrypt(self, api_key: str) -> str:
        """
        Encrypt an API key using Fernet symmetric encryption.

        Args:
            api_key: The plain text API key to encrypt

        Returns:
            Encrypted API key (base64 encoded)

        Raises:
            ValueError: If encryption is not configured
        """
        if not self._fernet:
            return api_key

        try:
            encrypted = self._fernet.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("Failed to encrypt API key", error=str(e))
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_key: str) -> str:
        """
        Decrypt an API key using Fernet symmetric encryption.

        Args:
            encrypted_key: The encrypted API key to decrypt

        Returns:
            Decrypted plain text API key

        Raises:
            ValueError: If decryption fails or encryption not configured
        """
        if not self._fernet:
            return encrypted_key

        try:
            decrypted = self._fernet.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("Failed to decrypt API key", error=str(e))
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Encrypt sensitive fields in a config dict.

        Encrypts fields like 'api_key', 'auth_token', 'secret' etc.
        """
        if not config:
            return {}

        sensitive_keys = {"api_key", "auth_token", "secret", "password", "credential"}
        encrypted = {}

        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value

        return encrypted

    def decrypt_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt sensitive fields in a config dict.
        """
        if not config:
            return {}

        sensitive_keys = {"api_key", "auth_token", "secret", "password", "credential"}
        decrypted = {}

        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except ValueError:
                    decrypted[key] = value
            else:
                decrypted[key] = value

        return decrypted


# Global encryptor instance
_encryptor: ApiKeyEncryptor | None = None


def get_encryptor() -> ApiKeyEncryptor:
    """Get or create the global encryptor instance."""
    global _encryptor
    if _encryptor is None:
        import os
        encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
        _encryptor = ApiKeyEncryptor(encryption_key)
    return _encryptor
