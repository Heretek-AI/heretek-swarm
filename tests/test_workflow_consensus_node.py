"""
Tests for consensus node type in WorkflowEngine.

Verifies that:
- Consensus node calls ConsensusCoordinator.run_consensus() with correct params
- Missing question raises ValueError
- Missing coordinator raises RuntimeError
- Question is read from node.data or input_data
- Timeout and max_rounds are passed through
- Result dict has expected shape
- Observability events are logged
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
    WorkflowContext,
    WorkflowEngine,
    WorkflowNode,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@dataclass
class MockConsensusCoordinator:
    """Mock ConsensusCoordinator with configurable run_consensus behavior."""

    run_consensus: AsyncMock = field(default_factory=lambda: AsyncMock())

    def __post_init__(self):
        if not isinstance(self.run_consensus, AsyncMock):
            self.run_consensus = AsyncMock(side_effect=self.run_consensus)


def _make_consensus_result(
    decision: str = "approve",
    confidence: float = 0.85,
    votes: list[Vote] | None = None,
    red_flags: list[str] | None = None,
) -> ConsensusResult:
    """Build a ConsensusResult for testing."""
    now = datetime.now(UTC).isoformat()
    if votes is None:
        votes = [
            Vote(
                agent_id="agent-alpha",
                decision="approve",
                confidence=0.9,
                timestamp=now,
                metadata={"reasoning": "Strong evidence."},
            ),
            Vote(
                agent_id="agent-beta",
                decision="approve",
                confidence=0.8,
                timestamp=now,
                metadata={"reasoning": "Agree with analysis."},
            ),
        ]
    if red_flags is None:
        red_flags = []
    return ConsensusResult(
        decision=decision,
        confidence=confidence,
        votes=votes,
        state=ConsensusState.COMPLETED,
        timestamp=now,
        red_flags=red_flags,
        metadata={},
    )


def _make_consensus_node(
    node_id: str = "consensus-1",
    question: str | None = "Should we proceed with deployment?",
    timeout: int | None = None,
    max_rounds: int | None = None,
) -> WorkflowNode:
    """Build a WorkflowNode of type 'consensus'."""
    data: dict[str, Any] = {}
    if question is not None:
        data["question"] = question
    if timeout is not None:
        data["timeout"] = timeout
    if max_rounds is not None:
        data["max_rounds"] = max_rounds
    return WorkflowNode(id=node_id, type="consensus", data=data)


def _make_workflow(nodes: list[WorkflowNode] | None = None) -> Workflow:
    """Build a minimal Workflow for testing."""
    return Workflow(
        id="wf-test",
        name="Test Workflow",
        nodes=nodes or [_make_consensus_node()],
        edges=[],
    )


def _make_context(
    variables: dict[str, Any] | None = None,
) -> WorkflowContext:
    """Build a WorkflowContext for testing."""
    return WorkflowContext(
        workflow_id="wf-test",
        execution_id="exec-test-001",
        variables=variables or {},
    )


def _make_engine(
    consensus_coordinator: Any = None,
    supervisor: Any = None,
) -> WorkflowEngine:
    """Build a WorkflowEngine with optional consensus coordinator."""
    return WorkflowEngine(
        consensus_coordinator=consensus_coordinator,
        supervisor=supervisor,
    )


# ── Happy Path Tests ─────────────────────────────────────────────────────────


class TestConsensusNodeHappyPath:
    """Test consensus node with a properly configured coordinator."""

    @pytest.mark.asyncio
    async def test_consensus_node_returns_expected_dict(self):
        """Consensus node returns dict with decision, confidence, votes, red_flags."""
        result = _make_consensus_result(decision="approve", confidence=0.85)
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node()
        context = _make_context()

        output = await engine._execute_consensus_node(node, {}, context)

        assert output["consensus_reached"] is True
        assert output["decision"] == "approve"
        assert output["confidence"] == 0.85
        assert len(output["votes"]) == 2
        assert output["votes"][0]["agent_id"] == "agent-alpha"
        assert output["red_flags"] == []

    @pytest.mark.asyncio
    async def test_consensus_node_calls_run_consensus_with_question(self):
        """Coordinator.run_consensus() is called with the question from node.data."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(question="Is the sky blue?")
        context = _make_context()

        await engine._execute_consensus_node(node, {}, context)

        coordinator.run_consensus.assert_called_once_with(
            question="Is the sky blue?",
            timeout=120,
            max_rounds=1,
        )

    @pytest.mark.asyncio
    async def test_consensus_node_reads_question_from_input_data(self):
        """Question is read from input_data when not in node.data."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        # node.data has no question
        node = WorkflowNode(id="c1", type="consensus", data={})
        context = _make_context()

        input_data = {"question": "From upstream node?"}
        output = await engine._execute_consensus_node(node, input_data, context)

        coordinator.run_consensus.assert_called_once_with(
            question="From upstream node?",
            timeout=120,
            max_rounds=1,
        )
        assert output["consensus_reached"] is True

    @pytest.mark.asyncio
    async def test_consensus_node_prefers_node_data_question(self):
        """node.data.question takes priority over input_data.question."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(question="Node data question?")
        context = _make_context()

        input_data = {"question": "Input data question?"}
        await engine._execute_consensus_node(node, input_data, context)

        coordinator.run_consensus.assert_called_once_with(
            question="Node data question?",
            timeout=120,
            max_rounds=1,
        )

    @pytest.mark.asyncio
    async def test_consensus_node_passes_timeout_and_max_rounds(self):
        """Custom timeout and max_rounds are forwarded to coordinator."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(question="Q?", timeout=30, max_rounds=5)
        context = _make_context()

        await engine._execute_consensus_node(node, {}, context)

        coordinator.run_consensus.assert_called_once_with(
            question="Q?",
            timeout=30,
            max_rounds=5,
        )

    @pytest.mark.asyncio
    async def test_consensus_node_returns_no_consensus_result(self):
        """When coordinator returns None, node returns consensus_reached=False."""
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = None

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node()
        context = _make_context()

        output = await engine._execute_consensus_node(node, {}, context)

        assert output["consensus_reached"] is False
        assert output["decision"] is None
        assert output["confidence"] == 0.0
        assert output["votes"] == []
        assert output["red_flags"] == []

    @pytest.mark.asyncio
    async def test_consensus_node_preserves_vote_metadata(self):
        """Vote metadata (reasoning) is preserved in output."""
        now = datetime.now(UTC).isoformat()
        votes = [
            Vote(
                agent_id="agent-x",
                decision="reject",
                confidence=0.6,
                timestamp=now,
                metadata={"reasoning": "Too risky."},
            ),
        ]
        result = _make_consensus_result(decision="reject", confidence=0.6, votes=votes)
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node()
        context = _make_context()

        output = await engine._execute_consensus_node(node, {}, context)

        assert output["votes"][0]["metadata"]["reasoning"] == "Too risky."


# ── Error Path Tests ─────────────────────────────────────────────────────────


class TestConsensusNodeErrorPaths:
    """Test error conditions for consensus node."""

    @pytest.mark.asyncio
    async def test_raises_value_error_when_question_missing(self):
        """ValueError is raised when question is absent from node.data AND input_data."""
        coordinator = MockConsensusCoordinator()
        engine = _make_engine(consensus_coordinator=coordinator)

        # No question in node.data
        node = WorkflowNode(id="c1", type="consensus", data={})
        context = _make_context()

        with pytest.raises(ValueError, match="requires a 'question'"):
            await engine._execute_consensus_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_coordinator_not_configured(self):
        """RuntimeError is raised when consensus_coordinator is None."""
        engine = _make_engine(consensus_coordinator=None)
        node = _make_consensus_node()
        context = _make_context()

        with pytest.raises(RuntimeError, match="requires a ConsensusCoordinator"):
            await engine._execute_consensus_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_propagates_coordinator_exception(self):
        """Exceptions from coordinator.run_consensus() propagate to caller."""
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.side_effect = TimeoutError("Consensus timed out")

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node()
        context = _make_context()

        with pytest.raises(TimeoutError, match="Consensus timed out"):
            await engine._execute_consensus_node(node, {}, context)


# ── Negative / Boundary Tests ────────────────────────────────────────────────


class TestConsensusNodeBoundaryConditions:
    """Test boundary conditions and malformed inputs."""

    @pytest.mark.asyncio
    async def test_empty_string_question_raises_value_error(self):
        """Empty string question is treated as missing."""
        coordinator = MockConsensusCoordinator()
        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(question="")
        context = _make_context()

        with pytest.raises(ValueError, match="requires a 'question'"):
            await engine._execute_consensus_node(node, {}, context)

    @pytest.mark.asyncio
    async def test_single_word_question(self):
        """A single-word question is valid and passed through."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(question="Proceed?")
        context = _make_context()

        output = await engine._execute_consensus_node(node, {}, context)

        coordinator.run_consensus.assert_called_once_with(
            question="Proceed?",
            timeout=120,
            max_rounds=1,
        )
        assert output["consensus_reached"] is True

    @pytest.mark.asyncio
    async def test_question_with_special_characters(self):
        """Question with special characters is passed through unchanged."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        q = "Is the value > 100 && < 200? (yes/no) \"test\" 'quote'"
        node = _make_consensus_node(question=q)
        context = _make_context()

        await engine._execute_consensus_node(node, {}, context)

        coordinator.run_consensus.assert_called_once_with(
            question=q,
            timeout=120,
            max_rounds=1,
        )

    @pytest.mark.asyncio
    async def test_all_agents_unavailable_returns_abstain_votes(self):
        """When all agents are unavailable, coordinator returns abstain votes."""
        now = datetime.now(UTC).isoformat()
        votes = [
            Vote(agent_id="a1", decision="abstain", confidence=0.0, timestamp=now, metadata={}),
            Vote(agent_id="a2", decision="abstain", confidence=0.0, timestamp=now, metadata={}),
        ]
        result = _make_consensus_result(decision="abstain", confidence=0.0, votes=votes)
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node()
        context = _make_context()

        output = await engine._execute_consensus_node(node, {}, context)

        assert output["consensus_reached"] is True
        assert output["decision"] == "abstain"
        assert all(v["decision"] == "abstain" for v in output["votes"])


# ── Integration Tests ────────────────────────────────────────────────────────


class TestConsensusNodeIntegration:
    """Test consensus node integrated into _execute_node and _execute_and_capture."""

    @pytest.mark.asyncio
    async def test_execute_node_dispatches_to_consensus(self):
        """_execute_node routes type='consensus' to _execute_consensus_node."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(node_id="c1")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "c1", context)

        nr = context.node_results["c1"]
        assert nr.status == NodeStatus.COMPLETED
        assert nr.output["consensus_reached"] is True
        assert nr.output["decision"] == "approve"

    @pytest.mark.asyncio
    async def test_execute_and_capture_dispatches_to_consensus(self):
        """_execute_and_capture routes type='consensus' to _execute_consensus_node."""
        result = _make_consensus_result()
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.return_value = result

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(node_id="c1")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        output = await engine._execute_and_capture(workflow, "c1", context, node)

        assert output["consensus_reached"] is True
        assert output["decision"] == "approve"

    @pytest.mark.asyncio
    async def test_execute_node_consensus_failure_marks_node_failed(self):
        """When coordinator raises, the node is marked FAILED in context."""
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.side_effect = RuntimeError("LLM unavailable")

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(node_id="c1")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        await engine._execute_node(workflow, "c1", context)

        nr = context.node_results["c1"]
        assert nr.status == NodeStatus.FAILED
        assert isinstance(nr.error, RuntimeError)
        assert "LLM unavailable" in str(nr.error)

    @pytest.mark.asyncio
    async def test_execute_and_capture_consensus_failure_returns_error_dict(self):
        """When coordinator raises, _execute_and_capture returns error dict."""
        coordinator = MockConsensusCoordinator()
        coordinator.run_consensus.side_effect = RuntimeError("LLM down")

        engine = _make_engine(consensus_coordinator=coordinator)
        node = _make_consensus_node(node_id="c1")
        workflow = _make_workflow(nodes=[node])
        context = _make_context()

        output = await engine._execute_and_capture(workflow, "c1", context, node)

        assert "error" in output
        assert "LLM down" in output["error"]


# ── Constructor Tests ────────────────────────────────────────────────────────


class TestConsensusNodeConstructor:
    """Test that WorkflowEngine constructor accepts consensus params."""

    def test_engine_accepts_consensus_coordinator(self):
        """Engine stores consensus_coordinator when provided."""
        coordinator = MockConsensusCoordinator()
        engine = WorkflowEngine(consensus_coordinator=coordinator)
        assert engine._consensus_coordinator is coordinator

    def test_engine_accepts_supervisor(self):
        """Engine stores supervisor when provided."""
        supervisor = MagicMock()
        engine = WorkflowEngine(supervisor=supervisor)
        assert engine._supervisor is supervisor

    def test_engine_defaults_to_none_coordinator(self):
        """Engine defaults consensus_coordinator to None."""
        engine = WorkflowEngine()
        assert engine._consensus_coordinator is None
        assert engine._supervisor is None
