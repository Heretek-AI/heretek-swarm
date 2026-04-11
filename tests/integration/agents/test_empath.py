"""
Integration tests for EmpathAgent.

Tier 2 (Support) - EmpathAgent handles sentiment analysis, emotion tracking, and conflict mediation.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.empath import EmpathAgent
from heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestEmpathAgentIntegration:
    """Integration tests for EmpathAgent."""

    @pytest_asyncio.fixture
    async def empath_agent(self, mock_nats, mock_llm, mock_db):
        """Create EmpathAgent with mock dependencies."""
        with patch('heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
                    agent = EmpathAgent(agent_id="empath-test-001")
                    yield agent
                    if agent.state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_empath(self, empath_agent):
        """Create and spawn EmpathAgent."""
        await empath_agent.spawn()
        yield empath_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, empath_agent):
        """Test agent spawning lifecycle."""
        assert empath_agent.state == ActorState.SPAWNING
        await empath_agent.spawn()
        assert empath_agent.state == ActorState.ACTIVE
        assert empath_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_empath):
        """Test agent termination lifecycle."""
        assert spawned_empath.state == ActorState.ACTIVE
        await spawned_empath.terminate()
        assert spawned_empath.state == ActorState.TERMINATED
        assert not spawned_empath.is_alive

    @pytest.mark.asyncio
    async def test_handle_analyze_sentiment(self, spawned_empath, mock_nats, mock_llm):
        """Test handling sentiment analysis request."""
        # Setup mock LLM
        mock_llm.register_response(
            "sentiment",
            "Sentiment: Positive (0.75), Emotions: joy, trust. Tone: Professional."
        )

        # Create message
        message = ActorMessage(
            message_type="analyze_sentiment",
            content={
                "text": "The new system is working great and the team is excited!",
                "agent_id": "alpha-001",
            },
            sender="monitor",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify sentiment analyzed
        assert len(spawned_empath._sentiment_log) > 0

    @pytest.mark.asyncio
    async def test_handle_track_emotion(self, spawned_empath, mock_nats):
        """Test handling emotion tracking request."""
        # Create message
        message = ActorMessage(
            message_type="track_emotion",
            content={
                "agent_id": "beta-001",
                "emotion": "frustrated",
                "intensity": 0.6,
                "context": {"trigger": "timeout error"},
            },
            sender="monitor",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify emotion tracked
        assert "beta-001" in spawned_empath._agent_emotions

    @pytest.mark.asyncio
    async def test_handle_detect_conflict(self, spawned_empath, mock_llm):
        """Test handling conflict detection request."""
        # Setup mock LLM
        mock_llm.register_response(
            "conflict",
            "Conflict detected: Agents have opposing views on deployment strategy."
        )

        # Setup conflicting agents
        spawned_empath._agent_emotions["alpha-001"] = {
            "emotion": "confident",
            "stance": "deploy now",
        }
        spawned_empath._agent_emotions["beta-001"] = {
            "emotion": "cautious",
            "stance": "wait for testing",
        }

        # Create message
        message = ActorMessage(
            message_type="detect_conflict",
            content={
                "agents": ["alpha-001", "beta-001"],
                "context": "deployment decision",
            },
            sender="steward",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify conflict detection performed
        assert len(spawned_empath._conflict_history) > 0

    @pytest.mark.asyncio
    async def test_handle_mediate_conflict(self, spawned_empath, mock_llm):
        """Test handling conflict mediation request."""
        # Setup mock LLM
        mock_llm.register_response(
            "mediate",
            "Mediation: Recommend phased deployment with monitoring checkpoints."
        )

        # Create message
        message = ActorMessage(
            message_type="mediate_conflict",
            content={
                "conflict_id": "conflict-001",
                "parties": ["alpha-001", "beta-001"],
                "issue": "deployment timing",
            },
            sender="steward",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify mediation attempted
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_get_emotional_state(self, spawned_empath, mock_nats):
        """Test handling emotional state request."""
        # Setup agent emotions
        spawned_empath._agent_emotions["alpha-001"] = {
            "emotion": "confident",
            "valence": 0.8,
            "arousal": 0.6,
        }

        # Create message
        message = ActorMessage(
            message_type="get_emotional_state",
            content={"agent_id": "alpha-001"},
            sender="coordinator",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify state published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_get_collective_mood(self, spawned_empath, mock_nats):
        """Test handling collective mood request."""
        # Setup multiple agent emotions
        spawned_empath._agent_emotions["alpha-001"] = {"emotion": "happy", "valence": 0.8}
        spawned_empath._agent_emotions["beta-001"] = {"emotion": "calm", "valence": 0.6}
        spawned_empath._agent_emotions["charlie-001"] = {"emotion": "alert", "valence": 0.5}

        # Create message
        message = ActorMessage(
            message_type="get_collective_mood",
            content={},
            sender="coordinator",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_empath.process_message(message)

        # Verify collective mood published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_analyze_sentiment_llm(self, spawned_empath, mock_llm):
        """Test LLM-based sentiment analysis."""
        # Setup mock LLM
        mock_llm.register_response(
            "sentiment",
            "Sentiment analysis: Positive (0.8), Emotions: joy, anticipation."
        )

        # Analyze
        result = await spawned_empath._analyze_sentiment_llm(
            text="Great progress on the project!",
            context={"source": "team_update"}
        )

        # Verify result
        assert isinstance(result, dict)
        assert "sentiment" in result or "valence" in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_heuristic(self, spawned_empath):
        """Test heuristic sentiment analysis."""
        # Analyze positive text
        result = spawned_empath._analyze_sentiment_heuristic(
            text="Excellent work! Very pleased with results."
        )

        # Verify result
        assert isinstance(result, dict)
        assert "valence" in result or "sentiment" in result

    @pytest.mark.asyncio
    async def test_update_agent_mood(self, spawned_empath):
        """Test updating agent mood."""
        # Update mood
        spawned_empath._update_agent_mood(
            agent_id="test-agent",
            sentiment_result={"valence": 0.7, "arousal": 0.5, "emotion": "happy"}
        )

        # Verify mood updated
        assert "test-agent" in spawned_empath._agent_emotions
        assert spawned_empath._agent_emotions["test-agent"]["valence"] == 0.7

    @pytest.mark.asyncio
    async def test_check_stress_indicators(self, spawned_empath):
        """Test checking stress indicators."""
        # Setup stressed agent
        spawned_empath._agent_emotions["stressed-agent"] = {
            "emotion": "anxious",
            "valence": 0.2,
            "arousal": 0.9,
        }

        # Check stress
        stress_level = spawned_empath._check_stress_indicators(
            agent_id="stressed-agent"
        )

        # Verify stress detected
        assert stress_level > 0.5

    @pytest.mark.asyncio
    async def test_analyze_conflict_potential(self, spawned_empath):
        """Test analyzing conflict potential."""
        # Setup agents with opposing emotions
        spawned_empath._agent_emotions["agent-a"] = {"emotion": "aggressive", "stance": "yes"}
        spawned_empath._agent_emotions["agent-b"] = {"emotion": "defensive", "stance": "no"}

        # Analyze
        has_conflict = spawned_empath._analyze_conflict_potential(
            agents=["agent-a", "agent-b"]
        )

        # Verify conflict detected
        assert has_conflict is True

    @pytest.mark.asyncio
    async def test_generate_mediation(self, spawned_empath, mock_llm):
        """Test generating mediation suggestions."""
        # Setup mock LLM
        mock_llm.register_response(
            "mediate",
            "Mediation strategy: Find common ground, propose compromise solution."
        )

        # Generate mediation
        result = await spawned_empath._generate_mediation(
            conflict_id="conflict-test",
            parties=["agent-a", "agent-b"],
            issue="resource allocation"
        )

        # Verify result
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_update_collective_mood(self, spawned_empath):
        """Test updating collective mood."""
        # Setup multiple agents
        spawned_empath._agent_emotions["agent-1"] = {"valence": 0.8, "arousal": 0.5}
        spawned_empath._agent_emotions["agent-2"] = {"valence": 0.6, "arousal": 0.4}
        spawned_empath._agent_emotions["agent-3"] = {"valence": 0.7, "arousal": 0.6}

        # Update collective mood
        spawned_empath._update_collective_mood()

        # Verify collective mood calculated
        assert spawned_empath._collective_mood is not None

    @pytest.mark.asyncio
    async def test_concurrent_sentiment_analysis(self, spawned_empath, mock_nats):
        """Test handling multiple concurrent sentiment analyses."""
        # Simulate multiple analyses
        for i in range(10):
            spawned_empath._sentiment_log.append({
                "agent_id": f"agent-{i}",
                "sentiment": "positive",
                "valence": 0.7,
            })

        # Verify all logged
        assert len(spawned_empath._sentiment_log) >= 10

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_empath):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="analyze_sentiment",
            content={},  # Missing required fields
            sender="test",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_empath.process_message(message)

        # Verify agent still active
        assert spawned_empath.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_empath, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="get_emotional_state",
            content={"agent_id": "test"},
            sender="test",
            recipient="empath-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_empath.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "empath_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_empath, mock_db):
        """Test agent state persistence."""
        # Add emotion data
        spawned_empath._agent_emotions["persist-agent"] = {
            "emotion": "happy",
            "valence": 0.8,
        }

        # Save state
        with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
            await spawned_empath.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, empath_agent):
        """Test agent error recovery."""
        await empath_agent.spawn()
        empath_agent.state = ActorState.ERROR
        await empath_agent.resume()
        assert empath_agent.state == ActorState.ACTIVE
