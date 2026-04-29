"""Tests for CLI display functions — startup banner and deliberation result output.

Verifies that ``_print_startup_banner()`` and ``_display_deliberation_results()``
render text to stdout without errors, covering happy-path, error, and empty
result scenarios.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from heretek_swarm.cli import _display_deliberation_results, _print_startup_banner


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_result_with_analyses(
    analyses: list[dict],
    challenges: list[dict] | None = None,
) -> dict[str, dict]:
    """Build a full ``run_deliberation()``-style result dict.

    Args:
        analyses: List of analysis entries for alpha and beta
        challenges: List of challenge entries for charlie (defaults to ``analyses``)

    Returns:
        Dict keyed by ``"alpha"``, ``"beta"``, ``"charlie"``.
    """
    if challenges is None:
        challenges = analyses
    return {
        "alpha": {"analyses": analyses},
        "beta": {"analyses": analyses},
        "charlie": {"challenges": challenges},
    }


# ---------------------------------------------------------------------------
# _print_startup_banner tests
# ---------------------------------------------------------------------------


class TestPrintStartupBanner:
    """Tests for ``_print_startup_banner()``."""

    @staticmethod
    def test_prints_component_status_table(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints the startup banner with all component rows and a
        separator line, without raising."""
        swarm = MagicMock()
        swarm.get_startup_status.return_value = {
            "Channels": "✓ Initialized",
            "Memory": "✓ Initialized",
            "RAG": "✓ Initialized",
            "Consensus": "✓ Initialized",
            "Event Mesh": "✓ Connected",
            "MCP Tools": "✓ Initialized",
            "Agents": "✓ 23 spawned",
        }

        _print_startup_banner(swarm)
        captured = capsys.readouterr().out

        assert "Component" in captured
        assert "Status" in captured
        assert "Channels" in captured
        assert "✓ Initialized" in captured
        assert "Agents" in captured
        assert "✓ 23 spawned" in captured
        # All healthy — no degraded warning
        assert "degraded" not in captured.lower()

    @staticmethod
    def test_shows_degraded_warning_on_failure(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When any component status starts with ``✗``, prints a warning
        about degraded capabilities."""
        swarm = MagicMock()
        swarm.get_startup_status.return_value = {
            "Channels": "✓ Initialized",
            "Event Mesh": "✗ Unavailable",
            "Agents": "✓ 23 spawned",
        }

        _print_startup_banner(swarm)
        captured = capsys.readouterr().out

        assert "✗ Unavailable" in captured
        assert "degraded capabilities" in captured.lower()


# ---------------------------------------------------------------------------
# _display_deliberation_results tests
# ---------------------------------------------------------------------------


class TestDisplayDeliberationResults:
    """Tests for ``_display_deliberation_results()``."""

    @staticmethod
    def test_shows_agent_id_labels(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints ALPHA, BETA, CHARLIE headings for each agent's result."""
        results = _make_result_with_analyses([
            {"analysis": "First analysis", "decision": "first"},
        ])

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "ALPHA response:" in captured
        assert "BETA response:" in captured
        assert "CHARLIE response:" in captured
        assert "Deliberation complete." in captured

    @staticmethod
    def test_shows_analysis_content(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints the analysis/decision text for each agent."""
        results = _make_result_with_analyses([
            {"analysis": "Alpha primary analysis", "decision": "alpha_decision"},
        ])

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "Alpha primary analysis" in captured
        assert "alpha_decision" not in captured  # "analysis" is preferred key

    @staticmethod
    def test_uses_decision_fallback(capsys: pytest.CaptureFixture[str]) -> None:
        """When an entry lacks an ``analysis`` key, falls back to
        ``decision``."""
        results = _make_result_with_analyses([
            {"decision": "fallback_decision_key"},
        ])

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "fallback_decision_key" in captured

    @staticmethod
    def test_extracts_nested_decision_from_analysis_dict(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``analysis`` is itself a dict with a ``decision`` key,
        extracts the inner ``decision`` value."""
        results = _make_result_with_analyses([
            {"analysis": {"decision": "nested_decision_value"}},
        ])

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "nested_decision_value" in captured

    @staticmethod
    def test_shows_error_message(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints ``[Error: ...]`` when a result dict contains an
        ``error`` key, while still showing other agents' results."""
        results = {
            "alpha": {"analyses": [{"analysis": "alpha ok"}]},
            "beta": {"error": "Agent beta not found"},
            "charlie": {"challenges": [{"analysis": "charlie input"}]},
        }

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "[Error: Agent beta not found]" in captured
        assert "alpha ok" in captured
        assert "charlie input" in captured

    @staticmethod
    def test_shows_no_analysis_produced(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints ``[No analysis produced]`` when an agent's analyses
        list is empty."""
        results = _make_result_with_analyses([])

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "[No analysis produced]" in captured

    @staticmethod
    def test_missing_agent_returns_empty_string(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When an agent ID is missing from the results dict (not even
        an empty entry), the function still prints the heading and then
        ``[No analysis produced]`` because ``{}.get("analyses", [])`` is
        empty."""
        results = {
            "alpha": {"analyses": [{"analysis": "only alpha"}]},
            # beta and charlie deliberately absent
        }

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "ALPHA response:" in captured
        assert "only alpha" in captured
        assert "[No analysis produced]" in captured
