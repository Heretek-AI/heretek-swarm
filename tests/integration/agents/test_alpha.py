"""
Integration tests for AlphaAgent.

Tier 1 (Core Triad) - AlphaAgent performs primary analysis and decision-making.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import from same path as the module under test to avoid enum identity issues
from heretek_swarm.actors.triad import AlphaAgent
from heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestAlphaAgentIntegration:
    """Integration tests for AlphaAgent."""

    @pytest_asyncio.fixture
    async def alpha_agent(self, mock_nats, mock_llm):
        """Create AlphaAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                agent = AlphaAgent(agent_id="alpha-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_alpha(self, alpha_agent):
        """Create and spawn AlphaAgent."""
        await alpha_agent.spawn()
        yield alpha_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, alpha_agent):
        """Test agent spawning lifecycle."""
        assert alpha_agent.state == ActorState.SPAWNING
        await alpha_agent.spawn()
        assert alpha_agent.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_alpha):
        """Test agent termination lifecycle."""
        assert spawned_alpha.state == ActorState.ACTIVE
        await spawned_alpha.terminate()
        assert spawned_alpha.state == ActorState.TERMINATED