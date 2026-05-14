"""Tests for ApiKeyEncryptor file-based key persistence and encryption.

All tests use tempfile for key paths — no Docker or external services needed.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from cryptography.fernet import Fernet

from heretek_swarm.config.encryption import (  # type: ignore[import-untyped]
    ApiKeyEncryptor,
    _read_key_file,
    _write_key_file,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def temp_key_path(monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Create a temp directory and redirect _KEY_PATH to it.

    Each test gets a clean temp dir; the key file does not exist initially.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = str(Path(tmpdir) / "encryption.key")
        monkeypatch.setattr(
            "heretek_swarm.config.encryption._KEY_PATH", key_path
        )
        yield key_path


# ── Happy-path tests ────────────────────────────────────────────────────────


def test_no_arg_constructor_generates_key(temp_key_path: str) -> None:
    """No-arg constructor generates a key file when none exists."""
    key_file = Path(temp_key_path)
    assert not key_file.is_file()

    encryptor = ApiKeyEncryptor()

    assert encryptor.is_available
    assert key_file.is_file()
    # Key file exists and contains data (permissions are platform-dependent;
    # 0o600 is enforced on Unix via os.open, advisory-only on Windows)
    assert key_file.stat().st_size > 0


def test_encrypt_decrypt_round_trip(temp_key_path: str) -> None:
    """encrypt/decrypt round-trip preserves original plaintext."""
    encryptor = ApiKeyEncryptor()

    plaintext = "sk-test-secret-api-key-12345"
    ciphertext = encryptor.encrypt(plaintext)

    assert ciphertext != plaintext
    assert encryptor.decrypt(ciphertext) == plaintext


def test_encrypt_decrypt_special_characters(temp_key_path: str) -> None:
    """encrypt/decrypt handles special chars and unicode."""
    encryptor = ApiKeyEncryptor()

    special = "🔑key!@#$%^&*()\n\t\r\0stuff"
    ciphertext = encryptor.encrypt(special)
    assert encryptor.decrypt(ciphertext) == special


def test_encrypt_empty_string(temp_key_path: str) -> None:
    """encrypt/decrypt handles empty string."""
    encryptor = ApiKeyEncryptor()

    ciphertext = encryptor.encrypt("")
    assert encryptor.decrypt(ciphertext) == ""


def test_file_based_key_loading_persistence(temp_key_path: str) -> None:
    """Key survives across separate ApiKeyEncryptor instances (simulates restart)."""
    # First instance generates and persists the key
    e1 = ApiKeyEncryptor()
    plaintext = "survive-restart-test-key"
    ciphertext = e1.encrypt(plaintext)

    # Second instance loads the key from disk
    e2 = ApiKeyEncryptor()
    assert e2.is_available
    assert e2.decrypt(ciphertext) == plaintext


def test_encrypt_config_and_decrypt_config(temp_key_path: str) -> None:
    """encrypt_config/decrypt_config handle sensitive fields correctly."""
    encryptor = ApiKeyEncryptor()

    config = {
        "openai_api_key": "sk-openai-secret",
        "model_name": "gpt-4",
        "auth_token": "bearer-token-123",
        "secret": "super-secret",
        "password": "pw123",
        "credential": "cred-data",
        "non_sensitive": "public-value",
    }

    encrypted_config = encryptor.encrypt_config(config)

    # Sensitive keys should be encrypted (changed from original)
    for sensitive in ("openai_api_key", "auth_token", "secret", "password", "credential"):
        assert encrypted_config[sensitive] != config[sensitive]

    # Non-sensitive keys should be unchanged
    assert encrypted_config["model_name"] == "gpt-4"
    assert encrypted_config["non_sensitive"] == "public-value"

    # decrypt_config restores original sensitive values
    decrypted_config = encryptor.decrypt_config(encrypted_config)
    for key in config:
        assert decrypted_config[key] == config[key]


def test_encrypt_config_empty(temp_key_path: str) -> None:
    """encrypt_config/decrypt_config handle empty dicts."""
    encryptor = ApiKeyEncryptor()
    assert encryptor.encrypt_config({}) == {}
    assert encryptor.decrypt_config({}) == {}


# ── Fernet-not-initialized tests ────────────────────────────────────────────


def test_encrypt_raises_valueerror_when_fernet_none(temp_key_path: str) -> None:
    """encrypt raises ValueError when _fernet is forced to None (simulates init failure)."""
    encryptor = ApiKeyEncryptor()
    encryptor._fernet = None

    with pytest.raises(ValueError, match="Encryption not available"):
        encryptor.encrypt("test-key")


def test_decrypt_raises_valueerror_when_fernet_none(temp_key_path: str) -> None:
    """decrypt raises ValueError when _fernet is forced to None (simulates init failure)."""
    encryptor = ApiKeyEncryptor()
    encryptor._fernet = None

    with pytest.raises(ValueError, match="Encryption not available"):
        encryptor.decrypt("some-ciphertext")


# ── Corrupt key file tests ──────────────────────────────────────────────────


def test_runtime_error_on_corrupt_key_file(temp_key_path: str) -> None:
    """RuntimeError is raised when the persisted key file contains invalid bytes."""
    # Write garbage to the key file
    Path(temp_key_path).write_bytes(b"this-is-not-a-valid-fernet-key!!!")

    with pytest.raises(
        RuntimeError, match="Encryption key validation failed"
    ):
        ApiKeyEncryptor()


def test_runtime_error_on_truncated_key_file(temp_key_path: str) -> None:
    """RuntimeError is raised when the key file is truncated."""
    Path(temp_key_path).write_bytes(b"too-short")

    with pytest.raises(
        RuntimeError, match="Encryption key validation failed"
    ):
        ApiKeyEncryptor()


def test_runtime_error_on_empty_key_file(temp_key_path: str) -> None:
    """RuntimeError is raised when the key file is empty."""
    Path(temp_key_path).touch()

    with pytest.raises(
        RuntimeError, match="Encryption key validation failed"
    ):
        ApiKeyEncryptor()


# ── Low-level helper tests ──────────────────────────────────────────────────


def test_write_and_read_key_file_round_trip(temp_key_path: str) -> None:
    """_write_key_file and _read_key_file round-trip correctly."""
    key_bytes = Fernet.generate_key()
    _write_key_file(temp_key_path, key_bytes)

    read_bytes = _read_key_file(temp_key_path)
    assert read_bytes == key_bytes


def test_write_key_file_permissions(temp_key_path: str) -> None:
    """_write_key_file creates file; permissions are platform-dependent."""
    _write_key_file(temp_key_path, Fernet.generate_key())

    key_file = Path(temp_key_path)
    assert key_file.is_file()
    assert key_file.stat().st_size > 0
