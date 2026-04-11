"""
Integration tests for MetisAgent.

Tier 2 (Support) - MetisAgent handles strategic planning and resource allocation.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from src.heretek_swarm.actors.base import ActorMessage, ActorState
from src.heretek_swarm.actors.metis import MetisAgent

_pytestmark = pytest.mark.integration


class TestMetisAgentIntegration:
    """Integration tests for MetisAgent."""

    @pytest_asyncio.fixture
    async def metis_agent(self, _mock_nats, _mock_llm, _mock_db):
        """Create MetisAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.metis.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                with patch('src.heretek_swarm.actors.metis.get_db_pool', return_value=mock_db):
                    _agent = MetisAgent(agent_id="metis-test-001")
                    yield agent
                    if agent._state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_metis(self, _metis_agent):
        """Create and spawn MetisAgent."""
        await metis_agent.spawn()
        yield metis_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, _metis_agent):
        """Test agent spawning lifecycle."""
        assert metis_agent._state == ActorState.SPAWNING
        await metis_agent.spawn()
        assert metis_agent._state == ActorState.ACTIVE
        assert metis_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, _spawned_metis):
        """Test agent termination lifecycle."""
        assert spawned_metis._state == ActorState.ACTIVE
        await spawned_metis.terminate()
        assert spawned_metis._state == ActorState.TERMINATED
        assert not spawned_metis.is_alive

    @pytest.mark.asyncio
    async def test_handle_create_strategic_plan(self, _spawned_metis, _mock_nats, _mock_llm):
        """Test handling strategic plan creation."""
        # Setup mock LLM
        mock_llm.register_response(
            "strategic plan",
            "Strategic Plan: Phase 1 - Foundation, Phase 2 - Growth, Phase 3 - Scale."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "create_strategic_plan",
            _content = {
                "objective": "Achieve market leadership",
                "timeline": "12 months",
                "constraints": ["budget", "resources"],
            },
            _sender = "coordinator",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify plan created
        assert len(spawned_metis._plans) > 0

    @pytest.mark.asyncio
    async def test_handle_allocate_resources(self, _spawned_metis, _mock_llm):
        """Test handling resource allocation."""
        # Setup mock LLM
        mock_llm.register_response(
            "allocate",
            "Resource allocation: 40% engineering, 30% marketing, 30% operations."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "allocate_resources",
            _content = {
                "plan_id": "plan-001",
                "resources": {"budget": 1000000, "headcount": 50},
                "priorities": ["product", "growth"],
            },
            _sender = "coordinator",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify allocation tracked
        assert "plan-001" in spawned_metis._allocations

    @pytest.mark.asyncio
    async def test_handle_assess_risks(self, _spawned_metis, _mock_llm):
        """Test handling risk assessment."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: Market risk=medium, Technical risk=low, Financial risk=low."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "assess_risks",
            _content = {
                "plan_id": "plan-001",
                "scenario": "Market expansion",
            },
            _sender = "steward",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify risks assessed
        assert "plan-001" in spawned_metis._risk_assessments

    @pytest.mark.asyncio
    async def test_handle_analyze_scenarios(self, _spawned_metis, _mock_llm):
        """Test handling scenario analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "scenario",
            "Scenario analysis: Best case - 50% growth, Base case - 30% growth, Worst case - 10% growth."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "analyze_scenarios",
            _content = {
                "scenarios": ["optimistic", "baseline", "pessimistic"],
                "variables": ["market", "competition", "resources"],
            },
            _sender = "coordinator",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify scenarios analyzed
        _stats = await spawned_metis.get_strategic_summary()
        assert stats["total_scenarios"] >= 1

    @pytest.mark.asyncio
    async def test_handle_set_strategic_objective(self, _spawned_metis, _mock_llm):
        """Test handling strategic objective setting."""
        # Setup mock LLM
        mock_llm.register_response(
            "objective",
            "Strategic objective defined with measurable KPIs and milestones."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "set_strategic_objective",
            _content = {
                "objective": "Increase market share by 25%",
                "key_results": ["KPI 1", "KPI 2", "KPI 3"],
                "deadline": "2024-12-31",
            },
            _sender = "governance",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify objective set
        assert len(spawned_metis._objectives) > 0

    @pytest.mark.asyncio
    async def test_handle_get_plan_status(self, _spawned_metis, _mock_nats):
        """Test handling plan status request."""
        # Setup plan
        spawned_metis._plans["plan-status-001"] = {
            "plan_id": "plan-status-001",
            "objective": "Test objective",
            "phases": [{"name": "Phase 1", "status": "complete"}],
            "status": "in_progress",
        }

        # Create message
        _message = ActorMessage(
            _message_type = "get_plan_status",
            _content = {"plan_id": "plan-status-001"},
            _sender = "monitor",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_metis.process_message(message)

        # Verify status published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_generate_strategic_plan(self, _spawned_metis, _mock_llm):
        """Test generating strategic plan."""
        # Setup mock LLM
        mock_llm.register_response(
            "strategic plan",
            "Strategic Plan: 1) Market analysis, 2) Product development, 3) Go-to-market."
        )

        # Generate plan
        _plan = await spawned_metis._generate_strategic_plan(
            _objective = "Launch new product",
            _context = {"market": "enterprise", "timeline": "6 months"}
        )

        # Verify plan
        assert isinstance(plan, dict)
        assert "phases" in plan or "steps" in plan

    @pytest.mark.asyncio
    async def test_optimize_resource_allocation(self, _spawned_metis, _mock_llm):
        """Test optimizing resource allocation."""
        # Setup mock LLM
        mock_llm.register_response(
            "optimize",
            "Optimized allocation: Engineering 50%, Marketing 25%, Sales 25%."
        )

        # Optimize
        _allocation = await spawned_metis._optimize_resource_allocation(
            _plan_id = "plan-opt-001",
            _resources = {"budget": 500000, "people": 20},
            _constraints = ["time", "budget"]
        )

        # Verify allocation
        assert isinstance(allocation, dict)

    @pytest.mark.asyncio
    async def test_assess_plan_risks(self, _spawned_metis, _mock_llm):
        """Test assessing plan risks."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: 3 high risks identified with mitigations."
        )

        # Assess risks
        _risks = await spawned_metis._assess_plan_risks(
            _plan_id = "plan-risk-001",
            _scenario = "aggressive growth"
        )

        # Verify risks
        assert isinstance(risks, list)

    @pytest.mark.asyncio
    async def test_generate_scenarios(self, _spawned_metis, _mock_llm):
        """Test generating scenarios."""
        # Setup mock LLM
        mock_llm.register_response(
            "scenario",
            "Scenarios generated: Optimistic, Baseline, Pessimistic with probabilities."
        )

        # Generate scenarios
        _scenarios = await spawned_metis._generate_scenarios(
            _plan_id = "plan-scenario-001",
            _variables = ["market_growth", "competition", "regulation"]
        )

        # Verify scenarios
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 3

    @pytest.mark.asyncio
    async def test_concurrent_planning(self, _spawned_metis, _mock_nats):
        """Test handling multiple concurrent plans."""
        # Create multiple plans
        for i in range(5):
            spawned_metis._plans[f"plan-{i}"] = {
                "plan_id": f"plan-{i}",
                "objective": f"Objective {i}",
                "status": "active",
            }

        # Verify all plans tracked
        _summary = await spawned_metis.get_strategic_summary()
        assert summary["total_plans"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, _spawned_metis):
        """Test message validation."""
        # Create invalid message
        _message = ActorMessage(
            _message_type = "create_strategic_plan",
            _content = {},  # Missing required fields
            _sender = "test",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_metis.process_message(message)

        # Verify agent still active
        assert spawned_metis._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_metis, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        _message = ActorMessage(
            _message_type = "get_plan_status",
            _content = {"plan_id": "test"},
            _sender = "test",
            _recipient = "metis-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        _start = time.time()
        await spawned_metis.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "metis_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_metis, _mock_db):
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
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, _metis_agent):
        """Test agent error recovery."""
        await metis_agent.spawn()
        metis_agent._state = ActorState.ERROR
        await metis_agent.resume()
        assert metis_agent._state == ActorState.ACTIVE
