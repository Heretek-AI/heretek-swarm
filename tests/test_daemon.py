"""Tests for the daemon module — PID file, Unix socket, signal handling, and
cleanup.

These tests focus on the functions that do **not** require an actual fork or
daemon process (``read_pid_file``, ``send_stop``, ``cleanup_daemon``,
``_build_status_response``).  The ``daemonize`` function itself is tested
indirectly via integration tests.

Note on platform: several functions (``send_stop``, ``read_pid_file``) use
``os.kill`` / ``os.open`` which are available on both Unix and Windows, but
the daemonisation path itself is gated on ``sys.platform != "win32"``.
"""

from __future__ import annotations

import json
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

from heretek_swarm.actors.base import ActorState, ActorStatus
from heretek_swarm.runtime.daemon import (
    DEFAULT_PID_FILE,
    DEFAULT_SOCKET_PATH,
    _build_status_response,
    cleanup_daemon,
    read_pid_file,
    send_stop,
)

# =========================================================================
# read_pid_file
# =========================================================================


class TestReadPidFile:
    """Tests for ``read_pid_file()``."""

    @staticmethod
    def test_reads_valid_pid(tmp_path: Path) -> None:
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("12345\n")

        assert read_pid_file(pid_file) == 12345

    @staticmethod
    def test_returns_none_for_missing_file(tmp_path: Path) -> None:
        pid_file = tmp_path / "nonexistent.pid"
        assert read_pid_file(pid_file) is None

    @staticmethod
    def test_returns_none_for_invalid_content(tmp_path: Path) -> None:
        pid_file = tmp_path / "bad.pid"
        pid_file.write_text("not_a_number")
        assert read_pid_file(pid_file) is None

    @staticmethod
    def test_returns_none_for_empty_file(tmp_path: Path) -> None:
        pid_file = tmp_path / "empty.pid"
        pid_file.write_text("")
        assert read_pid_file(pid_file) is None

    @staticmethod
    def test_strips_whitespace(tmp_path: Path) -> None:
        pid_file = tmp_path / "whitespace.pid"
        pid_file.write_text("  98765  \n")
        assert read_pid_file(pid_file) == 98765


# =========================================================================
# send_stop
# =========================================================================


class TestSendStop:
    """Tests for ``send_stop()``."""

    @staticmethod
    def test_sends_sigterm_to_running_pid() -> None:
        # Use our own PID — sending SIGTERM to self would kill us,
        # so we use os.kill(pid, 0) pattern but with SIGTERM on the
        # current process would be fatal.  Instead we mock os.kill.
        with patch("heretek_swarm.runtime.daemon.os.kill") as mock_kill:
            result = send_stop(99999)
            assert result is True
            mock_kill.assert_called_once_with(99999, signal.SIGTERM)

    @staticmethod
    def test_returns_false_on_process_lookup_error() -> None:
        with patch("heretek_swarm.runtime.daemon.os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError()
            result = send_stop(99999)
            assert result is False

    @staticmethod
    def test_returns_false_on_permission_error() -> None:
        with patch("heretek_swarm.runtime.daemon.os.kill") as mock_kill:
            mock_kill.side_effect = PermissionError()
            result = send_stop(99999)
            assert result is False


# =========================================================================
# cleanup_daemon
# =========================================================================


class TestCleanupDaemon:
    """Tests for ``cleanup_daemon()``."""

    @staticmethod
    def test_removes_pid_and_socket(tmp_path: Path) -> None:
        pid_file = tmp_path / "test.pid"
        socket_path = tmp_path / "test.sock"

        pid_file.write_text("12345")
        socket_path.write_text("stale")

        assert pid_file.exists()
        assert socket_path.exists()

        cleanup_daemon(pid_file, socket_path)

        assert not pid_file.exists()
        assert not socket_path.exists()

    @staticmethod
    def test_does_not_raise_on_missing_files(tmp_path: Path) -> None:
        pid_file = tmp_path / "missing.pid"
        socket_path = tmp_path / "missing.sock"

        # Should not raise FileNotFoundError
        cleanup_daemon(pid_file, socket_path)
        assert True


# =========================================================================
# _build_status_response
# =========================================================================


class TestBuildStatusResponse:
    """Tests for ``_build_status_response()``."""

    @staticmethod
    def make_mock_status(
        agent_id: str,
        state_value: str = "active",
        mailbox_size: int = 0,
        message_count: int = 0,
        last_activity: str | None = None,
        error_count: int = 0,
    ) -> ActorStatus:
        return ActorStatus(
            agent_id=agent_id,
            state=ActorState(state_value),
            message_count=message_count,
            created_at="2025-01-01T00:00:00Z",
            topics=[],
            capabilities=[],
            mailbox_size=mailbox_size,
            last_activity=last_activity,
            error_count=error_count,
        )

    @staticmethod
    def test_returns_agent_list() -> None:
        swarm = MagicMock()
        swarm.supervisor.get_all_status.return_value = {
            "alpha": TestBuildStatusResponse.make_mock_status(
                "alpha", mailbox_size=2, message_count=10
            ),
            "beta": TestBuildStatusResponse.make_mock_status(
                "beta", mailbox_size=0, message_count=5
            ),
        }

        response = _build_status_response(swarm)
        assert "agents" in response
        assert len(response["agents"]) == 2

        agent_ids = {a["agent_id"] for a in response["agents"]}
        assert agent_ids == {"alpha", "beta"}

    @staticmethod
    def test_includes_status_fields() -> None:
        swarm = MagicMock()
        swarm.supervisor.get_all_status.return_value = {
            "steward": TestBuildStatusResponse.make_mock_status(
                "steward",
                state_value="active",
                mailbox_size=1,
                message_count=42,
                last_activity="2025-06-01T12:00:00Z",
                error_count=3,
            ),
        }

        response = _build_status_response(swarm)
        agent = response["agents"][0]
        assert agent["agent_id"] == "steward"
        assert agent["state"] == "active"
        assert agent["mailbox_size"] == 1
        assert agent["message_count"] == 42
        assert agent["last_activity"] == "2025-06-01T12:00:00Z"
        assert agent["error_count"] == 3

    @staticmethod
    def test_handles_none_supervisor() -> None:
        swarm = MagicMock()
        swarm.supervisor = None
        response = _build_status_response(swarm)
        assert response["agents"] == []
        assert "error" in response

    @staticmethod
    def test_handles_empty_supervisor() -> None:
        swarm = MagicMock()
        swarm.supervisor.get_all_status.return_value = {}
        response = _build_status_response(swarm)
        assert response["agents"] == []
        assert "error" not in response

    @staticmethod
    def test_handles_exception_from_get_all_status() -> None:
        swarm = MagicMock()
        swarm.supervisor.get_all_status.side_effect = RuntimeError("boom")
        response = _build_status_response(swarm)
        assert response["agents"] == []
        assert "error" in response

    @staticmethod
    def test_response_is_json_serializable() -> None:
        swarm = MagicMock()
        swarm.supervisor.get_all_status.return_value = {
            "steward": TestBuildStatusResponse.make_mock_status(
                "steward",
                mailbox_size=3,
                message_count=7,
            ),
        }
        response = _build_status_response(swarm)
        # Should not raise
        json.dumps(response, default=str)


# =========================================================================
# DaemonContext defaults
# =========================================================================


class TestDefaults:
    """Smoke tests for default path constants."""

    @staticmethod
    def test_default_pid_file() -> None:
        assert Path("/var/run/heretek-swarm.pid") == DEFAULT_PID_FILE

    @staticmethod
    def test_default_socket_path() -> None:
        assert Path("/tmp/heretek-swarm.sock") == DEFAULT_SOCKET_PATH
