"""
Integration tests for MetisAgent.

Tier 2 (Support) - MetisAgent handles strategic planning and resource allocation.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.heretek_swarm.actors.metis import MetisAgent
from src.heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestMetisAgentIntegration:
    """Integration tests for MetisAgent."""

    @pytest_asyncio.fixture
    async def metis_agent(self, mock_nats, mock_llm, mock_db):
        """Create MetisAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.metis.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                with patch('src.heretek_swarm.actors.metis.get_db_pool', return_value=mock_db):
                    agent = MetisAgent(agent_id="metis-test-001")
                    yield agent
                    if agent._state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_metis(self, metis_agent):
        """Create and spawn MetisAgent."""
        await metis_agent.spawn()
        yield metis_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, metis_agent):
        """Test agent spawning lifecycle."""
        assert metis_agent._state == ActorState.SPAWNING
        await metis_agent.spawn()
        assert metis_agent._state == ActorState.ACTIVE
        assert metis_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_metis):
        """Test agent termination lifecycle."""
        assert spawned_metis._state == ActorState.ACTIVE
        await spawned_metis.terminate()
        assert spawned_metis._state == ActorState.TERMINATED
        assert not spawned_metis.is_alive

    @pytest.mark.asyncio
    async def test_handle_create_strategic_plan(self, spawned_metis, mock_nats, mock_llm):
        """Test handling strategic plan creation."""
        # Setup mock LLM
        mock_llm.register_response(
            "strategic plan",
            "Strategic Plan: Phase 1 - Foundation, Phase 2 - Growth, Phase 3 - Scale."
        )

        # Create message
        message = ActorMessage(
            message_type="create_strategic_plan",
            content={
                "objective": "Achieve market leadership",
                "timeline": "12 months",
                "constraints": ["budget", "resources"],
            },
            sender="coordinator",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify plan created
        assert len(spawned_metis._plans) > 0

    @pytest.mark.asyncio
    async def test_handle_allocate_resources(self, spawned_metis, mock_llm):
        """Test handling resource allocation."""
        # Setup mock LLM
        mock_llm.register_response(
            "allocate",
            "Resource allocation: 40% engineering, 30% marketing, 30% operations."
        )

        # Create message
        message = ActorMessage(
            message_type="allocate_resources",
            content={
                "plan_id": "plan-001",
                "resources": {"budget": 1000000, "headcount": 50},
                "priorities": ["product", "growth"],
            },
            sender="coordinator",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify allocation tracked
        assert "plan-001" in spawned_metis._allocations

    @pytest.mark.asyncio
    async def test_handle_assess_risks(self, spawned_metis, mock_llm):
        """Test handling risk assessment."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: Market risk=medium, Technical risk=low, Financial risk=low."
        )

        # Create message
        message = ActorMessage(
            message_type="assess_risks",
            content={
                "plan_id": "plan-001",
                "scenario": "Market expansion",
            },
            sender="steward",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify risks assessed
        assert "plan-001" in spawned_metis._risk_assessments

    @pytest.mark.asyncio
    async def test_handle_analyze_scenarios(self, spawned_metis, mock_llm):
        """Test handling scenario analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "scenario",
            "Scenario analysis: Best case - 50% growth, Base case - 30% growth, Worst case - 10% growth."
        )

        # Create message
        message = ActorMessage(
            message_type="analyze_scenarios",
            content={
                "scenarios": ["optimistic", "baseline", "pessimistic"],
                "variables": ["market", "competition", "resources"],
            },
            sender="coordinator",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify scenarios analyzed
        stats = await spawned_metis.get_strategic_summary()
        assert stats["total_scenarios"] >= 1

    @pytest.mark.asyncio
    async def test_handle_set_strategic_objective(self, spawned_metis, mock_llm):
        """Test handling strategic objective setting."""
        # Setup mock LLM
        mock_llm.register_response(
            "objective",
            "Strategic objective defined with measurable KPIs and milestones."
        )

        # Create message
        message = ActorMessage(
            message_type="set_strategic_objective",
            content={
                "objective": "Increase market share by 25%",
                "key_results": ["KPI 1", "KPI 2", "KPI 3"],
                "deadline": "2024-12-31",
            },
            sender="governance",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify objective set
        assert len(spawned_metis._objectives) > 0

    @pytest.mark.asyncio
    async def test_handle_get_plan_status(self, spawned_metis, mock_nats):
        """Test handling plan status request."""
        # Setup plan
        spawned_metis._plans["plan-status-001"] = {
            "plan_id": "plan-status-001",
            "objective": "Test objective",
            "phases": [{"name": "Phase 1", "status": "complete"}],
            "status": "in_progress",
        }

        # Create message
        message = ActorMessage(
            message_type="get_plan_status",
            content={"plan_id": "plan-status-001"},
            sender="monitor",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify status published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_generate_strategic_plan(self, spawned_metis, mock_llm):
        """Test generating strategic plan."""
        # Setup mock LLM
        mock_llm.register_response(
            "strategic plan",
            "Strategic Plan: 1) Market analysis, 2) Product development, 3) Go-to-market."
        )

        # Generate plan
        plan = await spawned_metis._generate_strategic_plan(
            objective="Launch new product",
            context={"market": "enterprise", "timeline": "6 months"}
        )

        # Verify plan
        assert isinstance(plan, dict)
        assert "phases" in plan or "steps" in plan

    @pytest.mark.asyncio
    async def test_optimize_resource_allocation(self, spawned_metis, mock_llm):
        """Test optimizing resource allocation."""
        # Setup mock LLM
        mock_llm.register_response(
            "optimize",
            "Optimized allocation: Engineering 50%, Marketing 25%, Sales 25%."
        )

        # Optimize
        allocation = await spawned_metis._optimize_resource_allocation(
            plan_id="plan-opt-001",
            resources={"budget": 500000, "people": 20},
            constraints=["time", "budget"]
        )

        # Verify allocation
        assert isinstance(allocation, dict)

    @pytest.mark.asyncio
    async def test_assess_plan_risks(self, spawned_metis, mock_llm):
        """Test assessing plan risks."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: 3 high risks identified with mitigations."
        )

        # Assess risks
        risks = await spawned_metis._assess_plan_risks(
            plan_id="plan-risk-001",
            scenario="aggressive growth"
        )

        # Verify risks
        assert isinstance(risks, list)

    @pytest.mark.asyncio
    async def test_generate_scenarios(self, spawned_metis, mock_llm):
        """Test generating scenarios."""
        # Setup mock LLM
        mock_llm.register_response(
            "scenario",
            "Scenarios generated: Optimistic, Baseline, Pessimistic with probabilities."
        )

        # Generate scenarios
        scenarios = await spawned_metis._generate_scenarios(
            plan_id="plan-scenario-001",
            variables=["market_growth", "competition", "regulation"]
        )

        # Verify scenarios
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 3

    @pytest.mark.asyncio
    async def test_concurrent_planning(self, spawned_metis, mock_nats):
        """Test handling multiple concurrent plans."""
        # Create multiple plans
        for i in range(5):
            spawned_metis._plans[f"plan-{i}"] = {
                "plan_id": f"plan-{i}",
                "objective": f"Objective {i}",
                "status": "active",
            }

        # Verify all plans tracked
        summary = await spawned_metis.get_strategic_summary()
        assert summary["total_plans"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_metis):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="create_strategic_plan",
            content={},  # Missing required fields
            sender="test",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_metis.process_message(message)

        # Verify agent still active
        assert spawned_metis._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_metis, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="get_plan_status",
            content={"plan_id": "test"},
            sender="test",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_metis.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "metis_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_metis, mock_db):
        """Test agent state persistence."""
        # Add plan
        spawned_metis._plans["persist-test"] = {
            "plan_id": "persist-test",
            "objective": "Persistent objective",
            "status": "active",
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_metis.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, metis_agent):
        """Test agent error recovery."""
        await metis_agent.spawn()
        metis_agent._state = ActorState.ERROR
        await metis_agent.resume()
        assert metis_agent._state == ActorState.ACTIVE
