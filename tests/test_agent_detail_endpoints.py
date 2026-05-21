"""
HTTP-level agent detail endpoint tests.

Tests GET endpoints from heretek_swarm.api.agents.instances:
  - /api/agents/{instance_id}/memory
  - /api/agents/{instance_id}/tools
  - /api/agents/{instance_id}/tasks

Each endpoint is tested:
  1. Without auth → HTTP 401
  2. With valid auth (dependency_overrides) → HTTP 200
  3. Unknown agent → HTTP 404
  4. Edge cases: unavailable memory, empty tools, not_running tasks

Covers T01/T02/T03/T04 of milestone M016 slice S01.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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

# Detail endpoints for parametrized auth / not-found tests
DETAIL_ENDPOINTS: list[tuple[str, str]] = [
    ("get", f"{PREFIX}/{{instance_id}}/memory"),
    ("get", f"{PREFIX}/{{instance_id}}/tools"),
    ("get", f"{PREFIX}/{{instance_id}}/tasks"),
]


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
# Parametrized 401 tests — all three endpoints without auth
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize(
    ("method", "path_template"),
    DETAIL_ENDPOINTS,
    ids=[ep.split("/")[-1].replace("{instance_id}", "id") for _, ep in DETAIL_ENDPOINTS],
)
def test_detail_endpoint_without_auth_returns_401(method: str, path_template: str) -> None:
    """Each detail endpoint must reject unauthenticated requests."""
    app = _build_app()
    client = TestClient(app)
    url = path_template.format(instance_id=INSTANCE_ID)
    fn = getattr(client, method)
    r = fn(url)
    assert r.status_code == 401, (
        f"{method.upper()} {url} without auth: expected 401, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Parametrized 404 tests — all three endpoints for unknown agent
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize(
    ("method", "path_template"),
    DETAIL_ENDPOINTS,
    ids=[ep.split("/")[-1].replace("{instance_id}", "id") for _, ep in DETAIL_ENDPOINTS],
)
def test_detail_endpoint_unknown_agent_returns_404(method: str, path_template: str) -> None:
    """Each detail endpoint must return 404 for an unknown agent."""
    app = _build_app()
    app.dependency_overrides[verify_auth] = lambda: "test"
    app.dependency_overrides[get_registry] = lambda: _make_mock_registry_empty()
    client = TestClient(app)

    url = path_template.format(instance_id="nonexistent")
    fn = getattr(client, method)
    r = fn(url, headers={"Authorization": "Bearer test"})

    assert r.status_code == 404, (
        f"{method.upper()} {url}: expected 404, got {r.status_code}: {r.text}"
    )


# ---------------------------------------------------------------------------
# Memory endpoint tests (T01)
# ---------------------------------------------------------------------------

class TestMemoryEndpoint:
    """Tests for GET /api/agents/{instance_id}/memory."""

    @pytest.mark.unit
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

    @pytest.mark.unit
    def test_memory_status_unavailable_when_both_backends_none(self):
        """Returns status:'unavailable' when memory_store and mem0_backend are both None."""
        from heretek_swarm.api import main as api_main

        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        with patch.object(api_main, "memory_store", None), patch.object(
            api_main, "mem0_backend", None
        ):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/memory",
                headers={"Authorization": "Bearer test"},
            )

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["status"] == "unavailable", (
            f"Expected status='unavailable', got '{data['status']}'"
        )
        assert data["total_memories"] == 0
        assert data["by_type"] == {}
        assert data["recent_entries"] == []

    @pytest.mark.unit
    def test_memory_status_available_with_mem0_backend(self):
        """Returns status:'available' when mem0_backend provides entries."""
        from heretek_swarm.api import main as api_main

        mock_mem0 = MagicMock()
        mock_mem0.get_all.return_value = []

        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        with patch.object(api_main, "memory_store", None), patch.object(
            api_main, "mem0_backend", mock_mem0
        ):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/memory",
                headers={"Authorization": "Bearer test"},
            )

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["status"] == "available", (
            f"Expected status='available', got '{data['status']}'"
        )
        assert data["total_memories"] == 0
        assert data["by_type"] == {}
        assert data["recent_entries"] == []


# ---------------------------------------------------------------------------
# Tools endpoint tests (T02)
# ---------------------------------------------------------------------------

class TestToolsEndpoint:
    """Tests for GET /api/agents/{instance_id}/tools."""

    @pytest.mark.unit
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

    @pytest.mark.unit
    def test_tools_empty_when_no_skills_or_plugins(self):
        """Returns empty lists when skill registry and plugin runtime have no data."""
        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        # Mock skill registry returning empty skills
        mock_skill_registry = MagicMock()
        mock_skill_registry.get_agent_skills.return_value = []

        # Mock plugin runtime returning empty plugins
        mock_plugin_runtime = MagicMock()
        mock_plugin_runtime.list_plugins.return_value = []

        with patch(
            "heretek_swarm.agents.skills.get_agent_skill_registry",
            return_value=mock_skill_registry,
        ), patch(
            "heretek_swarm.plugins.manager.get_plugin_runtime",
            return_value=mock_plugin_runtime,
        ):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/tools",
                headers={"Authorization": "Bearer test"},
            )

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["skills"] == [], "Expected empty skills list"
        assert data["plugins"] == [], "Expected empty plugins list"
        assert data["total"] == 0, f"Expected total=0, got {data['total']}"


# ---------------------------------------------------------------------------
# Tasks endpoint tests (T03)
# ---------------------------------------------------------------------------

class TestTasksEndpoint:
    """Tests for GET /api/agents/{instance_id}/tasks."""

    @pytest.mark.unit
    def test_tasks_returns_200_with_required_keys(self):
        """Request with auth and known agent returns 200 with correct shape."""
        from heretek_swarm.api.agents import instances as mod

        # Build a mock supervisor with a mock actor
        mock_actor = MagicMock()
        mock_actor.get_status.return_value = MagicMock(
            agent_id=INSTANCE_ID,
            state=MagicMock(value="active"),
            message_count=42,
            created_at="2025-01-01T00:00:00+00:00",
            topics=["topic1", "topic2"],
            capabilities=["learn", "reason"],
            mailbox_size=3,
            last_activity="2025-01-15T12:00:00+00:00",
            error_count=1,
        )
        mock_supervisor = MagicMock()
        mock_supervisor.actors = {INSTANCE_ID: mock_actor}

        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        with patch.object(mod, "_get_tasks_supervisor", return_value=mock_supervisor):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/tasks",
                headers={"Authorization": "Bearer test"},
            )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        data = r.json()
        required_keys = {
            "agent_id", "status", "capabilities", "topics",
            "message_count", "error_count", "last_activity", "uptime_seconds",
        }
        missing = required_keys - set(data.keys())
        assert not missing, f"Missing keys: {missing}"

        assert data["agent_id"] == INSTANCE_ID
        assert data["status"] == "active"
        assert data["capabilities"] == ["learn", "reason"]
        assert data["topics"] == ["topic1", "topic2"]
        assert data["message_count"] == 42
        assert data["error_count"] == 1
        assert data["last_activity"] == "2025-01-15T12:00:00+00:00"
        assert isinstance(data["uptime_seconds"], int)

    @pytest.mark.unit
    def test_tasks_not_running_without_supervisor(self):
        """Returns status:'not_running' when supervisor is not available."""
        from heretek_swarm.api.agents import instances as mod

        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        with patch.object(mod, "_get_tasks_supervisor", return_value=None):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/tasks",
                headers={"Authorization": "Bearer test"},
            )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        data = r.json()
        assert data["status"] == "not_running"
        assert data["message_count"] == 0
        assert data["error_count"] == 0

    @pytest.mark.unit
    def test_tasks_not_running_when_actor_not_in_supervisor(self):
        """Returns status:'not_running' when actor is absent from supervisor."""
        from heretek_swarm.api.agents import instances as mod

        mock_supervisor = MagicMock()
        mock_supervisor.actors = {"other-agent": MagicMock()}

        app = _build_app()
        app.dependency_overrides[verify_auth] = lambda: "test"
        app.dependency_overrides[get_registry] = lambda: _make_mock_registry_with_instance()

        with patch.object(mod, "_get_tasks_supervisor", return_value=mock_supervisor):
            client = TestClient(app)
            r = client.get(
                f"{PREFIX}/{INSTANCE_ID}/tasks",
                headers={"Authorization": "Bearer test"},
            )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        data = r.json()
        assert data["status"] == "not_running"
