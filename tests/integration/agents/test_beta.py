"""
Integration tests for BetaAgent.

Tier 1 (Core Triad) - BetaAgent performs secondary analysis, validation, and error detection.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.heretek_swarm.actors.triad import BetaAgent
from src.heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestBetaAgentIntegration:
    """Integration tests for BetaAgent."""

    @pytest_asyncio.fixture
    async def beta_agent(self, mock_nats, mock_llm):
        """Create BetaAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                agent = BetaAgent(agent_id="beta-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_beta(self, beta_agent):
        """Create and spawn BetaAgent."""
        await beta_agent.spawn()
        yield beta_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, beta_agent):
        """Test agent spawning lifecycle."""
        assert beta_agent.state == ActorState.SPAWNING
        await beta_agent.spawn()
        assert beta_agent.state == ActorState.ACTIVE
        assert beta_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_beta):
        """Test agent termination lifecycle."""
        assert spawned_beta.state == ActorState.ACTIVE
        await spawned_beta.terminate()
        assert spawned_beta.state == ActorState.TERMINATED
        assert not spawned_beta.is_alive

    @pytest.mark.asyncio
    async def test_handle_deliberation_request(self, spawned_beta, mock_nats):
        """Test handling deliberation request."""
        # Setup mock LLM response
        spawned_beta._llm_provider.register_response(
            "analyze",
            "Beta analysis: Secondary review confirms Alpha findings with additional validation."
        )

        # Create message
        message = ActorMessage(
            message_type="deliberation_request",
            content={
                "session_id": "delib-beta-001",
                "problem": "Review architecture decision",
                "alpha_analysis": {"recommendation": "approve"},
            },
            sender="steward",
            recipient="beta-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify analysis was performed
        assert "delib-beta-001" in spawned_beta._analyses

    @pytest.mark.asyncio
    async def test_handle_validation_request(self, spawned_beta, mock_llm):
        """Test handling validation request."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Validation complete. Content verified. No errors detected."
        )

        # Create message
        message = ActorMessage(
            message_type="validation_request",
            content={
                "content": {"decision": "deploy", "version": "1.0.0"},
                "criteria": ["correctness", "completeness"],
            },
            sender="alpha",
            recipient="beta-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify validation completed
        stats = spawned_beta.get_validation_statistics()
        assert stats["total_validations"] >= 1

    @pytest.mark.asyncio
    async def test_handle_error_check(self, spawned_beta, mock_llm):
        """Test handling error check request."""
        # Setup mock LLM
        mock_llm.register_response(
            "check",
            "Error check complete. Found 0 critical errors, 1 warning."
        )

        # Create message
        message = ActorMessage(
            message_type="error_check",
            content={
                "target": "code_review",
                "content": "def process():\n    return True",
            },
            sender="charlie",
            recipient="beta-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify error check completed
        stats = spawned_beta.get_validation_statistics()
        assert stats["total_error_checks"] >= 1

    @pytest.mark.asyncio
    async def test_perform_analysis(self, spawned_beta, mock_llm):
        """Test performing secondary analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "analyze",
            "Secondary analysis: Alpha findings validated. Additional considerations identified."
        )

        # Perform analysis
        result = await spawned_beta._perform_analysis(
            problem="Verify system design choices"
        )

        # Verify result
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_validate_decision(self, spawned_beta, mock_llm):
        """Test validating decision."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Decision validation: All criteria met. Recommendation: APPROVE."
        )

        # Validate decision
        result = await spawned_beta._validate_decision(
            decision={"action": "deploy"},
            criteria=["safety", "correctness"]
        )

        # Verify result
        assert isinstance(result, dict)
        assert "valid" in result or "status" in result

    @pytest.mark.asyncio
    async def test_detect_errors(self, spawned_beta, mock_llm):
        """Test error detection."""
        # Setup mock LLM
        mock_llm.register_response(
            "detect",
            "Error detection: No critical errors found. 2 minor issues identified."
        )

        # Detect errors
        errors = await spawned_beta._detect_errors(
            content={"code": "invalid_syntax_here"}
        )

        # Verify errors list
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_validation_with_alpha_findings(self, spawned_beta, mock_llm):
        """Test validation considering Alpha findings."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Validation considering Alpha analysis: Findings confirmed."
        )

        # Validate with Alpha findings
        result = await spawned_beta._validate_decision(
            decision={"action": "approve"},
            criteria=["accuracy"],
            alpha_findings={"analysis": "thorough", "confidence": 0.9}
        )

        # Verify result
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_validations(self, spawned_beta, mock_nats):
        """Test handling multiple concurrent validations."""
        # Simulate multiple validations
        for i in range(5):
            spawned_beta._validations[f"validation-{i}"] = {
                "content": f"Content {i}",
                "status": "valid",
                "errors": [],
            }

        # Verify all validations tracked
        stats = spawned_beta.get_validation_statistics()
        assert stats["total_validations"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_beta):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="validation_request",
            content={},  # Missing required fields
            sender="test",
            recipient="beta-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_beta.process_message(message)

        # Verify agent still active
        assert spawned_beta._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_beta, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="validation_request",
            content={"content": {}},
            sender="test",
            recipient="beta-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_beta.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "beta_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_beta, mock_db):
        """Test agent state persistence."""
        # Add validation
        spawned_beta._validations["persist-test"] = {
            "content": "Persistent validation",
            "status": "valid",
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_beta.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, beta_agent):
        """Test agent error recovery."""
        await beta_agent.spawn()
        beta_agent._state = ActorState.ERROR
        await beta_agent.resume()
        assert beta_agent._state == ActorState.ACTIVE
