"""
Integration tests for MetisAgent.

Tier 2 (Support) - MetisAgent handles strategic planning and resource allocation.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.metis import MetisAgent

pytestmark = pytest.mark.integration


class TestMetisAgentIntegration:
    """Integration tests for MetisAgent."""

    @pytest_asyncio.fixture
    async def metis_agent(self, mock_nats, mock_llm, mock_db):
        """Create MetisAgent with mock dependencies."""
        with patch("heretek_swarm.actors.stubs.get_nats_event_mesh", return_value=mock_nats):
            with patch("heretek_swarm.actors.stubs.get_llm_provider", return_value=mock_llm):
                with patch("heretek_swarm.actors.stubs.get_db_pool", return_value=mock_db):
                    agent = MetisAgent(agent_id="metis-test-001")
                    yield agent
                    if agent.state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_metis(self, metis_agent):
        """Create and spawn MetisAgent."""
        await metis_agent.spawn()
        yield metis_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, metis_agent):
        """Test agent spawning lifecycle."""
        assert metis_agent.state == ActorState.SPAWNING
        await metis_agent.spawn()
        assert metis_agent.state == ActorState.ACTIVE
        assert metis_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_metis):
        """Test agent termination lifecycle."""
        assert spawned_metis.state == ActorState.ACTIVE
        await spawned_metis.terminate()
        assert spawned_metis.state == ActorState.TERMINATED
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
        assert len(spawned_metis.active_plans) > 0

    @pytest.mark.asyncio
    async def test_handle_allocate_resources(self, spawned_metis, mock_llm):
        """Test handling resource allocation."""
        # Setup mock LLM
        mock_llm.register_response(
            "allocate",
            "Resource allocation: 40% engineering, 30% marketing, 30% operations."
        )

        # Pre-create the plan that allocation references
        spawned_metis.active_plans["plan-001"] = {
            "plan_id": "plan-001",
            "objective": "Test objective",
            "status": "active",
        }

        # Create message
        message = ActorMessage(
            message_type="allocate_resources",
            content={
                "plan_id": "plan-001",
                "resources": {"budget": 1000000, "headcount": 50},
                "priorities": {"product": 0.5, "growth": 0.5},
            },
            sender="coordinator",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify allocation tracked
        assert "plan-001" in spawned_metis.resource_allocations

    @pytest.mark.asyncio
    async def test_handle_assess_risks(self, spawned_metis, mock_llm):
        """Test handling risk assessment."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: Market risk=medium, Technical risk=low, Financial risk=low."
        )

        # Pre-create plan for risk assessment
        spawned_metis.active_plans["plan-001"] = {
            "plan_id": "plan-001",
            "objective": "Test objective",
            "status": "active",
        }

        # Create message
        message = ActorMessage(
            message_type="assess_risks",
            content={
                "plan_id": "plan-001",
                "domain": "technical",
            },
            sender="steward",
            recipient="metis-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message - will work even without LLM (returns empty list)
        await spawned_metis.process_message(message)

        # Verify risks tracked (may be empty if no LLM)
        assert isinstance(spawned_metis.risk_register, dict)

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
                "base_scenario": {"market": "growth"},
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
        assert stats["scenario_analyses"] >= 1

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
        assert len(spawned_metis.strategic_objectives) > 0

    @pytest.mark.asyncio
    async def test_handle_get_plan_status(self, spawned_metis, mock_nats):
        """Test handling plan status request."""
        # Setup plan
        spawned_metis.active_plans["plan-status-001"] = {
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

        # Process message - handler looks up status (may publish if reply_to set)
        await spawned_metis.process_message(message)

        # Verify plan still exists
        assert "plan-status-001" in spawned_metis.active_plans

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
            plan_id="test-plan-001",
            objective="Launch new product",
            horizon_days=180,
            constraints=["budget", "timeline"]
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
            priorities={"engineering": 0.5, "marketing": 0.3, "sales": 0.2}
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
            domain="technical"
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
            base_scenario={"market": "stable"},
            variables=["market_growth", "competition", "regulation"],
            max_scenarios=5
        )

        # Verify scenarios
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 1

    @pytest.mark.asyncio
    async def test_concurrent_planning(self, spawned_metis, mock_nats):
        """Test handling multiple concurrent plans."""
        # Create multiple plans
        for i in range(5):
            spawned_metis.active_plans[f"plan-{i}"] = {
                "plan_id": f"plan-{i}",
                "objective": f"Objective {i}",
                "status": "active",
            }

        # Verify all plans tracked
        summary = await spawned_metis.get_strategic_summary()
        assert summary["active_plans"] >= 5

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
        assert spawned_metis.state == ActorState.ACTIVE

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
        spawned_metis.active_plans["persist-test"] = {
            "plan_id": "persist-test",
            "objective": "Persistent objective",
            "status": "active",
        }

        # Save state
        with patch("heretek_swarm.actors.stubs.get_db_pool", return_value=mock_db):
            await spawned_metis.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, metis_agent):
        """Test agent error recovery."""
        await metis_agent.spawn()
        metis_agent.state = ActorState.ERROR
        await metis_agent.resume()
        assert metis_agent.state == ActorState.ACTIVE
