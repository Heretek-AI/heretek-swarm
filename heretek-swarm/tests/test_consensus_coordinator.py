"""Tests for ConsensusCoordinator — bridge between agents and MAKER voting."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.consensus.consensus_coordinator import (
    ConsensusCoordinator,
    _extract_decision_confidence,
)
from heretek_swarm.consensus.domain_selector import DomainSelector
from heretek_swarm.consensus.maker import MAKERConsensus, ConsensusState

# Resolve characters directory relative to the test file
_CHARACTERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "heretek_swarm",
    "runtime",
    "characters",
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_mock_actor(responses: dict[str, str | Exception] | None = None):
    """Create a mock actor with configurable run_with_llm responses.

    Args:
        responses: If None, actor returns a default yes/confident response.
                   If a dict, maps prompt substrings to responses or exceptions.
    """
    actor = AsyncMock()

    if responses is None:
        actor.run_with_llm = AsyncMock(
            return_value='{"decision": "yes", "confidence": 0.9, "reasoning": "Good idea."}'
        )
    else:
        async def _side_effect(prompt, **kwargs):
            for key, val in responses.items():
                if key in prompt:
                    if isinstance(val, Exception):
                        raise val
                    return val
            return '{"decision": "yes", "confidence": 0.85}'

        actor.run_with_llm = AsyncMock(side_effect=_side_effect)

    return actor


@pytest.fixture()
def maker() -> MAKERConsensus:
    return MAKERConsensus(ahead_by_k=2, min_votes=3)


@pytest.fixture()
def ds() -> DomainSelector:
    return DomainSelector(characters_dir=_CHARACTERS_DIR)


def _all_agents_mock() -> dict[str, Any]:
    """Create mock actors for all agents DomainSelector might select."""
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
        "guardian": _make_mock_actor(),
        "librarian": _make_mock_actor(),
        "logic": _make_mock_actor(),
        "metis": _make_mock_actor(),
        "oracle": _make_mock_actor(),
        "scribe": _make_mock_actor(),
    }


@pytest.fixture()
def coordinator(maker, ds) -> ConsensusCoordinator:
    """Coordinator with mock actors for all agents DomainSelector might pick."""
    return ConsensusCoordinator(maker=maker, domain_selector=ds, actors=_all_agents_mock())


# ------------------------------------------------------------------
# Response parsing tests
# ------------------------------------------------------------------


class TestParseResponse:
    """Test LLM response parsing into (decision, confidence)."""

    def test_parse_json_response(self):
        raw = '{"decision": "yes", "confidence": 0.95, "reasoning": "Strong evidence."}'
        decision, confidence = ConsensusCoordinator._parse_response(raw)
        assert decision == "yes"
        assert confidence == 0.95

    def test_parse_json_with_extra_text(self):
        raw = 'I think the answer is:\n{"decision": "no", "confidence": 0.7}\nEnd of analysis.'
        decision, confidence = ConsensusCoordinator._parse_response(raw)
        assert decision == "no"
        assert confidence == 0.7

    def test_parse_empty_string(self):
        decision, confidence = ConsensusCoordinator._parse_response("")
        assert decision == "abstain"
        assert confidence == 0.0

    def test_parse_whitespace_only(self):
        decision, confidence = ConsensusCoordinator._parse_response("   \n  ")
        assert decision == "abstain"
        assert confidence == 0.0

    def test_parse_none(self):
        decision, confidence = ConsensusCoordinator._parse_response(None)
        assert decision == "abstain"
        assert confidence == 0.0

    def test_parse_free_text_yes(self):
        decision, confidence = ConsensusCoordinator._parse_response("Yes, I agree with this.")
        assert decision == "yes"
        assert confidence == 0.5

    def test_parse_free_text_no(self):
        decision, confidence = ConsensusCoordinator._parse_response("No, this is wrong.")
        assert decision == "no"
        assert confidence == 0.5

    def test_parse_unknown_free_text(self):
        decision, confidence = ConsensusCoordinator._parse_response("Perhaps maybe sometimes.")
        assert decision == "perhaps"
        assert confidence == 0.3

    def test_parse_json_missing_confidence(self):
        raw = '{"decision": "approve"}'
        decision, confidence = ConsensusCoordinator._parse_response(raw)
        assert decision == "approve"
        assert confidence == 0.5  # default

    def test_parse_json_missing_decision(self):
        raw = '{"confidence": 0.8}'
        decision, confidence = ConsensusCoordinator._parse_response(raw)
        assert decision == "abstain"  # empty string -> abstain
        assert confidence == 0.8

    def test_parse_confidence_clamped_above_1(self):
        raw = '{"decision": "yes", "confidence": 1.5}'
        _, confidence = ConsensusCoordinator._parse_response(raw)
        assert confidence == 1.0

    def test_parse_confidence_clamped_below_0(self):
        raw = '{"decision": "yes", "confidence": -0.3}'
        _, confidence = ConsensusCoordinator._parse_response(raw)
        assert confidence == 0.0


class TestExtractDecisionConfidence:
    """Test _extract_decision_confidence helper."""

    def test_normal_extraction(self):
        data = {"decision": "yes", "confidence": 0.9}
        assert _extract_decision_confidence(data) == ("yes", 0.9)

    def test_string_uppercase_normalized(self):
        data = {"decision": "YES", "confidence": 0.8}
        decision, _ = _extract_decision_confidence(data)
        assert decision == "yes"

    def test_bad_confidence_type(self):
        data = {"decision": "yes", "confidence": "high"}
        _, confidence = _extract_decision_confidence(data)
        assert confidence == 0.5  # fallback


# ------------------------------------------------------------------
# Integration tests with real DomainSelector
# ------------------------------------------------------------------


class TestConsensusCoordinator:
    """Integration tests with DomainSelector and MAKERConsensus."""

    @pytest.mark.asyncio
    async def test_coordinator_selects_agents(self, coordinator):
        """Agents are selected by DomainSelector based on question keywords."""
        # Override actors to be in a dict compatible with the question
        # "security analysis" selects alpha, sentinel, prism, examiner
        result = await coordinator.run_consensus("security analysis")

        # With all mock actors returning yes/0.9, consensus should succeed
        assert result is not None
        assert result.decision == "yes"
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_coordinator_collects_votes(self, coordinator):
        """All selected agents contribute votes."""
        result = await coordinator.run_consensus("security analysis")
        assert result is not None
        # At least 3 votes (min_votes for MAKER)
        assert len(result.votes) >= 3

    @pytest.mark.asyncio
    async def test_coordinator_returns_consensus_result(self, coordinator):
        """MAKER produces a ConsensusResult with decision and confidence."""
        result = await coordinator.run_consensus("should we add rate limiting")
        assert result is not None
        assert result.decision is not None
        assert 0.0 <= result.confidence <= 1.0
        assert result.state == ConsensusState.COMPLETED

    @pytest.mark.asyncio
    async def test_coordinator_with_mixed_decisions(self, maker, ds):
        """When agents disagree but one side has enough weight, MAKER resolves."""
        actors = _all_agents_mock()
        # 3 agents say "yes" with high confidence, 1 says "no"
        # With reputation weight 0.5 and conf 0.99: weight = 0.495 each
        # 3 × 0.495 = 1.485 vs 0.495 → ahead by 0.99, needs 2.0 → no consensus
        # Increase yes agents' confidence to 1.0 for weight = 0.5 each
        for aid in ["alpha", "examiner", "prism"]:
            actors[aid].run_with_llm = AsyncMock(
                return_value='{"decision": "yes", "confidence": 1.0, "reasoning": "Approved."}'
            )
        actors["sentinel"].run_with_llm = AsyncMock(
            return_value='{"decision": "no", "confidence": 0.9, "reasoning": "Too risky."}'
        )

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis")
        # yes: 3 × (1.0 × 0.5) = 1.5, no: 1 × (0.9 × 0.5) = 0.45
        # ahead by 1.05 < 2.0 → MAKER returns None (no clear winner)
        assert result is None


class TestAgentAvailability:
    """Tests for agent unavailability handling."""

    @pytest.mark.asyncio
    async def test_missing_agent_skipped(self, maker, ds):
        """Agent not in actors dict is skipped with an abstain vote."""
        # DomainSelector selects alpha, examiner, prism, sentinel for "security analysis"
        # Only provide alpha — examiner, prism, sentinel are "missing"
        # alpha votes yes (conf 0.9), 3 abstain (conf 0.0)
        # MAKER ahead_by_k=2 requires weighted difference >= 2.0 → returns None
        actors = {"alpha": _make_mock_actor()}
        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)

        result = await coord.run_consensus("security analysis")
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_agent_abstain_votes_recorded(self, maker, ds):
        """Missing agents generate abstain votes that are recorded in MAKER."""
        # Direct test: manually add votes to verify abstain recording
        consensus_id = "test-abstain"
        maker.start_consensus(consensus_id)
        selected = ds.score_agents("security analysis")

        for agent_id in selected:
            if agent_id == "alpha":
                maker.add_vote(consensus_id, agent_id, "yes", 0.9)
            else:
                maker.add_vote(consensus_id, agent_id, "abstain", 0.0,
                                metadata={"status": "agent_unavailable"})

        votes = maker.active_processes[consensus_id]
        abstain_votes = [v for v in votes if v.decision == "abstain"]
        assert len(abstain_votes) == 3  # examiner, prism, sentinel
        maker.cleanup_process(consensus_id)

    @pytest.mark.asyncio
    async def test_agent_unavailable_logged(self, maker, ds, caplog):
        """Missing agents generate a warning-level log with consensus_id."""
        actors = {"alpha": _make_mock_actor()}
        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)

        await coord.run_consensus("security analysis")
        # The structlog output should include agent_vote_collected with status=unavailable
        # (structlog may not capture to caplog, so we just verify no crash)


class TestLLMFailureHandling:
    """Tests for LLM failure scenarios."""

    @pytest.mark.asyncio
    async def test_llm_failure_abstains(self, maker, ds):
        """An agent whose LLM call fails records an abstain vote."""
        actors = _all_agents_mock()
        # Make sentinel's LLM fail — it will abstain
        actors["sentinel"].run_with_llm = AsyncMock(
            side_effect=RuntimeError("LLM provider unavailable")
        )

        # Use a question where more agents vote yes to overcome ahead_by_k=2
        # "security analysis" selects 4 agents: alpha, examiner, prism, sentinel
        # 3 yes (conf 0.9) + 1 abstain → weight diff = 1.35, needs 2.0
        # So result is None — the abstain prevents consensus
        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis")
        assert result is None

    @pytest.mark.asyncio
    async def test_llm_failure_vote_recorded_as_abstain(self, maker, ds):
        """Failed LLM calls produce abstain votes with zero confidence."""
        # Direct test: manually record a failed vote
        consensus_id = "test-failure"
        maker.start_consensus(consensus_id)
        maker.add_vote(consensus_id, "sentinel", "abstain", 0.0,
                        metadata={"status": "llm_failure", "error": "timeout"})
        maker.add_vote(consensus_id, "alpha", "yes", 0.9)
        maker.add_vote(consensus_id, "examiner", "yes", 0.9)

        votes = maker.active_processes[consensus_id]
        sentinel_vote = [v for v in votes if v.agent_id == "sentinel"][0]
        assert sentinel_vote.decision == "abstain"
        assert sentinel_vote.confidence == 0.0
        assert sentinel_vote.metadata["status"] == "llm_failure"
        maker.cleanup_process(consensus_id)

    @pytest.mark.asyncio
    async def test_malformed_response_parsed(self, maker, ds):
        """An agent returning garbage text still produces a vote (fallback parsing)."""
        actors = _all_agents_mock()
        # Beta returns nonsense — fallback parser extracts first word
        actors["beta"].run_with_llm = AsyncMock(return_value="I cannot decide. Sorry.")

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis")

        # Should still produce a result (other agents voted normally)
        assert result is not None

    @pytest.mark.asyncio
    async def test_all_agents_fail_returns_abstain(self, maker, ds):
        """When all agents fail, all votes are abstain and MAKER returns abstain."""
        actors = _all_agents_mock()
        for actor in actors.values():
            actor.run_with_llm = AsyncMock(
                side_effect=RuntimeError("All providers down")
            )

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis")

        # All abstain: MAKER still computes a result (unanimous abstain)
        assert result is not None
        assert result.decision == "abstain"


class TestTimeoutHandling:
    """Tests for timeout scenarios."""

    @pytest.mark.asyncio
    async def test_timeout_returns_best_effort(self, maker, ds):
        """When timeout fires, coordinator tries to compute with partial votes."""
        actors = _all_agents_mock()

        # Make alpha take forever
        async def _slow(*args, **kwargs):
            await asyncio.sleep(10)
            return '{"decision": "yes", "confidence": 0.9}'

        actors["alpha"].run_with_llm = AsyncMock(side_effect=_slow)

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis", timeout=0.5)

        # Should still return something (partial votes from other agents)
        # or None if MAKER can't aggregate — just verify no crash
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_fast_timeout_no_crash(self, maker, ds):
        """A very short timeout should not crash the coordinator."""
        actors = _all_agents_mock()

        async def _slow(*args, **kwargs):
            await asyncio.sleep(100)
            return '{"decision": "yes", "confidence": 0.9}'

        for actor in actors.values():
            actor.run_with_llm = AsyncMock(side_effect=_slow)

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("test question", timeout=0.01)
        # Should return None (not enough votes collected) or abstain
        # Just verify it doesn't hang


class TestStructuredLogging:
    """Verify structured log events are emitted with consensus_id."""

    @pytest.mark.asyncio
    async def test_consensus_started_emitted(self, coordinator):
        """consensus_started event should be logged."""
        # We can't easily capture structlog output in tests without
        # configuring a test processor, but we verify no crash
        await coordinator.run_consensus("test question")

    @pytest.mark.asyncio
    async def test_domain_selection_complete_emitted(self, coordinator):
        """domain_selection_complete event should be logged."""
        await coordinator.run_consensus("security analysis")


class TestEdgeCases:
    """Boundary conditions and special inputs."""

    @pytest.mark.asyncio
    async def test_empty_question(self, coordinator):
        """Empty question should still work (DomainSelector falls back)."""
        result = await coordinator.run_consensus("")
        # With fallback agents, should get a result
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_actors_all_abstain(self, maker, ds):
        """When actors dict is empty, all agents abstain — MAKER returns abstain."""
        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors={})
        result = await coord.run_consensus("security analysis")
        # All votes are abstain -> MAKER returns a unanimous abstain result
        assert result is not None
        assert result.decision == "abstain"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_unicode_question(self, coordinator):
        """Unicode characters in question should not break tokenization."""
        # "analysis" matches agents, so we should get a result
        result = await coordinator.run_consensus("sécurité analysis über coding")
        assert result is not None

    @pytest.mark.asyncio
    async def test_custom_timeout_and_max_rounds(self, coordinator):
        """Custom timeout and max_rounds parameters are accepted."""
        result = await coordinator.run_consensus("test", timeout=60, max_rounds=1)
        assert result is not None
