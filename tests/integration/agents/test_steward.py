"""
Integration tests for StewardAgent.

Tier 1 (Core Triad) - StewardAgent coordinates deliberation and manages governance policies.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.triad import StewardAgent

_pytestmark = pytest.mark.integration


class TestStewardAgentIntegration:
    """Integration tests for StewardAgent."""

    @pytest_asyncio.fixture
    async def steward_agent(self, _mock_nats, _mock_llm):
        """Create StewardAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                _agent = StewardAgent(agent_id="steward-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_steward(self, _steward_agent):
        """Create and spawn StewardAgent."""
        await steward_agent.spawn()
        yield steward_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, _steward_agent):
        """Test agent spawning lifecycle."""
        # Verify initial state
        assert steward_agent.state == ActorState.SPAWNING

        # Spawn agent
        await steward_agent.spawn()

        # Verify active state
        assert steward_agent.state == ActorState.ACTIVE
        assert steward_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, _spawned_steward):
        """Test agent termination lifecycle."""
        # Verify active state
        assert spawned_steward.state == ActorState.ACTIVE

        # Terminate agent
        await spawned_steward.terminate()

        # Verify terminated state
        assert spawned_steward.state == ActorState.TERMINATED
        assert not spawned_steward.is_alive

    @pytest.mark.asyncio
    async def test_handle_start_deliberation(self, _spawned_steward, _mock_nats, _sample_deliberation):
        """Test handling deliberation start request."""
        # Setup mock LLM response
        spawned_steward._llm_provider.register_response(
            "coordinate",
            "Coordinated deliberation initiated. Awaiting Alpha analysis."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "start_deliberation",
            _content = sample_deliberation,
            _sender = "coordinator",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify deliberation was initiated
        assert "delib-001" in spawned_steward._deliberations

    @pytest.mark.asyncio
    async def test_handle_request_decision(self, _spawned_steward, _mock_nats):
        """Test handling decision request."""
        # Setup existing deliberation
        spawned_steward._deliberations["delib-002"] = {
            "session_id": "delib-002",
            "problem": "Test problem",
            "phase": "alpha",
            "started_at": datetime.utcnow().isoformat(),
        }

        # Create message
        _message = ActorMessage(
            _message_type = "request_decision",
            _content = {"session_id": "delib-002"},
            _sender = "alpha",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify deliberation phase updated
        assert spawned_steward._deliberations["delib-002"]["phase"] == "beta"

    @pytest.mark.asyncio
    async def test_handle_report_status(self, _spawned_steward):
        """Test handling status report request."""
        # Create message
        _message = ActorMessage(
            _message_type = "report_status",
            _content = {"requester": "monitor"},
            _sender = "monitor",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify status was published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_policy_update(self, _spawned_steward):
        """Test handling policy update."""
        # Create message
        _message = ActorMessage(
            _message_type = "policy_update",
            _content = {
                "policy_id": "pol-001",
                "rules": [{"field": "input", "constraint": "required"}],
            },
            _sender = "governance",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify policy was updated
        assert "pol-001" in spawned_steward._policies

    @pytest.mark.asyncio
    async def test_coordinate_triad(self, _spawned_steward, _mock_nats, _mock_llm):
        """Test Triad coordination."""
        # Setup mock LLM
        mock_llm.register_response(
            "coordinate",
            "Triad coordination: Alpha analyzing, Beta validating, Charlie challenging."
        )

        # Coordinate deliberation
        _result = await spawned_steward.coordinate_triad(
            _problem = "Should we implement feature X?",
            _context = {"priority": "high"},
        )

        # Verify result
        assert isinstance(result, dict)
        assert "session_id" in result
        assert "phase" in result

    @pytest.mark.asyncio
    async def test_get_deliberation_status(self, _spawned_steward):
        """Test getting deliberation status."""
        # Setup deliberation
        spawned_steward._deliberations["delib-003"] = {
            "session_id": "delib-003",
            "problem": "Test",
            "phase": "complete",
            "decision": "APPROVE",
        }

        # Get status
        _status = spawned_steward.get_deliberation_status("delib-003")

        # Verify status
        assert status is not None
        assert status["session_id"] == "delib-003"
        assert status["phase"] == "complete"

    @pytest.mark.asyncio
    async def test_message_validation(self, _spawned_steward):
        """Test message validation."""
        # Create invalid message (missing required fields)
        _message = ActorMessage(
            _message_type = "start_deliberation",
            _content = {},  # Empty content
            _sender = "test",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_steward.process_message(message)

        # Verify error was handled
        assert spawned_steward.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_concurrent_deliberations(self, _spawned_steward, _mock_nats):
        """Test handling multiple concurrent deliberations."""
        # Start multiple deliberations
        for i in range(5):
            spawned_steward._deliberations[f"delib-{i:03d}"] = {
                "session_id": f"delib-{i:03d}",
                "problem": f"Problem {i}",
                "phase": "alpha",
                "started_at": datetime.utcnow().isoformat(),
            }

        # Verify all deliberations tracked
        assert len(spawned_steward._deliberations) == 5

        # Get status for all
        _statuses = spawned_steward.get_all_deliberation_statuses()
        assert len(statuses) == 5

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_steward, _mock_db):
        """Test agent state persistence."""
        # Setup deliberation
        spawned_steward._deliberations["delib-persist"] = {
            "session_id": "delib-persist",
            "problem": "Persistent problem",
            "phase": "beta",
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_steward.save_state()

        # Verify state saved
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_steward, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        # Create message
        _message = ActorMessage(
            _message_type = "report_status",
            _content = {},
            _sender = "test",
            _recipient = "steward-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Measure latency
        _start = time.time()
        await spawned_steward.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        # Assert baseline
        assert_latency_baseline(latency_ms, "steward_message_process")

    @pytest.mark.asyncio
    async def test_error_recovery(self, _steward_agent):
        """Test agent error recovery."""
        # Spawn agent
        await steward_agent.spawn()

        # Simulate error condition
        steward_agent.state = ActorState.ERROR

        # Resume should recover
        await steward_agent.resume()

        # Verify recovered
        assert steward_agent.state == ActorState.ACTIVE
