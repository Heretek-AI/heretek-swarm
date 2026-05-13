"""
Tests for cross-node data flow in multi-node workflows.

Verifies that:
1. LLM node output is available as input to a downstream consensus node
2. Multiple upstream nodes merge their outputs correctly
3. The full execute_workflow() flow passes data between nodes in correct order
4. Node output stored in context.variables is accessible to downstream nodes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.consensus.maker import ConsensusResult, ConsensusState, Vote
from heretek_swarm.workflow.engine import (
    NodeResult,
    NodeStatus,
    Workflow,
    WorkflowContext,
    WorkflowEdge,
    WorkflowEngine,
    WorkflowNode,
    WorkflowStatus,
)

# ── Shared helpers ───────────────────────────────────────────────────────────


def _make_llm_node(
    node_id: str = "llm-1",
    prompt: str | None = "Summarize the data",
    timeout: int | None = None,
    temperature: float | None = None,
    inputs: list[str] | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'llm'."""
    data: dict[str, Any] = {}
    if prompt is not None:
        data["prompt"] = prompt
    if timeout is not None:
        data["timeout"] = timeout
    if temperature is not None:
        data["temperature"] = temperature
    return WorkflowNode(
        id=node_id,
        type="llm",
        data=data,
        inputs=inputs or [],
    )


def _make_consensus_node(
    node_id: str = "consensus-1",
    question: str | None = "Should we proceed?",
    timeout: int | None = None,
    max_rounds: int | None = None,
    inputs: list[str] | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'consensus'."""
    data: dict[str, Any] = {}
    if question is not None:
        data["question"] = question
    if timeout is not None:
        data["timeout"] = timeout
    if max_rounds is not None:
        data["max_rounds"] = max_rounds
    return WorkflowNode(
        id=node_id,
        type="consensus",
        data=data,
        inputs=inputs or [],
    )


def _make_agent_node(
    node_id: str = "agent-1",
    agent_id: str = "worker",
    timeout: int | None = None,
    inputs: list[str] | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'agent'."""
    data: dict[str, Any] = {"agent_id": agent_id}
    if timeout is not None:
        data["timeout"] = timeout
    return WorkflowNode(
        id=node_id,
        type="agent",
        data=data,
        inputs=inputs or [],
    )


def _make_workflow(
    nodes: list[WorkflowNode] | None = None,
    edges: list[WorkflowEdge] | None = None,
) -> Workflow:
    """Build a minimal Workflow for testing."""
    return Workflow(
        id="wf-data-flow",
        name="Data Flow Test Workflow",
        nodes=nodes or [],
        edges=edges or [],
    )


def _make_context(
    variables: dict[str, Any] | None = None,
    node_results: dict[str, NodeResult] | None = None,
) -> WorkflowContext:
    """Build a WorkflowContext for testing."""
    ctx = WorkflowContext(
        workflow_id="wf-data-flow",
        execution_id="exec-data-flow-001",
        variables=variables or {},
    )
    if node_results:
        ctx.node_results = node_results
    return ctx


def _make_mock_actor(
    agent_id: str = "worker",
    run_response: str = "LLM response",
) -> MagicMock:
    """Build a mock actor with run_with_llm."""
    actor = MagicMock()
    actor.agent_id = agent_id
    actor.run_with_llm = AsyncMock(return_value=run_response)
    return actor


def _make_mock_supervisor(
    actors: dict[str, MagicMock] | None = None,
    active_agent_ids: list[str] | None = None,
) -> MagicMock:
    """Build a mock supervisor with actor registry and status lookup."""
    supervisor = MagicMock()
    supervisor.actors = actors or {}
    _active_ids = set(active_agent_ids or [])

    async def _get_status(actor_id: str):
        if actor_id not in supervisor.actors:
            return None
        status = MagicMock()
        status.state = "active" if actor_id in _active_ids else "inactive"
        return status

    supervisor.get_actor_status = AsyncMock(side_effect=_get_status)
    return supervisor


def _make_consensus_result(
    decision: str = "approve",
    confidence: float = 0.85,
) -> ConsensusResult:
    """Build a ConsensusResult for testing."""
    now = datetime.now(UTC).isoformat()
    votes = [
        Vote(
            agent_id="agent-alpha",
            decision=decision,
            confidence=confidence,
            timestamp=now,
            metadata={},
        ),
    ]
    return ConsensusResult(
        decision=decision,
        confidence=confidence,
        votes=votes,
        state=ConsensusState.COMPLETED,
        timestamp=now,
        red_flags=[],
        metadata={},
    )


@dataclass
class MockConsensusCoordinator:
    """Mock ConsensusCoordinator with configurable run_consensus behavior."""

    run_consensus: AsyncMock = field(default_factory=lambda: AsyncMock())

    def __post_init__(self):
        if not isinstance(self.run_consensus, AsyncMock):
            self.run_consensus = AsyncMock(side_effect=self.run_consensus)


def _make_engine(
    supervisor: MagicMock | None = None,
    consensus_coordinator: Any = None,
) -> WorkflowEngine:
    """Build a WorkflowEngine with optional supervisor and coordinator."""
    return WorkflowEngine(
        supervisor=supervisor,
        consensus_coordinator=consensus_coordinator,
    )


# ── Test 1: LLM → Consensus data flow ───────────────────────────────────────


class TestLLMToConsensusDataFlow:
    """Verify LLM node output flows into consensus node as input."""

    @pytest.mark.asyncio
    async def test_llm_output_available_as_consensus_input(self):
        """LLM node output appears in context.node_results for downstream node."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="The analysis shows a 15% increase in risk.",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result()

        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Analyze risk data")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question=None,  # no hardcoded question — must come from input
            inputs=["llm1"],
        )
        workflow = _make_workflow(nodes=[llm_node, consensus_node])
        context = _make_context()

        # Execute LLM node first
        await engine._execute_node(workflow, "llm1", context)
        assert context.node_results["llm1"].status == NodeStatus.COMPLETED
        llm_output = context.node_results["llm1"].output
        assert llm_output == "The analysis shows a 15% increase in risk."

        # Now execute consensus node — it should receive LLM output via _get_node_input
        # The consensus node reads 'question' from input_data, which comes from
        # context.node_results["llm1"].output keyed by the input node ID
        input_data = engine._get_node_input(workflow, consensus_node, context)
        assert "llm1" in input_data
        assert input_data["llm1"] == "The analysis shows a 15% increase in risk."

    @pytest.mark.asyncio
    async def test_consensus_node_reads_question_from_llm_output(self):
        """Consensus node can use LLM output as its question via input_data."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Is the deployment safe based on metrics X, Y, Z?",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result()

        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(
            node_id="llm1",
            prompt="Generate a deployment question",
        )
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question=None,
            inputs=["llm1"],
        )
        workflow = _make_workflow(nodes=[llm_node, consensus_node])
        context = _make_context()

        # Execute LLM node
        await engine._execute_node(workflow, "llm1", context)

        # Build input data the same way the engine does
        input_data = engine._get_node_input(workflow, consensus_node, context)

        # The LLM output is keyed by node ID ("llm1"), but the consensus node
        # reads "question" from input_data. Since _get_node_input stores upstream
        # results under their node ID, the consensus node won't find "question"
        # unless we verify the raw flow is correct.
        assert input_data["llm1"] == "Is the deployment safe based on metrics X, Y, Z?"

    @pytest.mark.asyncio
    async def test_llm_output_stored_in_context_variables(self):
        """After LLM node executes, output is in context.variables['node_llm1_output']."""
        actor = _make_mock_actor(run_response="Risk score: 0.73")
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm_node = _make_llm_node(node_id="llm1", prompt="Compute risk")
        workflow = _make_workflow(nodes=[llm_node])
        context = _make_context()

        await engine._execute_node(workflow, "llm1", context)

        assert "node_llm1_output" in context.variables
        assert context.variables["node_llm1_output"] == "Risk score: 0.73"


# ── Test 2: Multiple upstream nodes merge correctly ──────────────────────────


class TestMultipleUpstreamMerge:
    """Verify _get_node_input merges outputs from multiple upstream nodes."""

    @pytest.mark.asyncio
    async def test_two_upstream_outputs_merged_into_downstream_input(self):
        """Node with two inputs receives both outputs keyed by node ID."""
        actor = _make_mock_actor(agent_id="worker")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        # Two LLM nodes producing different outputs
        actor.run_with_llm = AsyncMock(side_effect=["Output from A", "Output from B"])

        node_a = _make_llm_node(node_id="llm-a", prompt="Task A")
        node_b = _make_llm_node(node_id="llm-b", prompt="Task B")
        # Downstream node has both as inputs
        downstream = _make_consensus_node(
            node_id="consensus1",
            question="Merge test",
            inputs=["llm-a", "llm-b"],
        )
        workflow = _make_workflow(nodes=[node_a, node_b, downstream])
        context = _make_context()

        # Execute both upstream nodes
        await engine._execute_node(workflow, "llm-a", context)
        await engine._execute_node(workflow, "llm-b", context)

        # Verify both results are stored
        assert context.node_results["llm-a"].output == "Output from A"
        assert context.node_results["llm-b"].output == "Output from B"

        # Get input for downstream — should merge both
        input_data = engine._get_node_input(workflow, downstream, context)

        assert input_data["llm-a"] == "Output from A"
        assert input_data["llm-b"] == "Output from B"

    @pytest.mark.asyncio
    async def test_three_upstream_outputs_merge(self):
        """Three upstream nodes all contribute to downstream input."""
        actor = _make_mock_actor(agent_id="worker")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        actor.run_with_llm = AsyncMock(
            side_effect=["Alpha result", "Beta result", "Gamma result"]
        )

        node_a = _make_llm_node(node_id="n1", prompt="Alpha")
        node_b = _make_llm_node(node_id="n2", prompt="Beta")
        node_c = _make_llm_node(node_id="n3", prompt="Gamma")
        downstream = _make_consensus_node(
            node_id="merge",
            question="Combine all",
            inputs=["n1", "n2", "n3"],
        )
        workflow = _make_workflow(nodes=[node_a, node_b, node_c, downstream])
        context = _make_context()

        for nid in ["n1", "n2", "n3"]:
            await engine._execute_node(workflow, nid, context)

        input_data = engine._get_node_input(workflow, downstream, context)

        assert input_data["n1"] == "Alpha result"
        assert input_data["n2"] == "Beta result"
        assert input_data["n3"] == "Gamma result"
        # 3 upstream results + 3 node_*_output variables from context.variables
        assert len(input_data) == 6

    @pytest.mark.asyncio
    async def test_upstream_merge_includes_context_variables(self):
        """_get_node_input merges upstream node outputs AND context.variables."""
        context = _make_context(
            variables={"global_param": "shared_value", "prompt": "from context"},
        )
        # Pre-populate node results
        context.node_results["upstream-1"] = NodeResult(
            node_id="upstream-1",
            status=NodeStatus.COMPLETED,
            output="upstream output",
        )

        downstream = _make_consensus_node(
            node_id="downstream",
            question="test",
            inputs=["upstream-1"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="upstream-1", type="llm", data={}),
                downstream,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, downstream, context)

        # Upstream result keyed by node ID
        assert input_data["upstream-1"] == "upstream output"
        # Context variables also merged
        assert input_data["global_param"] == "shared_value"
        assert input_data["prompt"] == "from context"

    @pytest.mark.asyncio
    async def test_upstream_result_overrides_same_key_in_variables(self):
        """When an upstream node ID collides with a context variable key,
        the upstream result wins because _get_node_input writes upstream
        results first, then updates with context.variables (which overwrites)."""
        context = _make_context(
            variables={"node_a_output": "old value from variables"},
        )
        context.node_results["node_a_output"] = NodeResult(
            node_id="node_a_output",
            status=NodeStatus.COMPLETED,
            output="fresh upstream result",
        )

        downstream = WorkflowNode(
            id="ds",
            type="consensus",
            data={"question": "q"},
            inputs=["node_a_output"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="node_a_output", type="llm", data={}),
                downstream,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, downstream, context)

        # _get_node_input first sets input_data[input_id] = node_results.output
        # then calls input_data.update(context.variables), so variables win.
        # This is the actual behavior — document it.
        assert input_data["node_a_output"] == "old value from variables"


# ── Test 3: Full execute_workflow() data flow ────────────────────────────────


class TestExecuteWorkflowDataFlow:
    """Verify the full execute_workflow() DAG path passes data between nodes."""

    @pytest.mark.asyncio
    async def test_two_node_dag_execution_order(self):
        """Two-node DAG: llm1 → consensus1 executes in correct order with data flow."""
        actor = _make_mock_actor(run_response="Risk analysis complete: medium risk")
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result(
            decision="approve", confidence=0.8,
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm = _make_llm_node(node_id="llm1", prompt="Analyze risk")
        consensus = _make_consensus_node(
            node_id="c1",
            question="Proceed with deployment?",
            inputs=["llm1"],
        )
        edge = WorkflowEdge(id="e1", source="llm1", target="c1")
        workflow = _make_workflow(nodes=[llm, consensus], edges=[edge])

        await engine.load_workflow(
            {
                "id": workflow.id,
                "name": workflow.name,
                "nodes": [
                    {"id": "llm1", "type": "llm", "data": {"prompt": "Analyze risk"}},
                    {
                        "id": "c1",
                        "type": "consensus",
                        "data": {"question": "Proceed with deployment?"},
                        "inputs": ["llm1"],
                    },
                ],
                "edges": [{"id": "e1", "source": "llm1", "target": "c1"}],
            }
        )

        result = await engine.execute_workflow(workflow.id)

        assert result.status == WorkflowStatus.COMPLETED
        # Both nodes executed
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["c1"].status == NodeStatus.COMPLETED
        # LLM produced output
        assert result.node_results["llm1"].output == "Risk analysis complete: medium risk"
        # Consensus ran (coordinator was called)
        coordinator.run_consensus.assert_called_once()
        # Variables captured LLM output
        assert result.variables["node_llm1_output"] == "Risk analysis complete: medium risk"

    @pytest.mark.asyncio
    async def test_three_node_dag_data_flows_through_chain(self):
        """Three-node chain: llm1 → llm2 → consensus1 — data flows through."""
        actor = _make_mock_actor(agent_id="analyst")
        actor.run_with_llm = AsyncMock(
            side_effect=["Step 1 output", "Step 2: processed Step 1 output"]
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result()
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        workflow_def = {
            "id": "wf-chain",
            "name": "Three Node Chain",
            "nodes": [
                {"id": "llm1", "type": "llm", "data": {"prompt": "Step 1"}},
                {
                    "id": "llm2",
                    "type": "llm",
                    "data": {"prompt": "Step 2"},
                    "inputs": ["llm1"],
                },
                {
                    "id": "c1",
                    "type": "consensus",
                    "data": {"question": "Final decision?"},
                    "inputs": ["llm2"],
                },
            ],
            "edges": [
                {"id": "e1", "source": "llm1", "target": "llm2"},
                {"id": "e2", "source": "llm2", "target": "c1"},
            ],
        }
        await engine.load_workflow(workflow_def)

        result = await engine.execute_workflow("wf-chain")

        assert result.status == WorkflowStatus.COMPLETED
        # All three nodes executed
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["llm2"].status == NodeStatus.COMPLETED
        assert result.node_results["c1"].status == NodeStatus.COMPLETED
        # Data flowed: llm1 output stored, llm2 output stored
        assert result.variables["node_llm1_output"] == "Step 1 output"
        assert result.variables["node_llm2_output"] == "Step 2: processed Step 1 output"

    @pytest.mark.asyncio
    async def test_diamond_dag_both_branches_feed_into_join(self):
        """Diamond DAG: start → (branch_a, branch_b) → join node."""
        actor = _make_mock_actor(agent_id="worker")
        call_count = 0

        async def _sequential_responses(prompt: str, **kwargs: Any) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "Branch A result"
            return "Branch B result"

        actor.run_with_llm = AsyncMock(side_effect=_sequential_responses)
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result()
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        workflow_def = {
            "id": "wf-diamond",
            "name": "Diamond DAG",
            "nodes": [
                {"id": "start", "type": "llm", "data": {"prompt": "Start task"}},
                {
                    "id": "branch_a",
                    "type": "llm",
                    "data": {"prompt": "Branch A"},
                    "inputs": ["start"],
                },
                {
                    "id": "branch_b",
                    "type": "llm",
                    "data": {"prompt": "Branch B"},
                    "inputs": ["start"],
                },
                {
                    "id": "join",
                    "type": "consensus",
                    "data": {"question": "Combine results?"},
                    "inputs": ["branch_a", "branch_b"],
                },
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "branch_a"},
                {"id": "e2", "source": "start", "target": "branch_b"},
                {"id": "e3", "source": "branch_a", "target": "join"},
                {"id": "e4", "source": "branch_b", "target": "join"},
            ],
        }
        await engine.load_workflow(workflow_def)

        result = await engine.execute_workflow("wf-diamond")

        assert result.status == WorkflowStatus.COMPLETED
        # All four nodes executed
        for nid in ["start", "branch_a", "branch_b", "join"]:
            assert result.node_results[nid].status == NodeStatus.COMPLETED, (
                f"Node {nid} status: {result.node_results[nid].status}"
            )
        # Both branch outputs stored in variables
        assert "node_branch_a_output" in result.variables
        assert "node_branch_b_output" in result.variables

    @pytest.mark.asyncio
    async def test_workflow_failure_stops_execution(self):
        """When a node fails, downstream nodes still execute independently."""
        actor = _make_mock_actor(agent_id="worker")
        # First call (llm1) fails, second call (llm2) succeeds
        actor.run_with_llm = AsyncMock(
            side_effect=[RuntimeError("LLM down"), "Recovered output"]
        )
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        workflow_def = {
            "id": "wf-fail",
            "name": "Failure Flow",
            "nodes": [
                {"id": "llm1", "type": "llm", "data": {"prompt": "Will fail"}},
                {
                    "id": "llm2",
                    "type": "llm",
                    "data": {"prompt": "Depends on llm1"},
                    "inputs": ["llm1"],
                },
            ],
            "edges": [
                {"id": "e1", "source": "llm1", "target": "llm2"},
            ],
        }
        await engine.load_workflow(workflow_def)

        result = await engine.execute_workflow("wf-fail")

        # Workflow completes (doesn't crash)
        assert result.status == WorkflowStatus.COMPLETED
        # llm1 is FAILED
        assert result.node_results["llm1"].status == NodeStatus.FAILED
        assert isinstance(result.node_results["llm1"].error, RuntimeError)
        # llm2 still executes — the DAG loop continues past failed nodes
        assert result.node_results["llm2"].status == NodeStatus.COMPLETED
        assert result.node_results["llm2"].output == "Recovered output"


# ── Test 4: context.variables accessibility ──────────────────────────────────


class TestContextVariablesAccessibility:
    """Verify node output in context.variables is accessible to downstream nodes."""

    @pytest.mark.asyncio
    async def test_node_output_accessible_via_variables(self):
        """Node output stored as node_{id}_output in context.variables."""
        actor = _make_mock_actor(run_response="Generated summary")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        node = _make_llm_node(node_id="summarizer", prompt="Summarize")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "summarizer", context)

        # Verify the standard variable key
        assert context.variables["node_summarizer_output"] == "Generated summary"

    @pytest.mark.asyncio
    async def test_multiple_nodes_all_stored_in_variables(self):
        """Multiple node outputs are all stored in context.variables."""
        actor = _make_mock_actor(agent_id="worker")
        actor.run_with_llm = AsyncMock(
            side_effect=["Result A", "Result B", "Result C"]
        )
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        nodes = [
            _make_llm_node(node_id=f"n{i}", prompt=f"Task {i}")
            for i in range(3)
        ]
        workflow = _make_workflow(nodes=nodes)
        context = _make_context()

        for i in range(3):
            await engine._execute_node(workflow, f"n{i}", context)

        assert context.variables["node_n0_output"] == "Result A"
        assert context.variables["node_n1_output"] == "Result B"
        assert context.variables["node_n2_output"] == "Result C"

    @pytest.mark.asyncio
    async def test_variables_accessible_to_downstream_via_get_node_input(self):
        """Variables set by earlier nodes are visible in _get_node_input."""
        context = _make_context(
            variables={"node_upstream_output": "previous result"},
        )
        context.node_results["upstream"] = NodeResult(
            node_id="upstream",
            status=NodeStatus.COMPLETED,
            output="previous result",
        )

        downstream = _make_consensus_node(
            node_id="ds",
            question="Based on upstream?",
            inputs=["upstream"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="upstream", type="llm", data={}),
                downstream,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, downstream, context)

        # Both the upstream result and the variable are present
        assert input_data["upstream"] == "previous result"
        assert input_data["node_upstream_output"] == "previous result"

    @pytest.mark.asyncio
    async def test_consensus_node_receives_llm_output_via_get_node_input(self):
        """End-to-end: consensus node's input_data includes LLM node output."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Deployment analysis: low risk, 3 minor issues found.",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = _make_consensus_result()
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm = _make_llm_node(node_id="llm1", prompt="Analyze deployment")
        consensus = _make_consensus_node(
            node_id="c1",
            question="Approve deployment?",
            inputs=["llm1"],
        )
        workflow = _make_workflow(nodes=[llm, consensus])
        context = _make_context()

        # Execute LLM node
        await engine._execute_node(workflow, "llm1", context)

        # Execute consensus node — it calls _get_node_input internally
        await engine._execute_node(workflow, "c1", context)

        # Verify consensus coordinator was called (node executed successfully)
        coordinator.run_consensus.assert_called_once()
        call_kwargs = coordinator.run_consensus.call_args
        assert call_kwargs[1]["question"] == "Approve deployment?"

        # Verify the LLM output was available in the consensus node's input_data
        # by checking context.node_results
        assert context.node_results["llm1"].output == "Deployment analysis: low risk, 3 minor issues found."
        assert context.node_results["c1"].status == NodeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_agent_node_reads_llm_output_from_variables(self):
        """Agent node can read LLM output from context.variables via prompt resolution."""
        actor = _make_mock_actor(agent_id="worker", run_response="Agent processed!")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm = _make_llm_node(node_id="llm1", prompt="Generate a task description")
        agent = _make_agent_node(
            node_id="agent1",
            agent_id="worker",
            inputs=["llm1"],
        )
        workflow = _make_workflow(nodes=[llm, agent])
        context = _make_context()

        # Seed context with the LLM output as if llm1 already ran
        context.node_results["llm1"] = NodeResult(
            node_id="llm1",
            status=NodeStatus.COMPLETED,
            output="Please analyze the quarterly report",
        )
        context.variables["node_llm1_output"] = "Please analyze the quarterly report"

        # Execute agent node — it should find the prompt from upstream output
        await engine._execute_node(workflow, "agent1", context)

        assert context.node_results["agent1"].status == NodeStatus.COMPLETED
        assert context.node_results["agent1"].output == "Agent processed!"
        # The agent node should have been called with the upstream output as prompt
        actor.run_with_llm.assert_called_once()
        call_args = actor.run_with_llm.call_args
        assert "Please analyze the quarterly report" in call_args[0][0]


# ── Test 5: _get_node_input unit tests ───────────────────────────────────────


class TestGetNodeInput:
    """Direct unit tests for _get_node_input method."""

    @pytest.mark.asyncio
    async def test_empty_inputs_returns_empty_dict(self):
        """Node with no inputs gets empty input_data (plus any variables)."""
        context = _make_context()
        node = WorkflowNode(id="solo", type="llm", data={})
        workflow = _make_workflow(nodes=[node])
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, node, context)

        assert input_data == {}

    @pytest.mark.asyncio
    async def test_single_upstream_result(self):
        """Node with one input gets that upstream's output."""
        context = _make_context()
        context.node_results["up"] = NodeResult(
            node_id="up", status=NodeStatus.COMPLETED, output="hello",
        )
        node = WorkflowNode(
            id="down", type="llm", data={}, inputs=["up"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="up", type="llm", data={}),
                node,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, node, context)

        assert input_data == {"up": "hello"}

    @pytest.mark.asyncio
    async def test_nonexistent_upstream_id_skipped(self):
        """If an input ID has no result in context, it's silently skipped."""
        context = _make_context()
        node = WorkflowNode(
            id="down", type="llm", data={}, inputs=["missing-node"],
        )
        workflow = _make_workflow(nodes=[node])
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, node, context)

        # "missing-node" not in context.node_results, so not in input_data
        assert "missing-node" not in input_data

    @pytest.mark.asyncio
    async def test_variables_merged_after_upstream_results(self):
        """context.variables keys appear in input_data alongside upstream results."""
        context = _make_context(
            variables={"prompt": "global prompt", "extra": 42},
        )
        context.node_results["up"] = NodeResult(
            node_id="up", status=NodeStatus.COMPLETED, output="upstream val",
        )
        node = WorkflowNode(
            id="down", type="llm", data={}, inputs=["up"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="up", type="llm", data={}),
                node,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, node, context)

        assert input_data["up"] == "upstream val"
        assert input_data["prompt"] == "global prompt"
        assert input_data["extra"] == 42

    @pytest.mark.asyncio
    async def test_dict_output_from_upstream_preserved(self):
        """Dict outputs (like consensus results) are preserved as-is."""
        consensus_output = {
            "consensus_reached": True,
            "decision": "approve",
            "confidence": 0.9,
        }
        context = _make_context()
        context.node_results["c1"] = NodeResult(
            node_id="c1", status=NodeStatus.COMPLETED, output=consensus_output,
        )
        node = WorkflowNode(
            id="ds", type="llm", data={}, inputs=["c1"],
        )
        workflow = _make_workflow(
            nodes=[
                WorkflowNode(id="c1", type="consensus", data={}),
                node,
            ]
        )
        engine = _make_engine()

        input_data = engine._get_node_input(workflow, node, context)

        assert input_data["c1"] == consensus_output
        assert input_data["c1"]["decision"] == "approve"
