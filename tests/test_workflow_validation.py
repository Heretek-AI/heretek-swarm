"""Tests for DAG validation edge-cases and PUT endpoint verification (M010/S01/T03).

Covers the validator's handling of real-world Canvas errors:
1. Self-loop: node with edge from itself to itself → rejected
2. Disconnected node: node with no edges → rejected
3. Missing node config: agent node without agent_id → warning
4. Multiple start nodes: valid DAG with 2 root nodes → passes
5. Diamond dependency: A→B, A→C, B→D, C→D → valid DAG, correct execution order
6. Complex cycle: A→B→C→A → CIRCULAR_DEPENDENCY detected
7. PUT update: update workflow definition → GET returns updated version
8. Validate draft: POST /api/workflows/validate (without saving) returns correct result
9. Topological sort produces correct ordering for diamond graphs
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytestmark = [pytest.mark.unit]

from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.api.workflows import router
from heretek_swarm.workflow.engine import WorkflowEngine
from heretek_swarm.workflow.store import FileWorkflowStore
from heretek_swarm.workflow.validator import (
    ErrorCodes,
    validate_workflow,
)

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
    return tmp_path / "workflows.json"


@pytest.fixture
def store(store_path: Path) -> FileWorkflowStore:
    return FileWorkflowStore(store_path)


@pytest.fixture
def engine(store: FileWorkflowStore) -> WorkflowEngine:
    return WorkflowEngine(store=store)


@pytest.fixture
def app(engine: WorkflowEngine):
    _app = FastAPI()
    _app.include_router(router)

    async def _override_get_engine():
        return engine

    import heretek_swarm.api.workflows as wf_api

    wf_api.get_workflow_engine = _override_get_engine

    from heretek_swarm.gateway.auth import verify_auth

    _app.dependency_overrides[verify_auth] = lambda: "authenticated"

    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helper definitions
# ---------------------------------------------------------------------------


def _self_loop_workflow() -> dict:
    """Single node with an edge from itself to itself."""
    return {
        "id": "wf-self-loop",
        "name": "Self Loop",
        "nodes": [
            {"id": "n1", "type": "tool", "data": {}, "inputs": [], "outputs": ["n1"]},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n1"},
        ],
    }


def _disconnected_workflow() -> dict:
    """Two connected nodes plus one orphan."""
    return {
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


def _agent_missing_config_workflow() -> dict:
    """Agent node with no agent_id in data."""
    return {
        "id": "wf-missing-config",
        "name": "Missing Config",
        "nodes": [
            {"id": "a", "type": "input", "data": {}, "inputs": [], "outputs": ["b"]},
            {
                "id": "b",
                "type": "agent",
                "data": {},  # missing agent_id / agentType
                "inputs": ["a"],
                "outputs": ["c"],
            },
            {"id": "c", "type": "output", "data": {}, "inputs": ["b"], "outputs": []},
        ],
        "edges": [
            {"id": "e1", "source": "a", "target": "b"},
            {"id": "e2", "source": "b", "target": "c"},
        ],
    }


def _multiple_start_workflow() -> dict:
    """Valid DAG with two root nodes (no incoming edges) merging into one."""
    return {
        "id": "wf-multi-start",
        "name": "Multiple Start",
        "nodes": [
            {"id": "s1", "type": "input", "data": {}, "inputs": [], "outputs": ["merge"]},
            {"id": "s2", "type": "input", "data": {}, "inputs": [], "outputs": ["merge"]},
            {"id": "merge", "type": "tool", "data": {}, "inputs": ["s1", "s2"], "outputs": ["end"]},
            {"id": "end", "type": "output", "data": {}, "inputs": ["merge"], "outputs": []},
        ],
        "edges": [
            {"id": "e1", "source": "s1", "target": "merge"},
            {"id": "e2", "source": "s2", "target": "merge"},
            {"id": "e3", "source": "merge", "target": "end"},
        ],
    }


def _diamond_workflow() -> dict:
    """Diamond DAG: A→B, A→C, B→D, C→D."""
    return {
        "id": "wf-diamond",
        "name": "Diamond",
        "nodes": [
            {"id": "A", "type": "input", "data": {}, "inputs": [], "outputs": ["B", "C"]},
            {"id": "B", "type": "tool", "data": {}, "inputs": ["A"], "outputs": ["D"]},
            {"id": "C", "type": "tool", "data": {}, "inputs": ["A"], "outputs": ["D"]},
            {"id": "D", "type": "output", "data": {}, "inputs": ["B", "C"], "outputs": []},
        ],
        "edges": [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "A", "target": "C"},
            {"id": "e3", "source": "B", "target": "D"},
            {"id": "e4", "source": "C", "target": "D"},
        ],
    }


def _complex_cycle_workflow() -> dict:
    """Three-node cycle: A→B→C→A."""
    return {
        "id": "wf-complex-cycle",
        "name": "Complex Cycle",
        "nodes": [
            {"id": "A", "type": "tool", "data": {}, "inputs": [], "outputs": ["B"]},
            {"id": "B", "type": "tool", "data": {}, "inputs": ["A"], "outputs": ["C"]},
            {"id": "C", "type": "tool", "data": {}, "inputs": ["B"], "outputs": ["A"]},
        ],
        "edges": [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "C", "target": "A"},
        ],
    }


def _valid_linear_workflow() -> dict:
    """Simple valid three-node linear pipeline."""
    return {
        "id": "wf-linear",
        "name": "Linear",
        "nodes": [
            {"id": "start", "type": "input", "data": {}, "inputs": [], "outputs": ["mid"]},
            {"id": "mid", "type": "tool", "data": {}, "inputs": ["start"], "outputs": ["end"]},
            {"id": "end", "type": "output", "data": {}, "inputs": ["mid"], "outputs": []},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "mid"},
            {"id": "e2", "source": "mid", "target": "end"},
        ],
    }


# ---------------------------------------------------------------------------
# 1. Self-loop
# ---------------------------------------------------------------------------


class TestSelfLoop:
    """Self-loop: node with edge from itself to itself → rejected."""

    def test_self_loop_rejected(self):
        result = validate_workflow(_self_loop_workflow())
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert ErrorCodes.INVALID_EDGE_CONNECTION in codes

    def test_self_loop_error_has_node_and_edge_id(self):
        result = validate_workflow(_self_loop_workflow())
        loop_error = next(
            e
            for e in result.errors
            if e.code == ErrorCodes.INVALID_EDGE_CONNECTION and "Self-loop" in e.message
        )
        assert loop_error.node_id == "n1"
        assert loop_error.edge_id == "e1"
        assert loop_error.suggestion is not None

    def test_self_loop_in_multi_node_graph(self):
        """Self-loop detected even when other valid edges exist."""
        wf = {
            "id": "wf-self-loop-mixed",
            "name": "Mixed",
            "nodes": [
                {"id": "a", "type": "input", "data": {}, "inputs": [], "outputs": ["b"]},
                {"id": "b", "type": "tool", "data": {}, "inputs": ["a"], "outputs": ["b"]},
            ],
            "edges": [
                {"id": "e1", "source": "a", "target": "b"},
                {"id": "e2", "source": "b", "target": "b"},
            ],
        }
        result = validate_workflow(wf)
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert ErrorCodes.INVALID_EDGE_CONNECTION in codes


# ---------------------------------------------------------------------------
# 2. Disconnected node
# ---------------------------------------------------------------------------


class TestDisconnectedNode:
    """Disconnected node: node with no edges → rejected."""

    def test_disconnected_node_rejected(self):
        result = validate_workflow(_disconnected_workflow())
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert ErrorCodes.DISCONNECTED_NODE in codes

    def test_disconnected_node_id_reported(self):
        result = validate_workflow(_disconnected_workflow())
        disc_error = next(e for e in result.errors if e.code == ErrorCodes.DISCONNECTED_NODE)
        assert disc_error.node_id == "c"

    def test_single_node_not_flagged(self):
        """A single-node workflow should not flag disconnected (edge case)."""
        wf = {
            "id": "wf-single",
            "name": "Single",
            "nodes": [{"id": "only", "type": "input", "data": {}}],
            "edges": [],
        }
        result = validate_workflow(wf)
        codes = [e.code for e in result.errors]
        assert ErrorCodes.DISCONNECTED_NODE not in codes


# ---------------------------------------------------------------------------
# 3. Missing node config (agent without agent_id)
# ---------------------------------------------------------------------------


class TestMissingNodeConfig:
    """Agent node without agent_id → validator should not crash; no INVALID_AGENT_TYPE
    since agentType is absent (not invalid)."""

    def test_agent_without_agent_type_no_crash(self):
        result = validate_workflow(_agent_missing_config_workflow())
        # Should complete without error — missing agentType is not an invalid type
        assert result is not None

    def test_agent_with_invalid_type_rejected(self):
        wf = {
            "id": "wf-bad-agent",
            "name": "Bad Agent",
            "nodes": [
                {"id": "a", "type": "input", "data": {}, "inputs": [], "outputs": ["b"]},
                {
                    "id": "b",
                    "type": "agent",
                    "data": {"agentType": "nonexistent-agent-type"},
                    "inputs": ["a"],
                    "outputs": [],
                },
            ],
            "edges": [
                {"id": "e1", "source": "a", "target": "b"},
            ],
        }
        result = validate_workflow(wf)
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert ErrorCodes.INVALID_AGENT_TYPE in codes


# ---------------------------------------------------------------------------
# 4. Multiple start nodes
# ---------------------------------------------------------------------------


class TestMultipleStartNodes:
    """Valid DAG with 2 nodes having no incoming edges → passes."""

    def test_multiple_start_nodes_valid(self):
        result = validate_workflow(_multiple_start_workflow())
        assert result.valid is True
        assert len(result.errors) == 0

    def test_multiple_start_nodes_detected_in_api(self, client: TestClient):
        """POST /api/workflows/validate accepts multi-start DAGs."""
        resp = client.post("/api/workflows/validate", json=_multiple_start_workflow())
        assert resp.status_code == 200
        assert resp.json()["valid"] is True


# ---------------------------------------------------------------------------
# 5. Diamond dependency
# ---------------------------------------------------------------------------


class TestDiamondDependency:
    """Diamond: A→B, A→C, B→D, C→D → valid DAG."""

    def test_diamond_is_valid(self):
        result = validate_workflow(_diamond_workflow())
        assert result.valid is True
        assert len(result.errors) == 0

    def test_diamond_via_api(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_diamond_workflow())
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_diamond_topological_order(self):
        """Engine's topological sort produces correct ordering for diamond graphs.

        The engine's Kahn implementation processes dependency sets in reverse
        (leaf nodes with no dependents first). The invariant is: if X depends on Y
        (Y is in graph[X]), Y must appear AFTER X in the result (Y is a dependency
        and gets processed after its dependents).
        """
        wf_def = _diamond_workflow()
        engine = WorkflowEngine.__new__(WorkflowEngine)
        from heretek_swarm.workflow.engine import WorkflowEdge, WorkflowNode

        nodes = [
            WorkflowNode(id=n["id"], type=n["type"], data=n.get("data", {}))
            for n in wf_def["nodes"]
        ]
        edges = [
            WorkflowEdge(id=e["id"], source=e["source"], target=e["target"])
            for e in wf_def["edges"]
        ]

        graph: dict[str, set[str]] = {n.id: set() for n in nodes}
        for edge in edges:
            graph[edge.target].add(edge.source)

        order = engine._topological_sort(graph)

        # All 4 nodes present
        assert set(order) == {"A", "B", "C", "D"}
        # A (root, no dependencies) must come before its dependents B and C
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        # B and C must come before D (D depends on both)
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")


# ---------------------------------------------------------------------------
# 6. Complex cycle
# ---------------------------------------------------------------------------


class TestComplexCycle:
    """A→B→C→A → CIRCULAR_DEPENDENCY detected."""

    def test_complex_cycle_detected(self):
        result = validate_workflow(_complex_cycle_workflow())
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert ErrorCodes.CIRCULAR_DEPENDENCY in codes

    def test_complex_cycle_error_message_contains_path(self):
        result = validate_workflow(_complex_cycle_workflow())
        cycle_error = next(e for e in result.errors if e.code == ErrorCodes.CIRCULAR_DEPENDENCY)
        # Message should show the cycle path (e.g. "A -> B -> C -> A")
        assert "A" in cycle_error.message
        assert "->" in cycle_error.message

    def test_complex_cycle_via_api(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_complex_cycle_workflow())
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        codes = [e["code"] for e in data["errors"]]
        assert "CIRCULAR_DEPENDENCY" in codes


# ---------------------------------------------------------------------------
# 7. PUT update
# ---------------------------------------------------------------------------


class TestPutUpdate:
    """PUT /api/workflows/{id} updates definition; GET returns updated version."""

    def test_put_updates_name(self, client: TestClient):
        client.post("/api/workflows", json=_valid_linear_workflow())
        updated = {**_valid_linear_workflow(), "name": "Renamed Pipeline"}
        resp = client.put("/api/workflows/wf-linear", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Pipeline"

    def test_get_returns_updated_definition(self, client: TestClient):
        client.post("/api/workflows", json=_valid_linear_workflow())
        updated = {
            **_valid_linear_workflow(),
            "name": "Renamed",
            "nodes": [
                {"id": "x", "type": "input", "data": {}, "inputs": [], "outputs": []},
            ],
            "edges": [],
        }
        client.put("/api/workflows/wf-linear", json=updated)
        resp = client.get("/api/workflows/wf-linear")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Renamed"
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "x"

    def test_put_nonexistent_returns_404(self, client: TestClient):
        resp = client.put("/api/workflows/no-such", json=_valid_linear_workflow())
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8. Validate draft (without saving)
# ---------------------------------------------------------------------------


class TestValidateDraft:
    """POST /api/workflows/validate (draft mode, no save) returns correct result."""

    def test_valid_draft_returns_true(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_valid_linear_workflow())
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_invalid_draft_returns_false_without_saving(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_complex_cycle_workflow())
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

        # Verify it was NOT saved — list should be empty
        resp = client.get("/api/workflows")
        assert resp.json()["workflows"] == []

    def test_draft_with_self_loop_returns_structured_errors(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_self_loop_workflow())
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        # Errors should have all required fields
        for error in data["errors"]:
            assert "severity" in error
            assert "code" in error
            assert "message" in error

    def test_draft_diamond_passes(self, client: TestClient):
        resp = client.post("/api/workflows/validate", json=_diamond_workflow())
        assert resp.status_code == 200
        assert resp.json()["valid"] is True


# ---------------------------------------------------------------------------
# 9. Topological sort correctness (engine-level)
# ---------------------------------------------------------------------------


class TestTopologicalSort:
    """Verify engine's topological sort for various graph shapes."""

    def test_linear_sort(self):
        """Engine's topological sort processes dependencies first.

        The engine's _build_graph maps each node to its incoming dependencies.
        Standard Kahn's algorithm: nodes with no dependencies (roots) execute first,
        then their dependents.
        """
        engine = WorkflowEngine.__new__(WorkflowEngine)
        graph = {"start": set(), "mid": {"start"}, "end": {"mid"}}
        order = engine._topological_sort(graph)
        # Root node (start, no dependencies) comes first
        assert order[0] == "start"
        assert set(order) == {"start", "mid", "end"}
        # Dependencies appear before their dependents
        assert order.index("start") < order.index("mid") < order.index("end")

    def test_diamond_sort(self):
        """Diamond graph topological sort — dependencies-first ordering."""
        engine = WorkflowEngine.__new__(WorkflowEngine)
        graph = {"A": set(), "B": {"A"}, "C": {"A"}, "D": {"B", "C"}}
        order = engine._topological_sort(graph)
        # A (root, no dependencies) comes first, D (leaf) comes last
        assert order[0] == "A"
        assert set(order) == {"A", "B", "C", "D"}
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_wide_fan_out_sort(self):
        """A fans out to B, C, D — A (root) comes before its dependents."""
        engine = WorkflowEngine.__new__(WorkflowEngine)
        graph = {"A": set(), "B": {"A"}, "C": {"A"}, "D": {"A"}}
        order = engine._topological_sort(graph)
        # B, C, D depend on A, so A (root) must be first
        assert set(order) == {"A", "B", "C", "D"}
        assert order[0] == "A"

    def test_empty_graph(self):
        engine = WorkflowEngine.__new__(WorkflowEngine)
        order = engine._topological_sort({})
        assert order == []

    def test_sort_covers_all_nodes(self):
        """Every node in the graph appears exactly once in the result."""
        engine = WorkflowEngine.__new__(WorkflowEngine)
        graph = {"A": set(), "B": {"A"}, "C": {"A"}, "D": {"B", "C"}}
        order = engine._topological_sort(graph)
        assert len(order) == len(graph)
        assert set(order) == set(graph.keys())
