"""Tests for the Phase 1.3 fastapi-users spike (dry-mode only)."""

from __future__ import annotations

import uuid

from heretek_swarm.security.fastapi_users_spike import (
    UserCreate,
    UserManager,
    UserRead,
    UserUpdate,
    auth_backend,
    bearer_transport,
    get_jwt_strategy,
    make_fastapi_users,
    run_dry_spike,
)


def test_dry_spike_passes():
    """The fastapi-users API surface is valid."""
    run_dry_spike()


def test_user_read_has_tier_and_agent_id():
    """UserRead Pydantic schema exposes tier and agent_id."""
    fields = set(UserRead.model_fields.keys())
    assert "tier" in fields
    assert "agent_id" in fields
    # Inherited from fastapi-users BaseUser
    assert "id" in fields
    assert "email" in fields
    assert "is_active" in fields


def test_user_create_has_tier_default():
    """UserCreate defaults tier to 'authenticated'."""
    assert UserCreate.model_fields["tier"].default == "authenticated"


def test_user_update_optional_fields():
    """UserUpdate allows tier and agent_id to be optional."""
    fields = set(UserUpdate.model_fields.keys())
    assert "tier" in fields
    assert "agent_id" in fields


def test_user_manager_extends_uuid_id_mixin():
    """UserManager uses UUID id strategy (matches our existing user table)."""
    from fastapi_users import UUIDIDMixin

    assert issubclass(UserManager, UUIDIDMixin)


def test_auth_backend_is_jwt():
    """Auth backend is named 'jwt' and uses Bearer transport."""
    assert auth_backend.name == "jwt"
    assert auth_backend.transport is bearer_transport


def test_jwt_strategy_has_token_methods():
    """JWT strategy exposes write_token and read_token."""
    strategy = get_jwt_strategy()
    assert hasattr(strategy, "write_token")
    assert hasattr(strategy, "read_token")


def test_make_fastapi_users_returns_fastapi_users_instance():
    """The factory has the right signature; returns FastAPIUsers."""
    from fastapi_users import FastAPIUsers

    def _stub_get_user_manager():
        return None  # No actual manager; the factory only stores the callable.

    fusers = make_fastapi_users(_stub_get_user_manager)
    assert isinstance(fusers, FastAPIUsers)


def test_uuid_id_type():
    """User schemas use uuid.UUID (matches our existing user table)."""

    # The model_fields['id']['annotation'] is uuid.UUID
    id_annotation = UserRead.model_fields["id"].annotation
    assert id_annotation == uuid.UUID
