"""
Integration tests for StewardAgent.

Tier 1 (Core Triad) - StewardAgent coordinates deliberation and manages governance policies.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.heretek_swarm.actors.triad import StewardAgent
from src.heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestStewardAgentIntegration:
    """Integration tests for StewardAgent."""

    @pytest_asyncio.fixture
    async def steward_agent(self, mock_nats, mock_llm):
        """Create StewardAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                agent = StewardAgent(agent_id="steward-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_steward(self, steward_agent):
        """Create and spawn StewardAgent."""
        await steward_agent.spawn()
        yield steward_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, steward_agent):
        """Test agent spawning lifecycle."""
        # Verify initial state
        assert steward_agent.state == ActorState.SPAWNING

        # Spawn agent
        await steward_agent.spawn()

        # Verify active state
        assert steward_agent.state == ActorState.ACTIVE
        assert steward_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_steward):
        """Test agent termination lifecycle."""
        # Verify active state
        assert spawned_steward.state == ActorState.ACTIVE

        # Terminate agent
        await spawned_steward.terminate()

        # Verify terminated state
        assert spawned_steward.state == ActorState.TERMINATED
        assert not spawned_steward.is_alive

    @pytest.mark.asyncio
    async def test_handle_start_deliberation(self, spawned_steward, mock_nats, sample_deliberation):
        """Test handling deliberation start request."""
        # Setup mock LLM response
        spawned_steward._llm_provider.register_response(
            "coordinate",
            "Coordinated deliberation initiated. Awaiting Alpha analysis."
        )

        # Create message
        message = ActorMessage(
            message_type="start_deliberation",
            content=sample_deliberation,
            sender="coordinator",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify deliberation was initiated
        assert "delib-001" in spawned_steward._deliberations

    @pytest.mark.asyncio
    async def test_handle_request_decision(self, spawned_steward, mock_nats):
        """Test handling decision request."""
        # Setup existing deliberation
        spawned_steward._deliberations["delib-002"] = {
            "session_id": "delib-002",
            "problem": "Test problem",
            "phase": "alpha",
            "started_at": datetime.utcnow().isoformat(),
        }

        # Create message
        message = ActorMessage(
            message_type="request_decision",
            content={"session_id": "delib-002"},
            sender="alpha",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify deliberation phase updated
        assert spawned_steward._deliberations["delib-002"]["phase"] == "beta"

    @pytest.mark.asyncio
    async def test_handle_report_status(self, spawned_steward):
        """Test handling status report request."""
        # Create message
        message = ActorMessage(
            message_type="report_status",
            content={"requester": "monitor"},
            sender="monitor",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify status was published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_policy_update(self, spawned_steward):
        """Test handling policy update."""
        # Create message
        message = ActorMessage(
            message_type="policy_update",
            content={
                "policy_id": "pol-001",
                "rules": [{"field": "input", "constraint": "required"}],
            },
            sender="governance",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_steward.process_message(message)

        # Verify policy was updated
        assert "pol-001" in spawned_steward._policies

    @pytest.mark.asyncio
    async def test_coordinate_triad(self, spawned_steward, mock_nats, mock_llm):
        """Test Triad coordination."""
        # Setup mock LLM
        mock_llm.register_response(
            "coordinate",
            "Triad coordination: Alpha analyzing, Beta validating, Charlie challenging."
        )

        # Coordinate deliberation
        result = await spawned_steward.coordinate_triad(
            problem="Should we implement feature X?",
            context={"priority": "high"},
        )

        # Verify result
        assert isinstance(result, dict)
        assert "session_id" in result
        assert "phase" in result

    @pytest.mark.asyncio
    async def test_get_deliberation_status(self, spawned_steward):
        """Test getting deliberation status."""
        # Setup deliberation
        spawned_steward._deliberations["delib-003"] = {
            "session_id": "delib-003",
            "problem": "Test",
            "phase": "complete",
            "decision": "APPROVE",
        }

        # Get status
        status = spawned_steward.get_deliberation_status("delib-003")

        # Verify status
        assert status is not None
        assert status["session_id"] == "delib-003"
        assert status["phase"] == "complete"

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_steward):
        """Test message validation."""
        # Create invalid message (missing required fields)
        message = ActorMessage(
            message_type="start_deliberation",
            content={},  # Empty content
            sender="test",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_steward.process_message(message)

        # Verify error was handled
        assert spawned_steward.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_concurrent_deliberations(self, spawned_steward, mock_nats):
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
        statuses = spawned_steward.get_all_deliberation_statuses()
        assert len(statuses) == 5

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_steward, mock_db):
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
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_steward, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        # Create message
        message = ActorMessage(
            message_type="report_status",
            content={},
            sender="test",
            recipient="steward-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Measure latency
        start = time.time()
        await spawned_steward.process_message(message)
        latency_ms = (time.time() - start) * 1000

        # Assert baseline
        assert_latency_baseline(latency_ms, "steward_message_process")

    @pytest.mark.asyncio
    async def test_error_recovery(self, steward_agent):
        """Test agent error recovery."""
        # Spawn agent
        await steward_agent.spawn()

        # Simulate error condition
        steward_agent.state = ActorState.ERROR

        # Resume should recover
        await steward_agent.resume()

        # Verify recovered
        assert steward_agent.state == ActorState.ACTIVE
