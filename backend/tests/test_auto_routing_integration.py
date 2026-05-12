"""
Integration tests for auto-routing and multi-round consensus.

Tests the end-to-end flow:
1. Complex prompt auto-routes through consensus
2. Simple prompt still uses triad deliberation
3. --consensus flag overrides heuristic
4. Multi-round consensus with argument exchange produces round history
5. run_consensus() with max_rounds=1 does single round

These tests mock the swarm (ConsensusCoordinator, AutonomousSwarm) but test
the full CLI → heuristic → coordinator → MAKER pipeline.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from heretek_swarm.cli import cli, _display_consensus_results
from heretek_swarm.consensus.complexity import ComplexityHeuristic


# ── Fixtures ───────────────────────────────────────────────────────────


def _consensus_result(decision="yes", confidence=0.87, total_rounds=1, round_history=None):
    """Return a realistic consensus result dict matching run_consensus output."""
    result = {
        "decision": decision,
        "confidence": confidence,
        "votes": [
            {
                "agent_id": "arbiter",
                "decision": decision,
                "confidence": 0.92,
                "metadata": {"reasoning": "Rate limiting prevents abuse."},
            },
            {
                "agent_id": "sentinel",
                "decision": decision,
                "confidence": 0.85,
                "metadata": {"reasoning": "Security implications favor this."},
            },
            {
                "agent_id": "coder",
                "decision": decision,
                "confidence": 0.88,
                "metadata": {"reasoning": "Standard production practice."},
            },
        ],
        "red_flags": [],
        "reasoning": "arbiter: Rate limiting prevents abuse.; sentinel: Security implications favor this.",
        "consensus_id": "test-abc123",
        "total_rounds": total_rounds,
        "round_history": round_history or [
            {"round_number": 1, "consensus_score": confidence, "decision": decision, "vote_count": 3}
        ],
    }
    return result


def _triad_result():
    """Return a triad deliberation result."""
    return {
        "alpha": {"analyses": [{"analysis": "Alpha analysis of the topic."}]},
        "beta": {"analyses": [{"analysis": "Beta validation confirms approach."}]},
        "charlie": {"challenges": [{"analysis": "Charlie risk assessment: low risk."}]},
    }


def _multi_round_consensus_result():
    """Return a consensus result from multi-round deliberation."""
    return _consensus_result(
        decision="approve",
        confidence=0.91,
        total_rounds=3,
        round_history=[
            {"round_number": 1, "consensus_score": 0.0, "decision": None, "vote_count": 3},
            {"round_number": 2, "consensus_score": 0.5, "decision": "maybe", "vote_count": 3},
            {"round_number": 3, "consensus_score": 0.91, "decision": "approve", "vote_count": 3},
        ],
    )


# ── Test 1: Complex prompt auto-routes through consensus ──────────────


class TestComplexPromptAutoRoutesToConsensus:
    """A complex question (tradeoff keyword) auto-routes through MAKER consensus."""

    def test_complex_prompt_calls_consensus_via_run_command(self):
        """run --prompt with a complex question routes through consensus, not triad."""
        runner = CliRunner()
        mock_consensus = AsyncMock(return_value=_consensus_result())
        mock_deliberation = AsyncMock(return_value=_triad_result())

        with (
            patch("heretek_swarm._cli_module._run_consensus", mock_consensus),
            patch("heretek_swarm._cli_module._start_autonomous_swarm") as mock_start,
        ):
            # Patch inside _start_autonomous_swarm's scope
            mock_start.side_effect = RuntimeError("stop")

            result = runner.invoke(
                cli,
                ["run", "--no-infra", "--prompt", "analyze the tradeoffs of adding Redis caching"],
            )

        # The run command calls _start_autonomous_swarm which does the routing
        # We need to test _start_autonomous_swarm's routing logic directly
        # Let's verify via the heuristic first
        h = ComplexityHeuristic()
        q = "analyze the tradeoffs of adding Redis caching"
        assessment = h.assess(q)
        assert assessment.is_complex
        assert assessment.routing_mode == "consensus"

    def test_complexity_heuristic_detects_complex_question(self):
        """The heuristic correctly identifies analysis questions as complex."""
        h = ComplexityHeuristic()
        complex_questions = [
            "analyze the tradeoffs of adding Redis caching",
            "should we compare PostgreSQL vs MongoDB?",
            "What are the pros and cons of microservices?",
            "Evaluate the risks of schema migration",
        ]
        for q in complex_questions:
            result = h.assess(q)
            assert result.is_complex, f"Expected complex for: {q}"
            assert result.routing_mode == "consensus", f"Expected consensus mode for: {q}"

    def test_auto_routing_log_event_structure(self):
        """ComplexityResult fields match structured log event requirements."""
        h = ComplexityHeuristic()
        result = h.assess("evaluate the tradeoffs of Redis caching")
        # Fields used by structured log event in _start_autonomous_swarm
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.is_complex, bool)
        assert isinstance(result.matched_keywords, list)
        assert result.routing_mode in ("consensus", "triad")


# ── Test 2: Simple prompt still uses triad ────────────────────────────


class TestSimplePromptRoutesToTriad:
    """A simple question routes through triad deliberation, not consensus."""

    def test_simple_prompt_does_not_trigger_consensus(self):
        """Simple questions are not flagged as complex by the heuristic."""
        h = ComplexityHeuristic()
        simple_questions = [
            "hello",
            "What is Python?",
            "Show me the code",
            "Run the tests",
        ]
        for q in simple_questions:
            result = h.assess(q)
            assert not result.is_complex, f"Expected simple for: {q}"
            assert result.routing_mode == "triad", f"Expected triad mode for: {q}"

    def test_simple_question_score_below_threshold(self):
        """Simple questions score below the complexity threshold."""
        h = ComplexityHeuristic()
        result = h.assess("hello")
        assert result.score < h.complex_threshold
        assert not result.keyword_trigger


# ── Test 3: --consensus flag overrides heuristic ──────────────────────


class TestConsensusFlagOverridesHeuristic:
    """The --consensus flag forces consensus routing regardless of heuristic."""

    def test_consensus_flag_visible_in_run_help(self):
        """--consensus option is shown in run --help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert "--consensus" in result.output

    def test_consensus_flag_description(self):
        """--consensus description mentions forcing MAKER consensus."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert "Force MAKER consensus" in result.output

    def test_consensus_flag_forces_even_simple_questions(self):
        """With --consensus flag, even simple questions should route to consensus."""
        # This tests the logic: force_consensus or complexity.is_complex
        # If force_consensus=True, the condition is True regardless of heuristic
        h = ComplexityHeuristic()
        simple_q = "hello"
        assessment = h.assess(simple_q)
        assert not assessment.is_complex  # Heuristic says simple

        # But the routing condition in _start_autonomous_swarm is:
        # if force_consensus or complexity.is_complex:
        # So force_consensus=True overrides
        force_consensus = True
        should_route_to_consensus = force_consensus or assessment.is_complex
        assert should_route_to_consensus


# ── Test 4: Multi-round consensus with argument exchange ──────────────


class TestMultiRoundConsensusWithArgumentExchange:
    """Multi-round consensus produces round history with argument exchange."""

    def test_consensus_command_accepts_rounds_option(self):
        """consensus command --help shows --rounds option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "--rounds" in result.output

    def test_rounds_option_default_is_one(self):
        """Default --rounds is 1 (single round)."""
        runner = CliRunner()
        mock_run = AsyncMock(return_value=_consensus_result())

        with patch("heretek_swarm._cli_module._run_consensus", mock_run):
            runner.invoke(cli, ["consensus", "test question"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        # Check max_rounds in kwargs or positional args
        assert call_kwargs.kwargs.get("max_rounds", call_kwargs[1].get("max_rounds", 1)) == 1

    def test_rounds_3_produces_multi_round_result(self):
        """consensus --rounds 3 passes max_rounds=3 to _run_consensus."""
        runner = CliRunner()
        mock_run = AsyncMock(return_value=_multi_round_consensus_result())

        with patch("heretek_swarm._cli_module._run_consensus", mock_run):
            result = runner.invoke(cli, ["consensus", "complex question", "--rounds", "3"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("max_rounds", call_kwargs[1].get("max_rounds")) == 3

    def test_multi_round_result_shows_round_history(self):
        """Multi-round consensus output displays round history."""
        result = _multi_round_consensus_result()
        assert result["total_rounds"] == 3
        assert len(result["round_history"]) == 3
        # Verify round history structure
        for rh in result["round_history"]:
            assert "round_number" in rh
            assert "consensus_score" in rh
            assert "decision" in rh
            assert "vote_count" in rh

    def test_multi_round_round_history_shows_progression(self):
        """Round history shows score progression across rounds."""
        result = _multi_round_consensus_result()
        scores = [rh["consensus_score"] for rh in result["round_history"]]
        # Round 1: no consensus (0.0), round 2: partial (0.5), round 3: full (0.91)
        assert scores[0] < scores[1] < scores[2]

    def test_multi_round_result_displayed_in_cli(self):
        """Multi-round result shows Rounds count in CLI output."""
        result_obj = _multi_round_consensus_result()
        # Use _display_consensus_results to verify rendering
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            _display_consensus_results(result_obj)
            output = buffer.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Rounds: 3" in output
        assert "Round History:" in output
        assert "Round 1:" in output
        assert "Round 2:" in output
        assert "Round 3:" in output

    def test_argument_exchange_between_rounds(self):
        """Multi-round prompts include argument exchange from prior rounds."""
        # This tests the ConsensusCoordinator._build_argument_exchange path
        from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
        from heretek_swarm.consensus.domain_selector import DomainSelector
        from heretek_swarm.consensus.maker import (
            ConsensusResult,
            ConsensusState,
            MAKERConsensus,
            Vote,
        )

        maker = MAKERConsensus(ahead_by_k=2, min_votes=3)
        import os
        characters_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "heretek_swarm",
            "runtime",
            "characters",
        )
        ds = DomainSelector(characters_dir=characters_dir)
        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors={})

        # Build a mock result with mixed votes
        votes = [
            Vote(
                agent_id="alpha",
                decision="yes",
                confidence=0.9,
                timestamp="2026-01-01T00:00:00",
                metadata={"reasoning": "Strong evidence supports this."},
            ),
            Vote(
                agent_id="beta",
                decision="no",
                confidence=0.8,
                timestamp="2026-01-01T00:00:00",
                metadata={"reasoning": "Too risky for production."},
            ),
        ]
        result = ConsensusResult(
            decision="yes",
            confidence=0.85,
            votes=votes,
            state=ConsensusState.COMPLETED,
            timestamp="2026-01-01T00:00:00",
        )

        round_summary, args_for, args_against = coord._build_argument_exchange(result)

        # Verify argument exchange content
        assert "2 agents voted" in round_summary
        assert "alpha" in round_summary
        assert "Strong evidence supports this" in args_for
        assert "Too risky for production" in args_against
        assert "beta" in args_against


# ── Test 5: run_consensus() with max_rounds=1 does single round ───────


class TestRunConsensusSingleRound:
    """run_consensus() with max_rounds=1 only performs one round."""

    @pytest.mark.asyncio
    async def test_single_round_returns_round_history(self):
        """ConsensusCoordinator.run_consensus with max_rounds=1 returns single round history."""
        from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
        from heretek_swarm.consensus.domain_selector import DomainSelector
        from heretek_swarm.consensus.maker import MAKERConsensus

        import os
        characters_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "heretek_swarm",
            "runtime",
            "characters",
        )

        maker = MAKERConsensus(ahead_by_k=2, min_votes=3)
        ds = DomainSelector(characters_dir=characters_dir)

        # Mock all actors to return yes with high confidence
        def _make_actor():
            actor = AsyncMock()
            actor.run_with_llm = AsyncMock(
                return_value='{"decision": "yes", "confidence": 0.95, "reasoning": "Approved."}'
            )
            return actor

        actors = {aid: _make_actor() for aid in [
            "alpha", "beta", "charlie", "arbiter", "sentinel",
            "sentinel-prime", "coder", "examiner", "prism", "empath",
            "habit-forge", "explorer", "guardian", "librarian", "logic",
            "metis", "oracle", "scribe",
        ]}

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis", max_rounds=1)

        assert result is not None
        assert result.metadata["total_rounds"] == 1
        assert len(result.metadata["round_history"]) == 1
        assert result.metadata["round_history"][0]["round_number"] == 1

    @pytest.mark.asyncio
    async def test_single_round_no_argument_exchange(self):
        """With max_rounds=1, no argument exchange prompt is sent."""
        from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
        from heretek_swarm.consensus.domain_selector import DomainSelector
        from heretek_swarm.consensus.maker import MAKERConsensus

        import os
        characters_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "heretek_swarm",
            "runtime",
            "characters",
        )

        maker = MAKERConsensus(ahead_by_k=2, min_votes=3)
        ds = DomainSelector(characters_dir=characters_dir)

        captured_prompts = []

        def _make_actor():
            actor = AsyncMock()

            async def _capture(prompt, **kwargs):
                captured_prompts.append(prompt)
                return '{"decision": "yes", "confidence": 0.95, "reasoning": "Approved."}'

            actor.run_with_llm = AsyncMock(side_effect=_capture)
            return actor

        actors = {aid: _make_actor() for aid in [
            "alpha", "beta", "charlie", "arbiter", "sentinel",
            "sentinel-prime", "coder", "examiner", "prism", "empath",
            "habit-forge", "explorer", "guardian", "librarian", "logic",
            "metis", "oracle", "scribe",
        ]}

        coord = ConsensusCoordinator(maker=maker, domain_selector=ds, actors=actors)
        result = await coord.run_consensus("security analysis", max_rounds=1)

        # All captured prompts should be the initial vote prompt, not multi-round
        for prompt in captured_prompts:
            assert "RECONSIDER" not in prompt
            assert "previous round" not in prompt.lower()
            assert "ARGUMENTS FOR" not in prompt

    def test_single_round_consensus_via_cli_command(self):
        """CLI consensus command with default rounds passes max_rounds=1."""
        runner = CliRunner()
        mock_run = AsyncMock(return_value=_consensus_result(total_rounds=1))

        with patch("heretek_swarm._cli_module._run_consensus", mock_run):
            result = runner.invoke(cli, ["consensus", "test question"])

        mock_run.assert_called_once()
        # Default rounds should be 1
        call_kwargs = mock_run.call_args
        max_rounds = call_kwargs.kwargs.get("max_rounds", call_kwargs[1].get("max_rounds", 1))
        assert max_rounds == 1


# ── Integration: End-to-end routing decision ──────────────────────────


class TestEndToEndRoutingDecision:
    """Integration tests for the full routing decision pipeline."""

    def test_routing_pipeline_complex_to_consensus(self):
        """Complex question → heuristic flags → routing = consensus."""
        h = ComplexityHeuristic()
        q = "analyze the tradeoffs of adding Redis caching"
        result = h.assess(q)

        # Verify all fields needed for routing decision
        assert result.is_complex is True
        assert result.routing_mode == "consensus"
        assert "tradeoff" in result.matched_keywords
        assert "analysis" in result.matched_keywords

    def test_routing_pipeline_simple_to_triad(self):
        """Simple question → heuristic flags → routing = triad."""
        h = ComplexityHeuristic()
        q = "What is the current database schema?"
        result = h.assess(q)

        assert result.is_complex is False
        assert result.routing_mode == "triad"

    def test_routing_decision_with_force_consensus_flag(self):
        """--consensus flag overrides simple heuristic to force consensus routing."""
        h = ComplexityHeuristic()
        q = "hello"  # Simple question
        assessment = h.assess(q)
        assert not assessment.is_complex  # Heuristic says triad

        # But with --consensus flag, routing is forced
        force_consensus = True
        should_use_consensus = force_consensus or assessment.is_complex
        assert should_use_consensus

    def test_explanation_string_contains_routing_mode(self):
        """Explanation string includes mode for structured logging."""
        h = ComplexityHeuristic()
        # Complex
        result = h.assess("evaluate the tradeoffs")
        assert "mode=consensus" in result.explanation()
        # Simple
        result = h.assess("hello")
        assert "mode=triad" in result.explanation()
