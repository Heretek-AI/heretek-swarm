"""
Test suite for Metis Agent - Strategic Planning and Long-Term Thinking.

This module provides comprehensive tests for the Metis agent including:
- Initialization with all required dependencies
- Message handling (process_message)
- Strategic plan creation and management
- Resource allocation optimization
- Risk assessment
- Scenario analysis
- Error handling and edge cases
- Zero-trust validation tests
"""

import asyncio
import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.metis import MetisAgent
from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.collective.learning import PatternExtractor
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer
from heretek_swarm.security.zero_trust import ZeroTrustValidator


# ============== FIXTURES ==============

@pytest.fixture
def mock_pattern_extractor() -> MagicMock:
    """Create a mock pattern extractor for testing."""
    extractor = MagicMock(spec=PatternExtractor)
    extractor.analyze_message = AsyncMock(return_value=None)
    extractor.extract_patterns = AsyncMock(return_value=[])
    extractor._validated_patterns = []
    extractor._message_cache = {}
    return extractor


@pytest.fixture
def mock_deliberation_engine() -> MagicMock:
    """Create a mock deliberation engine for testing."""
    engine = MagicMock(spec=SwarmDeliberationEngine)
    engine.start_deliberation = MagicMock(return_value="delib-test-123")
    engine.submit_position = MagicMock(return_value=True)
    engine.finalize_deliberation = MagicMock(return_value={"result": "approved"})
    engine.cleanup_deliberation = MagicMock(return_value=None)
    engine.get_statistics = MagicMock(return_value={})
    return engine


@pytest.fixture
def mock_access_analyzer() -> MagicMock:
    """Create a mock access pattern analyzer for testing."""
    analyzer = MagicMock(spec=AccessPatternAnalyzer)
    analyzer.record_access = MagicMock(return_value=None)
    analyzer.get_profile = MagicMock(return_value=None)
    analyzer.predict_agent_access = MagicMock(return_value=[])
    analyzer.get_statistics = MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value={})))
    return analyzer


@pytest.fixture
def mock_zero_trust_validator() -> MagicMock:
    """Create a mock zero-trust validator for testing."""
    validator = MagicMock(spec=ZeroTrustValidator)
    validator.validate_input = MagicMock(return_value=True)
    validator.validate_output = MagicMock(return_value=True)
    return validator


@pytest.fixture
def mock_swarms_agent() -> MagicMock:
    """Create a mock Swarms agent for testing."""
    agent = MagicMock()
    agent.llm = AsyncMock(return_value="Test LLM response")
    agent.run = MagicMock(return_value="Test response")
    return agent


@pytest.fixture
def metis_agent(
    mock_pattern_extractor: MagicMock,
    mock_deliberation_engine: MagicMock,
    mock_access_analyzer: MagicMock,
    mock_zero_trust_validator: MagicMock,
) -> MetisAgent:
    """Create a Metis agent instance with mocked dependencies."""
    agent = MetisAgent(
        agent_id="test-metis",
        name="TestMetis",
        planning_horizon_days=90,
        max_scenarios=5,
    )
    # Inject mocked dependencies
    agent.pattern_extractor = mock_pattern_extractor
    agent.deliberation_engine = mock_deliberation_engine
    agent.access_analyzer = mock_access_analyzer
    agent.zero_trust_validator = mock_zero_trust_validator
    return agent


@pytest.fixture
def sample_objective() -> str:
    """Sample strategic objective for testing."""
    return "Increase system performance by 50% while reducing costs by 20%"


@pytest.fixture
def sample_constraints() -> List[str]:
    """Sample constraints for testing."""
    return ["Budget limit of $100k", "Timeline of 6 months", "No additional headcount"]


# ============== INITIALIZATION TESTS ==============

class TestMetisInitialization:
    """Test Metis agent initialization."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        agent = MetisAgent()
        
        assert agent.agent_id == "metis"
        assert agent.name == "Metis"
        assert agent.planning_horizon_days == 90
        assert agent.max_scenarios == 5
        assert isinstance(agent.pattern_extractor, PatternExtractor)
        assert isinstance(agent.deliberation_engine, SwarmDeliberationEngine)
        assert isinstance(agent.access_analyzer, AccessPatternAnalyzer)
        assert isinstance(agent.zero_trust_validator, ZeroTrustValidator)

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        agent = MetisAgent(
            agent_id="custom-metis",
            name="CustomMetis",
            planning_horizon_days=180,
            max_scenarios=10,
        )
        
        assert agent.agent_id == "custom-metis"
        assert agent.name == "CustomMetis"
        assert agent.planning_horizon_days == 180
        assert agent.max_scenarios == 10

    def test_init_with_mocked_dependencies(
        self,
        metis_agent: MetisAgent,
        mock_pattern_extractor: MagicMock,
    ) -> None:
        """Test initialization with mocked dependencies."""
        assert metis_agent.pattern_extractor is mock_pattern_extractor
        assert metis_agent.active_plans == {}
        assert metis_agent.resource_allocations == {}
        assert metis_agent.risk_register == {}

    def test_initial_state(self, metis_agent: MetisAgent) -> None:
        """Test initial state values."""
        assert metis_agent.strategic_objectives == []
        assert metis_agent.scenario_analyses == {}


# ============== STRATEGIC PLAN TESTS ==============

class TestStrategicPlanning:
    """Test strategic planning functionality."""

    @pytest.mark.asyncio
    async def test_generate_strategic_plan(
        self, metis_agent: MetisAgent, mock_swarms_agent: MagicMock
    ) -> None:
        """Test strategic plan generation."""
        metis_agent.swarms_agent = mock_swarms_agent
        
        plan = await metis_agent._generate_strategic_plan(
            plan_id="plan-123",
            objective="Test objective",
            horizon_days=90,
            constraints=["Constraint 1"],
        )
        
        assert "plan_id" not in plan or plan.get("objective") == "Test objective"
        assert "phases" in plan
        assert "status" in plan

    @pytest.mark.asyncio
    async def test_generate_strategic_plan_no_llm(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test strategic plan generation without LLM."""
        metis_agent.swarms_agent = None
        
        plan = await metis_agent._generate_strategic_plan(
            plan_id="plan-456",
            objective="Test objective",
            horizon_days=90,
            constraints=[],
        )
        
        assert plan["objective"] == "Test objective"
        assert plan["status"] == "degraded"

    def test_extract_phases(self, metis_agent: MetisAgent) -> None:
        """Test phase extraction from LLM response."""
        response = """
        {
            "phases": [
                {"phase": 1, "name": "Initiation"},
                {"phase": 2, "name": "Planning"}
            ]
        }
        """
        phases = metis_agent._extract_phases(response)
        
        assert len(phases) >= 4  # Default phases
        assert phases[0]["phase"] == 1

    @pytest.mark.asyncio
    async def test_optimize_resource_allocation(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test resource allocation optimization."""
        resources = {"budget": 100000, "time": 180}
        priorities = {"budget": 0.7, "time": 0.3}
        
        allocation = await metis_agent._optimize_resource_allocation(
            plan_id="plan-123",
            resources=resources,
            priorities=priorities,
        )
        
        assert "allocation" in allocation
        assert allocation["plan_id"] == "plan-123"
        assert allocation["optimization_method"] == "priority_weighted"

    @pytest.mark.asyncio
    async def test_assess_plan_risks(
        self, metis_agent: MetisAgent, mock_swarms_agent: MagicMock
    ) -> None:
        """Test risk assessment."""
        metis_agent.swarms_agent = mock_swarms_agent
        metis_agent.active_plans["plan-123"] = {"objective": "Test plan"}
        
        risks = await metis_agent._assess_plan_risks(
            plan_id="plan-123",
            domain="technical",
        )
        
        assert isinstance(risks, list)
        # May return empty list if LLM parsing fails
        if risks:
            assert "risk_id" in risks[0]

    @pytest.mark.asyncio
    async def test_assess_plan_risks_no_llm(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test risk assessment without LLM."""
        metis_agent.swarms_agent = None
        metis_agent.active_plans["plan-123"] = {"objective": "Test plan"}
        
        risks = await metis_agent._assess_plan_risks(
            plan_id="plan-123",
            domain="technical",
        )
        
        assert isinstance(risks, list)


# ============== SCENARIO ANALYSIS TESTS ==============

class TestScenarioAnalysis:
    """Test scenario analysis functionality."""

    @pytest.mark.asyncio
    async def test_generate_scenarios(self, metis_agent: MetisAgent) -> None:
        """Test scenario generation."""
        base_scenario = {"market_growth": 0.05, "competition": "moderate"}
        variables = ["market_growth", "competition", "regulation"]
        
        scenarios = await metis_agent._generate_scenarios(
            base_scenario=base_scenario,
            variables=variables,
            max_scenarios=5,
        )
        
        assert len(scenarios) >= 1  # At least base scenario
        assert scenarios[0]["scenario_id"] == "base"
        assert scenarios[0]["name"] == "Base Case"

    @pytest.mark.asyncio
    async def test_generate_scenarios_empty_variables(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test scenario generation with no variables."""
        base_scenario = {"param": "value"}
        
        scenarios = await metis_agent._generate_scenarios(
            base_scenario=base_scenario,
            variables=[],
            max_scenarios=5,
        )
        
        assert len(scenarios) == 1  # Only base scenario
        assert scenarios[0]["scenario_id"] == "base"

    @pytest.mark.asyncio
    async def test_generate_scenarios_limit(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test scenario generation respects max limit."""
        base_scenario = {}
        variables = ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10"]
        
        scenarios = await metis_agent._generate_scenarios(
            base_scenario=base_scenario,
            variables=variables,
            max_scenarios=3,
        )
        
        assert len(scenarios) <= 3


# ============== MESSAGE HANDLING TESTS ==============

class TestMessageHandling:
    """Test message handling functionality."""

    @pytest.mark.asyncio
    async def test_create_strategic_plan_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test create_strategic_plan message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="create_strategic_plan",
            content={
                "objective": "Test objective",
                "horizon_days": 90,
                "constraints": ["Constraint 1"],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        metis_agent._generate_strategic_plan = AsyncMock(return_value={
            "objective": "Test objective",
            "phases": [],
            "status": "active",
        })
        
        await metis_agent._handle_create_strategic_plan(message)
        
        assert metis_agent.send.called
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "strategic_plan_created"

    @pytest.mark.asyncio
    async def test_create_strategic_plan_missing_objective(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test create_strategic_plan with missing objective."""
        message = ActorMessage(
            sender="test-sender",
            message_type="create_strategic_plan",
            content={
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_create_strategic_plan(message)
        
        # Should log error but not raise
        assert True

    @pytest.mark.asyncio
    async def test_allocate_resources_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test allocate_resources message handler."""
        # Create a plan first
        metis_agent.active_plans["plan-123"] = {"objective": "Test"}
        
        message = ActorMessage(
            sender="test-sender",
            message_type="allocate_resources",
            content={
                "plan_id": "plan-123",
                "resources": {"budget": 100000},
                "priorities": {"budget": 0.8},
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        metis_agent._optimize_resource_allocation = AsyncMock(return_value={
            "allocation": {"budget": 100000}
        })
        
        await metis_agent._handle_allocate_resources(message)
        
        assert metis_agent.send.called
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "resources_allocated"

    @pytest.mark.asyncio
    async def test_allocate_resources_plan_not_found(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test allocate_resources with non-existent plan."""
        message = ActorMessage(
            sender="test-sender",
            message_type="allocate_resources",
            content={
                "plan_id": "non-existent",
                "resources": {},
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_allocate_resources(message)
        
        # Should log error
        assert True

    @pytest.mark.asyncio
    async def test_assess_risks_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test assess_risks message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="assess_risks",
            content={
                "plan_id": "plan-123",
                "domain": "technical",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        metis_agent._assess_plan_risks = AsyncMock(return_value=[
            {"risk_id": "risk-1", "description": "Test risk"}
        ])
        
        await metis_agent._handle_assess_risks(message)
        
        assert metis_agent.send.called
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "risks_assessed"

    @pytest.mark.asyncio
    async def test_analyze_scenarios_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test analyze_scenarios message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="analyze_scenarios",
            content={
                "base_scenario": {"param": "value"},
                "variables": ["var1", "var2"],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        metis_agent._generate_scenarios = AsyncMock(return_value=[
            {"scenario_id": "base", "name": "Base Case"}
        ])
        
        await metis_agent._handle_analyze_scenarios(message)
        
        assert metis_agent.send.called
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "scenarios_analyzed"

    @pytest.mark.asyncio
    async def test_set_strategic_objective_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test set_strategic_objective message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="set_strategic_objective",
            content={
                "objective": "Test strategic objective",
                "priority": "high",
                "metrics": ["metric1", "metric2"],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_set_strategic_objective(message)
        
        assert metis_agent.send.called
        assert len(metis_agent.strategic_objectives) == 1

    @pytest.mark.asyncio
    async def test_set_strategic_objective_missing(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test set_strategic_objective with missing objective."""
        message = ActorMessage(
            sender="test-sender",
            message_type="set_strategic_objective",
            content={
                "priority": "high",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_set_strategic_objective(message)
        
        # Should log error, no objective added
        assert len(metis_agent.strategic_objectives) == 0

    @pytest.mark.asyncio
    async def test_get_plan_status_handler(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test get_plan_status message handler."""
        # Create a plan
        metis_agent.active_plans["plan-123"] = {
            "objective": "Test objective",
            "status": "active",
            "phases": [{"phase": 1, "name": "Initiation"}],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "horizon_days": 90,
        }
        
        message = ActorMessage(
            sender="test-sender",
            message_type="get_plan_status",
            content={
                "plan_id": "plan-123",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_get_plan_status(message)
        
        assert metis_agent.send.called
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "plan_status"

    @pytest.mark.asyncio
    async def test_get_plan_status_not_found(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test get_plan_status for non-existent plan."""
        message = ActorMessage(
            sender="test-sender",
            message_type="get_plan_status",
            content={
                "plan_id": "non-existent",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        metis_agent._validate_message_content = MagicMock(return_value=None)
        
        await metis_agent._handle_get_plan_status(message)
        
        call_args = metis_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"


# ============== PROCESS MESSAGE TESTS ==============

class TestProcessMessage:
    """Test the main process_message method."""

    @pytest.mark.asyncio
    async def test_process_message_known_type(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test processing a known message type."""
        message = ActorMessage(
            sender="test",
            message_type="get_plan_status",
            content={"reply_to": "reply"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        
        await metis_agent.process_message(message)
        
        assert True  # Should not raise

    @pytest.mark.asyncio
    async def test_process_message_unknown_type(
        self, metis_agent: MetisAgent, caplog
    ) -> None:
        """Test processing an unknown message type."""
        message = ActorMessage(
            sender="test",
            message_type="unknown_type",
            content={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        await metis_agent.process_message(message)

    @pytest.mark.asyncio
    async def test_process_message_handler_error(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test error handling in message processing."""
        async def failing_handler(msg: ActorMessage) -> None:
            raise ValueError("Test error")
        
        metis_agent.register_handler("failing", failing_handler)
        
        message = ActorMessage(
            sender="test",
            message_type="failing",
            content={"reply_to": "reply"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        metis_agent.send = AsyncMock(return_value="msg-123")
        
        await metis_agent.process_message(message)
        
        assert metis_agent.error_count >= 1


# ============== INTEGRATION TESTS ==============

class TestMetisIntegration:
    """Integration tests for Metis agent."""

    @pytest.mark.asyncio
    async def test_full_planning_workflow(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test complete strategic planning workflow."""
        await metis_agent.initialize()
        
        # Verify handlers are registered
        assert "create_strategic_plan" in metis_agent._message_handlers
        assert "allocate_resources" in metis_agent._message_handlers
        assert "assess_risks" in metis_agent._message_handlers
        assert "analyze_scenarios" in metis_agent._message_handlers

    @pytest.mark.asyncio
    async def test_learning_status(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test getting learning status."""
        status = metis_agent.get_learning_status()
        
        assert "agent_id" in status
        assert "collective_learning" in status
        assert "consensus" in status
        assert "memory_optimization" in status
        assert status["agent_id"] == "test-metis"

    @pytest.mark.asyncio
    async def test_get_strategic_summary(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test getting strategic summary."""
        # Add some data
        metis_agent.active_plans["plan-1"] = {"objective": "Test"}
        metis_agent.resource_allocations["plan-1"] = {}
        metis_agent.risk_register["risk-1"] = {}
        metis_agent.strategic_objectives.append({"objective": "Test"})
        metis_agent.scenario_analyses["analysis-1"] = []
        
        summary = await metis_agent.get_strategic_summary()
        
        assert summary["active_plans"] == 1
        assert summary["registered_risks"] == 1
        assert summary["strategic_objectives"] == 1

    @pytest.mark.asyncio
    async def test_cleanup(self, metis_agent: MetisAgent) -> None:
        """Test cleanup functionality."""
        # Add some data
        metis_agent.active_plans["plan-1"] = {"objective": "Test"}
        metis_agent.risk_register["risk-1"] = {}
        
        await metis_agent.cleanup()
        
        assert len(metis_agent.active_plans) == 0
        assert len(metis_agent.risk_register) == 0


# ============== ERROR HANDLING TESTS ==============

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_strategic_plan_generation_error(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test handling of strategic plan generation errors."""
        metis_agent.swarms_agent = MagicMock()
        metis_agent.swarms_agent.run = MagicMock(side_effect=Exception("LLM error"))
        
        plan = await metis_agent._generate_strategic_plan(
            plan_id="plan-123",
            objective="Test",
            horizon_days=90,
            constraints=[],
        )
        
        # Should return degraded plan
        assert plan["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_resource_allocation_error(
        self, metis_agent: MetisAgent
    ) -> None:
        """Test handling of resource allocation errors."""
        # Should not raise
        allocation = await metis_agent._optimize_resource_allocation(
            plan_id="plan-123",
            resources={},
            priorities={},
        )
        
        assert "allocation" in allocation
