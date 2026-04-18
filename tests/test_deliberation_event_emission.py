"""
Tests for deliberation event emission from triad handlers and MAKER consensus.

Verifies that SwarmEvents are emitted for deliberation phases and consensus
completion without blocking the primary logic flow.

Reference: M011/S01/T03-PLAN.md
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestTriadEventEmission:
    """Test event emission from triad agent handlers."""

    @pytest.fixture
    def mock_publisher(self):
        """Create a mock NATS publisher."""
        publisher = MagicMock()
        publisher.emit_agent_event = AsyncMock(return_value=True)
        return publisher

    @pytest.fixture
    def timestamp(self):
        """Create a test timestamp."""
        return datetime.now(UTC).isoformat()

    @pytest.mark.asyncio
    async def test_steward_emits_deliberation_request_event(self, mock_publisher, timestamp):
        """
        Test that StewardAgent emits 'deliberation.request' event when starting deliberation.
        """
        from heretek_swarm.actors.triad.agent import StewardAgent, _emit_agent_event

        agent = StewardAgent()

        # Mock get_nats_publisher to return our mock
        with patch("heretek_swarm.actors.triad.agent.get_nats_publisher", return_value=mock_publisher):
            with patch("heretek_swarm.actors.triad.agent._emit_agent_event") as mock_emit:
                # Simulate deliberation start
                from heretek_swarm.actors.base import ActorMessage
                message = ActorMessage(
                    sender="test-sender",
                    message_type="start_deliberation",
                    content={
                        "deliberation_id": "test-del-001",
                        "topic": "test-domain",
                        "triad_members": ["alpha", "beta", "charlie"],
                    },
                    timestamp=timestamp,
                    correlation_id="test-corr",
                )

                # Call the handler
                await agent._handle_start_deliberation(message)

                # Verify the event was emitted
                mock_emit.assert_called_once()
                call_kwargs = mock_emit.call_args
                assert call_kwargs.kwargs["agent_id"] == "steward"
                assert call_kwargs.kwargs["event_type"] == "deliberation.request"
                assert call_kwargs.kwargs["payload"]["consensus_id"] == "test-del-001"
                assert call_kwargs.kwargs["payload"]["domain"] == "test-domain"

    @pytest.mark.asyncio
    async def test_alpha_emits_deliberation_vote_event(self, mock_publisher, timestamp):
        """
        Test that AlphaAgent emits 'deliberation.vote' event when submitting vote.
        """
        from heretek_swarm.actors.triad.agent import AlphaAgent

        agent = AlphaAgent()

        # Mock the _perform_analysis to return quickly
        agent._perform_analysis = AsyncMock(return_value={
            "decision": "alpha-decision",
            "confidence": 0.85,
            "reasoning": "test-reasoning",
        })

        # Mock send and event emission
        agent.send = AsyncMock()
        with patch("heretek_swarm.actors.triad.agent._emit_agent_event") as mock_emit:
            from heretek_swarm.actors.base import ActorMessage
            message = ActorMessage(
                sender="steward",
                message_type="deliberation_request",
                content={
                    "deliberation_id": "test-del-002",
                    "topic": "test-topic",
                },
                timestamp=timestamp,
                correlation_id="test-corr",
            )

            await agent._handle_deliberation_request(message)

            # Verify vote event was emitted
            mock_emit.assert_called_once()
            call_kwargs = mock_emit.call_args
            # Use agent's actual agent_id, not hardcoded string
            assert call_kwargs.kwargs["agent_id"] == agent.agent_id
            assert call_kwargs.kwargs["event_type"] == "deliberation.vote"
            assert call_kwargs.kwargs["payload"]["consensus_id"] == "test-del-002"
            assert call_kwargs.kwargs["payload"]["decision"] == "alpha-decision"

    @pytest.mark.asyncio
    async def test_beta_emits_deliberation_vote_event(self, mock_publisher, timestamp):
        """
        Test that BetaAgent emits 'deliberation.vote' event when submitting vote.
        """
        from heretek_swarm.actors.triad.agent import BetaAgent

        agent = BetaAgent()

        # Mock the _perform_analysis
        agent._perform_analysis = AsyncMock(return_value={
            "decision": "beta-decision",
            "confidence": 0.80,
            "reasoning": "beta-reasoning",
        })

        agent.send = AsyncMock()
        with patch("heretek_swarm.actors.triad.agent._emit_agent_event") as mock_emit:
            from heretek_swarm.actors.base import ActorMessage
            message = ActorMessage(
                sender="steward",
                message_type="deliberation_request",
                content={
                    "deliberation_id": "test-del-003",
                    "topic": "test-topic",
                },
                timestamp=timestamp,
                correlation_id="test-corr",
            )

            await agent._handle_deliberation_request(message)

            # Verify vote event was emitted
            mock_emit.assert_called_once()
            call_kwargs = mock_emit.call_args
            # Use agent's actual agent_id
            assert call_kwargs.kwargs["agent_id"] == agent.agent_id
            assert call_kwargs.kwargs["event_type"] == "deliberation.vote"
            assert call_kwargs.kwargs["payload"]["consensus_id"] == "test-del-003"

    @pytest.mark.asyncio
    async def test_charlie_emits_deliberation_challenge_event(self, mock_publisher, timestamp):
        """
        Test that CharlieAgent emits 'deliberation.challenge' event when providing third perspective.
        """
        from heretek_swarm.actors.triad.agent import CharlieAgent

        agent = CharlieAgent()

        # Mock the _perform_analysis
        agent._perform_analysis = AsyncMock(return_value={
            "decision": "charlie-decision",
            "confidence": 0.75,
            "reasoning": "charlie-reasoning",
            "challenges": ["risk-1", "risk-2"],
        })

        agent.send = AsyncMock()
        with patch("heretek_swarm.actors.triad.agent._emit_agent_event") as mock_emit:
            from heretek_swarm.actors.base import ActorMessage
            message = ActorMessage(
                sender="steward",
                message_type="deliberation_request",
                content={
                    "deliberation_id": "test-del-004",
                    "topic": "test-topic",
                },
                timestamp=timestamp,
                correlation_id="test-corr",
            )

            await agent._handle_deliberation_request(message)

            # Verify challenge event was emitted
            mock_emit.assert_called_once()
            call_kwargs = mock_emit.call_args
            # Use agent's actual agent_id
            assert call_kwargs.kwargs["agent_id"] == agent.agent_id
            assert call_kwargs.kwargs["event_type"] == "deliberation.challenge"
            assert call_kwargs.kwargs["payload"]["consensus_id"] == "test-del-004"
            assert "risk-1" in call_kwargs.kwargs["payload"]["challenges"]


class TestMAKERConsensusEventEmission:
    """Test consensus result event emission from MAKER enhanced."""

    @pytest.fixture
    def mock_publisher(self):
        """Create a mock NATS publisher."""
        publisher = MagicMock()
        publisher.emit_agent_event = AsyncMock(return_value=True)
        return publisher

    @pytest.mark.asyncio
    async def test_consensus_result_emitted_on_completion(self, mock_publisher):
        """
        Test that 'consensus.result' event is emitted when consensus is computed.
        """
        from heretek_swarm.consensus.maker_enhanced import EnhancedMAKERConsensus, _emit_consensus_result

        consensus = EnhancedMAKERConsensus()

        # Set up consensus with some votes
        consensus.start_consensus("test-consensus-001", proposal="test proposal")

        # Add some votes
        consensus.add_vote("test-consensus-001", "alpha", "approve", 0.9)
        consensus.add_vote("test-consensus-001", "beta", "approve", 0.8)
        consensus.add_vote("test-consensus-001", "charlie", "approve", 0.85)

        with patch("heretek_swarm.consensus.maker_enhanced._emit_consensus_result") as mock_emit:
            # Mock super().compute_consensus to return a result
            mock_result = MagicMock()
            mock_result.decision = "approve"
            mock_result.confidence = 0.85
            mock_result.votes = {"approve": 3}

            with patch.object(
                consensus.__class__.__bases__[0],
                "compute_consensus",
                return_value=mock_result
            ):
                result = consensus.compute_consensus("test-consensus-001")

                # Verify consensus result event was emitted
                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                # First positional arg is result, second is consensus_id
                assert call_args[0][0] is mock_result
                assert call_args[0][1] == "test-consensus-001"

    @pytest.mark.asyncio
    async def test_event_emission_is_fire_and_forget(self):
        """
        Test that event emission doesn't block consensus computation.
        """
        from heretek_swarm.consensus.maker_enhanced import _emit_consensus_result

        # Create a mock result
        mock_result = MagicMock()
        mock_result.decision = "test-decision"
        mock_result.confidence = 0.9

        # Track timing
        start_time = asyncio.get_event_loop().time()

        # Call the emission function
        await _emit_consensus_result(mock_result, "test-id")

        # The function should return quickly (fire-and-forget)
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time

        # Should complete in under 100ms (no actual network call)
        assert elapsed < 0.1, f"Event emission took too long: {elapsed}s"


class TestEventEmissionFailureHandling:
    """Test that event emission failures don't crash agents/consensus."""

    @pytest.fixture
    def timestamp(self):
        """Create a test timestamp."""
        return datetime.now(UTC).isoformat()

    @pytest.mark.asyncio
    async def test_steward_handles_emission_failure_gracefully(self, timestamp):
        """Test that Steward continues normally even if NATS emission fails."""
        from heretek_swarm.actors.triad.agent import StewardAgent

        agent = StewardAgent()

        # Mock get_nats_publisher to raise an exception
        with patch(
            "heretek_swarm.actors.triad.agent.get_nats_publisher",
            side_effect=Exception("NATS unavailable")
        ):
            from heretek_swarm.actors.base import ActorMessage
            message = ActorMessage(
                sender="test-sender",
                message_type="start_deliberation",
                content={
                    "deliberation_id": "test-del-005",
                    "topic": "test-domain",
                    "triad_members": ["alpha"],
                },
                timestamp=timestamp,
                correlation_id="test-corr",
            )

            # Should not raise
            try:
                await agent._handle_start_deliberation(message)
            except Exception as e:
                pytest.fail(f"Agent raised exception on emission failure: {e}")

    @pytest.mark.asyncio
    async def test_alpha_handles_emission_failure_gracefully(self, timestamp):
        """Test that Alpha continues normally even if NATS emission fails."""
        from heretek_swarm.actors.triad.agent import AlphaAgent

        agent = AlphaAgent()

        # Mock _perform_analysis to return quickly
        agent._perform_analysis = AsyncMock(return_value={
            "decision": "test-decision",
            "confidence": 0.9,
            "reasoning": "test",
        })

        # Mock get_nats_publisher to raise
        with patch(
            "heretek_swarm.actors.triad.agent.get_nats_publisher",
            side_effect=Exception("NATS unavailable")
        ):
            from heretek_swarm.actors.base import ActorMessage
            message = ActorMessage(
                sender="steward",
                message_type="deliberation_request",
                content={
                    "deliberation_id": "test-del-006",
                    "topic": "test-topic",
                },
                timestamp=timestamp,
                correlation_id="test-corr",
            )

            # Should not raise
            try:
                await agent._handle_deliberation_request(message)
            except Exception as e:
                pytest.fail(f"Agent raised exception on emission failure: {e}")


# =============================================================================
# Test Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])