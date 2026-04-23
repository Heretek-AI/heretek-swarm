"""
Integration tests for consciousness event emission.

Tests:
(a) emit_consciousness_events publishes phi/fep/agency for all agents
(b) phi_update normalizes IIT phi to 0.0–1.0 range
(c) fep_update includes free_energy and surprise
(d) agency_update includes agency_score and autonomy_score
(e) emit skips agents without metrics gracefully
(f) autonomous_runtime consciousness_metrics_loop calls emit_consciousness_events
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.plugins.consciousness_enhanced import (
    EnhancedConsciousnessPlugin,
)


class TestEmitConsciousnessEvents:
    """Tests (a)–(e): plugin-level emit behavior."""

    @pytest.fixture
    async def plugin_with_two_agents(self):
        """Create plugin with 2 synthetic agents in agent_metrics."""
        plugin = EnhancedConsciousnessPlugin()
        await plugin.initialize()

        # Add metrics for 2 agents
        for i in range(2):
            plugin.calculate_consciousness_metrics(
                agent_id=f"agent_{i}",
                gwt_score=0.7 + i * 0.1,
                ast_competence=0.6 + i * 0.1,
            )

        yield plugin
        await plugin.shutdown()

    # -------------------------------------------------------------------------
    # (a) test_emit_consciousness_events_publishes_phi_fep_agency
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_emit_consciousness_events_publishes_phi_fep_agency(
        self, plugin_with_two_agents
    ):
        """
        Verify emit_consciousness_events calls publish_to_nats exactly
        3 * num_agents times (phi_update, fep_update, agency_update per agent).
        """
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_two_agents.emit_consciousness_events(mock_publisher)

        # 2 agents × 3 event types = 6 publishes
        assert mock_publisher.publish_to_nats.call_count == 6

        # All calls target the correct topic
        for call in mock_publisher.publish_to_nats.call_args_list:
            assert call[0][0] == "swarm.metrics.consciousness"

    # -------------------------------------------------------------------------
    # (b) test_phi_update_normalizes_iit_phi
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_phi_update_normalizes_iit_phi(self, plugin_with_two_agents):
        """
        Verify phi_score in phi_update events falls in the 0.0–1.0 range.

        The emit method normalizes IIT phi by dividing by max_agents count.
        """
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_two_agents.emit_consciousness_events(mock_publisher)

        phi_calls = [
            call
            for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "phi_update"
        ]

        assert len(phi_calls) == 2  # One per agent
        for call in phi_calls:
            event = call[0][1]
            assert "phi_score" in event
            assert 0.0 <= event["phi_score"] <= 1.0, (
                f"phi_score {event['phi_score']} outside [0,1]"
            )

    # -------------------------------------------------------------------------
    # (c) test_fep_update_includes_free_energy_and_surprise
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_fep_update_includes_free_energy_and_surprise(
        self, plugin_with_two_agents
    ):
        """
        Verify fep_update events contain free_energy and surprise fields.
        """
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_two_agents.emit_consciousness_events(mock_publisher)

        fep_calls = [
            call
            for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "fep_update"
        ]

        assert len(fep_calls) == 2  # One per agent
        for call in fep_calls:
            event = call[0][1]
            assert "free_energy" in event, "fep_update missing free_energy"
            assert "surprise" in event, "fep_update missing surprise"
            assert 0.0 <= event["free_energy"] <= 1.0
            assert 0.0 <= event["surprise"] <= 1.0

    # -------------------------------------------------------------------------
    # (d) test_agency_update_includes_scores
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_agency_update_includes_scores(self, plugin_with_two_agents):
        """
        Verify agency_update events contain agency_score and autonomy_score.
        """
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_two_agents.emit_consciousness_events(mock_publisher)

        agency_calls = [
            call
            for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "agency_update"
        ]

        assert len(agency_calls) == 2  # One per agent
        for call in agency_calls:
            event = call[0][1]
            assert "agency_score" in event, "agency_update missing agency_score"
            assert "autonomy_score" in event, "agency_update missing autonomy_score"
            assert 0.0 <= event["agency_score"] <= 1.0
            assert 0.0 <= event["autonomy_score"] <= 1.0

    # -------------------------------------------------------------------------
    # (e) test_emit_skips_agents_without_metrics
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_emit_skips_agents_without_metrics(self):
        """
        Verify emit_consciousness_events skips agents that are not in
        agent_metrics gracefully (no KeyError, no publish calls).
        """
        plugin = EnhancedConsciousnessPlugin()
        await plugin.initialize()

        # No agents in agent_metrics — simulate a tracked list that includes
        # an agent without metrics
        plugin.agent_metrics = {}  # empty — no metrics at all

        mock_publisher = AsyncMock(return_value=True)
        await plugin.emit_consciousness_events(mock_publisher)

        # Should not call publish at all
        mock_publisher.publish_to_nats.assert_not_called()

        await plugin.shutdown()


class TestAutonomousRuntimeConsciousnessLoop:
    """
    Test (f): Integration test verifying AutonomousRuntime's
    _consciousness_metrics_loop calls emit_consciousness_events.
    """

    @pytest.mark.asyncio
    async def test_autonomous_runtime_consciousness_loop_calls_emit(self):
        """
        Mock the NATS publisher and verify the runtime's metrics loop
        calls emit_consciousness_events on the singleton plugin.
        """
        # Patch the consciousness plugin at import time so the runtime
        # uses our controlled instance
        mock_plugin_instance = MagicMock()
        mock_plugin_instance.get_statistics.return_value = {
            "total_agents": 0,
            "iit_average_phi": 0.0,
            "conscious_agents": 0,
        }
        mock_plugin_instance.emit_consciousness_events = AsyncMock()

        with patch(
            "heretek_swarm.plugins.consciousness_enhanced.EnhancedConsciousnessPlugin",
            return_value=mock_plugin_instance,
        ):
            from heretek_swarm.runtime.autonomous_runtime import AutonomousRuntime
            from heretek_swarm.runtime.autonomous_runtime_config import (
                AutonomousRuntimeConfig,
            )

            # Build minimal config with consciousness plugin enabled
            config = AutonomousRuntimeConfig(
                consciousness_plugin_enabled=True,
                consciousness_metrics_interval=1,  # 1s for fast test
            )
            runtime = AutonomousRuntime(config)

            # Wire a mock NATS publisher so _collect_consciousness_metrics can call emit
            runtime._nats_publisher = AsyncMock(return_value=True)
            runtime._consciousness_plugin = mock_plugin_instance

            # Run _collect_consciousness_metrics once
            await runtime._collect_consciousness_metrics()

            # Verify emit was called with the nats_publisher
            mock_plugin_instance.emit_consciousness_events.assert_called_once()
            call_args = mock_plugin_instance.emit_consciousness_events.call_args
            assert call_args[0][0] is runtime._nats_publisher
