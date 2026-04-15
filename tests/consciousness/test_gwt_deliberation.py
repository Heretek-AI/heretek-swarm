"""Tests for GWT Deliberation Integration."""

import pytest

from heretek_swarm.consciousness.gwt_deliberation import (
    DeliberationGWTIntegrator,
    GWTSalienceCalculator,
    GWTDeliberationMixin,
    integrate_gwt_with_agent,
)
from heretek_swarm.consciousness.gwt import (
    GWTConfig,
    GlobalWorkspaceBroadcast,
)


class TestGWTSalienceCalculator:
    """Test deliberation salience calculation."""

    def test_calculate_deliberation_salience_basic(self):
        """Test basic deliberation salience calculation."""
        from heretek_swarm.consensus.swarm_deliberation import (
            DeliberationResult,
            Position,
        )

        result = DeliberationResult(
            deliberation_id="test-123",
            proposal="Test proposal",
            final_position=Position.AGREE,
            consensus_score=0.75,
            participation_rate=0.8,
            rounds_completed=3,
            minority_report=["Agent3: disagree"],
            arguments_summary={"total_arguments": 5},
            decision_provenance={},
        )

        calculator = GWTSalienceCalculator()
        salience = calculator.calculate_deliberation_salience(result)

        assert "novelty" in salience
        assert "relevance" in salience
        assert "urgency" in salience
        assert "impact" in salience
        assert "confidence" in salience
        assert salience["confidence"] == 0.75

    def test_calculate_deliberation_salience_low_participation(self):
        """Test salience calculation with low participation."""
        from heretek_swarm.consensus.swarm_deliberation import (
            DeliberationResult,
            Position,
        )

        result = DeliberationResult(
            deliberation_id="test-456",
            proposal="Low participation test",
            final_position=Position.STRONG_AGREE,
            consensus_score=0.6,
            participation_rate=0.3,
            rounds_completed=1,
            minority_report=[],
            arguments_summary={},
            decision_provenance={},
        )

        calculator = GWTSalienceCalculator()
        salience = calculator.calculate_deliberation_salience(result)

        assert salience["novelty"] > 0.3
        assert salience["urgency"] > 0.3


class TestDeliberationGWTIntegrator:
    """Test deliberation GWT integrator."""

    def test_integrator_initialization(self):
        """Test integrator initialization."""
        integrator = DeliberationGWTIntegrator()
        assert integrator._gwt is not None
        assert integrator._auto_broadcast_enabled is True
        assert integrator._deliberation_callbacks == []

    def test_integrator_with_custom_config(self):
        """Test integrator with custom config."""
        config = GWTConfig(salience_threshold=0.5)
        integrator = DeliberationGWTIntegrator(config=config)
        assert integrator._gwt._config.salience_threshold == 0.5

    def test_enable_disable_auto_broadcast(self):
        """Test enabling and disabling auto broadcast."""
        integrator = DeliberationGWTIntegrator()
        integrator.disable_auto_broadcast()
        assert integrator._auto_broadcast_enabled is False
        integrator.enable_auto_broadcast()
        assert integrator._auto_broadcast_enabled is True

    def test_add_remove_callback(self):
        """Test adding and removing callbacks."""
        integrator = DeliberationGWTIntegrator()

        async def dummy_callback(content):
            pass

        integrator.add_deliberation_callback(dummy_callback)
        assert len(integrator._deliberation_callbacks) == 1

        integrator.remove_deliberation_callback(dummy_callback)
        assert len(integrator._deliberation_callbacks) == 0

    def test_gwt_broadcast_property(self):
        """Test gwt_broadcast property."""
        integrator = DeliberationGWTIntegrator()
        gwt = integrator.gwt_broadcast
        assert isinstance(gwt, GlobalWorkspaceBroadcast)


class MockAgent:
    """Mock agent for testing integration."""

    def __init__(self):
        self.agent_id = "test-agent"
        self.received_broadcasts = []
        self.received_deliberations = []

    async def receive_gwt_broadcast(self, content):
        self.received_broadcasts.append(content)

    async def receive_deliberation_broadcast(self, content):
        self.received_deliberations.append(content)


class TestIntegrateGWTWithAgent:
    """Test GWT integration with agents."""

    @pytest.mark.asyncio
    async def test_integrate_basic(self):
        """Test basic agent integration."""
        agent = MockAgent()
        gwt = GlobalWorkspaceBroadcast()

        subscriptions = await integrate_gwt_with_agent(
            agent=agent,
            gwt_broadcast=gwt,
            subscribe_to_deliberations=False,
            subscribe_to_broadcasts=False,
        )

        assert agent._gwt_broadcast == gwt
        assert subscriptions == {}

    @pytest.mark.asyncio
    async def test_integrate_with_subscriptions_no_client(self):
        """Test agent integration with subscriptions when no NATS client."""
        agent = MockAgent()
        gwt = GlobalWorkspaceBroadcast()

        subscriptions = await integrate_gwt_with_agent(
            agent=agent,
            gwt_broadcast=gwt,
            subscribe_to_deliberations=True,
            subscribe_to_broadcasts=True,
        )
        assert subscriptions == {}


class TestGWTDeliberationMixin:
    """Test GWT deliberation mixin."""

    def test_mixin_properties(self):
        """Test mixin has correct properties."""
        mixin = GWTDeliberationMixin()
        assert mixin._gwt_broadcast is None
        assert mixin._gwt_deliberation_integrator is None

    @pytest.mark.asyncio
    async def test_broadcast_via_gwt_not_configured(self):
        """Test broadcast when GWT not configured."""
        from heretek_swarm.consciousness.gwt_deliberation import GWTDeliberationMixin

        class TestAgent(GWTDeliberationMixin):
            def __init__(self):
                self.agent_id = "test-agent"

        agent = TestAgent()
        result = await agent._broadcast_via_gwt(
            content_type="test",
            payload={"key": "value"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_receive_gwt_broadcast(self):
        """Test receiving GWT broadcast."""
        agent = MockAgent()
        from heretek_swarm.consciousness.gwt import GWTContent, GWTSalienceMetrics

        salience = GWTSalienceMetrics(
            novelty=0.7,
            relevance=0.8,
            urgency=0.6,
            impact=0.75,
            confidence=0.85,
        )
        content = GWTContent(
            content_id="test-123",
            source_agent="other-agent",
            content_type="decision",
            payload={},
            salience_metrics=salience,
        )

        await agent.receive_gwt_broadcast(content)
        assert len(agent.received_broadcasts) == 1
        assert agent.received_broadcasts[0] == content

    @pytest.mark.asyncio
    async def test_receive_deliberation_broadcast(self):
        """Test receiving deliberation broadcast."""
        agent = MockAgent()
        from heretek_swarm.consciousness.gwt import GWTContent, GWTSalienceMetrics

        salience = GWTSalienceMetrics(
            novelty=0.7,
            relevance=0.8,
            urgency=0.6,
            impact=0.75,
            confidence=0.85,
        )
        content = GWTContent(
            content_id="test-456",
            source_agent="deliberation-engine",
            content_type="deliberation_outcome",
            payload={
                "deliberation_id": "delib-123",
                "proposal": "Test proposal",
            },
            salience_metrics=salience,
        )

        await agent.receive_deliberation_broadcast(content)
        assert len(agent.received_deliberations) == 1
        assert agent.received_deliberations[0].payload["deliberation_id"] == "delib-123"
