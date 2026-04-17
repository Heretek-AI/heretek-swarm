"""
Behavioral equivalence tests for triad.py agents.

These tests verify that each of the four triad agents (Steward, Alpha, Beta, Charlie)
from heretek_swarm.actors.triad:
1. Instantiate with default and custom arguments
2. Have the required state attributes
3. Register handlers in initialize()
4. _perform_analysis returns expected dict keys

These tests serve as the regression guard for the T02 refactoring that extracts
a shared TriadAgent base class.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.triad import (
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    StewardAgent,
)

# ============================================================================
# Fixtures
# ============================================================================


class MockEventMesh:
    """In-memory mock event mesh."""

    def __init__(self):
        self.published: list[tuple[str, dict]] = []

    async def publish(self, subject: str, data: dict):
        self.published.append((subject, data))
        return True

    async def send_to_json(self, subject: str, data: dict):
        self.published.append((subject, data))

    async def connect(self):
        pass

    async def disconnect(self):
        pass


@pytest.fixture
def mock_mesh():
    return MockEventMesh()


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.run = AsyncMock(return_value="Mock LLM response")
    return llm


def _make_agent(cls, agent_id, mesh, llm, **kwargs):
    """Create an agent with mocked stubs."""
    with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mesh):
        with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=llm):
            return cls(agent_id=agent_id, **kwargs)


# ============================================================================
# StewardAgent Tests
# ============================================================================


class TestStewardAgentInstantiation:
    """Test StewardAgent initialization with default and custom args."""

    def test_default_instantiation(self, mock_mesh, mock_llm):
        """StewardAgent instantiates with defaults."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert agent.agent_id == "steward"
        assert agent.name == "Steward"
        assert agent.state == ActorState.SPAWNING

    def test_custom_args(self, mock_mesh, mock_llm):
        """StewardAgent accepts custom agent_id, name, description."""
        agent = _make_agent(
            StewardAgent,
            "my-steward",
            mock_mesh,
            mock_llm,
            name="My Steward",
            description="Custom description",
        )

        assert agent.agent_id == "my-steward"
        assert agent.name == "My Steward"
        assert agent.description == "Custom description"


class TestStewardAgentStateAttributes:
    """Test StewardAgent has required state attributes."""

    def test_active_deliberations(self, mock_mesh, mock_llm):
        """StewardAgent has active_deliberations dict."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert hasattr(agent, "active_deliberations")
        assert isinstance(agent.active_deliberations, dict)

    def test_deliberations_alias(self, mock_mesh, mock_llm):
        """StewardAgent._deliberations is alias for active_deliberations."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert hasattr(agent, "_deliberations")
        assert agent._deliberations is agent.active_deliberations

    def test_governance_policies(self, mock_mesh, mock_llm):
        """StewardAgent has governance_policies dict."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert hasattr(agent, "governance_policies")
        assert isinstance(agent.governance_policies, dict)

    def test_policies_alias(self, mock_mesh, mock_llm):
        """StewardAgent._policies is alias for governance_policies."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert hasattr(agent, "_policies")
        assert agent._policies is agent.governance_policies

    def test_resource_allocations(self, mock_mesh, mock_llm):
        """StewardAgent has resource_allocations dict."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        assert hasattr(agent, "resource_allocations")
        assert isinstance(agent.resource_allocations, dict)


class TestStewardAgentHandlerRegistration:
    """Test StewardAgent registers handlers in initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(self, mock_mesh, mock_llm):
        """StewardAgent.initialize() registers message handlers."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)
        await agent.initialize()

        # Verify handlers are registered
        assert "start_deliberation" in agent._message_handlers
        assert "request_decision" in agent._message_handlers
        assert "report_status" in agent._message_handlers
        assert "policy_update" in agent._message_handlers


class TestStewardAgentPublicAPIs:
    """Test StewardAgent public API methods."""

    @pytest.mark.asyncio
    async def test_coordinate_triad_returns_deliberation_id(self, mock_mesh, mock_llm):
        """StewardAgent.coordinate_triad() returns deliberation record."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        result = await agent.coordinate_triad(
            topic="Test topic",
            triad_members=["alpha", "beta", "charlie"],
        )

        assert isinstance(result, dict)
        assert "session_id" in result
        assert "topic" in result
        assert "phase" in result

    def test_get_deliberation_status(self, mock_mesh, mock_llm):
        """StewardAgent.get_deliberation_status() returns status dict."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        # Add a deliberation
        agent.active_deliberations["del-001"] = {"topic": "test", "status": "active"}

        status = agent.get_deliberation_status("del-001")
        assert status is not None
        assert status["topic"] == "test"

    def test_get_deliberation_status_not_found(self, mock_mesh, mock_llm):
        """StewardAgent.get_deliberation_status() returns None for missing id."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        status = agent.get_deliberation_status("nonexistent")
        assert status is None

    def test_get_all_deliberation_statuses(self, mock_mesh, mock_llm):
        """StewardAgent.get_all_deliberation_statuses() returns all statuses."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        agent.active_deliberations["del-001"] = {"topic": "test1"}
        agent.active_deliberations["del-002"] = {"topic": "test2"}

        statuses = agent.get_all_deliberation_statuses()
        assert len(statuses) == 2
        assert "del-001" in statuses
        assert "del-002" in statuses

    def test_get_governance_policy(self, mock_mesh, mock_llm):
        """StewardAgent.get_governance_policy() returns policy dict."""
        agent = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)

        agent.governance_policies["policy-001"] = {"rule": "test"}

        policy = agent.get_governance_policy("policy-001")
        assert policy is not None
        assert policy["rule"] == "test"


# ============================================================================
# AlphaAgent Tests
# ============================================================================


class TestAlphaAgentInstantiation:
    """Test AlphaAgent initialization with default and custom args."""

    def test_default_instantiation(self, mock_mesh, mock_llm):
        """AlphaAgent instantiates with defaults."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        assert agent.agent_id == "alpha"
        assert agent.name == "Alpha"
        assert agent.state == ActorState.SPAWNING

    def test_custom_args(self, mock_mesh, mock_llm):
        """AlphaAgent accepts custom agent_id, name, description, analysis_depth."""
        agent = _make_agent(
            AlphaAgent,
            "my-alpha",
            mock_mesh,
            mock_llm,
            name="My Alpha",
            description="Primary analyst",
            analysis_depth="shallow",
        )

        assert agent.agent_id == "my-alpha"
        assert agent.name == "My Alpha"
        assert agent.analysis_depth == "shallow"


class TestAlphaAgentStateAttributes:
    """Test AlphaAgent has required state attributes."""

    def test_analysis_history(self, mock_mesh, mock_llm):
        """AlphaAgent has analysis_history list."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        assert hasattr(agent, "analysis_history")
        assert isinstance(agent.analysis_history, list)

    def test_decision_count(self, mock_mesh, mock_llm):
        """AlphaAgent has decision_count int."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        assert hasattr(agent, "decision_count")
        assert isinstance(agent.decision_count, int)

    def test_analysis_depth(self, mock_mesh, mock_llm):
        """AlphaAgent has analysis_depth attribute."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm, analysis_depth="deep")

        assert hasattr(agent, "analysis_depth")
        assert agent.analysis_depth == "deep"

    def test_max_history_size(self, mock_mesh, mock_llm):
        """AlphaAgent has max_history_size for memory protection."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000


class TestAlphaAgentHandlerRegistration:
    """Test AlphaAgent registers handlers in initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(self, mock_mesh, mock_llm):
        """AlphaAgent.initialize() registers message handlers."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        await agent.initialize()

        assert "deliberation_request" in agent._message_handlers
        assert "analysis_request" in agent._message_handlers
        assert "validation_request" in agent._message_handlers


class TestAlphaAgentPerformAnalysis:
    """Test AlphaAgent._perform_analysis returns expected dict keys."""

    @pytest.mark.asyncio
    async def test_perform_analysis_returns_required_keys(self, mock_mesh, mock_llm):
        """AlphaAgent._perform_analysis returns decision, confidence, reasoning, depth."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert isinstance(result, dict)
        assert "decision" in result, "Missing 'decision' key"
        assert "confidence" in result, "Missing 'confidence' key"
        assert "reasoning" in result, "Missing 'reasoning' key"
        assert "depth" in result, "Missing 'depth' key"

    @pytest.mark.asyncio
    async def test_perform_analysis_confidence_in_range(self, mock_mesh, mock_llm):
        """AlphaAgent._perform_analysis confidence is between 0 and 1."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert 0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_perform_analysis_depth_matches_config(self, mock_mesh, mock_llm):
        """AlphaAgent._perform_analysis depth matches analysis_depth config."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm, analysis_depth="shallow")

        result = await agent._perform_analysis("Test problem")

        assert result["depth"] == "shallow"


class TestAlphaAgentPublicAPIs:
    """Test AlphaAgent public API methods."""

    @pytest.mark.asyncio
    async def test_get_analysis_statistics(self, mock_mesh, mock_llm):
        """AlphaAgent.get_analysis_statistics() returns statistics dict."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)

        stats = agent.get_analysis_statistics()

        assert isinstance(stats, dict)
        assert "total_analyses" in stats
        assert "total_decisions" in stats
        assert "analysis_depth" in stats


# ============================================================================
# BetaAgent Tests
# ============================================================================


class TestBetaAgentInstantiation:
    """Test BetaAgent initialization with default and custom args."""

    def test_default_instantiation(self, mock_mesh, mock_llm):
        """BetaAgent instantiates with defaults."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert agent.agent_id == "beta"
        assert agent.name == "Beta"
        assert agent.state == ActorState.SPAWNING

    def test_custom_args(self, mock_mesh, mock_llm):
        """BetaAgent accepts custom agent_id, name, description, validation_strictness."""
        agent = _make_agent(
            BetaAgent,
            "my-beta",
            mock_mesh,
            mock_llm,
            name="My Beta",
            description="Secondary validator",
            validation_strictness=0.9,
        )

        assert agent.agent_id == "my-beta"
        assert agent.name == "My Beta"
        assert agent.validation_strictness == 0.9


class TestBetaAgentStateAttributes:
    """Test BetaAgent has required state attributes."""

    def test_validation_history(self, mock_mesh, mock_llm):
        """BetaAgent has validation_history list."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "validation_history")
        assert isinstance(agent.validation_history, list)

    def test_error_detections(self, mock_mesh, mock_llm):
        """BetaAgent has error_detections list."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "error_detections")
        assert isinstance(agent.error_detections, list)

    def test_validation_strictness(self, mock_mesh, mock_llm):
        """BetaAgent has validation_strictness attribute."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm, validation_strictness=0.95)

        assert hasattr(agent, "validation_strictness")
        assert agent.validation_strictness == 0.95

    def test_validations_dict(self, mock_mesh, mock_llm):
        """BetaAgent has _validations dict for test-injectable state."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "_validations")
        assert isinstance(agent._validations, dict)

    def test_analyses_dict(self, mock_mesh, mock_llm):
        """BetaAgent has _analyses dict for test-injectable state."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "_analyses")
        assert isinstance(agent._analyses, dict)

    def test_error_checks_dict(self, mock_mesh, mock_llm):
        """BetaAgent has _error_checks dict for test-injectable state."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "_error_checks")
        assert isinstance(agent._error_checks, dict)

    def test_max_history_size(self, mock_mesh, mock_llm):
        """BetaAgent has max_history_size for memory protection."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000


class TestBetaAgentHandlerRegistration:
    """Test BetaAgent registers handlers in initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(self, mock_mesh, mock_llm):
        """BetaAgent.initialize() registers message handlers."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        await agent.initialize()

        assert "deliberation_request" in agent._message_handlers
        assert "validation_request" in agent._message_handlers
        assert "error_check" in agent._message_handlers


class TestBetaAgentPerformAnalysis:
    """Test BetaAgent._perform_analysis returns expected dict keys."""

    @pytest.mark.asyncio
    async def test_perform_analysis_returns_required_keys(self, mock_mesh, mock_llm):
        """BetaAgent._perform_analysis returns decision, confidence, reasoning, perspective."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert isinstance(result, dict)
        assert "decision" in result, "Missing 'decision' key"
        assert "confidence" in result, "Missing 'confidence' key"
        assert "reasoning" in result, "Missing 'reasoning' key"
        assert "perspective" in result, "Missing 'perspective' key"

    @pytest.mark.asyncio
    async def test_perform_analysis_perspective_secondary(self, mock_mesh, mock_llm):
        """BetaAgent._perform_analysis perspective is 'secondary'."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert result["perspective"] == "secondary"


class TestBetaAgentPublicAPIs:
    """Test BetaAgent public API methods."""

    @pytest.mark.asyncio
    async def test_get_validation_statistics(self, mock_mesh, mock_llm):
        """BetaAgent.get_validation_statistics() returns statistics dict."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)

        stats = agent.get_validation_statistics()

        assert isinstance(stats, dict)
        assert "total_validations" in stats
        assert "total_error_checks" in stats
        assert "validation_strictness" in stats


# ============================================================================
# CharlieAgent Tests
# ============================================================================


class TestCharlieAgentInstantiation:
    """Test CharlieAgent initialization with default and custom args."""

    def test_default_instantiation(self, mock_mesh, mock_llm):
        """CharlieAgent instantiates with defaults."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert agent.agent_id == "charlie"
        assert agent.name == "Charlie"
        assert agent.state == ActorState.SPAWNING

    def test_custom_args(self, mock_mesh, mock_llm):
        """CharlieAgent accepts custom agent_id, name, description, challenge_intensity."""
        agent = _make_agent(
            CharlieAgent,
            "my-charlie",
            mock_mesh,
            mock_llm,
            name="My Charlie",
            description="Challenger agent",
            challenge_intensity="high",
        )

        assert agent.agent_id == "my-charlie"
        assert agent.name == "My Charlie"
        assert agent.challenge_intensity == "high"


class TestCharlieAgentStateAttributes:
    """Test CharlieAgent has required state attributes."""

    def test_challenges_raised(self, mock_mesh, mock_llm):
        """CharlieAgent has challenges_raised list."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert hasattr(agent, "challenges_raised")
        assert isinstance(agent.challenges_raised, list)

    def test_risk_assessments(self, mock_mesh, mock_llm):
        """CharlieAgent has risk_assessments list."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert hasattr(agent, "risk_assessments")
        assert isinstance(agent.risk_assessments, list)

    def test_challenge_intensity(self, mock_mesh, mock_llm):
        """CharlieAgent has challenge_intensity attribute."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm, challenge_intensity="low")

        assert hasattr(agent, "challenge_intensity")
        assert agent.challenge_intensity == "low"

    def test_challenges_dict(self, mock_mesh, mock_llm):
        """CharlieAgent has _challenges dict for test-injectable state."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert hasattr(agent, "_challenges")
        assert isinstance(agent._challenges, dict)

    def test_risk_assessments_dict(self, mock_mesh, mock_llm):
        """CharlieAgent has _risk_assessments dict for test-injectable state."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert hasattr(agent, "_risk_assessments")
        assert isinstance(agent._risk_assessments, dict)

    def test_max_history_size(self, mock_mesh, mock_llm):
        """CharlieAgent has max_history_size for memory protection."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000


class TestCharlieAgentHandlerRegistration:
    """Test CharlieAgent registers handlers in initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(self, mock_mesh, mock_llm):
        """CharlieAgent.initialize() registers message handlers."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)
        await agent.initialize()

        assert "deliberation_request" in agent._message_handlers
        assert "challenge_request" in agent._message_handlers
        assert "risk_assessment" in agent._message_handlers


class TestCharlieAgentPerformAnalysis:
    """Test CharlieAgent._perform_analysis returns expected dict keys."""

    @pytest.mark.asyncio
    async def test_perform_analysis_returns_required_keys(self, mock_mesh, mock_llm):
        """CharlieAgent._perform_analysis returns decision, confidence, reasoning, perspective, challenges."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert isinstance(result, dict)
        assert "decision" in result, "Missing 'decision' key"
        assert "confidence" in result, "Missing 'confidence' key"
        assert "reasoning" in result, "Missing 'reasoning' key"
        assert "perspective" in result, "Missing 'perspective' key"
        assert "challenges" in result, "Missing 'challenges' key"

    @pytest.mark.asyncio
    async def test_perform_analysis_perspective_challenger(self, mock_mesh, mock_llm):
        """CharlieAgent._perform_analysis perspective is 'challenger'."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert result["perspective"] == "challenger"

    @pytest.mark.asyncio
    async def test_perform_analysis_challenges_list(self, mock_mesh, mock_llm):
        """CharlieAgent._perform_analysis challenges is a list."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        result = await agent._perform_analysis("Test problem")

        assert isinstance(result["challenges"], list)


class TestCharlieAgentPublicAPIs:
    """Test CharlieAgent public API methods."""

    @pytest.mark.asyncio
    async def test_get_challenge_statistics(self, mock_mesh, mock_llm):
        """CharlieAgent.get_challenge_statistics() returns statistics dict."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        stats = agent.get_challenge_statistics()

        assert isinstance(stats, dict)
        assert "total_challenges" in stats
        assert "total_risk_assessments" in stats
        assert "challenge_intensity" in stats


# ============================================================================
# Cross-Agent Equivalence Tests
# ============================================================================


class TestAgentEquivalence:
    """Test that all triad agents share structural equivalence."""

    def test_all_agents_inherit_from_agent_actor(self, mock_mesh, mock_llm):
        """All four agents inherit from AgentActor base class."""
        from heretek_swarm.actors.base.core import AgentActor

        steward = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert isinstance(steward, AgentActor)
        assert isinstance(alpha, AgentActor)
        assert isinstance(beta, AgentActor)
        assert isinstance(charlie, AgentActor)

    def test_all_agents_have_async_initialize(self, mock_mesh, mock_llm):
        """All four agents have async initialize() method."""
        steward = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert callable(steward.initialize)
        assert callable(alpha.initialize)
        assert callable(beta.initialize)
        assert callable(charlie.initialize)

    def test_all_agents_have_process_message(self, mock_mesh, mock_llm):
        """All four agents have async process_message() method."""
        steward = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert callable(steward.process_message)
        assert callable(alpha.process_message)
        assert callable(beta.process_message)
        assert callable(charlie.process_message)

    def test_alpha_beta_charlie_have_perform_analysis(self, mock_mesh, mock_llm):
        """Alpha, Beta, and Charlie agents have async _perform_analysis() method.
        
        Note: StewardAgent does not have _perform_analysis as it coordinates
        rather than performing analysis directly.
        """
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert callable(alpha._perform_analysis)
        assert callable(beta._perform_analysis)
        assert callable(charlie._perform_analysis)

    def test_all_agents_support_max_history_size(self, mock_mesh, mock_llm):
        """All four agents have max_history_size for memory protection."""
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        # Steward doesn't have max_history_size (different state model)
        assert hasattr(alpha, "max_history_size")
        assert hasattr(beta, "max_history_size")
        assert hasattr(charlie, "max_history_size")

    def test_all_agents_handle_message_types(self, mock_mesh, mock_llm):
        """All four agents can handle messages with different message types."""
        from datetime import UTC, datetime

        steward = _make_agent(StewardAgent, "steward", mock_mesh, mock_llm)
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        # Each agent should be able to process a message without crashing
        msg = ActorMessage(
            sender="test",
            message_type="unknown_type",  # Will be logged as warning, not crash
            content={},
            timestamp=datetime.now(UTC).isoformat(),
        )

        # None should raise exceptions for unknown message types
        import asyncio

        async def test_process():
            await steward.process_message(msg)
            await alpha.process_message(msg)
            await beta.process_message(msg)
            await charlie.process_message(msg)

        asyncio.run(test_process())


class TestAgentHistorySizeLimit:
    """Test that agents have max_history_size for memory protection."""

    @pytest.mark.asyncio
    async def test_alpha_max_history_size_exists(self, mock_mesh, mock_llm):
        """AlphaAgent has max_history_size attribute for memory protection."""
        agent = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000

    @pytest.mark.asyncio
    async def test_beta_max_history_size_exists(self, mock_mesh, mock_llm):
        """BetaAgent has max_history_size attribute for memory protection."""
        agent = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000

    @pytest.mark.asyncio
    async def test_charlie_max_history_size_exists(self, mock_mesh, mock_llm):
        """CharlieAgent has max_history_size attribute for memory protection."""
        agent = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)
        assert hasattr(agent, "max_history_size")
        assert agent.max_history_size == 1000

    @pytest.mark.asyncio
    async def test_history_lists_initialized_empty(self, mock_mesh, mock_llm):
        """All agent history lists are initialized as empty lists."""
        alpha = _make_agent(AlphaAgent, "alpha", mock_mesh, mock_llm)
        beta = _make_agent(BetaAgent, "beta", mock_mesh, mock_llm)
        charlie = _make_agent(CharlieAgent, "charlie", mock_mesh, mock_llm)

        assert alpha.analysis_history == []
        assert beta.validation_history == []
        assert beta.error_detections == []
        assert charlie.challenges_raised == []
        assert charlie.risk_assessments == []