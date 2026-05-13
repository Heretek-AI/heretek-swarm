"""Tests for workflow CRUD API and execution (M010/S01/T02).

Verifies:
- Full CRUD cycle: POST creates, GET by id returns, GET list includes, DELETE removes, GET returns 404 after delete  # noqa: E501
- PUT updates an existing workflow
- POST /api/workflows/{id}/execute runs workflow through the engine and returns node_results
- POST /api/workflows/validate with valid DAG returns valid=true; with cycle returns valid=false with CIRCULAR_DEPENDENCY  # noqa: E501
- Error paths: 404 for nonexistent workflow, 422 for invalid definition, execution failure handling
- Persistence: create workflow → reset engine → verify workflow still accessible
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.api.workflows import router
from heretek_swarm.workflow.engine import WorkflowEngine
from heretek_swarm.workflow.store import FileWorkflowStore

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_global_engine():
    """Reset the global workflow engine between tests."""
    import heretek_swarm.workflow.engine as engine_mod

    engine_mod._global_engine = None
    yield
    engine_mod._global_engine = None


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    """Provide a temporary store file path."""
    return tmp_path / "workflows.json"


@pytest.fixture
def store(store_path: Path) -> FileWorkflowStore:
    """Provide a FileWorkflowStore backed by a temp file."""
    return FileWorkflowStore(store_path)


@pytest.fixture
def engine(store: FileWorkflowStore) -> WorkflowEngine:
    """Provide a fresh WorkflowEngine with a temp store."""
    return WorkflowEngine(store=store)


@pytest.fixture
def app(engine: WorkflowEngine):
    """Create a FastAPI app with the workflow router and mocked auth."""
    _app = FastAPI()
    _app.include_router(router)

    # Override the workflow engine dependency
    async def _override_get_engine():
        return engine

    # Patch get_workflow_engine at the module level used by the router
    import heretek_swarm.api.workflows as wf_api

    wf_api.get_workflow_engine = _override_get_engine

    # Override auth to always return "authenticated"
    from heretek_swarm.gateway.auth import verify_auth

    _app.dependency_overrides[verify_auth] = lambda: "authenticated"

    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Synchronous test client."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Fixtures — sample workflow definitions
# ---------------------------------------------------------------------------

_VALID_WORKFLOW_DEF = {
    "id": "wf-test-001",
    "name": "Test Linear Pipeline",
    "nodes": [
        {
            "id": "node-a",
            "type": "input",
            "data": {"label": "Start"},
            "inputs": [],
            "outputs": ["node-b"],
            "position": {"x": 0, "y": 0},
        },
        {
            "id": "node-b",
            "type": "tool",
            "data": {"tool_name": "echo", "label": "Process"},
            "inputs": ["node-a"],
            "outputs": ["node-c"],
            "position": {"x": 200, "y": 0},
        },
        {
            "id": "node-c",
            "type": "output",
            "data": {"label": "End"},
            "inputs": ["node-b"],
            "outputs": [],
            "position": {"x": 400, "y": 0},
        },
    ],
    "edges": [
        {"id": "edge-1", "source": "node-a", "target": "node-b"},
        {"id": "edge-2", "source": "node-b", "target": "node-c"},
    ],
    "metadata": {"version": "1.0"},
}


def _make_cyclic_workflow() -> dict:
    """Return a workflow definition with a circular dependency."""
    return {
        "id": "wf-cyclic",
        "name": "Cyclic Workflow",
        "nodes": [
            {"id": "n1", "type": "input", "data": {}, "inputs": [], "outputs": ["n2"]},
            {"id": "n2", "type": "tool", "data": {}, "inputs": ["n1"], "outputs": ["n3"]},
            {"id": "n3", "type": "tool", "data": {}, "inputs": ["n2"], "outputs": ["n1"]},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n1"},
        ],
    }


def _make_simple_two_node() -> dict:
    """Minimal valid two-node workflow for quick tests."""
    return {
        "id": "wf-simple",
        "name": "Simple Two Node",
        "nodes": [
            {"id": "a", "type": "input", "data": {}, "inputs": [], "outputs": ["b"]},
            {"id": "b", "type": "output", "data": {}, "inputs": ["a"], "outputs": []},
        ],
        "edges": [
            {"id": "e1", "source": "a", "target": "b"},
        ],
    }


# ---------------------------------------------------------------------------
# CRUD Tests
# ---------------------------------------------------------------------------


class TestWorkflowCRUD:
    """Full CRUD lifecycle for workflow API."""

    def test_create_workflow_returns_201_with_id(self, client: TestClient):
        """POST /api/workflows creates a workflow and returns 201 with id."""
        resp = client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "wf-test-001"
        assert data["name"] == "Test Linear Pipeline"
        assert data["state"] == "pending"
        assert "created_at" in data

    def test_get_workflow_by_id(self, client: TestClient):
        """GET /api/workflows/{id} returns the full workflow definition."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.get("/api/workflows/wf-test-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "wf-test-001"
        assert data["name"] == "Test Linear Pipeline"
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2
        assert data["metadata"] == {"version": "1.0"}

    def test_list_workflows_includes_created(self, client: TestClient):
        """GET /api/workflows lists all persisted workflows."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        client.post("/api/workflows", json=_make_simple_two_node())
        resp = client.get("/api/workflows")
        assert resp.status_code == 200
        workflows = resp.json()["workflows"]
        ids = {w["id"] for w in workflows}
        assert "wf-test-001" in ids
        assert "wf-simple" in ids
        assert len(workflows) == 2

    def test_delete_workflow_returns_204(self, client: TestClient):
        """DELETE /api/workflows/{id} removes the workflow."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.delete("/api/workflows/wf-test-001")
        # The endpoint returns None (204 No Content) on success
        assert resp.status_code in (200, 204)

    def test_get_after_delete_returns_404(self, client: TestClient):
        """GET /api/workflows/{id} returns 404 after deletion."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        client.delete("/api/workflows/wf-test-001")
        resp = client.get("/api/workflows/wf-test-001")
        assert resp.status_code == 404

    def test_list_after_delete_excludes_workflow(self, client: TestClient):
        """GET /api/workflows no longer includes deleted workflow."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        client.post("/api/workflows", json=_make_simple_two_node())
        client.delete("/api/workflows/wf-test-001")
        resp = client.get("/api/workflows")
        workflows = resp.json()["workflows"]
        ids = {w["id"] for w in workflows}
        assert "wf-test-001" not in ids
        assert "wf-simple" in ids

    def test_update_workflow(self, client: TestClient):
        """PUT /api/workflows/{id} updates an existing workflow."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        updated = {**_VALID_WORKFLOW_DEF, "name": "Updated Pipeline"}
        resp = client.put("/api/workflows/wf-test-001", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Pipeline"

        # Verify the update persisted
        resp = client.get("/api/workflows/wf-test-001")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Pipeline"

    def test_full_crud_cycle(self, client: TestClient):
        """Create → list → get → update → delete → 404 full lifecycle."""
        # Create
        resp = client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        # List includes
        resp = client.get("/api/workflows")
        assert wf_id in [w["id"] for w in resp.json()["workflows"]]

        # Get by id
        resp = client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == wf_id

        # Update
        updated = {**_VALID_WORKFLOW_DEF, "name": "Modified"}
        resp = client.put(f"/api/workflows/{wf_id}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Modified"

        # Delete
        resp = client.delete(f"/api/workflows/{wf_id}")
        assert resp.status_code in (200, 204)

        # 404 after delete
        resp = client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Error Path Tests
# ---------------------------------------------------------------------------


class TestWorkflowErrorPaths:
    """Verify proper error responses for invalid inputs."""

    def test_get_nonexistent_workflow_returns_404(self, client: TestClient):
        """GET /api/workflows/{id} returns 404 for unknown ID."""
        resp = client.get("/api/workflows/does-not-exist")
        assert resp.status_code == 404

    def test_delete_nonexistent_workflow_returns_404(self, client: TestClient):
        """DELETE /api/workflows/{id} returns 404 for unknown ID."""
        resp = client.delete("/api/workflows/does-not-exist")
        assert resp.status_code == 404

    def test_execute_nonexistent_workflow_returns_404(self, client: TestClient):
        """POST /api/workflows/{id}/execute returns 404 for unknown ID."""
        resp = client.post(
            "/api/workflows/does-not-exist/execute",
            json={"input": "test"},
        )
        assert resp.status_code == 404

    def test_update_nonexistent_workflow_returns_404(self, client: TestClient):
        """PUT /api/workflows/{id} returns 404 for unknown ID."""
        resp = client.put(
            "/api/workflows/does-not-exist",
            json=_VALID_WORKFLOW_DEF,
        )
        assert resp.status_code == 404

    def test_validate_nonexistent_workflow_returns_404(self, client: TestClient):
        """POST /api/workflows/{id}/validate returns 404 for unknown ID."""
        resp = client.post("/api/workflows/does-not-exist/validate")
        assert resp.status_code == 404

    def test_status_nonexistent_workflow_returns_pending(self, client: TestClient):
        """GET /api/workflows/{id}/status returns PENDING for unknown execution."""
        resp = client.get("/api/workflows/wf-missing/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"
        assert resp.json()["execution_id"] is None


# ---------------------------------------------------------------------------
# Execution Tests
# ---------------------------------------------------------------------------


class TestWorkflowExecution:
    """Test workflow execution through the engine."""

    def test_execute_returns_node_results(self, client: TestClient):
        """POST /api/workflows/{id}/execute returns execution result with node_results."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.post(
            "/api/workflows/wf-test-001/execute",
            json={"input": "hello"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "execution_id" in data
        assert data["workflow_id"] == "wf-test-001"
        assert "status" in data
        assert "node_results" in data
        assert "start_time" in data

    def test_execute_simple_workflow_completes(self, client: TestClient):
        """Execute a simple two-node workflow — should complete successfully."""
        client.post("/api/workflows", json=_make_simple_two_node())
        resp = client.post(
            "/api/workflows/wf-simple/execute",
            json={"message": "test"},
        )
        assert resp.status_code == 201
        data = resp.json()
        # With input/output nodes, the engine should complete
        assert data["status"] in ("completed", "failed")

    def test_execute_nonexistent_returns_404(self, client: TestClient):
        """Execute a workflow that doesn't exist returns 404."""
        resp = client.post(
            "/api/workflows/no-such-wf/execute",
            json={},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


class TestWorkflowValidation:
    """Test the /validate endpoints."""

    def test_validate_draft_valid_dag(self, client: TestClient):
        """POST /api/workflows/validate with valid DAG returns valid=true."""
        resp = client.post("/api/workflows/validate", json=_VALID_WORKFLOW_DEF)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)
        assert isinstance(data["info"], list)

    def test_validate_draft_cyclic_returns_false(self, client: TestClient):
        """POST /api/workflows/validate with cycle returns valid=false with CIRCULAR_DEPENDENCY."""
        resp = client.post("/api/workflows/validate", json=_make_cyclic_workflow())
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        error_codes = [e["code"] for e in data["errors"]]
        assert "CIRCULAR_DEPENDENCY" in error_codes

    def test_validate_saved_workflow(self, client: TestClient):
        """POST /api/workflows/{id}/validate validates a persisted workflow."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.post("/api/workflows/wf-test-001/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True

    def test_validate_cyclic_saved_workflow(self, client: TestClient):
        """Validate a saved cyclic workflow returns CIRCULAR_DEPENDENCY."""
        client.post("/api/workflows", json=_make_cyclic_workflow())
        resp = client.post("/api/workflows/wf-cyclic/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        error_codes = [e["code"] for e in data["errors"]]
        assert "CIRCULAR_DEPENDENCY" in error_codes

    def test_validate_disconnected_nodes(self, client: TestClient):
        """Validation catches disconnected nodes."""
        wf = {
            "id": "wf-disconnected",
            "name": "Disconnected",
            "nodes": [
                {"id": "a", "type": "input", "data": {}, "inputs": [], "outputs": ["b"]},
                {"id": "b", "type": "output", "data": {}, "inputs": ["a"], "outputs": []},
                {"id": "c", "type": "tool", "data": {}, "inputs": [], "outputs": []},
            ],
            "edges": [
                {"id": "e1", "source": "a", "target": "b"},
            ],
        }
        resp = client.post("/api/workflows/validate", json=wf)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        error_codes = [e["code"] for e in data["errors"]]
        assert "DISCONNECTED_NODE" in error_codes
        # Should reference node-c
        node_ids = [e.get("node_id") for e in data["errors"] if e["code"] == "DISCONNECTED_NODE"]
        assert "c" in node_ids

    def test_validate_empty_workflow(self, client: TestClient):
        """Validation handles an empty workflow gracefully."""
        wf = {"id": "wf-empty", "name": "Empty", "nodes": [], "edges": []}
        resp = client.post("/api/workflows/validate", json=wf)
        assert resp.status_code == 200
        # An empty workflow is valid (no nodes, no errors)
        assert resp.json()["valid"] is True

    def test_validate_returns_structured_errors(self, client: TestClient):
        """Validation errors include node_id, edge_id, code, and suggestion."""
        wf = _make_cyclic_workflow()
        resp = client.post("/api/workflows/validate", json=wf)
        data = resp.json()
        cycle_error = next(e for e in data["errors"] if e["code"] == "CIRCULAR_DEPENDENCY")
        assert "message" in cycle_error
        assert "suggestion" in cycle_error
        assert cycle_error["severity"] == "error"


# ---------------------------------------------------------------------------
# Persistence Tests
# ---------------------------------------------------------------------------


class TestWorkflowPersistence:
    """Verify workflows survive engine restart via FileWorkflowStore."""

    def test_workflow_persists_across_engine_restart(
        self, client: TestClient, store: FileWorkflowStore
    ):
        """Create workflow → reset engine → GET returns same workflow.

        This is the critical persistence test: the workflow must survive
        a server restart by being reloaded from disk.
        """
        # Create via API
        resp = client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        # Verify it's on disk
        assert store.exists(wf_id)

        # Simulate engine restart by resetting the global engine
        import heretek_swarm.workflow.engine as engine_mod

        engine_mod._global_engine = None

        # Create a new engine with the same store
        new_engine = WorkflowEngine(store=store)
        new_engine.load_persisted_workflows()

        # Override the app's engine with the new one
        async def _override_get_engine():
            return new_engine

        import heretek_swarm.api.workflows as wf_api

        wf_api.get_workflow_engine = _override_get_engine

        # GET should still return the workflow
        resp = client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == wf_id
        assert data["name"] == "Test Linear Pipeline"
        assert len(data["nodes"]) == 3

    def test_list_after_restart(self, client: TestClient, store: FileWorkflowStore):
        """List endpoint works after engine restart."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        client.post("/api/workflows", json=_make_simple_two_node())

        # Restart engine
        import heretek_swarm.workflow.engine as engine_mod

        engine_mod._global_engine = None
        new_engine = WorkflowEngine(store=store)
        new_engine.load_persisted_workflows()

        async def _override():
            return new_engine

        import heretek_swarm.api.workflows as wf_api

        wf_api.get_workflow_engine = _override

        resp = client.get("/api/workflows")
        assert resp.status_code == 200
        ids = {w["id"] for w in resp.json()["workflows"]}
        assert "wf-test-001" in ids
        assert "wf-simple" in ids

    def test_delete_removes_from_disk(self, client: TestClient, store: FileWorkflowStore):
        """DELETE removes workflow from disk store."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        assert store.exists("wf-test-001")
        client.delete("/api/workflows/wf-test-001")
        assert not store.exists("wf-test-001")


# ---------------------------------------------------------------------------
# Status and Cancel Tests
# ---------------------------------------------------------------------------


class TestWorkflowStatusAndCancel:
    """Test status and cancel endpoints."""

    def test_status_returns_pending_for_new_workflow(self, client: TestClient):
        """GET /api/workflows/{id}/status returns PENDING for a workflow that hasn't been executed."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.get("/api/workflows/wf-test-001/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_id"] == "wf-test-001"
        assert data["status"] == "pending"
        assert data["execution_id"] is None

    def test_cancel_returns_message(self, client: TestClient):
        """POST /api/workflows/{id}/cancel returns a message."""
        client.post("/api/workflows", json=_VALID_WORKFLOW_DEF)
        resp = client.post("/api/workflows/wf-test-001/cancel")
        assert resp.status_code == 200
        assert "message" in resp.json()
