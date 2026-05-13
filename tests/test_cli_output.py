"""Tests for CLI display functions — startup banner, deliberation result output,
and daemon status display.

Verifies that ``_print_startup_banner()``, ``_display_deliberation_results()``,
``_display_daemon_status()``, and ``_query_daemon_socket()`` render / interact
correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from heretek_swarm.cli import (
    _display_daemon_status,
    _display_deliberation_results,
    _print_startup_banner,
    _query_daemon_socket,
)

if TYPE_CHECKING:
    import pytest

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
        results = _make_result_with_analyses(
            [
                {"analysis": "First analysis", "decision": "first"},
            ]
        )

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "ALPHA response:" in captured
        assert "BETA response:" in captured
        assert "CHARLIE response:" in captured
        assert "Deliberation complete." in captured

    @staticmethod
    def test_shows_analysis_content(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints the analysis/decision text for each agent."""
        results = _make_result_with_analyses(
            [
                {"analysis": "Alpha primary analysis", "decision": "alpha_decision"},
            ]
        )

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "Alpha primary analysis" in captured
        assert "alpha_decision" not in captured  # "analysis" is preferred key

    @staticmethod
    def test_uses_decision_fallback(capsys: pytest.CaptureFixture[str]) -> None:
        """When an entry lacks an ``analysis`` key, falls back to
        ``decision``."""
        results = _make_result_with_analyses(
            [
                {"decision": "fallback_decision_key"},
            ]
        )

        _display_deliberation_results(results)
        captured = capsys.readouterr().out

        assert "fallback_decision_key" in captured

    @staticmethod
    def test_extracts_nested_decision_from_analysis_dict(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``analysis`` is itself a dict with a ``decision`` key,
        extracts the inner ``decision`` value."""
        results = _make_result_with_analyses(
            [
                {"analysis": {"decision": "nested_decision_value"}},
            ]
        )

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


# ---------------------------------------------------------------------------
# _display_daemon_status tests
# ---------------------------------------------------------------------------


class TestDisplayDaemonStatus:
    """Tests for ``_display_daemon_status()``."""

    @staticmethod
    def test_prints_header_and_pid(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints a header with the daemon PID."""
        _display_daemon_status({"agents": []}, pid=12345, output_json=False)
        captured = capsys.readouterr().out
        assert "Daemon PID: 12345" in captured
        assert "Heretek Swarm Status (daemon)" in captured

    @staticmethod
    def test_shows_no_agent_message(capsys: pytest.CaptureFixture[str]) -> None:
        """Shows a message when the agent list is empty."""
        _display_daemon_status({"agents": []}, pid=999, output_json=False)
        captured = capsys.readouterr().out
        assert "No agent data available from daemon" in captured

    @staticmethod
    def test_prints_agent_table(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints a formatted table of agent status."""
        data = {
            "agents": [
                {
                    "agent_id": "alpha",
                    "state": "active",
                    "mailbox_size": 2,
                    "message_count": 10,
                    "error_count": 0,
                    "last_activity": "2025-01-01T00:00:00Z",
                },
                {
                    "agent_id": "beta",
                    "state": "idle",
                    "mailbox_size": 0,
                    "message_count": 5,
                    "error_count": 1,
                    "last_activity": "",
                },
            ],
        }
        _display_daemon_status(data, pid=42, output_json=False)
        captured = capsys.readouterr().out

        assert "Agent ID" in captured
        assert "State" in captured
        assert "Mailbox" in captured
        assert "Messages" in captured
        assert "Errors" in captured
        assert "alpha" in captured
        assert "beta" in captured
        assert "active" in captured
        assert "idle" in captured
        assert "2 agent(s) running" in captured

    @staticmethod
    def test_outputs_json_when_requested(capsys: pytest.CaptureFixture[str]) -> None:
        """Outputs valid JSON when output_json=True."""
        data = {
            "agents": [
                {
                    "agent_id": "gamma",
                    "state": "active",
                    "mailbox_size": 0,
                    "message_count": 3,
                    "error_count": 0,
                    "last_activity": "",
                },
            ],
        }
        import json

        _display_daemon_status(data, pid=77, output_json=True)
        captured = capsys.readouterr().out
        parsed = json.loads(captured)
        assert parsed["daemon_pid"] == 77
        assert len(parsed["agents"]) == 1
        assert parsed["agents"][0]["agent_id"] == "gamma"

    @staticmethod
    def test_json_mode_includes_agent_count(capsys: pytest.CaptureFixture[str]) -> None:
        """JSON output includes an agent_count field."""
        import json

        _display_daemon_status({"agents": []}, pid=1, output_json=True)
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["agent_count"] == 0

    @staticmethod
    def test_handles_missing_agent_data_keys(capsys: pytest.CaptureFixture[str]) -> None:
        """Missing keys in agent dicts don't cause errors."""
        data = {
            "agents": [
                {"agent_id": "minimal"},
            ],
        }
        # Should not raise
        _display_daemon_status(data, pid=9, output_json=False)
        captured = capsys.readouterr().out
        assert "minimal" in captured
        assert "1 agent(s) running" in captured


# ---------------------------------------------------------------------------
# _query_daemon_socket tests (mock-based)
# ---------------------------------------------------------------------------


class TestQueryDaemonSocket:
    """Tests for ``_query_daemon_socket()``."""

    @staticmethod
    def test_returns_none_when_socket_missing() -> None:
        """Returns None when the socket file does not exist."""
        with patch("heretek_swarm.cli.Path.exists") as mock_exists:
            mock_exists.return_value = False
            result = _query_daemon_socket()
            assert result is None

    @staticmethod
    def test_returns_none_on_connection_error() -> None:
        """Returns None when connecting to the socket fails."""
        import socket

        # AF_UNIX not available on Windows; add it so the function can look it up.
        if not hasattr(socket, "AF_UNIX"):
            socket.AF_UNIX = 1  # arbitrary, mock won't actually use it

        with (
            patch("heretek_swarm.cli.Path.exists") as mock_exists,
            patch("socket.socket") as mock_socket_cls,
        ):
            mock_exists.return_value = True
            mock_socket = MagicMock()
            mock_socket_cls.return_value = mock_socket
            mock_socket.connect.side_effect = OSError("Connection refused")
            result = _query_daemon_socket()
            assert result is None

    @staticmethod
    def test_returns_parsed_response() -> None:
        """Returns parsed JSON on successful exchange."""
        import socket

        if not hasattr(socket, "AF_UNIX"):
            socket.AF_UNIX = 1

        with (
            patch("heretek_swarm.cli.Path.exists") as mock_exists,
            patch("socket.socket") as mock_socket_cls,
        ):
            mock_exists.return_value = True
            mock_socket = MagicMock()
            mock_socket_cls.return_value = mock_socket
            mock_socket.recv.side_effect = [b'{"agents":[],"ok":true}\n', b""]
            result = _query_daemon_socket()
            assert result == {"agents": [], "ok": True}

    @staticmethod
    def test_sends_status_query() -> None:
        """Sends {\"type\": \"status\"} over the socket."""
        import socket

        if not hasattr(socket, "AF_UNIX"):
            socket.AF_UNIX = 1

        with (
            patch("heretek_swarm.cli.Path.exists") as mock_exists,
            patch("socket.socket") as mock_socket_cls,
        ):
            mock_exists.return_value = True
            mock_socket = MagicMock()
            mock_socket_cls.return_value = mock_socket
            mock_socket.recv.side_effect = [b'{"ok":true}\n', b""]
            _query_daemon_socket()
            # Check that the sent data contains the status query
            sent_data = mock_socket.sendall.call_args[0][0]
            import json

            assert json.loads(sent_data.decode()) == {"type": "status"}


# ---------------------------------------------------------------------------
# _display_routed_result tests
# ---------------------------------------------------------------------------


class TestDisplayRoutedResult:
    """Tests for ``_display_routed_result()``."""

    @staticmethod
    def test_shows_dispatched_result(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints success icon, target agent, task type, and message ID
        when status is ``\"dispatched\"``."""
        from heretek_swarm.cli import _display_routed_result

        result = {
            "status": "dispatched",
            "target_agent": "coder",
            "task_type": "code_analysis",
            "message_id": "msg_abc123",
        }
        _display_routed_result(result)
        captured = capsys.readouterr().out

        assert "Routed to agent: coder" in captured
        assert "Task type:       code_analysis" in captured
        assert "Status:          dispatched" in captured
        assert "Message ID:      msg_abc123" in captured
        assert "Route complete." in captured

    @staticmethod
    def test_shows_failed_result(capsys: pytest.CaptureFixture[str]) -> None:
        """Prints failure icon and error message when status is
        ``\"failed\"``."""
        from heretek_swarm.cli import _display_routed_result

        result = {
            "status": "failed",
            "target_agent": "coder",
            "task_type": "code_analysis",
            "message_id": "?",
            "error": "Agent not found in registry",
        }
        _display_routed_result(result)
        captured = capsys.readouterr().out

        assert "Routed to agent: coder" in captured
        assert "Status:          failed" in captured
        assert "Error:           Agent not found in registry" in captured

    @staticmethod
    def test_shows_unknown_status(capsys: pytest.CaptureFixture[str]) -> None:
        """Uses ``?`` icon when status is unrecognized."""
        from heretek_swarm.cli import _display_routed_result

        result = {"status": "pending"}
        _display_routed_result(result)
        captured = capsys.readouterr().out

        assert "Routed to agent: ?" in captured
        assert "Status:          pending" in captured

    @staticmethod
    def test_handles_empty_dict(capsys: pytest.CaptureFixture[str]) -> None:
        """Does not raise when given an empty dict — falls back to
        default values for all fields."""
        from heretek_swarm.cli import _display_routed_result

        result: dict = {}
        _display_routed_result(result)
        captured = capsys.readouterr().out

        assert "Routed to agent: ?" in captured
