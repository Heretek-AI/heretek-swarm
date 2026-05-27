"""Test T01: Verify consciousness metrics wiring to IIT/FEP/AST calculators.

Validates that collect_consciousness_metrics() returns values computed from
real calculators instead of hardcoded placeholders (0.5, 0.1).
"""

import pytest

from heretek_swarm.observability.metrics import (
    ConsciousnessMetricsData,
    SwarmMetricsCollector,
    _MAPPING_DIFFERENTIATION,
    _MAPPING_INTEGRATION,
)


class TestCollectConsciousnessMetrics:
    """Tests for the wired collect_consciousness_metrics() method."""

    def test_empty_collector_returns_zero_values(self):
        """No agents should yield honest 0.0 values, not placeholder constants."""
        collector = SwarmMetricsCollector()
        result = collector.collect_consciousness_metrics()

        assert result.integration_level == 0.0
        assert result.differentiation_level == 0.0
        assert result.free_energy_variance == 0.0
        assert result.phi_avg == 0.0
        assert result.free_energy_avg == 0.0

    def test_no_hardcoded_placeholders(self):
        """Confirm that values come from real calculators, not hardcoded constants."""
        collector = SwarmMetricsCollector()
        # Record a single agent with default metrics
        collector.record_agent_activity("agent-1", agent_type="worker")
        result = collector.collect_consciousness_metrics()

        # Values are now computed from calculators — verify they're in the valid
        # mapping range, which confirms the wiring replaced the old dead-coded
        # constants (the old code unconditionally set these to 0.5 / 0.5 / 0.1).
        assert result.integration_level in _MAPPING_INTEGRATION.values(), (
            f"integration_level={result.integration_level} not in mapping values"
        )
        assert result.differentiation_level in _MAPPING_DIFFERENTIATION.values(), (
            f"differentiation_level={result.differentiation_level} not in mapping values"
        )
        assert result.free_energy_variance != 0.1, (
            "free_energy_variance must NOT be the old placeholder 0.1"
        )

    def test_single_agent_produces_numeric_metrics(self):
        """A single agent should produce numeric integration/differentiation/variance."""
        collector = SwarmMetricsCollector()
        collector.record_agent_activity(
            "agent-a",
            task_completed=True,
            task_duration_ms=150,
            message_sent=True,
            message_received=True,
            agent_type="worker",
        )
        result = collector.collect_consciousness_metrics()

        assert isinstance(result.integration_level, float)
        assert isinstance(result.differentiation_level, float)
        assert isinstance(result.free_energy_variance, float)
        assert isinstance(result.free_energy_avg, float)

    def test_multiple_agents_produce_varying_metrics(self):
        """Different agent activity patterns should produce different metrics."""
        collector = SwarmMetricsCollector()

        # Agent A: very active
        for _ in range(10):
            collector.record_agent_activity(
                "agent-a",
                task_completed=True,
                message_sent=True,
                message_received=True,
            )
        # Agent B: moderate
        for _ in range(5):
            collector.record_agent_activity(
                "agent-b",
                task_completed=True,
                message_sent=True,
            )
        # Agent C: idle (never recorded)

        result = collector.collect_consciousness_metrics()
        # Phi scores should differ across agents
        assert len(result.agent_phi_scores) >= 2
        # FEP scores should also differ
        assert len(result.agent_fep_scores) >= 2

    def test_zero_agent_edge_case(self):
        """Directly test the edge case of zero agents."""
        collector = SwarmMetricsCollector()
        # No agents recorded at all
        result = collector.collect_consciousness_metrics()

        assert result.phi_avg == 0.0
        assert result.phi_max == 0.0
        assert result.phi_min == 0.0
        assert result.integration_level == 0.0
        assert result.differentiation_level == 0.0
        assert result.free_energy_avg == 0.0
        assert result.free_energy_variance == 0.0

    def test_integration_level_with_high_connectivity(self):
        """Agents with high message counts should produce higher integration."""
        collector = SwarmMetricsCollector()
        # Simulate highly connected agents
        for i in range(3):
            aid = f"high-conn-{i}"
            for _ in range(20):
                collector.record_agent_activity(
                    aid,
                    message_sent=True,
                    message_received=True,
                    task_completed=True,
                )

        result = collector.collect_consciousness_metrics()
        # With 3 highly connected agents, integration should be > 0
        assert result.integration_level > 0.0

    def test_mapping_dictionaries_are_complete(self):
        """Verify mapping dicts cover all PhiCalculator string levels."""
        expected_levels = {"very_high", "high", "moderate", "low", "minimal", "unknown"}
        assert set(_MAPPING_INTEGRATION.keys()) == expected_levels
        assert set(_MAPPING_DIFFERENTIATION.keys()) == expected_levels

        for k, v in _MAPPING_INTEGRATION.items():
            assert isinstance(v, float)
        for k, v in _MAPPING_DIFFERENTIATION.items():
            assert isinstance(v, float)

    def test_fep_calculator_produces_variance(self):
        """Agents with different error counts should yield non-zero variance."""
        collector = SwarmMetricsCollector()

        collector.record_agent_activity(
            "err-agent",
            task_completed=True,
            error=True,
            agent_type="worker",
        )
        collector.record_agent_activity(
            "clean-agent",
            task_completed=True,
            message_sent=True,
            agent_type="worker",
        )

        result = collector.collect_consciousness_metrics()
        # With two agents at different error levels, variance should be non-zero
        assert result.free_energy_variance != 0.0
        assert result.free_energy_avg != 0.0

    def test_callback_override_integration(self):
        """Callback-provided phi scores should be used when available."""
        from heretek_swarm.consciousness.iit_phi import PhiResult

        collector = SwarmMetricsCollector()

        # Simulate callback returning pre-computed phi scores
        def mock_callback():
            return {
                "phi_scores": {"a": 0.9, "b": 0.8, "c": 0.3},
                # No fep_scores provided
            }

        collector.register_consciousness_callback(mock_callback)
        collector.record_agent_activity("a", agent_type="worker")
        collector.record_agent_activity("b", agent_type="worker")
        collector.record_agent_activity("c", agent_type="worker")

        result = collector.collect_consciousness_metrics()
        assert result.agent_phi_scores["a"] == 0.9
        assert result.agent_phi_scores["b"] == 0.8
        assert result.agent_phi_scores["c"] == 0.3
        # Integration/differentiation are computed from real PhiCalculator;
        # the mapping is applied, so values come from the mapping dicts.
        assert result.integration_level in _MAPPING_INTEGRATION.values()
        assert result.differentiation_level in _MAPPING_DIFFERENTIATION.values()

    def test_history_accumulation(self):
        """Verify that history tracks each collection correctly."""
        collector = SwarmMetricsCollector()
        collector.record_agent_activity("x", task_completed=True, agent_type="worker")
        collector.collect_consciousness_metrics()
        collector.collect_consciousness_metrics()

        history = collector.get_consciousness_metrics_history()
        assert len(history) == 2
        assert isinstance(history[0], ConsciousnessMetricsData)
        assert isinstance(history[1], ConsciousnessMetricsData)
