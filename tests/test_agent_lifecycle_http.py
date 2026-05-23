"""
HTTP-level agent lifecycle endpoint tests.

Tests POST endpoints from heretek_swarm.api.agents.lifecycle:
  - /api/agents/{instance_id}/start
  - /api/agents/{instance_id}/stop
  - /api/agents/{instance_id}/suspend
  - /api/agents/{instance_id}/resume

Each endpoint is tested:
  1. Without auth → HTTP 401
  2. With valid auth (dependency_overrides) → HTTP 200

References test_actor_lifecycle.py patterns for lifecycle state assertion
conventions (ACTIVE, STOPPED, SUSPENDED, RUNNING).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = [pytest.mark.integration]

from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.api.agents.lifecycle import get_registry, router
from heretek_swarm.gateway.auth import verify_auth

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INSTANCE_ID = "test-instance-01"
PREFIX = "/api/agents"

# Lifecycle endpoints: (method, path, expected_status_value)
LIFECYCLE_ENDPOINTS: list[tuple[str, str, str]] = [
    ("post", f"{PREFIX}/{INSTANCE_ID}/start", "running"),
    ("post", f"{PREFIX}/{INSTANCE_ID}/stop", "stopped"),
    ("post", f"{PREFIX}/{INSTANCE_ID}/suspend", "suspended"),
    ("post", f"{PREFIX}/{INSTANCE_ID}/resume", "running"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_registry() -> MagicMock:
    """Create a mock EnhancedAgentRegistry with async lifecycle methods."""
    registry = MagicMock()
    registry.get_instance = MagicMock(return_value=MagicMock())
    registry.start_agent = AsyncMock(return_value=True)
    registry.stop_agent = AsyncMock(return_value=True)
    registry.suspend_agent = AsyncMock(return_value=True)
    registry.resume_agent = AsyncMock(return_value=True)
    return registry


def _create_app() -> FastAPI:
    """Create a minimal FastAPI app with the lifecycle router."""
    app = FastAPI()
    app.include_router(router, prefix=PREFIX)
    return app


# ---------------------------------------------------------------------------
# Tests — unauthenticated access
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "expected_status"),
    LIFECYCLE_ENDPOINTS,
    ids=[f"no_auth_{ep}" for ep, _, _ in
         [(s.split("/")[-1], p, s) for _, p, s in LIFECYCLE_ENDPOINTS]],
)
def test_lifecycle_endpoint_returns_401_without_auth(
    method: str,
    path: str,
    expected_status: str,
) -> None:
    """Verify {method.upper()} {path} returns 401 without auth."""
    app = _create_app()
    client = TestClient(app, raise_server_exceptions=False)

    fn = getattr(client, method)
    resp = fn(path)

    assert resp.status_code == 401, (
        f"{method.upper()} {path} without auth: expected 401, "
        f"got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Tests — authenticated access (with dependency_overrides)
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_client() -> TestClient:
    """Return a TestClient with verify_auth and registry overridden."""
    app = _create_app()

    registry = _make_mock_registry()

    async def mock_verify_auth() -> str:
        return "authenticated"

    def mock_get_registry():
        return registry

    app.dependency_overrides[verify_auth] = mock_verify_auth
    app.dependency_overrides[get_registry] = mock_get_registry

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("method", "path", "expected_status_value"),
    LIFECYCLE_ENDPOINTS,
    ids=[f"auth_{ep}" for ep, _, _ in
         [(s.split("/")[-1], p, s) for _, p, s in LIFECYCLE_ENDPOINTS]],
)
def test_lifecycle_endpoint_with_valid_auth(
    auth_client: TestClient,
    method: str,
    path: str,
    expected_status_value: str,
) -> None:
    """Verify {method.upper()} {path} returns 200 with valid auth."""
    fn = getattr(auth_client, method)
    resp = fn(path)

    assert resp.status_code == 200, (
        f"{method.upper()} {path} with auth: expected 200, "
        f"got {resp.status_code}: {resp.text}"
    )

    body = resp.json()
    assert body["instance_id"] == INSTANCE_ID
    assert body["status"] == expected_status_value, (
        f"Expected status={expected_status_value}, got {body.get('status')}"
    )


# ---------------------------------------------------------------------------
# Negative: 404 when instance not found (authenticated)
# ---------------------------------------------------------------------------


def test_lifecycle_start_returns_404_for_unknown_instance() -> None:
    """POST start returns 404 when registry has no matching instance."""
    app = _create_app()

    registry = MagicMock()
    registry.get_instance = MagicMock(return_value=None)  # not found

    async def mock_verify_auth() -> str:
        return "authenticated"

    def mock_get_registry():
        return registry

    app.dependency_overrides[verify_auth] = mock_verify_auth
    app.dependency_overrides[get_registry] = mock_get_registry

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(f"{PREFIX}/nonexistent/start")

    assert resp.status_code == 404, (
        f"Expected 404 for unknown instance, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Negative: 500 when registry operation fails (authenticated)
# ---------------------------------------------------------------------------


def test_lifecycle_stop_returns_500_on_registry_failure() -> None:
    """POST stop returns 500 when registry.stop_agent returns False."""
    app = _create_app()

    registry = MagicMock()
    registry.get_instance = MagicMock(return_value=MagicMock())
    registry.stop_agent = AsyncMock(return_value=False)  # simulate failure

    async def mock_verify_auth() -> str:
        return "authenticated"

    def mock_get_registry():
        return registry

    app.dependency_overrides[verify_auth] = mock_verify_auth
    app.dependency_overrides[get_registry] = mock_get_registry

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(f"{PREFIX}/{INSTANCE_ID}/stop")

    assert resp.status_code == 500, (
        f"Expected 500 on registry failure, got {resp.status_code}"
    )
