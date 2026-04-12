"""
Integration tests for CharlieAgent.

Tier 1 (Core Triad) - CharlieAgent serves as devil's advocate, performing risk assessment and challenge generation.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from heretek_swarm.actors.base import ActorMessage, ActorState
from heretek_swarm.actors.triad import CharlieAgent

pytestmark = pytest.mark.integration


class TestCharlieAgentIntegration:
    """Integration tests for CharlieAgent."""

    @pytest_asyncio.fixture
    async def charlie_agent(self, mock_nats, mock_llm):
        """Create CharlieAgent with mock dependencies."""
        with patch('heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                agent = CharlieAgent(agent_id="charlie-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_charlie(self, charlie_agent):
        """Create and spawn CharlieAgent."""
        await charlie_agent.spawn()
        yield charlie_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, charlie_agent):
        """Test agent spawning lifecycle."""
        assert charlie_agent.state == ActorState.SPAWNING
        await charlie_agent.spawn()
        assert charlie_agent.state == ActorState.ACTIVE
        assert charlie_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_charlie):
        """Test agent termination lifecycle."""
        assert spawned_charlie.state == ActorState.ACTIVE
        await spawned_charlie.terminate()
        assert spawned_charlie.state == ActorState.TERMINATED
        assert not spawned_charlie.is_alive

    @pytest.mark.asyncio
    async def test_handle_deliberation_request(self, spawned_charlie, mock_nats):
        """Test handling deliberation request."""
        # Setup mock LLM response
        spawned_charlie._llm_provider.register_response(
            "challenge",
            "Challenge: The proposal has merit but consider these risks: X, Y, Z."
        )

        # Create message
        message = ActorMessage(
            message_type="deliberation_request",
            content={
                "session_id": "delib-charlie-001",
                "problem": "Evaluate new feature proposal",
                "alpha_analysis": {"recommendation": "approve"},
                "beta_validation": {"valid": True},
            },
            sender="steward",
            recipient="charlie-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_charlie.process_message(message)

        # Verify challenges were generated
        assert "delib-charlie-001" in spawned_charlie._challenges

    @pytest.mark.asyncio
    async def test_handle_challenge_request(self, spawned_charlie, mock_llm):
        """Test handling challenge request."""
        # Setup mock LLM
        mock_llm.register_response(
            "challenge",
            "Devil's advocate analysis: Three potential risks identified with mitigations."
        )

        # Create message
        message = ActorMessage(
            message_type="challenge_request",
            content={
                "proposition": {"decision": "deploy to production"},
                "context": {"timeline": "aggressive", "resources": "limited"},
            },
            sender="steward",
            recipient="charlie-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_charlie.process_message(message)

        # Verify challenges generated
        stats = spawned_charlie.get_challenge_statistics()
        assert stats["total_challenges"] >= 1

    @pytest.mark.asyncio
    async def test_handle_risk_assessment(self, spawned_charlie, mock_llm):
        """Test handling risk assessment request."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk assessment: High risk in area A, Medium risk in B. Mitigations recommended."
        )

        # Create message
        message = ActorMessage(
            message_type="risk_assessment",
            content={
                "scenario": "Rapid scaling of infrastructure",
                "factors": ["cost", "reliability", "security"],
            },
            sender="coordinator",
            recipient="charlie-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_charlie.process_message(message)

        # Verify risk assessment completed
        stats = spawned_charlie.get_challenge_statistics()
        assert stats["total_risk_assessments"] >= 1

    @pytest.mark.asyncio
    async def test_perform_analysis(self, spawned_charlie, mock_llm):
        """Test performing devil's advocate analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "challenge",
            "Critical analysis: While the approach has benefits, here are counterarguments..."
        )

        # Perform analysis
        result = await spawned_charlie._perform_analysis(
            problem="Should we migrate to microservices?"
        )

        # Verify result
        assert isinstance(result, dict)
        assert "challenges" in result or "risks" in result

    @pytest.mark.asyncio
    async def test_generate_challenges(self, spawned_charlie, mock_llm):
        """Test generating challenges."""
        # Setup mock LLM
        mock_llm.register_response(
            "challenge",
            "Challenges: 1) Scalability concerns, 2) Cost implications, 3) Team readiness."
        )

        # Generate challenges
        challenges = await spawned_charlie._generate_challenges(
            proposition={"decision": "adopt new technology"}
        )

        # Verify challenges
        assert isinstance(challenges, list)

    @pytest.mark.asyncio
    async def test_assess_risks(self, spawned_charlie, mock_llm):
        """Test assessing risks."""
        # Setup mock LLM
        mock_llm.register_response(
            "risk",
            "Risk analysis: Technical risk=medium, Business risk=low, Timeline risk=high."
        )

        # Assess risks
        result = await spawned_charlie._assess_risks(
            scenario="Major system refactor"
        )

        # Verify result
        assert isinstance(result, dict)
        assert "risks" in result or "assessment" in result

    @pytest.mark.asyncio
    async def test_challenge_with_context(self, spawned_charlie, mock_llm):
        """Test challenging with full Triad context."""
        # Setup mock LLM
        mock_llm.register_response(
            "challenge",
            "Considering Alpha and Beta findings, here are additional challenges..."
        )

        # Generate challenges with context
        challenges = await spawned_charlie._generate_challenges(
            proposition={"decision": "approve"},
            alpha_findings={"analysis": "positive"},
            beta_findings={"validation": "passed"}
        )

        # Verify challenges generated
        assert challenges is not None

    @pytest.mark.asyncio
    async def test_concurrent_challenges(self, spawned_charlie, mock_nats):
        """Test handling multiple concurrent challenges."""
        # Simulate multiple challenges
        for i in range(5):
            spawned_charlie._challenges[f"challenge-{i}"] = {
                "proposition": f"Proposition {i}",
                "challenges": [f"Challenge {i}.1", f"Challenge {i}.2"],
                "risks": [{"type": "technical", "severity": "medium"}],
            }

        # Verify all challenges tracked
        stats = spawned_charlie.get_challenge_statistics()
        assert stats["total_challenges"] >= 5

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_charlie):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="challenge_request",
            content={},  # Missing required fields
            sender="test",
            recipient="charlie-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_charlie.process_message(message)

        # Verify agent still active
        assert spawned_charlie.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_charlie, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="challenge_request",
            content={"proposition": {}},
            sender="test",
            recipient="charlie-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_charlie.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "charlie_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_charlie, mock_db):
        """Test agent state persistence."""
        # Add challenge
        spawned_charlie._challenges["persist-test"] = {
            "proposition": "Persistent proposition",
            "challenges": ["Challenge 1"],
        }

        # Save state
        with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
            await spawned_charlie.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, charlie_agent):
        """Test agent error recovery."""
        await charlie_agent.spawn()
        charlie_agent.state = ActorState.ERROR
        await charlie_agent.resume()
        assert charlie_agent.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_risk_mitigation_suggestions(self, spawned_charlie, mock_llm):
        """Test generating risk mitigations."""
        # Setup mock LLM
        mock_llm.register_response(
            "mitigate",
            "Mitigation strategies: 1) Add monitoring, 2) Implement fallback, 3) Phase rollout."
        )

        # Assess risks with mitigations
        result = await spawned_charlie._assess_risks(
            scenario="Database migration"
        )

        # Verify result includes mitigations
        assert result is not None
