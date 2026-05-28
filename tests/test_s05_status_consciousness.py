"""
Tests for S05: consciousness metrics wired into daemon _build_status_response()
and CLI status --json output.

Covers:
- _build_status_response includes consciousness dict with correct fields
- JSON output path includes consciousness from daemon response
- API fallback JSON path includes consciousness when agent data exists
- Error paths: empty consciousness on collection failure, no phantom consciousness
  when no agents exist
- Human-readable output includes Consciousness Metrics section
"""

from __future__ import annotations

import json as json_mod
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.observability.metrics import (
    ConsciousnessMetricsData,
    SwarmMetricsCollector,
    get_metrics_collector,
)
from heretek_swarm.runtime.daemon import _build_status_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeStateEnum:
    """Stand-in for the real AgentState enum — exposes ``.value``."""

    def __init__(self, value: str) -> None:
        self.value = value


class _FakeAgentStatus:
    """Minimal stub matching what supervisor.get_all_status() returns."""

    def __init__(self, state_str: str = "active") -> None:
        self._state = _FakeStateEnum(state_str)

    @property
    def state(self) -> _FakeStateEnum:
        return self._state

    @property
    def mailbox_size(self) -> int:
        return 5

    @property
    def message_count(self) -> int:
        return 42

    @property
    def last_activity(self) -> str:
        return "2026-05-28T09:00:00Z"

    @property
    def error_count(self) -> int:
        return 1


def _make_mock_swarm(agent_ids: list[str] | None = None) -> MagicMock:
    """Build a mock AutonomousSwarm with a supervisor returning fake agents."""
    if agent_ids is None:
        agent_ids = ["agent-alpha", "agent-beta", "agent-gamma"]

    all_status = {aid: _FakeAgentStatus("active") for aid in agent_ids}
    supervisor = MagicMock()
    supervisor.get_all_status.return_value = all_status

    swarm = MagicMock()
    swarm.supervisor = supervisor
    return swarm


def _populate_collector_with_agents(
    collector: SwarmMetricsCollector,
    agent_ids: list[str],
) -> None:
    """Record some activity so collector has agent data."""
    for i, aid in enumerate(agent_ids):
        collector.record_agent_activity(
            aid,
            task_completed=True,
            task_failed=(i % 2 == 0),  # alternate success/failure
            task_duration_ms=100.0 + i * 50,
            message_sent=True,
            message_received=True,
            error=(i == 0),  # first agent has an error
        )


# ---------------------------------------------------------------------------
# _build_status_response — daemon side
# ---------------------------------------------------------------------------

class TestBuildStatusResponseConsciousness:
    """Verify _build_status_response includes consciousness metrics."""

    def test_includes_consciousness_keys(self) -> None:
        """Response contains consciousness dict with expected phi/FEP fields."""
        swarm = _make_mock_swarm(["a1", "a2", "a3"])
        collector = get_metrics_collector()
        _populate_collector_with_agents(collector, ["a1", "a2", "a3"])

        resp = _build_status_response(swarm)

        assert "consciousness" in resp
        c = resp["consciousness"]
        for key in (
            "phi_avg",
            "phi_max",
            "phi_min",
            "integration_level",
            "differentiation_level",
            "free_energy_avg",
            "free_energy_variance",
            "agent_phi_scores",
            "agent_fep_scores",
        ):
            assert key in c, f"Missing key: {key}"

    def test_phi_values_are_not_static_half(self) -> None:
        """phi_avg is not the old placeholder 0.5 when agents have activity."""
        swarm = _make_mock_swarm(["a1", "a2", "a3"])
        collector = get_metrics_collector()
        _populate_collector_with_agents(collector, ["a1", "a2", "a3"])

        resp = _build_status_response(swarm)
        phi_avg = resp["consciousness"]["phi_avg"]

        # With real agents, phi_avg should not be a static 0.5 placeholder.
        # The exact value depends on activity — just verify it's computed,
        # not exactly 0.5.
        assert phi_avg != 0.5, f"phi_avg is static 0.5 placeholder: {phi_avg}"

    def test_top_5_agent_phi_scores(self) -> None:
        """agent_phi_scores in response is limited to top-5."""
        many_agents = [f"agent-{i:02d}" for i in range(12)]
        swarm = _make_mock_swarm(many_agents)
        collector = get_metrics_collector()
        _populate_collector_with_agents(collector, many_agents)

        resp = _build_status_response(swarm)
        top_phi = resp["consciousness"]["agent_phi_scores"]

        assert len(top_phi) <= 5

    def test_collection_failure_returns_empty_consciousness(self) -> None:
        """When collect_consciousness_metrics raises, consciousness is empty dict."""
        swarm = _make_mock_swarm(["a1"])

        with patch.object(
            get_metrics_collector(),
            "collect_consciousness_metrics",
            side_effect=RuntimeError("simulated failure"),
        ):
            resp = _build_status_response(swarm)

        assert resp["consciousness"] == {}

    def test_none_swarm_returns_error_no_crash(self) -> None:
        """None swarm should not crash — returns error dict."""
        resp = _build_status_response(None)
        assert "error" in resp
        assert resp["agents"] == []

    def test_no_supervisor_returns_error_no_crash(self) -> None:
        """Swarm with None supervisor returns error dict."""
        swarm = MagicMock()
        swarm.supervisor = None
        resp = _build_status_response(swarm)
        assert "error" in resp


# ---------------------------------------------------------------------------
# Status JSON output — daemon path
# ---------------------------------------------------------------------------

class TestStatusJsonDaemonPath:
    """Verify CLI --json includes consciousness from daemon response."""

    def test_json_includes_consciousness_from_daemon(self) -> None:
        """When daemon returns consciousness, JSON output includes it."""
        from heretek_swarm.cli.status import _display_daemon_status

        agent_data = {
            "agents": [
                {
                    "agent_id": "a1",
                    "state": "active",
                    "mailbox_size": 5,
                    "message_count": 10,
                    "last_activity": "",
                    "error_count": 0,
                }
            ],
            "consciousness": {
                "phi_avg": 0.72,
                "phi_max": 0.9,
                "phi_min": 0.5,
                "integration_level": 0.75,
                "differentiation_level": 0.5,
                "free_energy_avg": 0.3,
                "free_energy_variance": 0.02,
                "agent_phi_scores": {"a1": 0.72},
                "agent_fep_scores": {"a1": 0.8},
            },
        }

        with patch("click.echo") as mock_echo:
            _display_daemon_status(agent_data, pid=12345, output_json=True)

        output = mock_echo.call_args[0][0]
        parsed = json_mod.loads(output)

        assert "consciousness" in parsed
        assert parsed["consciousness"]["phi_avg"] == 0.72
        assert parsed["daemon_pid"] == 12345

    def test_json_no_consciousness_when_daemon_has_none(self) -> None:
        """When daemon response has no consciousness key, JSON omits it."""
        from heretek_swarm.cli.status import _display_daemon_status

        agent_data = {
            "agents": [
                {
                    "agent_id": "a1",
                    "state": "active",
                    "mailbox_size": 5,
                    "message_count": 10,
                    "last_activity": "",
                    "error_count": 0,
                }
            ]
            # No consciousness key
        }

        with patch("click.echo") as mock_echo:
            _display_daemon_status(agent_data, pid=12345, output_json=True)

        output = mock_echo.call_args[0][0]
        parsed = json_mod.loads(output)

        assert "consciousness" not in parsed


# ---------------------------------------------------------------------------
# Status human-readable output — daemon path
# ---------------------------------------------------------------------------

class TestStatusHumanReadableDaemonPath:
    """Verify human-readable output includes Consciousness Metrics section."""

    def test_human_readable_includes_consciousness_section(self) -> None:
        """When consciousness has positive phi_avg, Consciousness Metrics printed."""
        from heretek_swarm.cli.status import _display_daemon_status

        agent_data = {
            "agents": [
                {
                    "agent_id": "a1",
                    "state": "active",
                    "mailbox_size": 5,
                    "message_count": 10,
                    "last_activity": "",
                    "error_count": 0,
                }
            ],
            "consciousness": {
                "phi_avg": 0.72,
                "phi_max": 0.9,
                "phi_min": 0.5,
                "integration_level": 0.75,
                "differentiation_level": 0.5,
                "free_energy_avg": 0.3,
                "free_energy_variance": 0.02,
                "agent_phi_scores": {"a1": 0.72},
                "agent_fep_scores": {"a1": 0.8},
            },
        }

        with patch("click.echo") as mock_echo:
            _display_daemon_status(agent_data, pid=12345, output_json=False)

        # Collect all echo output
        all_output = "\n".join(str(call.args[0]) for call in mock_echo.call_args_list)

        assert "Consciousness Metrics:" in all_output
        assert "Phi (avg/max/min)" in all_output
        assert "Integration:" in all_output
        assert "Free Energy (avg)" in all_output

    def test_human_readable_skips_consciousness_when_zero(self) -> None:
        """When phi_avg is 0, no Consciousness Metrics section appears."""
        from heretek_swarm.cli.status import _display_daemon_status

        agent_data = {
            "agents": [
                {
                    "agent_id": "a1",
                    "state": "active",
                    "mailbox_size": 5,
                    "message_count": 10,
                    "last_activity": "",
                    "error_count": 0,
                }
            ],
            "consciousness": {
                "phi_avg": 0.0,
                "phi_max": 0.0,
                "phi_min": 0.0,
                "integration_level": 0.0,
                "differentiation_level": 0.0,
                "free_energy_avg": 0.0,
                "free_energy_variance": 0.0,
                "agent_phi_scores": {},
                "agent_fep_scores": {},
            },
        }

        with patch("click.echo") as mock_echo:
            _display_daemon_status(agent_data, pid=12345, output_json=False)

        all_output = "\n".join(
            str(call.args[0]) for call in mock_echo.call_args_list if call.args
        )
        assert "Consciousness Metrics:" not in all_output


# ---------------------------------------------------------------------------
# ConsciousnessMetricsData — structural validation
# ---------------------------------------------------------------------------

class TestConsciousnessMetricsData:
    """Verify ConsciousnessMetricsData serialization and invariants."""

    def test_to_dict_includes_all_fields(self) -> None:
        """to_dict() returns all expected keys."""
        data = ConsciousnessMetricsData(
            phi_avg=0.5,
            phi_max=0.8,
            phi_min=0.2,
            integration_level=0.75,
            differentiation_level=0.5,
            free_energy_avg=0.3,
            free_energy_variance=0.02,
            agent_phi_scores={"a": 0.5, "b": 0.8, "c": 0.2},
            agent_fep_scores={"a": 0.7, "b": 0.3},
        )
        d = data.to_dict()

        for key in (
            "phi_score",
            "phi_avg",
            "phi_max",
            "phi_min",
            "integration_level",
            "differentiation_level",
            "free_energy_avg",
            "free_energy_variance",
            "agent_phi_scores",
            "agent_fep_scores",
            "timestamp",
        ):
            assert key in d, f"Missing key: {key}"

    def test_default_values_are_zero(self) -> None:
        """Default ConsciousnessMetricsData has all-zero scores."""
        data = ConsciousnessMetricsData()
        assert data.phi_avg == 0.0
        assert data.phi_max == 0.0
        assert data.free_energy_avg == 0.0
        assert data.agent_phi_scores == {}


# ---------------------------------------------------------------------------
# collect_consciousness_metrics — empty agent guard
# ---------------------------------------------------------------------------

class TestCollectConsciousnessEmptyGuard:
    """Verify empty-agent edge case returns honest zeros, not placeholders."""

    def test_empty_agents_returns_zeros(self) -> None:
        """Fresh collector with no agents returns zeros, not static 0.5."""
        collector = SwarmMetricsCollector()
        result = collector.collect_consciousness_metrics()

        assert result.phi_avg == 0.0
        assert result.phi_max == 0.0
        assert result.phi_min == 0.0
        assert result.integration_level == 0.0
        assert result.differentiation_level == 0.0
        assert result.agent_phi_scores == {}
        assert result.agent_fep_scores == {}
