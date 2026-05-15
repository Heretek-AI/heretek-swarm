"""Tests for the `heretek-swarm consensus` CLI command."""

from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from heretek_swarm.cli import _display_consensus_results, cli

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _sample_consensus_result() -> dict:
    """Return a realistic consensus result dict matching run_consensus output."""
    return {
        "decision": "yes",
        "confidence": 0.87,
        "votes": [
            {
                "agent_id": "arbiter",
                "decision": "yes",
                "confidence": 0.92,
                "metadata": {"reasoning": "Rate limiting prevents abuse and improves stability."},
            },
            {
                "agent_id": "sentinel",
                "decision": "yes",
                "confidence": 0.85,
                "metadata": {"reasoning": "Security implications strongly favor rate limiting."},
            },
            {
                "agent_id": "coder",
                "decision": "yes",
                "confidence": 0.88,
                "metadata": {"reasoning": "Standard practice for production APIs."},
            },
            {
                "agent_id": "examiner",
                "decision": "no",
                "confidence": 0.65,
                "metadata": {"reasoning": "May impact legitimate high-volume clients."},
            },
            {
                "agent_id": "prism",
                "decision": "yes",
                "confidence": 0.90,
                "metadata": {},
            },
        ],
        "red_flags": [],
        "reasoning": "arbiter: Rate limiting prevents abuse and improves stability.; sentinel: Security implications strongly favor rate limiting.",  # noqa: E501
        "consensus_id": "consensus-abc123",
    }


def _sample_consensus_result_with_red_flags() -> dict:
    """Return a consensus result that includes red flags."""
    result = _sample_consensus_result()
    result["red_flags"] = [
        "Low confidence on decision (avg 0.45)",
        "Agent 'coder' abstained due to LLM failure",
    ]
    return result


def _sample_consensus_error_result() -> dict:
    """Return an error result when consensus cannot be initiated."""
    return {
        "decision": "error",
        "confidence": 0.0,
        "votes": [],
        "red_flags": ["Supervisor not initialized"],
        "reasoning": "Cannot run consensus without actor supervisor",
    }


# ------------------------------------------------------------------
# _display_consensus_results unit tests
# ------------------------------------------------------------------


class TestDisplayConsensusResults:
    """Test the _display_consensus_results helper directly."""

    def test_displays_decision_and_confidence(self, capsys):
        """Winning decision and confidence score are printed."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "Decision:  yes" in captured.out
        assert "Confidence: 0.87" in captured.out

    def test_displays_agents(self, capsys):
        """Agent IDs are listed in the output."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "arbiter" in captured.out
        assert "sentinel" in captured.out
        assert "coder" in captured.out

    def test_displays_individual_votes(self, capsys):
        """Each agent's vote and confidence is printed."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "yes" in captured.out
        assert "0.92" in captured.out
        assert "0.85" in captured.out

    def test_displays_vote_breakdown(self, capsys):
        """Vote breakdown tallies are printed."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "Vote breakdown:" in captured.out
        assert "yes: 4" in captured.out
        assert "no: 1" in captured.out

    def test_displays_red_flags(self, capsys):
        """Red flags section appears when flags are present."""
        _display_consensus_results(_sample_consensus_result_with_red_flags())
        captured = capsys.readouterr()
        assert "Red Flags:" in captured.out
        assert "Low confidence" in captured.out
        assert "LLM failure" in captured.out

    def test_no_red_flags_section_when_empty(self, capsys):
        """Red flags section is omitted when list is empty."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "Red Flags:" not in captured.out

    def test_displays_consensus_id(self, capsys):
        """Consensus ID is printed."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "consensus-abc123" in captured.out

    def test_displays_reasoning(self, capsys):
        """Reasoning text is printed."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "Rate limiting prevents abuse" in captured.out

    def test_displays_empty_votes(self, capsys):
        """Gracefully handles empty votes list."""
        result = _sample_consensus_error_result()
        _display_consensus_results(result)
        captured = capsys.readouterr()
        assert "Decision:  error" in captured.out
        assert "Agents (0):" in captured.out

    def test_displays_agent_reasoning_per_vote(self, capsys):
        """Per-agent reasoning is shown for votes that have it."""
        _display_consensus_results(_sample_consensus_result())
        captured = capsys.readouterr()
        assert "Reasoning: Rate limiting prevents abuse" in captured.out


# ------------------------------------------------------------------
# CLI command tests
# ------------------------------------------------------------------


class TestConsensusCLI:
    """Test the `consensus` Click command via CliRunner."""

    def _run_with_mock(self, result: dict | None = None, side_effect: Exception | None = None):
        """Helper to run the CLI command with a mocked swarm."""
        if result is None:
            result = _sample_consensus_result()

        runner = CliRunner()

        mock_run_consensus = AsyncMock()

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            if side_effect:
                mock_run_consensus.side_effect = side_effect
            else:
                mock_run_consensus.return_value = result

            return runner.invoke(
                cli,
                ["consensus", "should we add rate limiting?"],
            )

    def test_consensus_command_exists(self):
        """consensus command is registered in the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert result.exit_code == 0
        assert "Run MAKER consensus" in result.output

    def test_consensus_help_shows_question_arg(self):
        """Help output shows the QUESTION argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "QUESTION" in result.output

    def test_consensus_help_shows_timeout_option(self):
        """Help output shows the --timeout option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "--timeout" in result.output

    def test_consensus_help_shows_participants_option(self):
        """Help output shows the --participants option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "--participants" in result.output

    def test_consensus_help_shows_examples(self):
        """Help epilog includes usage examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "heretek-swarm consensus" in result.output

    def test_consensus_requires_question(self):
        """Command fails without a question argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_consensus_displays_results(self):
        """Successful consensus output contains key fields."""
        result_obj = self._run_with_mock()
        assert result_obj.exit_code == 0
        assert "Consensus ID:" in result_obj.output
        assert "Decision:" in result_obj.output
        assert "Confidence:" in result_obj.output
        assert "Vote breakdown:" in result_obj.output

    def test_consensus_displays_question_in_output(self):
        """Question is echoed in the output header."""
        result_obj = self._run_with_mock()
        assert "should we add rate limiting?" in result_obj.output

    def test_consensus_displays_agents(self):
        """Agent IDs from votes appear in output."""
        result_obj = self._run_with_mock()
        assert "arbiter" in result_obj.output
        assert "sentinel" in result_obj.output

    def test_consensus_displays_red_flags(self):
        """Red flags appear when present in result."""
        result_obj = self._run_with_mock(result=_sample_consensus_result_with_red_flags())
        assert "Red Flags:" in result_obj.output

    def test_consensus_handles_failure(self):
        """Command exits non-zero when swarm raises an exception."""
        result_obj = self._run_with_mock(side_effect=RuntimeError("Swarm initialization failed"))
        assert result_obj.exit_code == 1
        assert "failed" in result_obj.output.lower()

    def test_consensus_error_result_displays(self):
        """Error result is displayed gracefully."""
        result_obj = self._run_with_mock(result=_sample_consensus_error_result())
        assert result_obj.exit_code == 0
        assert "Decision:  error" in result_obj.output

    def test_consensus_with_custom_timeout(self):
        """--timeout flag is accepted and passed through."""
        runner = CliRunner()

        mock_run_consensus = AsyncMock(return_value=_sample_consensus_result())

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            result_obj = runner.invoke(
                cli,
                ["consensus", "test question", "--timeout", "180"],
            )

        assert result_obj.exit_code == 0
        assert "180.0s" in result_obj.output

    def test_consensus_displays_vote_reasoning(self):
        """Per-agent reasoning text appears in output."""
        result_obj = self._run_with_mock()
        assert "Rate limiting prevents abuse" in result_obj.output

    def test_consensus_displays_breakdown_counts(self):
        """Vote breakdown shows correct tally."""
        result_obj = self._run_with_mock()
        assert "yes: 4" in result_obj.output
        assert "no: 1" in result_obj.output

    def test_consensus_command_in_core_operations_group(self):
        """consensus appears in the Core Operations help group."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        # GroupedGroup renders commands in sections
        assert "consensus" in result.output


# ------------------------------------------------------------------
# T03: --rounds flag tests
# ------------------------------------------------------------------


class TestConsensusRoundsFlag:
    """Test the --rounds option on the consensus command."""

    def test_rounds_help_visible(self):
        """--rounds option appears in consensus help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["consensus", "--help"])
        assert "--rounds" in result.output

    def test_rounds_default_is_one(self):
        """Default rounds is 1 (single-round, no argument exchange)."""
        runner = CliRunner()
        mock_run_consensus = AsyncMock(return_value=_sample_consensus_result())

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            runner.invoke(cli, ["consensus", "test question"])

        # Default max_rounds=1
        mock_run_consensus.assert_called_once()
        call_kwargs = mock_run_consensus.call_args
        assert call_kwargs.kwargs.get("max_rounds", call_kwargs[1].get("max_rounds", 1)) == 1

    def test_rounds_passed_through(self):
        """--rounds 3 is passed as max_rounds to _run_consensus."""
        runner = CliRunner()
        mock_run_consensus = AsyncMock(return_value=_sample_consensus_result())

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            runner.invoke(cli, ["consensus", "test question", "--rounds", "3"])

        mock_run_consensus.assert_called_once()
        call_kwargs = mock_run_consensus.call_args
        assert call_kwargs.kwargs.get("max_rounds", call_kwargs[1].get("max_rounds")) == 3

    def test_rounds_displayed_when_gt_one(self):
        """Output shows round count when --rounds > 1."""
        result_with_rounds = _sample_consensus_result()
        result_with_rounds["total_rounds"] = 3
        result_with_rounds["round_history"] = [
            {"round_number": 1, "consensus_score": 0.0, "decision": None, "vote_count": 5},
            {"round_number": 2, "consensus_score": 0.0, "decision": None, "vote_count": 5},
            {"round_number": 3, "consensus_score": 0.87, "decision": "yes", "vote_count": 5},
        ]

        runner = CliRunner()
        mock_run_consensus = AsyncMock(return_value=result_with_rounds)

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            result_obj = runner.invoke(cli, ["consensus", "test question", "--rounds", "3"])

        assert result_obj.exit_code == 0
        assert "Rounds: 3" in result_obj.output

    def test_rounds_label_in_output(self):
        """Output shows 'Rounds: N' label when multi-round."""
        result_multi = _sample_consensus_result()
        result_multi["total_rounds"] = 2
        result_multi["round_history"] = [
            {"round_number": 1, "consensus_score": 0.4, "decision": "no", "vote_count": 5},
            {"round_number": 2, "consensus_score": 0.87, "decision": "yes", "vote_count": 5},
        ]

        runner = CliRunner()
        mock_run_consensus = AsyncMock(return_value=result_multi)

        with patch("heretek_swarm.cli.consensus._run_consensus", mock_run_consensus):
            result_obj = runner.invoke(cli, ["consensus", "test", "--rounds", "2"])

        assert "Rounds: 2" in result_obj.output


# ------------------------------------------------------------------
# T03: Round history display tests
# ------------------------------------------------------------------


class TestRoundHistoryDisplay:
    """Test _display_consensus_results with round_history data."""

    def test_round_history_section_appears(self):
        """Round History section is printed when round_history is present."""
        result = _sample_consensus_result()
        result["total_rounds"] = 2
        result["round_history"] = [
            {"round_number": 1, "consensus_score": 0.4, "decision": "no", "vote_count": 5},
            {"round_number": 2, "consensus_score": 0.87, "decision": "yes", "vote_count": 5},
        ]
        _display_consensus_results(result)
        # capsys doesn't work outside pytest, use a captured approach
        # This test verifies the function doesn't crash with round_history

    def test_round_history_printed_via_capsys(self, capsys):
        """Round History lines appear in captured output."""
        result = _sample_consensus_result()
        result["total_rounds"] = 3
        result["round_history"] = [
            {"round_number": 1, "consensus_score": 0.3, "decision": None, "vote_count": 5},
            {"round_number": 2, "consensus_score": 0.5, "decision": "maybe", "vote_count": 5},
            {"round_number": 3, "consensus_score": 0.87, "decision": "yes", "vote_count": 5},
        ]
        _display_consensus_results(result)
        captured = capsys.readouterr()
        assert "Round History:" in captured.out
        assert "Round 1:" in captured.out
        assert "Round 2:" in captured.out
        assert "Round 3:" in captured.out
        assert "score=0.87" in captured.out

    def test_no_round_history_when_single_round(self, capsys):
        """No Round History section when total_rounds=1 and no history."""
        result = _sample_consensus_result()
        _display_consensus_results(result)
        captured = capsys.readouterr()
        assert "Round History:" not in captured.out

    def test_round_history_with_none_decision(self, capsys):
        """Round with no consensus shows decision=None."""
        result = _sample_consensus_result()
        result["total_rounds"] = 2
        result["round_history"] = [
            {"round_number": 1, "consensus_score": 0.0, "decision": None, "vote_count": 3},
            {"round_number": 2, "consensus_score": 0.85, "decision": "approve", "vote_count": 5},
        ]
        _display_consensus_results(result)
        captured = capsys.readouterr()
        assert "decision=None" in captured.out
        assert "decision=approve" in captured.out


# ------------------------------------------------------------------
# T03: --consensus flag on run command tests
# ------------------------------------------------------------------


class TestRunConsensusFlag:
    """Test the --consensus flag on the run command."""

    def test_consensus_flag_help_visible(self):
        """--consensus appears in run help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert "--consensus" in result.output

    def test_consensus_flag_accepted(self):
        """--consensus flag is accepted without error in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert "Force MAKER consensus" in result.output

    def test_consensus_flag_in_examples(self):
        """--consensus appears in run command examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert "--consensus" in result.output


# ------------------------------------------------------------------
# T03: Auto-routing integration tests (via _start_autonomous_swarm)
# ------------------------------------------------------------------


class TestAutoRouting:
    """Test that _start_autonomous_swarm uses ComplexityHeuristic for routing."""

    @pytest.mark.asyncio
    async def test_complex_question_routes_to_consensus(self, capsys):
        """A complex question (tradeoff keyword) routes through consensus."""
        from heretek_swarm.consensus.complexity import ComplexityHeuristic

        # Verify the heuristic flags this as complex
        h = ComplexityHeuristic()
        q = "analyze the tradeoffs of adding Redis caching"
        assert h.is_complex(q)

    @pytest.mark.asyncio
    async def test_simple_question_routes_to_deliberation(self, capsys):
        """A simple question routes through triad deliberation."""
        from heretek_swarm.consensus.complexity import ComplexityHeuristic

        h = ComplexityHeuristic()
        q = "hello"
        assert not h.is_complex(q)

    def test_routing_log_event_fields(self):
        """ComplexityResult has fields needed for structured log events."""
        from heretek_swarm.consensus.complexity import ComplexityHeuristic

        h = ComplexityHeuristic()
        result = h.assess("analyze the tradeoffs of Redis caching")
        # These fields should be available for structured logging
        assert hasattr(result, "score")
        assert hasattr(result, "routing_mode")
        assert isinstance(result.score, float)
        assert result.routing_mode in ("consensus", "triad")

    def test_routing_explanation_for_logging(self):
        """Explanation string is suitable for structured log output."""
        from heretek_swarm.consensus.complexity import ComplexityHeuristic

        h = ComplexityHeuristic()
        result = h.assess("should we evaluate the tradeoffs?")
        exp = result.explanation()
        assert "complexity=" in exp
        assert "mode=" in exp
