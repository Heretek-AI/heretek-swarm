"""
Integration tests for BetaAgent.

Tier 1 (Core Triad) - BetaAgent performs secondary analysis, validation, and error detection.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.triad import BetaAgent

_pytestmark = pytest.mark.integration


class TestBetaAgentIntegration:
    """Integration tests for BetaAgent."""

    @pytest_asyncio.fixture
    async def beta_agent(self, _mock_nats, _mock_llm):
        """Create BetaAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                _agent = BetaAgent(agent_id="beta-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_beta(self, _beta_agent):
        """Create and spawn BetaAgent."""
        await beta_agent.spawn()
        yield beta_agent

    @pytest.mark.asyncio

    async def test_handle_deliberation_request(self, _spawned_beta, _mock_nats):
        """Test handling deliberation request."""
        # Setup mock LLM response
        spawned_beta._llm_provider.register_response(
            "analyze",
            "Beta analysis: Secondary review confirms Alpha findings with additional validation."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "deliberation_request",
            _content = {
                "session_id": "delib-beta-001",
                "problem": "Review architecture decision",
                "alpha_analysis": {"recommendation": "approve"},
            },
            _sender = "steward",
            _recipient = "beta-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify analysis was performed
        assert "delib-beta-001" in spawned_beta._analyses

    @pytest.mark.asyncio
    async def test_handle_validation_request(self, _spawned_beta, _mock_llm):
        """Test handling validation request."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Validation complete. Content verified. No errors detected."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "validation_request",
            _content = {
                "content": {"decision": "deploy", "version": "1.0.0"},
                "criteria": ["correctness", "completeness"],
            },
            _sender = "alpha",
            _recipient = "beta-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify validation completed
        _stats = spawned_beta.get_validation_statistics()
        assert stats["total_validations"] >= 1

    @pytest.mark.asyncio
    async def test_handle_error_check(self, _spawned_beta, _mock_llm):
        """Test handling error check request."""
        # Setup mock LLM
        mock_llm.register_response(
            "check",
            "Error check complete. Found 0 critical errors, 1 warning."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "error_check",
            _content = {
                "target": "code_review",
                "content": "def process():\n    return True",
            },
            _sender = "charlie",
            _recipient = "beta-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_beta.process_message(message)

        # Verify error check completed
        _stats = spawned_beta.get_validation_statistics()
        assert stats["total_error_checks"] >= 1

    @pytest.mark.asyncio
    async def test_perform_analysis(self, _spawned_beta, _mock_llm):
        """Test performing secondary analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "analyze",
            "Secondary analysis: Alpha findings validated. Additional considerations identified."
        )

        # Perform analysis
        _result = await spawned_beta._perform_analysis(
            _problem = "Verify system design choices"
        )

        # Verify result
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_validate_decision(self, _spawned_beta, _mock_llm):
        """Test validating decision."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Decision validation: All criteria met. Recommendation: APPROVE."
        )

        # Validate decision
        _result = await spawned_beta._validate_decision(
            _decision = {"action": "deploy"},
            _criteria = ["safety", "correctness"]
        )

        # Verify result
        assert isinstance(result, dict)
        assert "valid" in result or "status" in result

    @pytest.mark.asyncio
    async def test_detect_errors(self, _spawned_beta, _mock_llm):
        """Test error detection."""
        # Setup mock LLM
        mock_llm.register_response(
            "detect",
            "Error detection: No critical errors found. 2 minor issues identified."
        )

        # Detect errors
        _errors = await spawned_beta._detect_errors(
            _content = {"code": "invalid_syntax_here"}
        )

        # Verify errors list
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_validation_with_alpha_findings(self, _spawned_beta, _mock_llm):
        """Test validation considering Alpha findings."""
        # Setup mock LLM
        mock_llm.register_response(
            "validate",
            "Validation considering Alpha analysis: Findings confirmed."
        )

        # Validate with Alpha findings
        _result = await spawned_beta._validate_decision(
            _decision = {"action": "approve"},
            _criteria = ["accuracy"],
            _alpha_findings = {"analysis": "thorough", "confidence": 0.9}
        )

        # Verify result
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_validations(self, _spawned_beta, _mock_nats):
        """Test handling multiple concurrent validations."""
        # Simulate multiple validations
        for i in range(5):
            spawned_beta._validations[f"validation-{i}"] = {
                "content": f"Content {i}",
                "status": "valid",
                "errors": [],
            }

        # Verify all validations tracked
        _stats = spawned_beta.get_validation_statistics()
        assert stats["total_validations"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, _spawned_beta):
        """Test message validation."""
        # Create invalid message
        _message = ActorMessage(
            _message_type = "validation_request",
            _content = {},  # Missing required fields
            _sender = "test",
            _recipient = "beta-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_beta.process_message(message)

        # Verify agent still active
        assert spawned_beta.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_beta, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        _message = ActorMessage(
            _message_type = "validation_request",
            _content = {"content": {}},
            _sender = "test",
            _recipient = "beta-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        _start = time.time()
        await spawned_beta.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "beta_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_beta, _mock_db):
        """Test agent state persistence."""
        spawned_beta._validations["persist-test"] = {
            "content": "Persistent validation",
            "status": "valid",
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_beta.save_state()

        # Verify state saved
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, _beta_agent):
        """Test agent error recovery."""
        await beta_agent.spawn()
        beta_agent.state = ActorState.ERROR
        await beta_agent.resume()
        assert beta_agent.state == ActorState.ACTIVE
