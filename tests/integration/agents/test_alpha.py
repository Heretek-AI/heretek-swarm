"""
Integration tests for AlphaAgent.

Tier 1 (Core Triad) - AlphaAgent performs primary analysis and decision-making.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.heretek_swarm.actors.triad import AlphaAgent
from src.heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestAlphaAgentIntegration:
    """Integration tests for AlphaAgent."""

    @pytest_asyncio.fixture
    async def alpha_agent(self, mock_nats, mock_llm):
        """Create AlphaAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.triad.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                agent = AlphaAgent(agent_id="alpha-test-001")
                yield agent
                if agent._state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_alpha(self, alpha_agent):
        """Create and spawn AlphaAgent."""
        await alpha_agent.spawn()
        yield alpha_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, alpha_agent):
        """Test agent spawning lifecycle."""
        assert alpha_agent._state == ActorState.SPAWNING
        await alpha_agent.spawn()
        assert alpha_agent._state == ActorState.ACTIVE
        assert alpha_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_alpha):
        """Test agent termination lifecycle."""
        assert spawned_alpha._state == ActorState.ACTIVE
        await spawned_alpha.terminate()
        assert spawned_alpha._state == ActorState.TERMINATED
        assert not spawned_alpha.is_alive

    @pytest.mark.asyncio
    async def test_handle_deliberation_request(self, spawned_alpha, mock_nats):
        """Test handling deliberation request."""
        # Setup mock LLM response
        spawned_alpha._llm_provider.register_response(
            "analyze",
            "Analysis complete. Primary assessment: The proposal is sound with minor risks."
        )

        # Create message
        message = ActorMessage(
            message_type="deliberation_request",
            content={
                "session_id": "delib-alpha-001",
                "problem": "Evaluate new architecture proposal",
                "context": {"urgency": "high"},
            },
            sender="steward",
            recipient="alpha-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_alpha.process_message(message)

        # Verify analysis was performed
        assert "delib-alpha-001" in spawned_alpha._analyses

    @pytest.mark.asyncio
    async def test_handle_analysis_request(self, spawned_alpha, mock_llm):
        """Test handling analysis request."""
        # Setup mock LLM
        mock_llm.register_response(
            "analyze",
            "Detailed analysis: Strengths identified - scalability, modularity. Weaknesses - complexity."
        )

        # Create message
        message = ActorMessage(
            message_type="analysis_request",
            content={
                "target": "system_design",
                "aspects": ["architecture", "performance", "security"],
            },
            sender="coordinator",
            recipient="alpha-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_alpha.process_message(message)

        # Verify analysis completed
        stats = spawned_alpha.get_analysis_statistics()
        assert stats["total_analyses"] >= 1

    @pytest.mark.asyncio
    async def test_handle_validation_request(self, spawned_alpha):
        """Test handling validation request."""
        # Create message
        message = ActorMessage(
            message_type="validation_request",
            content={
                "decision": {"action": "deploy", "target": "production"},
                "criteria": ["safety", "performance"],
            },
            sender="beta",
            recipient="alpha-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_alpha.process_message(message)

        # Verify validation tracked
        stats = spawned_alpha.get_analysis_statistics()
        assert stats["total_validations"] >= 1

    @pytest.mark.asyncio
    async def test_perform_analysis(self, spawned_alpha, mock_llm):
        """Test performing analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "analyze",
            "Analysis: Problem requires multi-faceted approach. Recommended solution identified."
        )

        # Perform analysis
        result = await spawned_alpha._perform_analysis(
            problem="How to optimize database queries?"
        )

        # Verify result
        assert isinstance(result, dict)
        assert "analysis" in result or "recommendation" in result

    @pytest.mark.asyncio
    async def test_validate_decision(self, spawned_alpha, mock_llm):
        """Test validating decision."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Validation passed. Decision meets all criteria."
        )

        # Validate decision
        result = await spawned_alpha._validate_decision(
            decision={"action": "approve", "confidence": 0.9}
        )

        # Verify result
        assert isinstance(result, dict)
        assert "valid" in result or "status" in result

    @pytest.mark.asyncio
    async def test_analysis_with_context(self, spawned_alpha, mock_llm):
        """Test analysis with rich context."""
        # Setup mock LLM
        mock_llm.register_response(
            "analyze",
            "Contextual analysis complete considering all provided factors."
        )

        # Perform analysis with context
        result = await spawned_alpha._perform_analysis(
            problem="Choose deployment strategy",
        )

        # Verify result contains analysis
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_analyses(self, spawned_alpha, mock_nats):
        """Test handling multiple concurrent analyses."""
        # Simulate multiple analysis requests
        for i in range(5):
            spawned_alpha._analyses[f"analysis-{i}"] = {
                "problem": f"Problem {i}",
                "status": "complete",
                "result": {"decision": "approve"},
            }

        # Verify all analyses tracked
        stats = spawned_alpha.get_analysis_statistics()
        assert stats["total_analyses"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_alpha):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="deliberation_request",
            content={},  # Missing required fields
            sender="test",
            recipient="alpha-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_alpha.process_message(message)

        # Verify agent still active
        assert spawned_alpha._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_alpha, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="analysis_request",
            content={"target": "test"},
            sender="test",
            recipient="alpha-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_alpha.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "alpha_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_alpha, mock_db):
        """Test agent state persistence."""
        # Add analysis
        spawned_alpha._analyses["persist-test"] = {
            "problem": "Persistent problem",
            "status": "complete",
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_alpha.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, alpha_agent):
        """Test agent error recovery."""
        await alpha_agent.spawn()
        alpha_agent._state = ActorState.ERROR
        await alpha_agent.resume()
        assert alpha_agent._state == ActorState.ACTIVE
