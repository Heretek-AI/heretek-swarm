"""
Integration tests for AlphaAgent.

Tier 1 (Core Triad) - AlphaAgent performs primary analysis and decision-making.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch

# Import from same path as the module under test to avoid enum identity issues
from heretek_swarm.actors.triad import AlphaAgent
from heretek_swarm.actors.base import ActorState


_pytestmark = pytest.mark.integration


class TestAlphaAgentIntegration:
    """Integration tests for AlphaAgent."""

    @pytest_asyncio.fixture
    async def alpha_agent(self, _mock_nats, _mock_llm):
        """Create AlphaAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                _agent = AlphaAgent(agent_id="alpha-test-001")
                yield agent
                if agent.state != ActorState.TERMINATED:
                    await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_alpha(self, _alpha_agent):
        """Create and spawn AlphaAgent."""
        await alpha_agent.spawn()
        yield alpha_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, _alpha_agent):
        """Test agent spawning lifecycle."""
        assert alpha_agent.state == ActorState.SPAWNING
        await alpha_agent.spawn()
        assert alpha_agent.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_agent_terminate(self, _spawned_alpha):
        """Test agent termination lifecycle."""
        assert spawned_alpha.state == ActorState.ACTIVE
        await spawned_alpha.terminate()
        assert spawned_alpha.state == ActorState.TERMINATED