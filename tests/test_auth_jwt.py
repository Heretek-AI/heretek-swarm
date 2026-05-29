"""Tests for JWT token creation and verification in auth.py.

Covers:
- Roundtrip: create → verify
- Expired token rejection
- Invalid signature rejection
- Startup validation in production mode with missing JWT_SECRET
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from heretek_swarm.gateway.auth import (
    create_jwt_token,
    verify_jwt,
)

pytestmark = [pytest.mark.unit]

# 32+ byte secrets required by PyJWT ≥2.8 for HS256 (RFC 7518 §3.2)
_SECRET = "test-secret-" + "x" * 20  # 32 chars
_SECRET_OTHER = "wrong-key-" + "x" * 22  # 32 chars


class TestCreateJwtRoundtrip:
    """create_jwt_token → verify_jwt should return the username."""

    def test_create_jwt_roundtrip(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JWT_SECRET", _SECRET)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        token = create_jwt_token("alice", expiry_hours=1)
        assert isinstance(token, str)
        assert token.count(".") == 2  # standard JWT has 3 segments

        username = verify_jwt(token)
        assert username == "alice"


class TestJwtExpired:
    """verify_jwt returns None for an expired token."""

    def test_jwt_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JWT_SECRET", _SECRET)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        # Create a token that expired 1 hour ago
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "bob",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, _SECRET, algorithm="HS256")

        result = verify_jwt(expired_token)
        assert result is None


class TestJwtInvalidSignature:
    """verify_jwt returns None for a token with an invalid signature."""

    def test_jwt_invalid_signature(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JWT_SECRET", _SECRET)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        # Create a token signed with a different secret
        payload = {
            "sub": "eve",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        tampered_token = jwt.encode(payload, _SECRET_OTHER, algorithm="HS256")

        result = verify_jwt(tampered_token)
        assert result is None

    def test_jwt_invalid_signature_tampered_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tampering the payload after signing also fails."""
        monkeypatch.setenv("JWT_SECRET", _SECRET)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        token = create_jwt_token("mallory", expiry_hours=1)
        # Tamper with the payload segment
        parts = token.split(".")
        tampered_payload = jwt.encode(
            {
                "sub": "hacker",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            _SECRET,
            algorithm="HS256",
        ).split(".")[1]
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        result = verify_jwt(tampered_token)
        assert result is None


class TestMissingJwtSecretProduction:
    """Startup validation rejects missing JWT_SECRET in production."""

    def test_missing_jwt_secret_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("JWT_SECRET", raising=False)

        from heretek_swarm.gateway.auth import _get_jwt_secret

        with pytest.raises(RuntimeError, match="JWT_SECRET required in production"):
            _get_jwt_secret()

    def test_missing_jwt_secret_development_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In development, missing JWT_SECRET uses a default (no error)."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("JWT_SECRET", raising=False)

        from heretek_swarm.gateway.auth import _get_jwt_secret

        secret = _get_jwt_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0


class TestJwtEmptySub:
    """verify_jwt returns None for tokens with empty/missing sub claim."""

    def test_empty_sub(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JWT_SECRET", _SECRET)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        payload = {
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token_no_sub = jwt.encode(payload, _SECRET, algorithm="HS256")

        result = verify_jwt(token_no_sub)
        assert result is None
