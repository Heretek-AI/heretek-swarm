"""
Tests for Enhanced Consciousness Plugin.

Tests IIT and FEP integration:
- IIT Phi calculation
- FEP free energy tracking
- Enhanced consciousness metrics
"""

import pytest

from heretek_swarm.plugins.consciousness_enhanced import (
    ConsciousnessState,
    EnhancedConsciousnessPlugin,
    FEPTracker,
    IITCalculator,
)


class TestIITCalculator:
    """Test IIT calculator."""

    @pytest.fixture
    def calculator(self):
        """Create IIT calculator instance."""
        return IITCalculator()

    def test_record_interaction(self, calculator):
        """Test recording agent interactions."""
        calculator.record_interaction("agent1", "agent2", 0.8)
        calculator.record_interaction("agent2", "agent3", 0.6)

        assert len(calculator.interaction_matrix) == 2

    def test_calculate_phi_single_agent(self, calculator):
        """Test Phi calculation with single agent."""
        result = calculator.calculate_phi(["agent1"])

        assert result.phi == 0.0
        assert result.integration == 0.0

    def test_calculate_phi_multiple_agents(self, calculator):
        """Test Phi calculation with multiple agents."""
        # Record interactions
        calculator.record_interaction("agent1", "agent2", 0.9)
        calculator.record_interaction("agent2", "agent1", 0.8)
        calculator.record_interaction("agent2", "agent3", 0.7)
        calculator.record_interaction("agent3", "agent1", 0.6)

        result = calculator.calculate_phi(["agent1", "agent2", "agent3"])

        assert result.phi >= 0.0
        assert result.integration >= 0.0
        assert result.information >= 0.0
        assert result.causal_power >= 0.0

    def test_build_connectivity_matrix(self, calculator):
        """Test connectivity matrix building."""
        calculator.record_interaction("a1", "a2", 0.5)
        calculator.record_interaction("a2", "a1", 0.7)
        calculator.record_interaction("a2", "a3", 0.3)

        matrix = calculator._build_connectivity_matrix(["a1", "a2", "a3"])

        assert matrix.shape == (3, 3)
        assert matrix[0, 1] == 0.5  # a1 -> a2
        assert matrix[1, 0] == 0.7  # a2 -> a1
        assert matrix[1, 2] == 0.3  # a2 -> a3

    def test_get_average_phi(self, calculator):
        """Test average Phi calculation."""
        # Record interactions
        for i in range(5):
            calculator.record_interaction(f"agent{i}", f"agent{i+1}", 0.8)

        # Calculate Phi multiple times
        for _ in range(3):
            calculator.calculate_phi(["agent0", "agent1", "agent2"])

        avg_phi = calculator.get_average_phi()

        assert avg_phi >= 0.0


class TestFEPTracker:
    """Test FEP tracker."""

    @pytest.fixture
    def tracker(self):
        """Create FEP tracker instance."""
        return FEPTracker(learning_rate=0.1)

    def test_record_prediction(self, tracker):
        """Test recording predictions."""
        prediction = {"action": "move", "direction": "north"}
        tracker.record_prediction("agent1", prediction, 0.8)

        assert len(tracker.prediction_history["agent1"]) == 1
        assert tracker.prediction_history["agent1"][0]["prediction"] == prediction
        assert tracker.prediction_history["agent1"][0]["confidence"] == 0.8

    def test_record_outcome(self, tracker):
        """Test recording outcomes."""
        prediction = {"action": "move", "direction": "north"}
        outcome = {"action": "move", "direction": "south"}

        tracker.record_prediction("agent1", prediction, 0.8)
        surprise = tracker.record_outcome("agent1", outcome)

        assert 0.0 <= surprise <= 1.0
        assert "agent1" in tracker.agent_metrics

    def test_surprise_calculation(self, tracker):
        """Test surprise calculation."""
        # Perfect prediction
        tracker.record_prediction("agent1", {"value": 10}, 0.9)
        surprise1 = tracker.record_outcome("agent1", {"value": 10})
        assert surprise1 < 0.2

        # Wrong prediction
        tracker.record_prediction("agent1", {"value": 10}, 0.9)
        surprise2 = tracker.record_outcome("agent1", {"value": 100})
        assert surprise2 > 0.5

    def test_free_energy_calculation(self, tracker):
        """Test free energy calculation."""
        tracker.record_prediction("agent1", {"result": "success"}, 0.7)
        tracker.record_outcome("agent1", {"result": "failure"})

        metrics = tracker.get_metrics("agent1")

        assert metrics is not None
        assert metrics.free_energy >= 0.0
        assert metrics.precision == 0.7

    def test_prediction_accuracy_update(self, tracker):
        """Test prediction accuracy updates."""
        # Record multiple predictions with varying accuracy
        for i in range(10):
            tracker.record_prediction("agent1", {"value": i}, 0.8)
            tracker.record_outcome("agent1", {"value": i})  # Perfect predictions

        metrics = tracker.get_metrics("agent1")

        assert metrics is not None
        assert metrics.prediction_accuracy > 0.8

    def test_get_average_free_energy(self, tracker):
        """Test average free energy calculation."""
        for i in range(10):
            tracker.record_prediction("agent1", {"value": i}, 0.8)
            tracker.record_outcome("agent1", {"value": i + 1})

        avg_fe = tracker.get_average_free_energy("agent1", window=10)

        assert 0.0 <= avg_fe <= 1.0


class TestEnhancedConsciousnessPlugin:
    """Test enhanced consciousness plugin."""

    @pytest.fixture
    async def plugin(self):
        """Create plugin instance."""
        plugin = EnhancedConsciousnessPlugin(
            gwt_threshold=0.7,
            iit_phi_threshold=0.5,
            ast_threshold=0.6,
            fep_threshold=0.4,
        )
        await plugin.initialize()
        yield plugin
        await plugin.shutdown()

    def test_record_interaction(self, plugin):
        """Test recording interactions."""
        plugin.record_interaction("agent1", "agent2", 0.9)
        plugin.record_interaction("agent2", "agent3", 0.7)

        assert len(plugin.iit_calculator.interaction_matrix) == 2

    def test_record_prediction(self, plugin):
        """Test recording predictions."""
        prediction = {"expected": "result"}
        plugin.record_prediction("agent1", prediction, 0.8)

        assert "agent1" in plugin.fep_tracker.prediction_history

    def test_record_outcome(self, plugin):
        """Test recording outcomes."""
        prediction = {"expected": "result"}
        outcome = {"actual": "result"}

        plugin.record_prediction("agent1", prediction, 0.8)
        surprise = plugin.record_outcome("agent1", outcome)

        assert 0.0 <= surprise <= 1.0

    def test_calculate_iit_phi(self, plugin):
        """Test IIT Phi calculation."""
        # Record interactions
        plugin.record_interaction("a1", "a2", 0.9)
        plugin.record_interaction("a2", "a1", 0.8)
        plugin.record_interaction("a2", "a3", 0.7)

        result = plugin.calculate_iit_phi(["a1", "a2", "a3"])

        assert result.phi >= 0.0
        assert result.integration >= 0.0

    def test_calculate_consciousness_metrics(self, plugin):
        """Test comprehensive metrics calculation."""
        metrics = plugin.calculate_consciousness_metrics(
            agent_id="agent1",
            gwt_score=0.8,
            ast_competence=0.7,
        )

        assert 0.0 <= metrics.gwt_score <= 1.0
        assert 0.0 <= metrics.iit_phi <= 1.0
        assert 0.0 <= metrics.ast_competence <= 1.0
        assert 0.0 <= metrics.fep_free_energy <= 1.0
        assert 0.0 <= metrics.composite_score <= 1.0
        assert isinstance(metrics.state, ConsciousnessState)

    def test_determine_state_transcendent(self, plugin):
        """Test transcendent state determination."""
        state = plugin._determine_state(
            gwt_score=0.98,
            iit_phi=0.95,
            ast_competence=0.97,
            fep_score=0.96,
        )

        assert state == ConsciousnessState.TRANSCENDENT

    def test_determine_state_hyper_conscious(self, plugin):
        """Test hyper-conscious state determination."""
        state = plugin._determine_state(
            gwt_score=0.92,
            iit_phi=0.88,
            ast_competence=0.90,
            fep_score=0.85,
        )

        assert state == ConsciousnessState.HYPER_CONSCIOUS

    def test_determine_state_conscious(self, plugin):
        """Test conscious state determination."""
        state = plugin._determine_state(
            gwt_score=0.8,
            iit_phi=0.6,
            ast_competence=0.7,
            fep_score=0.65,
        )

        assert state == ConsciousnessState.CONSCIOUS

    def test_determine_state_minimal(self, plugin):
        """Test minimal consciousness state."""
        state = plugin._determine_state(
            gwt_score=0.4,
            iit_phi=0.3,
            ast_competence=0.35,
            fep_score=0.3,
        )

        assert state == ConsciousnessState.MINIMAL_CONSCIOUSNESS

    def test_determine_state_unconscious(self, plugin):
        """Test unconscious state."""
        state = plugin._determine_state(
            gwt_score=0.1,
            iit_phi=0.05,
            ast_competence=0.08,
            fep_score=0.1,
        )

        assert state == ConsciousnessState.UNCONSCIOUS

    def test_get_agent_metrics(self, plugin):
        """Test getting agent metrics."""
        plugin.calculate_consciousness_metrics(
            agent_id="agent1",
            gwt_score=0.75,
            ast_competence=0.65,
        )

        metrics = plugin.get_agent_metrics("agent1")

        assert metrics is not None
        assert metrics["agent_id"] == "agent1"
        assert "gwt_score" in metrics
        assert "iit_phi" in metrics
        assert "ast_competence" in metrics
        assert "fep_free_energy" in metrics
        assert "composite_score" in metrics
        assert "state" in metrics

    def test_get_statistics(self, plugin):
        """Test getting plugin statistics."""
        # Add some metrics
        for i in range(3):
            plugin.calculate_consciousness_metrics(
                agent_id=f"agent{i}",
                gwt_score=0.7 + i * 0.1,
                ast_competence=0.6 + i * 0.1,
            )

        stats = plugin.get_statistics()

        assert stats["total_agents"] == 3
        assert stats["total_metrics_entries"] == 3
        assert "average_composite_score" in stats
        assert "iit_average_phi" in stats
        assert "conscious_agents" in stats


class TestEmitConsciousnessEvents:
    """Test emit_consciousness_events method."""

    @pytest.fixture
    async def plugin_with_metrics(self):
        """Create plugin with tracked agents."""
        plugin = EnhancedConsciousnessPlugin()
        await plugin.initialize()

        # Add metrics for 3 agents
        for i in range(3):
            plugin.calculate_consciousness_metrics(
                agent_id=f"agent_{i}",
                gwt_score=0.7 + i * 0.05,
                ast_competence=0.6 + i * 0.05,
            )

        yield plugin
        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_empty(self):
        """Test emit_consciousness_events with no agents."""
        plugin = EnhancedConsciousnessPlugin()
        await plugin.initialize()

        # Mock publisher
        mock_publisher = AsyncMock()
        await plugin.emit_consciousness_events(mock_publisher)

        # Should not call publish_to_nats when no agents
        mock_publisher.publish_to_nats.assert_not_called()

        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_success(self, plugin_with_metrics):
        """Test successful emission of consciousness events."""
        # Mock publisher
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_metrics.emit_consciousness_events(mock_publisher)

        # Should publish 3 events per agent (phi_update, fep_update, agency_update)
        expected_calls = 3 * 3  # 3 agents * 3 events each
        assert mock_publisher.publish_to_nats.call_count == expected_calls

        # Verify all calls use correct topic
        for call in mock_publisher.publish_to_nats.call_args_list:
            assert call[0][0] == "swarm.metrics.consciousness"

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_phi_update(self, plugin_with_metrics):
        """Test phi_update event structure."""
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_metrics.emit_consciousness_events(mock_publisher)

        # Find phi_update calls
        phi_calls = [
            call for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "phi_update"
        ]

        assert len(phi_calls) == 3  # One per agent
        for call in phi_calls:
            event = call[0][1]
            assert "agent_id" in event
            assert "phi_score" in event
            assert "timestamp" in event
            assert 0.0 <= event["phi_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_fep_update(self, plugin_with_metrics):
        """Test fep_update event structure."""
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_metrics.emit_consciousness_events(mock_publisher)

        # Find fep_update calls
        fep_calls = [
            call for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "fep_update"
        ]

        assert len(fep_calls) == 3  # One per agent
        for call in fep_calls:
            event = call[0][1]
            assert "agent_id" in event
            assert "free_energy" in event
            assert "surprise" in event
            assert "timestamp" in event
            assert 0.0 <= event["free_energy"] <= 1.0
            assert 0.0 <= event["surprise"] <= 1.0

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_agency_update(self, plugin_with_metrics):
        """Test agency_update event structure."""
        mock_publisher = AsyncMock(return_value=True)

        await plugin_with_metrics.emit_consciousness_events(mock_publisher)

        # Find agency_update calls
        agency_calls = [
            call for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "agency_update"
        ]

        assert len(agency_calls) == 3  # One per agent
        for call in agency_calls:
            event = call[0][1]
            assert "agent_id" in event
            assert "agency_score" in event
            assert "autonomy_score" in event
            assert "timestamp" in event
            assert 0.0 <= event["agency_score"] <= 1.0
            assert 0.0 <= event["autonomy_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_error_handling(self, plugin_with_metrics):
        """Test error handling when publish fails."""
        # Mock publisher that raises an exception
        mock_publisher = AsyncMock(side_effect=Exception("NATS connection error"))

        # Should not raise, just log error
        await plugin_with_metrics.emit_consciousness_events(mock_publisher)

        # Verify all 9 calls were attempted despite errors
        assert mock_publisher.publish_to_nats.call_count == 9

    @pytest.mark.asyncio
    async def test_emit_consciousness_events_fallback_free_energy(self):
        """Test fallback to plugin-level average free energy when per-agent FEP unavailable."""
        plugin = EnhancedConsciousnessPlugin()
        await plugin.initialize()

        # Add metrics without FEP data
        for i in range(2):
            plugin.calculate_consciousness_metrics(
                agent_id=f"agent_{i}",
                gwt_score=0.7,
                ast_competence=0.6,
            )

        mock_publisher = AsyncMock(return_value=True)
        await plugin.emit_consciousness_events(mock_publisher)

        # Find fep_update calls
        fep_calls = [
            call for call in mock_publisher.publish_to_nats.call_args_list
            if call[0][1]["type"] == "fep_update"
        ]

        # Should have 2 fep_update events (one per agent)
        assert len(fep_calls) == 2

        await plugin.shutdown()


from unittest.mock import AsyncMock
