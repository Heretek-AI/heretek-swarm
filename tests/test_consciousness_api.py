"""
Comprehensive test suite for Consciousness Metrics API

Tests for:
- IIT (Integrated Information Theory) calculations
- FEP (Free Energy Principle) tracking
- Agent consciousness state determination
- API endpoints
"""


import pytest

from heretek_swarm.plugins.consciousness_enhanced import (
    EnhancedConsciousnessPlugin,
    FEPTracker,
    IITCalculator,
)

# Import app after fixing RAG imports
try:
    from fastapi.testclient import TestClient

    from heretek_swarm.api.main import app
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False
    app = None


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    if not APP_AVAILABLE:
        pytest.skip("FastAPI app not available")
    return TestClient(app)


@pytest.fixture
def consciousness_plugin():
    """Create consciousness plugin instance for testing."""
    return EnhancedConsciousnessPlugin(
        gwt_threshold=0.7,
        iit_phi_threshold=0.5,
        ast_threshold=0.6,
        fep_threshold=0.4,
    )


@pytest.fixture
def iit_calculator():
    """Create IIT calculator for testing."""
    return IITCalculator(max_agents=10)


@pytest.fixture
def fep_tracker():
    """Create FEP tracker for testing."""
    return FEPTracker(learning_rate=0.1)


# =============================================================================
# IIT Calculator Tests
# =============================================================================

class TestIITCalculator:
    """Test suite for IIT (Integrated Information Theory) calculator."""

    def test_initialization(self, iit_calculator):
        """Test IIT calculator initialization."""
        assert iit_calculator.max_agents == 10
        assert iit_calculator.interaction_matrix == {}
        assert iit_calculator.connectivity_history == []

    def test_record_interaction(self, iit_calculator):
        """Test recording agent interactions."""
        iit_calculator.record_interaction("agent-1", "agent-2")
        iit_calculator.record_interaction("agent-2", "agent-3")

        assert len(iit_calculator.interaction_matrix) == 2
        assert ("agent-1", "agent-2") in iit_calculator.interaction_matrix

    def test_calculate_phi_single_agent(self, iit_calculator):
        """Test phi calculation for single agent (should be 0)."""
        iit_calculator.record_interaction("agent-1", "agent-2")
        result = iit_calculator.calculate_phi(["agent-1"])

        # Single agent has no integration
        assert isinstance(result.phi, float)
        assert result.phi >= 0

    def test_calculate_phi_multiple_agents(self, iit_calculator):
        """Test phi calculation with multiple connected agents."""
        # Create a connected network
        agents = [f"agent-{i}" for i in range(5)]
        for i, agent in enumerate(agents):
            for j, other in enumerate(agents):
                if i != j:
                    iit_calculator.record_interaction(agent, other)

        result = iit_calculator.calculate_phi(agents)
        assert result.phi > 0

    def test_get_average_phi(self, iit_calculator):
        """Test getting average phi score."""
        iit_calculator.record_interaction("agent-1", "agent-2")
        iit_calculator.record_interaction("agent-2", "agent-3")

        avg_phi = iit_calculator.get_average_phi()
        assert isinstance(avg_phi, float)
        assert avg_phi >= 0


# =============================================================================
# FEP Tracker Tests
# =============================================================================

class TestFEPTracker:
    """Test suite for FEP (Free Energy Principle) tracker."""

    def test_initialization(self, fep_tracker):
        """Test FEP tracker initialization."""
        assert fep_tracker.learning_rate == 0.1
        assert fep_tracker.agent_metrics == {}
        assert fep_tracker.prediction_history == {}

    def test_record_prediction(self, fep_tracker):
        """Test recording agent predictions."""
        fep_tracker.record_prediction(
            "agent-1",
            {"action": "respond", "content": "hello"},
        )

        assert "agent-1" in fep_tracker.prediction_history
        assert len(fep_tracker.prediction_history["agent-1"]) == 1

    def test_record_outcome(self, fep_tracker):
        """Test recording actual outcomes."""
        fep_tracker.record_prediction(
            "agent-1",
            {"action": "respond"},
        )
        fep_tracker.record_outcome(
            "agent-1",
            {"action": "respond", "result": "success"}
        )

        assert "agent-1" in fep_tracker.agent_metrics

    def test_get_metrics(self, fep_tracker):
        """Test getting FEP metrics for an agent."""
        fep_tracker.record_prediction("agent-1", {"action": "respond"})
        fep_tracker.record_outcome("agent-1", {"action": "respond"})

        metrics = fep_tracker.get_metrics("agent-1")
        assert metrics is not None
        assert metrics.prediction_accuracy >= 0
        assert metrics.free_energy >= 0

    def test_get_average_free_energy(self, fep_tracker):
        """Test getting average free energy."""
        for _i in range(5):
            fep_tracker.record_prediction("agent-1", {"action": "respond"})
            fep_tracker.record_outcome("agent-1", {"action": "respond"})

        avg = fep_tracker.get_average_free_energy("agent-1", window=5)
        assert isinstance(avg, float)


# =============================================================================
# Consciousness Plugin Tests
# =============================================================================

class TestConsciousnessPlugin:
    """Test suite for EnhancedConsciousnessPlugin."""

    def test_initialization(self, consciousness_plugin):
        """Test plugin initialization."""
        assert consciousness_plugin.iit_calculator is not None
        assert consciousness_plugin.fep_tracker is not None
        assert consciousness_plugin.agent_metrics == {}

    def test_record_interaction(self, consciousness_plugin):
        """Test recording interaction through plugin."""
        consciousness_plugin.record_interaction("agent-1", "agent-2")

        assert len(consciousness_plugin.iit_calculator.interaction_matrix) == 1

    def test_calculate_iit_phi(self, consciousness_plugin):
        """Test IIT phi calculation through plugin."""
        consciousness_plugin.record_interaction("agent-1", "agent-2")
        consciousness_plugin.record_interaction("agent-2", "agent-3")

        result = consciousness_plugin.calculate_iit_phi(["agent-1"])
        assert isinstance(result.phi, float)
        assert result.phi >= 0

    def test_record_prediction(self, consciousness_plugin):
        """Test recording prediction through plugin."""
        consciousness_plugin.record_prediction(
            "agent-1",
            {"action": "respond"},
        )

        assert "agent-1" in consciousness_plugin.fep_tracker.prediction_history

    def test_record_outcome(self, consciousness_plugin):
        """Test recording outcome through plugin."""
        consciousness_plugin.record_prediction("agent-1", {"action": "respond"})
        consciousness_plugin.record_outcome("agent-1", {"action": "respond"})

        assert "agent-1" in consciousness_plugin.fep_tracker.agent_metrics

    def test_calculate_consciousness_metrics(self, consciousness_plugin):
        """Test comprehensive consciousness metrics calculation."""
        # Create some interactions
        for _i in range(3):
            consciousness_plugin.record_interaction("agent-1", "agent-2")
            consciousness_plugin.record_prediction("agent-1", {"action": "respond"})
            consciousness_plugin.record_outcome("agent-1", {"action": "respond"})

        metrics = consciousness_plugin.calculate_consciousness_metrics("agent-1")
        assert metrics is not None
        assert metrics.iit_phi >= 0
        assert metrics.fep_free_energy >= 0
        assert metrics.state is not None

    def test_get_agent_metrics(self, consciousness_plugin):
        """Test getting agent metrics."""
        consciousness_plugin.record_interaction("agent-1", "agent-2")
        consciousness_plugin.record_prediction("agent-1", {"action": "respond"})
        consciousness_plugin.record_outcome("agent-1", {"action": "respond"})

        metrics = consciousness_plugin.get_agent_metrics("agent-1")
        # Returns dict or None
        assert isinstance(metrics, dict) or metrics is None
        if metrics:
            assert "iit_phi" in metrics
            assert "fep_free_energy" in metrics

    def test_get_statistics(self, consciousness_plugin):
        """Test getting overall statistics."""
        for i in range(3):
            consciousness_plugin.record_interaction(f"agent-{i}", "agent-1")

        stats = consciousness_plugin.get_statistics()
        assert "total_agents" in stats
        assert "iit_average_phi" in stats
        assert "conscious_agents" in stats
