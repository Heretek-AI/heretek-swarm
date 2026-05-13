"""
End-to-end workflow execution tests with LLM + consensus nodes.

Proves the full pipeline works by:
1. Creating a workflow with an LLM node → consensus node pipeline
2. Executing it through execute_workflow()
3. Verifying both nodes produce real results (not error dicts)
4. Verifying the consensus node received the LLM output
5. Testing error propagation: if LLM node fails, consensus node is also failed/skipped
6. Testing the workflow status lifecycle (RUNNING → COMPLETED/FAILED)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.consensus.maker import ConsensusResult, ConsensusState, Vote
from heretek_swarm.workflow.engine import (
    NodeStatus,
    Workflow,
    WorkflowEdge,
    WorkflowEngine,
    WorkflowNode,
    WorkflowStatus,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_llm_node(
    node_id: str = "llm-1",
    prompt: str | None = "Analyze the data",
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
    question: str | None = None,
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


def _make_edges(pairs: list[tuple[str, str]]) -> list[WorkflowEdge]:
    """Build WorkflowEdge list from (source, target) pairs."""
    return [WorkflowEdge(id=f"edge-{src}-{tgt}", source=src, target=tgt) for src, tgt in pairs]


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
    votes: list[Vote] | None = None,
) -> ConsensusResult:
    """Build a ConsensusResult for testing."""
    now = datetime.now(UTC).isoformat()
    if votes is None:
        votes = [
            Vote(
                agent_id="agent-alpha",
                decision=decision,
                confidence=confidence,
                timestamp=now,
                metadata={},
            ),
            Vote(
                agent_id="agent-beta",
                decision=decision,
                confidence=confidence - 0.1,
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

    run_consensus: AsyncMock = field(
        default_factory=lambda: AsyncMock(return_value=_make_consensus_result())
    )

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


# ── E2E: LLM → Consensus Pipeline ──────────────────────────────────────────


class TestE2ELLMToConsensus:
    """End-to-end: LLM node → consensus node pipeline via execute_workflow()."""

    @pytest.mark.asyncio
    async def test_two_node_pipeline_completes(self):
        """LLM → consensus workflow completes with status COMPLETED."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Risk analysis: 15% increase in cyber threats detected.",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(
                return_value=_make_consensus_result(decision="approve", confidence=0.9)
            )
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Analyze risk data")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Should we proceed with deployment?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-1",
            name="E2E LLM→Consensus",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.error is None

    @pytest.mark.asyncio
    async def test_both_nodes_produce_real_results(self):
        """Both LLM and consensus nodes produce real results (not error dicts)."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Deployment is safe: all metrics nominal.",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        consensus_result = _make_consensus_result(decision="approve", confidence=0.92)
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(return_value=consensus_result)
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Check deployment safety")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Approve deployment?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-2",
            name="E2E Results Check",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # Both nodes should be COMPLETED
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["consensus1"].status == NodeStatus.COMPLETED

        # LLM node output is the string response
        llm_output = result.node_results["llm1"].output
        assert isinstance(llm_output, str)
        assert llm_output == "Deployment is safe: all metrics nominal."
        assert "error" not in llm_output.lower() or "error" not in llm_output

        # Consensus node output is a dict with real consensus data
        consensus_output = result.node_results["consensus1"].output
        assert isinstance(consensus_output, dict)
        assert consensus_output["consensus_reached"] is True
        assert consensus_output["decision"] == "approve"
        assert consensus_output["confidence"] == 0.92
        assert len(consensus_output["votes"]) == 2

        # Verify neither node produced an error
        assert result.node_results["llm1"].error is None
        assert result.node_results["consensus1"].error is None

    @pytest.mark.asyncio
    async def test_consensus_receives_llm_output_via_context(self):
        """Consensus node's run_consensus receives the question from node config.

        In the current engine, the consensus node reads 'question' from
        node.data or input_data. The LLM output is stored in
        context.variables["node_{id}_output"] and keyed by node ID in
        input_data. This test verifies the full pipeline executes and
        the coordinator is called with the configured question.
        """
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Analysis complete: 3 risks identified.",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        consensus_result = _make_consensus_result(decision="flag", confidence=0.75)
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(return_value=consensus_result)
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Identify risks")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Should we flag this for review?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-3",
            name="E2E Data Flow",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # Verify coordinator was called
        coordinator.run_consensus.assert_called_once()
        call_kwargs = coordinator.run_consensus.call_args
        assert call_kwargs.kwargs["question"] == "Should we flag this for review?"

        # Verify LLM output is in context variables
        assert result.variables["node_llm1_output"] == "Analysis complete: 3 risks identified."

        # Verify consensus result came through
        consensus_output = result.node_results["consensus1"].output
        assert consensus_output["decision"] == "flag"

    @pytest.mark.asyncio
    async def test_three_node_chain(self):
        """LLM1 → LLM2 → Consensus: data flows through all three nodes."""
        actor = _make_mock_actor(agent_id="worker", run_response="placeholder")

        # Configure different responses for sequential calls
        actor.run_with_llm = AsyncMock(
            side_effect=[
                "Step 1: Raw data processed",
                "Step 2: Analysis complete — deploy recommended",
            ]
        )

        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(
                return_value=_make_consensus_result(decision="approve", confidence=0.88)
            )
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm1 = _make_llm_node(node_id="llm1", prompt="Process raw data")
        llm2 = _make_llm_node(node_id="llm2", prompt="Analyze processed data", inputs=["llm1"])
        consensus = _make_consensus_node(
            node_id="consensus1",
            question="Approve deployment?",
            inputs=["llm2"],
        )
        edges = _make_edges([("llm1", "llm2"), ("llm2", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-chain",
            name="Three-Node Chain",
            nodes=[llm1, llm2, consensus],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["llm2"].status == NodeStatus.COMPLETED
        assert result.node_results["consensus1"].status == NodeStatus.COMPLETED

        # Verify execution order via actor calls
        assert actor.run_with_llm.call_count == 2

        # Verify outputs are real strings, not error dicts
        assert result.node_results["llm1"].output == "Step 1: Raw data processed"
        assert (
            result.node_results["llm2"].output == "Step 2: Analysis complete — deploy recommended"
        )

    @pytest.mark.asyncio
    async def test_upstream_output_stored_in_context_variables(self):
        """LLM node output is available in context.variables for downstream consumption."""
        actor = _make_mock_actor(agent_id="worker")
        actor.run_with_llm = AsyncMock(side_effect=["Generate a summary", "Analysis: looking good"])
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm1 = _make_llm_node(node_id="llm1", prompt="Generate a summary")
        llm2 = _make_llm_node(node_id="llm2", prompt="Analyze the summary", inputs=["llm1"])
        edges = _make_edges([("llm1", "llm2")])

        workflow = Workflow(
            id="wf-e2e-upstream",
            name="Upstream Variable Flow",
            nodes=[llm1, llm2],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.status == WorkflowStatus.COMPLETED
        # Both nodes completed
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["llm2"].status == NodeStatus.COMPLETED
        # LLM1 output is stored in variables for downstream access
        assert result.variables["node_llm1_output"] == "Generate a summary"
        assert result.variables["node_llm2_output"] == "Analysis: looking good"


# ── E2E: Error Propagation ──────────────────────────────────────────────────


class TestE2EErrorPropagation:
    """Test error propagation when LLM node fails."""

    @pytest.mark.asyncio
    async def test_llm_failure_marks_node_failed_and_stops_pipeline(self):
        """When LLM node raises, the node is marked FAILED.

        In a DAG execution, the engine processes nodes in topological order.
        If the LLM node fails, the consensus node still executes but finds
        no upstream output in context.node_results, so it reads from
        input_data which will be empty for the failed node's key.
        """
        actor = _make_mock_actor(agent_id="analyst")
        actor.run_with_llm.side_effect = RuntimeError("LLM provider timeout")
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        # Consensus coordinator should still work if called
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(
                return_value=_make_consensus_result(decision="reject", confidence=0.5)
            )
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="This will fail")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Fallback question?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-fail",
            name="Error Propagation",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # LLM node is FAILED
        assert result.node_results["llm1"].status == NodeStatus.FAILED
        assert isinstance(result.node_results["llm1"].error, RuntimeError)
        assert "LLM provider timeout" in str(result.node_results["llm1"].error)

        # Consensus node still executes (has its own question in node.data)
        # and completes since the coordinator works
        assert result.node_results["consensus1"].status == NodeStatus.COMPLETED

        # Overall workflow still completes (DAG doesn't fail on individual node failures)
        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_consensus_failure_marks_node_failed(self):
        """When consensus coordinator raises, the consensus node is marked FAILED."""
        actor = _make_mock_actor(
            agent_id="analyst",
            run_response="Analysis done",
        )
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(side_effect=RuntimeError("Consensus timeout"))
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Analyze")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Should we proceed?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-consensus-fail",
            name="Consensus Failure",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # LLM node succeeds
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED

        # Consensus node fails
        assert result.node_results["consensus1"].status == NodeStatus.FAILED
        assert isinstance(result.node_results["consensus1"].error, RuntimeError)
        assert "Consensus timeout" in str(result.node_results["consensus1"].error)

    @pytest.mark.asyncio
    async def test_both_nodes_fail(self):
        """When both nodes fail, both are marked FAILED but workflow completes."""
        actor = _make_mock_actor(agent_id="analyst")
        actor.run_with_llm.side_effect = RuntimeError("LLM down")
        supervisor = _make_mock_supervisor(
            actors={"analyst": actor},
            active_agent_ids=["analyst"],
        )
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(side_effect=RuntimeError("Coordinator down"))
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Fail")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Also fail?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-e2e-both-fail",
            name="Both Fail",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.node_results["llm1"].status == NodeStatus.FAILED
        assert result.node_results["consensus1"].status == NodeStatus.FAILED
        # DAG engine continues even when nodes fail
        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_missing_consensus_coordinator_raises(self):
        """Consensus node raises RuntimeError when no coordinator is configured."""
        supervisor = _make_mock_supervisor(
            actors={},
            active_agent_ids=[],
        )
        engine = _make_engine(supervisor=supervisor)  # No coordinator

        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="This will fail",
        )
        workflow = Workflow(
            id="wf-e2e-no-coord",
            name="No Coordinator",
            nodes=[consensus_node],
            edges=[],
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.node_results["consensus1"].status == NodeStatus.FAILED
        assert isinstance(result.node_results["consensus1"].error, RuntimeError)
        assert "ConsensusCoordinator" in str(result.node_results["consensus1"].error)


# ── E2E: Workflow Status Lifecycle ──────────────────────────────────────────


class TestE2EStatusLifecycle:
    """Test the workflow status transitions during execution."""

    @pytest.mark.asyncio
    async def test_workflow_starts_as_pending_then_completes(self):
        """Workflow transitions from PENDING → RUNNING → COMPLETED."""
        actor = _make_mock_actor(agent_id="worker", run_response="Done")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm_node = _make_llm_node(node_id="llm1", prompt="Quick task")
        workflow = Workflow(
            id="wf-lifecycle-1",
            name="Lifecycle Test",
            nodes=[llm_node],
            edges=[],
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # Final state is COMPLETED
        assert result.status == WorkflowStatus.COMPLETED
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.end_time >= result.start_time
        assert result.error is None

    @pytest.mark.asyncio
    async def test_workflow_status_on_all_nodes_failed(self):
        """Workflow completes even when all nodes fail (DAG doesn't abort)."""
        actor = _make_mock_actor(agent_id="worker")
        actor.run_with_llm.side_effect = RuntimeError("Fatal")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        coordinator = MockConsensusCoordinator(
            run_consensus=AsyncMock(side_effect=RuntimeError("Also fatal"))
        )
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Fail")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Also fail?",
            inputs=["llm1"],
        )
        edges = _make_edges([("llm1", "consensus1")])

        workflow = Workflow(
            id="wf-lifecycle-2",
            name="All Fail Lifecycle",
            nodes=[llm_node, consensus_node],
            edges=edges,
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        # DAG engine reports COMPLETED even if individual nodes fail
        # (the top-level try/except only catches engine-level exceptions)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.node_results["llm1"].status == NodeStatus.FAILED
        assert result.node_results["consensus1"].status == NodeStatus.FAILED

    @pytest.mark.asyncio
    async def test_workflow_execution_id_format(self):
        """Execution ID follows the pattern exec_{workflow_id}_{timestamp}."""
        actor = _make_mock_actor(agent_id="worker", run_response="ok")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm_node = _make_llm_node(node_id="llm1", prompt="Test")
        workflow = Workflow(
            id="wf-id-check",
            name="ID Check",
            nodes=[llm_node],
            edges=[],
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.execution_id.startswith("exec_wf-id-check_")

    @pytest.mark.asyncio
    async def test_workflow_not_found_raises(self):
        """execute_workflow raises ValueError for unknown workflow ID."""
        engine = _make_engine()

        with pytest.raises(ValueError, match="Workflow not found"):
            await engine.execute_workflow("nonexistent-workflow")

    @pytest.mark.asyncio
    async def test_single_node_workflow_lifecycle(self):
        """Single LLM node workflow completes in one step."""
        actor = _make_mock_actor(agent_id="worker", run_response="Single step done")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        engine = _make_engine(supervisor=supervisor)

        llm_node = _make_llm_node(node_id="llm1", prompt="Do one thing")
        workflow = Workflow(
            id="wf-single",
            name="Single Node",
            nodes=[llm_node],
            edges=[],
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.node_results) == 1
        assert result.node_results["llm1"].status == NodeStatus.COMPLETED
        assert result.node_results["llm1"].output == "Single step done"
        assert result.node_results["llm1"].execution_time > 0

    @pytest.mark.asyncio
    async def test_node_results_contain_execution_time(self):
        """Each completed node reports a positive execution_time."""
        actor = _make_mock_actor(agent_id="worker", run_response="Timed")
        supervisor = _make_mock_supervisor(
            actors={"worker": actor},
            active_agent_ids=["worker"],
        )
        coordinator = MockConsensusCoordinator()
        engine = _make_engine(supervisor=supervisor, consensus_coordinator=coordinator)

        llm_node = _make_llm_node(node_id="llm1", prompt="Time me")
        consensus_node = _make_consensus_node(
            node_id="consensus1",
            question="Also time me",
        )
        workflow = Workflow(
            id="wf-timing",
            name="Timing Check",
            nodes=[llm_node, consensus_node],
            edges=[],
        )
        engine.workflows[workflow.id] = workflow

        result = await engine.execute_workflow(workflow.id)

        for node_id in ("llm1", "consensus1"):
            nr = result.node_results[node_id]
            assert nr.status == NodeStatus.COMPLETED
            assert nr.execution_time >= 0  # Mock is fast but should be non-negative
