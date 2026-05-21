"""
HTTP-level agent detail endpoint tests.

Tests GET endpoints from heretek_swarm.api.agents.instances:
  - /api/agents/{instance_id}/memory

Each endpoint is tested:
  1. Without auth → HTTP 401
  2. With valid auth (dependency_overrides) → HTTP 200
  3. Unknown agent → HTTP 404

Covers T01/T02/T03/T04 of milestone M016 slice S01.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.api.agents.instances import get_registry, router
from heretek_swarm.gateway.auth import verify_auth

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INSTANCE_ID = "test-instance-01"
PREFIX = "/api/agents"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_registry_with_instance() -> MagicMock:
    """Create a mock registry that returns a valid instance."""
    instance = MagicMock()
    instance.instance_id = INSTANCE_ID
    instance.agent_type = "test-agent"
    registry = MagicMock()
    registry.get_instance = MagicMock(return_value=instance)
    return registry


def _make_mock_registry_empty() -> MagicMock:
    """Create a mock registry that returns None (agent not found)."""
    registry = MagicMock()
    registry.get_instance = MagicMock(return_value=None)
    return registry


def _build_app() -> FastAPI:
    """Build isolated test app with the instances router."""
    app = FastAPI()
    app.include_router(router, prefix=PREFIX)
    return app


# ---------------------------------------------------------------------------
# Memory endpoint tests (T01)
# ---------------------------------------------------------------------------

class TestMemoryEndpoint:
    """Tests for GET /api/agents/{instance_id}/memory."""

    def test_memory_without_auth_returns_401(self):
        """Unauthenticated requests must be rejected."""
        app = _build_app()
        client = TestClient(app)
        r = client.get(f"{PREFIX}/{INSTANCE_ID}/memory")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_memory_unknown_agent_returns_404(self):
        """Unknown agent returns 404."""
        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_empty()
        client = TestClient(app)
        r = client.get(
            f"{PREFIX}/nonexistent/memory",
            headers={"Authorization": "Bearer test"},
        )
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    @pytest.mark.parametrize("limit_param", [None, 5, 20, 50])
    def test_memory_returns_200_with_required_keys(self, limit_param):
        """Request with auth and known agent returns 200 with correct shape."""
        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()
        client = TestClient(app)

        url = f"{PREFIX}/{INSTANCE_ID}/memory"
        if limit_param is not None:
            url += f"?limit={limit_param}"

        r = client.get(url, headers={"Authorization": "Bearer test"})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        data = r.json()
        required_keys = {"agent_id", "total_memories", "by_type", "recent_entries", "status"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Missing keys: {missing}"

        assert data["agent_id"] == INSTANCE_ID
        assert isinstance(data["total_memories"], int)
        assert isinstance(data["by_type"], dict)
        assert isinstance(data["recent_entries"], list)
        assert data["status"] in ("available", "unavailable", "error"), (
            f"Invalid status: {data['status']}"
        )


# ---------------------------------------------------------------------------
# Tools endpoint tests (T02)
# ---------------------------------------------------------------------------

class TestToolsEndpoint:
    """Tests for GET /api/agents/{instance_id}/tools."""

    def test_tools_without_auth_returns_401(self):
        """Unauthenticated requests must be rejected."""
        app = _build_app()
        client = TestClient(app)
        r = client.get(f"{PREFIX}/{INSTANCE_ID}/tools")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_tools_unknown_agent_returns_404(self):
        """Unknown agent returns 404."""
        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_empty()
        client = TestClient(app)
        r = client.get(
            f"{PREFIX}/nonexistent/tools",
            headers={"Authorization": "Bearer test"},
        )
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_tools_returns_200_with_required_keys(self):
        """Request with auth and known agent returns 200 with correct shape."""
        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()
        client = TestClient(app)

        r = client.get(
            f"{PREFIX}/{INSTANCE_ID}/tools",
            headers={"Authorization": "Bearer test"},
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        data = r.json()
        required_keys = {"agent_id", "skills", "plugins", "total"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Missing keys: {missing}"

        assert data["agent_id"] == INSTANCE_ID
        assert isinstance(data["skills"], list)
        assert isinstance(data["plugins"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["skills"]) + len(data["plugins"]), (
            f"Total {data['total']} != skills({len(data['skills'])}) + plugins({len(data['plugins'])})"
        )
