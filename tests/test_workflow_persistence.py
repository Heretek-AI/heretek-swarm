"""Tests for workflow persistence — FileWorkflowStore and engine integration.

Verifies that:
- FileWorkflowStore CRUD operations work correctly
- Atomic writes produce valid JSON even under simulated failure
- WorkflowEngine persists workflows to disk on load
- Engine restores persisted workflows on startup (restart scenario)
- PUT endpoint updates existing workflows
- DELETE removes from both memory and disk
- List and GET endpoints return persisted data
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.workflow.store import FileWorkflowStore

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_store_path(tmp_path: Path) -> Path:
    """Provide a fresh temp file path for each test."""
    return tmp_path / "workflows.json"


@pytest.fixture
def store(tmp_store_path: Path) -> FileWorkflowStore:
    """Create a FileWorkflowStore backed by a temp file."""
    return FileWorkflowStore(store_path=tmp_store_path)


@pytest.fixture
def sample_definition() -> dict:
    """A minimal but valid workflow definition."""
    return {
        "id": "wf-test-001",
        "name": "Test Workflow",
        "nodes": [
            {"id": "n1", "type": "agent", "data": {"agent_id": "alpha"}},
            {"id": "n2", "type": "tool", "data": {"tool_name": "search"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ],
        "metadata": {"version": 1},
    }


@pytest.fixture
def sample_definition_2() -> dict:
    """A second workflow definition for multi-workflow tests."""
    return {
        "id": "wf-test-002",
        "name": "Second Workflow",
        "nodes": [
            {"id": "a1", "type": "agent", "data": {"agent_id": "beta"}},
        ],
        "edges": [],
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# FileWorkflowStore unit tests
# ---------------------------------------------------------------------------


class TestFileWorkflowStore:
    """Unit tests for FileWorkflowStore CRUD."""

    def test_save_and_load(self, store: FileWorkflowStore, sample_definition: dict):
        """save() persists and load() retrieves the same definition."""
        store.save("wf-test-001", sample_definition)
        loaded = store.load("wf-test-001")
        assert loaded is not None
        assert loaded["id"] == "wf-test-001"
        assert loaded["name"] == "Test Workflow"
        assert len(loaded["nodes"]) == 2
        assert loaded["created_at"]  # auto-populated
        assert loaded["updated_at"]

    def test_load_nonexistent(self, store: FileWorkflowStore):
        """load() returns None for unknown IDs."""
        assert store.load("does-not-exist") is None

    def test_save_updates_metadata(self, store: FileWorkflowStore, sample_definition: dict):
        """Saving twice preserves created_at but refreshes updated_at."""
        store.save("wf-1", sample_definition)
        first = store.load("wf-1")
        store.save("wf-1", {**sample_definition, "name": "Renamed"})
        second = store.load("wf-1")
        assert first is not None
        assert second is not None
        assert first["created_at"] == second["created_at"]
        assert second["name"] == "Renamed"

    def test_load_all(self, store: FileWorkflowStore, sample_definition: dict, sample_definition_2: dict):
        """load_all() returns every persisted workflow."""
        store.save("wf-1", sample_definition)
        store.save("wf-2", sample_definition_2)
        all_wfs = store.load_all()
        assert len(all_wfs) == 2
        assert "wf-1" in all_wfs
        assert "wf-2" in all_wfs

    def test_delete(self, store: FileWorkflowStore, sample_definition: dict):
        """delete() removes the workflow and returns True."""
        store.save("wf-1", sample_definition)
        assert store.delete("wf-1") is True
        assert store.load("wf-1") is None

    def test_delete_nonexistent(self, store: FileWorkflowStore):
        """delete() returns False for unknown IDs."""
        assert store.delete("nope") is False

    def test_exists(self, store: FileWorkflowStore, sample_definition: dict):
        """exists() reflects presence accurately."""
        assert store.exists("wf-1") is False
        store.save("wf-1", sample_definition)
        assert store.exists("wf-1") is True

    def test_atomic_write_produces_valid_json(self, store: FileWorkflowStore, sample_definition: dict):
        """The on-disk file is valid JSON after save."""
        store.save("wf-1", sample_definition)
        raw = store._path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "wf-1" in data

    def test_no_tmp_file_left_behind(self, store: FileWorkflowStore, sample_definition: dict):
        """Atomic write cleans up the .tmp file."""
        store.save("wf-1", sample_definition)
        tmp = store._path.with_suffix(".json.tmp")
        assert not tmp.exists()

    def test_empty_file_returns_empty_dict(self, tmp_store_path: Path):
        """Corrupt / empty file is handled gracefully."""
        tmp_store_path.write_text("not valid json", encoding="utf-8")
        store = FileWorkflowStore(store_path=tmp_store_path)
        assert store.load_all() == {}

    def test_missing_directory_auto_created(self, tmp_path: Path):
        """Store creates parent directories automatically."""
        deep_path = tmp_path / "a" / "b" / "c" / "workflows.json"
        store = FileWorkflowStore(store_path=deep_path)
        store.save("wf-1", {"name": "deep"})
        assert deep_path.exists()
        assert store.load("wf-1") is not None


# ---------------------------------------------------------------------------
# WorkflowEngine persistence integration tests
# ---------------------------------------------------------------------------


class TestWorkflowEnginePersistence:
    """Integration tests for engine ↔ store wiring."""

    @pytest.fixture
    def engine_with_store(self, tmp_store_path: Path):
        """Create a WorkflowEngine with a temp-backed store."""
        from heretek_swarm.workflow.engine import WorkflowEngine

        store = FileWorkflowStore(store_path=tmp_store_path)
        return WorkflowEngine(store=store)

    @pytest.mark.asyncio
    async def test_load_workflow_persists(
        self, engine_with_store, sample_definition: dict, tmp_store_path: Path
    ):
        """load_workflow writes to disk."""
        await engine_with_store.load_workflow(sample_definition)
        raw = json.loads(tmp_store_path.read_text(encoding="utf-8"))
        assert "wf-test-001" in raw

    @pytest.mark.asyncio
    async def test_get_workflow_reads_from_disk(
        self, engine_with_store, sample_definition: dict
    ):
        """get_workflow falls back to disk when not in memory."""
        await engine_with_store.load_workflow(sample_definition)
        # Clear in-memory cache
        engine_with_store.workflows.clear()
        wf = engine_with_store.get_workflow("wf-test-001")
        assert wf is not None
        assert wf.name == "Test Workflow"

    @pytest.mark.asyncio
    async def test_load_persisted_workflows(
        self, engine_with_store, sample_definition: dict, tmp_store_path: Path
    ):
        """load_persisted_workflows restores state after restart."""
        await engine_with_store.load_workflow(sample_definition)

        # Simulate restart: new engine, same store file
        from heretek_swarm.workflow.engine import WorkflowEngine

        store2 = FileWorkflowStore(store_path=tmp_store_path)
        engine2 = WorkflowEngine(store=store2)
        count = engine2.load_persisted_workflows()
        assert count == 1
        assert "wf-test-001" in engine2.workflows

    @pytest.mark.asyncio
    async def test_delete_workflow_removes_from_disk(
        self, engine_with_store, sample_definition: dict, tmp_store_path: Path
    ):
        """delete_workflow removes from both memory and disk."""
        await engine_with_store.load_workflow(sample_definition)
        assert engine_with_store.delete_workflow("wf-test-001") is True
        assert "wf-test-001" not in engine_with_store.workflows
        raw = json.loads(tmp_store_path.read_text(encoding="utf-8"))
        assert "wf-test-001" not in raw

    @pytest.mark.asyncio
    async def test_update_workflow(
        self, engine_with_store, sample_definition: dict
    ):
        """update_workflow replaces the definition."""
        await engine_with_store.load_workflow(sample_definition)
        updated = await engine_with_store.update_workflow(
            "wf-test-001",
            {**sample_definition, "name": "Updated Name"},
        )
        assert updated.name == "Updated Name"
        # Verify disk too
        stored = engine_with_store.store.load("wf-test-001")
        assert stored is not None
        assert stored["name"] == "Updated Name"


# ---------------------------------------------------------------------------
# API endpoint integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client(tmp_path: Path):
    """Create a TestClient with a temp-backed workflow engine."""
    from heretek_swarm.api.workflows import router
    from heretek_swarm.workflow.engine import WorkflowEngine
    from heretek_swarm.workflow.store import FileWorkflowStore

    store_path = tmp_path / "api_workflows.json"
    store = FileWorkflowStore(store_path=store_path)

    app = FastAPI()
    app.include_router(router)

    # Override auth dependency to always pass
    from heretek_swarm.gateway.auth import verify_auth

    async def _no_auth():
        return "authenticated"

    app.dependency_overrides[verify_auth] = _no_auth

    # Patch the global engine to use our temp store
    import heretek_swarm.workflow.engine as engine_mod

    original = engine_mod._global_engine
    engine_mod._global_engine = WorkflowEngine(store=store)

    client = TestClient(app)
    yield client

    engine_mod._global_engine = original


def _make_definition(wf_id: str = "wf-api-001", name: str = "API Workflow") -> dict:
    return {
        "id": wf_id,
        "name": name,
        "nodes": [
            {"id": "n1", "type": "agent", "data": {"agent_id": "a1"}},
        ],
        "edges": [],
        "metadata": {},
    }


class TestWorkflowAPIPersistence:
    """API-level tests for CRUD + persistence."""

    def test_create_and_get(self, api_client: TestClient):
        """POST creates, GET retrieves the same workflow."""
        resp = api_client.post("/api/workflows", json=_make_definition())
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        resp = api_client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "API Workflow"

    def test_list_workflows(self, api_client: TestClient):
        """GET /api/workflows lists persisted workflows."""
        api_client.post("/api/workflows", json=_make_definition("wf-1", "One"))
        api_client.post("/api/workflows", json=_make_definition("wf-2", "Two"))
        resp = api_client.get("/api/workflows")
        assert resp.status_code == 200
        ids = {w["id"] for w in resp.json()["workflows"]}
        assert "wf-1" in ids
        assert "wf-2" in ids

    def test_update_workflow(self, api_client: TestClient):
        """PUT updates an existing workflow."""
        api_client.post("/api/workflows", json=_make_definition())
        resp = api_client.put(
            "/api/workflows/wf-api-001",
            json=_make_definition(name="Renamed"),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

        # Verify the GET returns updated data
        resp = api_client.get("/api/workflows/wf-api-001")
        assert resp.json()["name"] == "Renamed"

    def test_update_nonexistent(self, api_client: TestClient):
        """PUT on unknown ID returns 404."""
        resp = api_client.put(
            "/api/workflows/ghost",
            json=_make_definition("ghost"),
        )
        assert resp.status_code == 404

    def test_delete_workflow(self, api_client: TestClient):
        """DELETE removes the workflow."""
        api_client.post("/api/workflows", json=_make_definition())
        resp = api_client.delete("/api/workflows/wf-api-001")
        assert resp.status_code == 200

        resp = api_client.get("/api/workflows/wf-api-001")
        assert resp.status_code == 404

    def test_delete_nonexistent(self, api_client: TestClient):
        """DELETE on unknown ID returns 404."""
        resp = api_client.delete("/api/workflows/ghost")
        assert resp.status_code == 404

    def test_persistence_across_restart(self, api_client: TestClient, tmp_path: Path):
        """POST → clear memory → GET still returns the workflow (disk persistence)."""
        resp = api_client.post("/api/workflows", json=_make_definition())
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        # Clear in-memory cache to simulate restart
        import heretek_swarm.workflow.engine as engine_mod

        engine_mod._global_engine.workflows.clear()

        resp = api_client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "API Workflow"

    def test_get_nonexistent(self, api_client: TestClient):
        """GET on unknown workflow returns 404."""
        resp = api_client.get("/api/workflows/ghost")
        assert resp.status_code == 404
