"""Tests for AutonomousSwarm.run_consensus() runtime integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_mock_actor(
    response: str = '{"decision": "yes", "confidence": 0.9, "reasoning": "Good."}',
):
    """Create a mock actor with a configurable run_with_llm response."""
    actor = AsyncMock()
    actor.run_with_llm = AsyncMock(return_value=response)
    return actor


def _make_failing_mock_actor(error: str = "LLM unavailable"):
    """Create a mock actor whose LLM call raises."""
    actor = AsyncMock()
    actor.run_with_llm = AsyncMock(side_effect=RuntimeError(error))
    return actor


def _all_mock_actors() -> dict[str, AsyncMock]:
    """Create mock actors for all agents that DomainSelector might select."""
    return {
        "alpha": _make_mock_actor(),
        "beta": _make_mock_actor(),
        "charlie": _make_mock_actor(),
        "arbiter": _make_mock_actor(),
        "sentinel": _make_mock_actor(),
        "sentinel-prime": _make_mock_actor(),
        "coder": _make_mock_actor(),
        "examiner": _make_mock_actor(),
        "prism": _make_mock_actor(),
        "empath": _make_mock_actor(),
        "habit-forge": _make_mock_actor(),
        "explorer": _make_mock_actor(),
        "metis": _make_mock_actor(),
        "historian": _make_mock_actor(),
        "steward": _make_mock_actor(),
        "coordinator": _make_mock_actor(),
        "nexus": _make_mock_actor(),
        "catalyst": _make_mock_actor(),
        "chronos": _make_mock_actor(),
        "perceiver": _make_mock_actor(),
        "perceiver-plus": _make_mock_actor(),
        "echo": _make_mock_actor(),
        "dreamer": _make_mock_actor(),
    }


@pytest.fixture
def mock_swarm():
    """Create a minimal AutonomousSwarm with mocked internals for testing run_consensus."""
    # Patch at import level to avoid NATS/infra dependencies
    with patch("heretek_swarm.runtime.main_loop.ActorSupervisor") as MockSupervisor:
        swarm = MagicMock()
        swarm.supervisor = MockSupervisor.return_value
        swarm.supervisor.actors = _all_mock_actors()

        # Real consensus engine
        from heretek_swarm.consensus.maker import MAKERConsensus

        swarm.consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)

        # Wire a DeliberationOrchestrator so run_consensus delegation works
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        return swarm


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestRunConsensus:
    """Test AutonomousSwarm.run_consensus() method."""

    @pytest.mark.asyncio
    async def test_run_consensus_returns_dict(self, mock_swarm):
        """run_consensus returns a dict with required keys."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="should we add rate limiting?",
            timeout=30,
        )

        assert isinstance(result, dict)
        assert "decision" in result
        assert "confidence" in result
        assert "votes" in result
        assert "red_flags" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_run_consensus_decision_is_string(self, mock_swarm):
        """Decision value is a string."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="is testing important?",
            timeout=30,
        )

        assert isinstance(result["decision"], str)

    @pytest.mark.asyncio
    async def test_run_consensus_confidence_in_range(self, mock_swarm):
        """Confidence is between 0.0 and 1.0."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="should we deploy?",
            timeout=30,
        )

        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_run_consensus_votes_is_list(self, mock_swarm):
        """Votes is a list of per-agent vote dicts."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="security analysis",
            timeout=30,
        )

        assert isinstance(result["votes"], list)
        assert len(result["votes"]) > 0
        # Each vote has agent_id, decision, confidence
        for vote in result["votes"]:
            assert "agent_id" in vote
            assert "decision" in vote
            assert "confidence" in vote

    @pytest.mark.asyncio
    async def test_run_consensus_uses_consensus_engine(self, mock_swarm):
        """self.consensus (MAKERConsensus) is used, not None."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        assert mock_swarm.consensus is not None
        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="test question",
            timeout=30,
        )
        assert result["decision"] != "error"

    @pytest.mark.asyncio
    async def test_run_consensus_with_all_mock_actors_yes(self, mock_swarm):
        """When all actors vote yes with high confidence, decision is 'yes'."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="security analysis",
            timeout=30,
        )

        assert result["decision"] == "yes"
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_run_consensus_no_supervisor_returns_error(self):
        """When supervisor is None, returns error dict."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = MagicMock()
        swarm.supervisor = None
        swarm.consensus = MagicMock()

        # Wire a DeliberationOrchestrator for delegation
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        result = await AutonomousSwarm.run_consensus(
            swarm,
            question="test",
        )

        assert result["decision"] == "error"
        assert "Supervisor not initialized" in result["red_flags"]

    @pytest.mark.asyncio
    async def test_run_consensus_no_consensus_engine_returns_error(self):
        """When consensus is None, returns error dict."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = MagicMock()
        swarm.supervisor = MagicMock()
        swarm.supervisor.actors = {}
        swarm.consensus = None

        # Wire a DeliberationOrchestrator for delegation
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        result = await AutonomousSwarm.run_consensus(
            swarm,
            question="test",
        )

        assert result["decision"] == "error"
        assert "Consensus engine not initialized" in result["red_flags"]

    @pytest.mark.asyncio
    async def test_run_consensus_with_failing_agents(self):
        """Agents with LLM failures produce abstain votes; consensus still completes."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = MagicMock()
        from heretek_swarm.consensus.maker import MAKERConsensus

        swarm.consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)
        swarm.supervisor = MagicMock()
        # Mix of working and failing actors
        actors = _all_mock_actors()
        actors["sentinel"] = _make_failing_mock_actor("timeout")
        actors["examiner"] = _make_failing_mock_actor("rate limited")
        swarm.supervisor.actors = actors

        # Wire DeliberationOrchestrator for delegation
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        result = await AutonomousSwarm.run_consensus(
            swarm,
            question="security analysis",
            timeout=30,
        )

        # Should complete without crashing
        assert isinstance(result, dict)
        assert "decision" in result
        # With 2 failures and 2 successes, MAKER may not reach consensus
        # (2 yes × 0.45 weighted = 0.9 < ahead_by_k=2.0 threshold)  # noqa: RUF003
        # Result is either "yes" (if MAKER aggregates) or "no_consensus"
        assert result["decision"] in ("yes", "no", "no_consensus", "abstain")

    @pytest.mark.asyncio
    async def test_run_consensus_with_empty_actors(self):
        """When actors dict is empty, returns no_consensus or abstain."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = MagicMock()
        from heretek_swarm.consensus.maker import MAKERConsensus

        swarm.consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)
        swarm.supervisor = MagicMock()
        swarm.supervisor.actors = {}

        # Wire DeliberationOrchestrator for delegation
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        result = await AutonomousSwarm.run_consensus(
            swarm,
            question="security analysis",
            timeout=30,
        )

        # Should not crash
        assert isinstance(result, dict)
        assert "decision" in result

    @pytest.mark.asyncio
    async def test_run_consensus_red_flags_is_list(self, mock_swarm):
        """red_flags is always a list."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="test question",
            timeout=30,
        )

        assert isinstance(result["red_flags"], list)

    @pytest.mark.asyncio
    async def test_run_consensus_reasoning_is_string(self, mock_swarm):
        """reasoning is always a string."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="test question",
            timeout=30,
        )

        assert isinstance(result["reasoning"], str)

    @pytest.mark.asyncio
    async def test_run_consensus_custom_timeout_accepted(self, mock_swarm):
        """Custom timeout parameter is passed through."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        result = await AutonomousSwarm.run_consensus(
            mock_swarm,
            question="quick question",
            timeout=5,
            max_rounds=1,
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_run_consensus_with_mixed_decisions(self):
        """When agents disagree, MAKER resolves or returns no_consensus."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = MagicMock()
        from heretek_swarm.consensus.maker import MAKERConsensus

        swarm.consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)
        swarm.supervisor = MagicMock()

        # Wire DeliberationOrchestrator for delegation
        from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator

        swarm._deliberation = DeliberationOrchestrator(
            supervisor=swarm.supervisor,
            consensus=swarm.consensus,
        )

        actors = _all_mock_actors()
        # Security analysis selects: alpha, examiner, prism, sentinel
        # 3 say yes with high confidence, 1 says no
        actors["alpha"] = _make_mock_actor(
            '{"decision": "yes", "confidence": 1.0, "reasoning": "Safe."}'
        )
        actors["examiner"] = _make_mock_actor(
            '{"decision": "yes", "confidence": 1.0, "reasoning": "Tests pass."}'
        )
        actors["prism"] = _make_mock_actor(
            '{"decision": "yes", "confidence": 1.0, "reasoning": "Good idea."}'
        )
        actors["sentinel"] = _make_mock_actor(
            '{"decision": "no", "confidence": 0.9, "reasoning": "Too risky."}'
        )
        swarm.supervisor.actors = actors

        result = await AutonomousSwarm.run_consensus(
            swarm,
            question="security analysis",
            timeout=30,
        )

        assert isinstance(result, dict)
        # Either consensus reached or no_consensus
        assert result["decision"] in ("yes", "no", "no_consensus")
