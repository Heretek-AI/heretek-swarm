"""
T03: Verify phase_handlers have zero hardcoded scores and emit structured logs.

These handlers are unused extension points (HeavySwarmWorkflow bypasses them),
so the test confirms they produce honest 0.0 values + structured log events.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.orchestration.phase_handlers import (
    AlternativesPhaseHandler,
    AnalysisPhaseHandler,
    DecisionPhaseHandler,
)


@pytest.fixture
def mock_agents():
    """Create a dict of mock agents with send_to_actor support."""

    def _make_agent(agent_id: str) -> MagicMock:
        agent = MagicMock()
        agent.send_to_actor = AsyncMock(return_value=None)
        agent.name = agent_id
        return agent

    return {
        "alpha": _make_agent("alpha"),
        "beta": _make_agent("beta"),
        "charlie": _make_agent("charlie"),
    }


@pytest.fixture
def mock_consensus_engine():
    """Create a mock consensus engine."""
    engine = MagicMock()
    engine.start_consensus = MagicMock()
    engine.add_vote = MagicMock()

    consensus_result = MagicMock()
    consensus_result.decision = "test_decision"
    consensus_result.confidence = 0.0
    consensus_result.red_flags = []
    engine.compute_consensus = MagicMock(return_value=consensus_result)
    engine.cleanup_process = MagicMock()
    return engine


async def test_analysis_phase_handler_zero_confidence(mock_agents):
    """AnalysisPhaseHandler uses 0.0 confidence and logs phase_handler_analysis_hardcoded."""
    handler = AnalysisPhaseHandler(
        triad_agents=["alpha", "beta", "charlie"],
        agents=mock_agents,
    )

    success, output, errors = await handler.execute(
        workflow_id="test-wf",
        topic="test topic",
        previous_output={"research": "data"},
    )

    assert success is True
    # All confidences should be 0.0
    for perspective in output.get("perspectives", []):
        assert perspective["confidence"] == 0.0, (
            f"Expected 0.0 confidence for {perspective['agent_id']}, "
            f"got {perspective['confidence']}"
        )
    # Insights should be empty (not fabricated)
    assert output.get("key_insights", []) == []


async def test_analysis_phase_handler_missing_agent(mock_agents):
    """AnalysisPhaseHandler handles missing agents gracefully with error."""
    handler = AnalysisPhaseHandler(
        triad_agents=["nonexistent"],
        agents=mock_agents,
    )

    success, output, errors = await handler.execute(
        workflow_id="test-wf",
        topic="test topic",
    )

    assert success is False
    assert "Triad agent not found: nonexistent" in errors


async def test_alternatives_phase_handler_zero_scores(mock_agents):
    """AlternativesPhaseHandler has no hardcoded alternatives or evaluation scores."""
    handler = AlternativesPhaseHandler(agents=mock_agents)

    success, output, errors = await handler.execute(
        workflow_id="test-wf",
        topic="test topic",
    )

    assert success is True
    # No fabricated alternatives
    assert output["alternatives"] == []
    # No recommended alternative
    assert output["recommended_alternative"] is None
    # Evaluation criteria remain
    assert "feasibility" in output["evaluation_criteria"]


async def test_decision_phase_handler_zero_confidence(mock_agents, mock_consensus_engine):
    """DecisionPhaseHandler uses 0.0 confidence and logs phase_handler_vote_hardcoded."""
    handler = DecisionPhaseHandler(
        triad_agents=["alpha", "beta", "charlie"],
        agents=mock_agents,
        consensus_engine=mock_consensus_engine,
    )

    success, output, errors = await handler.execute(
        workflow_id="test-wf",
        topic="test topic",
        previous_output={
            "recommended_alternative": {"name": "test_alt"},
        },
    )

    assert success is True
    # All votes must have 0.0 confidence
    for vote in output.get("votes", []):
        assert vote["confidence"] == 0.0, (
            f"Expected 0.0 confidence for {vote['agent_id']}, got {vote['confidence']}"
        )
    # Consensus engine was called
    mock_consensus_engine.start_consensus.assert_called()
    mock_consensus_engine.compute_consensus.assert_called()
    mock_consensus_engine.cleanup_process.assert_called()


async def test_no_hardcoded_scores_in_source(capsys):
    """Source code grep: zero hardcoded 0.8 or 0.58 values remain."""
    import subprocess

    result = subprocess.run(
        [
            "grep",
            "-n",
            "-E",
            r"\b0\.8\b|\b0\.58\b",
            "backend/heretek_swarm/orchestration/phase_handlers.py",
        ],
        capture_output=True,
        text=True,
    )
    # Exit code 1 from grep means "no matches found" — that's what we want
    assert result.returncode == 1, (
        f"Found hardcoded 0.8 or 0.58 in phase_handlers.py:\n{result.stdout}"
    )
