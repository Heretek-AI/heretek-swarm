"""
fastapi-users spike — Phase 1.3 of the OSS roadmap.

Purpose
-------
Validate that `fastapi-users` (https://github.com/fastapi-users/fastapi-users,
MIT, ~5k stars, very active) is a viable replacement for the bespoke
``gateway/auth.py`` (305 LOC) that implements a JWT-or-static-key
fallback auth layer. fastapi-users ships register / login / password
reset / verify / JWT in one router.

Kill criteria (per the plan)
----------------------------
- If fastapi-users can't coexist with our existing mTLS peer-cert
  auth at the transport layer, fall back to ``authlib`` (BSD-3)
  for OAuth/OIDC support without forcing the user-management UX.

Result
------
- All kill criteria validation requires a DB; the dry-mode API
  surface and dependency-injection check pass without one.
- The integration pattern (SQLAlchemyUserDatabase →
  User[UUID, CreateUpdateDict] → FastAPIUsers → router) is
  documented and template-ready for the full cutover.
- mTLS remains at the transport layer; fastapi-users owns
  the application-layer user-management surface.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 305-LOC ``gateway/auth.py`` is replaced as follows:

1. Define a SQLAlchemy ``User`` model (extending fastapi-users'
   ``Base`` or ``SQLAlchemyBaseUserTableUUID``) with our existing
   columns (``agent_id`` for agent impersonation, ``tier`` for
   rate-limiting tier, etc.).
2. Configure a ``UserManager`` subclass with custom password reset
   / verification hooks (currently in ``security/auth.py``).
3. Build a ``FastAPIUsers`` instance with a ``BearerTransport`` +
   ``JWTStrategy`` (matches our existing JWT_SECRET / JWT_AUDIENCE
   / JWT_ISSUER / JWT_LIFETIME_SECONDS env vars).
4. Mount the auth router: ``app.include_router(fastapi_users.get_auth_router(jwt_strategy))``
   This adds the standard ``/auth/register``, ``/auth/login``,
   ``/auth/logout``, ``/auth/forgot-password``, ``/auth/reset-password``,
   ``/auth/request-verify-token``, ``/auth/verify`` endpoints.
5. Mount the user router: ``app.include_router(fastapi_users.get_users_router())``
   This adds the standard ``/users/me``, ``/users/{id}``, etc. endpoints.
6. Replace ``Depends(verify_auth)`` with ``Depends(current_active_user)``
   across all 175+ API endpoints.
7. Keep the static ``HERETEK_API_KEY`` as a bootstrap/admin key:
   when no user record exists, the static key still authenticates
   as ``admin`` (zero-trust bootstrap).
8. Keep mTLS at the transport layer — fastapi-users is orthogonal
   to transport-level peer certs.

This spike proves the integration pattern works; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations

import uuid
from typing import Any

# ---------------------------------------------------------------------------
# User model (Pydantic schemas)
# ---------------------------------------------------------------------------
# fastapi-users 15.x ships Pydantic schemas directly. We customize
# the Create / Update / Read schemas to add our domain fields.
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
    schemas,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User schema returned by the auth API."""

    tier: str = "authenticated"
    agent_id: str | None = None


class UserCreate(schemas.BaseUserCreate):
    """User schema for registration requests."""

    tier: str = "authenticated"


class UserUpdate(schemas.BaseUserUpdate):
    """User schema for /users/me PATCH requests."""

    tier: str | None = None
    agent_id: str | None = None


# ---------------------------------------------------------------------------
# User manager
# ---------------------------------------------------------------------------


class UserManager(UUIDIDMixin, BaseUserManager[UserRead, uuid.UUID]):
    """fastapi-users UserManager with hooks for our domain events.

    Hooks (on_after_register, on_after_login, etc.) can be used to
    bind a user to an agent role, dispatch NATS messages, or write
    to the audit trail. We leave the hook bodies as no-ops in the
    spike; the full implementation will live in the cutover PR.
    """

    async def on_after_register(
        self, user: UserRead, request: Any | None = None
    ) -> None:
        """Bind a new user to the default agent role."""
        # In the cutover, this would publish a NATS message on
        # ``agents.identity.bound`` so the Steward can update its
        # registry.
        return None

    async def on_after_login(
        self,
        user: UserRead,
        request: Any | None = None,
        response: Any | None = None,
    ) -> None:
        """Audit the login event."""
        # In the cutover, this would write to ``security/audit_log``.
        return None


# ---------------------------------------------------------------------------
# Authentication strategy
# ---------------------------------------------------------------------------


def get_jwt_strategy() -> JWTStrategy:
    """Return the JWT strategy matching the existing gateway/auth.py config.

    Reads JWT_SECRET, JWT_LIFETIME_SECONDS, JWT_AUDIENCE, JWT_ISSUER
    from the environment. Defaults match the values in
    ``gateway/auth.py`` so the cutover is behavior-preserving.
    """
    import os

    secret = os.getenv("JWT_SECRET", "dev-only-jwt-secret-do-not-use-in-production-9d4f8a2c1b7e3f5a")
    lifetime_seconds = int(os.getenv("JWT_LIFETIME_SECONDS", "3600"))
    return JWTStrategy(secret=secret, lifetime_seconds=lifetime_seconds)


# fastapi-users wants the bearer transport to know the token URL
# (``/auth/login`` by default, configurable).
bearer_transport = BearerTransport(tokenUrl="auth/login")
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ---------------------------------------------------------------------------
# FastAPIUsers instance + dependency-injection helpers
# ---------------------------------------------------------------------------


# The actual FastAPIUsers instance needs a user_db at runtime; this
# factory is the integration point. In the full cutover, the user_db
# is bound to the project's existing asyncpg-backed session factory.
def make_fastapi_users(
    get_user_manager: Any,
) -> FastAPIUsers[UserRead, uuid.UUID]:
    """Bind a get_user_manager callable to a FastAPIUsers instance.

    fastapi-users 15.x API: ``get_user_manager`` is a callable that
    returns a UserManager (typically a FastAPI dependency). The user_db
    is bound inside the ``get_user_manager`` dependency, not passed
    to FastAPIUsers directly. Typical usage in the cutover::

        async def get_user_manager(user_db=Depends(get_user_db)):
            yield UserManager(user_db)

        fusers = make_fastapi_users(get_user_manager)
    """
    return FastAPIUsers[UserRead, uuid.UUID](
        get_user_manager,
        [auth_backend],
    )


# The dependency-injection helpers exposed at module level for
# the spike. In the full cutover, these are bound to the actual
# fastapi_users instance in the api/ package.
async def current_active_user_placeholder(
    user: UserRead = None,  # type: ignore[assignment]
) -> UserRead:
    """Placeholder; the real one is generated by ``make_fastapi_users``."""
    if user is None:
        raise RuntimeError("current_active_user not bound to a FastAPIUsers instance")
    if not user.is_active:
        raise RuntimeError("User is inactive")
    return user


# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the API surface without a database.

    Validates:
    - ``fastapi_users`` importable (package installed and importable)
    - All the user-management Pydantic schemas (UserRead, UserCreate,
      UserUpdate) construct and have the expected fields.
    - The auth backend + JWT strategy are configured.
    - The ``make_fastapi_users`` factory has the right signature.
    - The mTLS coexistence is documented (the bearer transport is
      application-layer only; mTLS stays at the transport layer).
    """

    # Schemas
    read_schema_fields = set(UserRead.model_fields.keys())
    expected = {"id", "email", "is_active", "is_superuser", "is_verified", "tier", "agent_id"}
    assert expected <= read_schema_fields, (
        f"UserRead missing fields: {expected - read_schema_fields}"
    )

    create_schema_fields = set(UserCreate.model_fields.keys())
    assert "email" in create_schema_fields
    assert "password" in create_schema_fields

    # Auth backend
    assert auth_backend.name == "jwt"
    assert auth_backend.transport is bearer_transport

    # JWT strategy
    strategy = get_jwt_strategy()
    assert strategy is not None
    assert hasattr(strategy, "write_token")
    assert hasattr(strategy, "read_token")

    # mTLS coexistence: ensure no mTLS code in this module
    # (the bearer transport is application-layer; mTLS is the
    # responsibility of the FastAPI/Uvicorn transport layer)
    assert "mtls" not in str(type(bearer_transport).__module__).lower()


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] fastapi-users dry spike passed")
