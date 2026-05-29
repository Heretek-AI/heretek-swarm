"""
Unit tests for verify_auth static-key and JWT-precedence behaviour.

Covers:
- Missing credentials → HTTP 401
- Invalid static key → HTTP 401
- Valid static key → "authenticated"
- JWT takes precedence over differing static key
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from heretek_swarm.gateway.auth import verify_auth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    """Build an HTTPAuthorizationCredentials with the given Bearer token."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


# ---------------------------------------------------------------------------
# Missing credentials
# ---------------------------------------------------------------------------


class TestMissingCredentials:
    async def test_missing_credentials_raises_401(self) -> None:
        """verify_auth(credentials=None) raises HTTPException with 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Missing authentication credentials" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


# ---------------------------------------------------------------------------
# Invalid static key
# ---------------------------------------------------------------------------


class TestInvalidStaticKey:
    async def test_invalid_static_key_raises_401(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pass a wrong Bearer token when HERETEK_API_KEY is set → 401."""
        monkeypatch.setenv("HERETEK_API_KEY", "htsk_correct-key-value")
        monkeypatch.delenv("JWT_SECRET", raising=False)  # Ensure JWT won't match
        monkeypatch.setenv("ENVIRONMENT", "development")

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth(credentials=_credentials("wrong-token"))

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


# ---------------------------------------------------------------------------
# Valid static key
# ---------------------------------------------------------------------------


class TestValidStaticKey:
    async def test_valid_static_key_returns_authenticated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pass the exact HERETEK_API_KEY value → returns 'authenticated'."""
        monkeypatch.setenv("HERETEK_API_KEY", "htsk_my-secret-key-value")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")

        result = await verify_auth(credentials=_credentials("htsk_my-secret-key-value"))
        assert result == "authenticated"


# ---------------------------------------------------------------------------
# JWT takes precedence over static key
# ---------------------------------------------------------------------------


class TestJwtPrecedenceOverStatic:
    async def test_jwt_takes_precedence_over_different_static_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JWT valid even when HERETEK_API_KEY holds a different value.

        The auth layer tries JWT first; if it decodes successfully the static
        key fallback is never reached.  This guarantees that a valid JWT works
        regardless of the current HERETEK_API_KEY.
        """
        monkeypatch.setenv(
            "JWT_SECRET", "test-jwt-secret-for-precedence-32"
        )
        monkeypatch.setenv("HERETEK_API_KEY", "htsk_different-static-key")
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        # Create a fresh JWT with the current JWT_SECRET
        from heretek_swarm.gateway.auth import create_jwt_token

        token = create_jwt_token("precedence-test", expiry_hours=1)

        result = await verify_auth(credentials=_credentials(token))
        assert result == "authenticated"


# ---------------------------------------------------------------------------
# Malformed / garbage token
# ---------------------------------------------------------------------------


class TestMalformedToken:
    async def test_garbage_token_raises_401(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A random string that is neither a valid JWT nor the static key → 401."""
        monkeypatch.setenv("HERETEK_API_KEY", "htsk_correct-key-value")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth(credentials=_credentials("not-a-jwt-not-a-key"))

        assert exc_info.value.status_code == 401
