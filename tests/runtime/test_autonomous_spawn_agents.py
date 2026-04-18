"""
Integration tests for AutonomousSwarm agent spawning.

Tests that all 23 agents are spawned correctly during initialization.
Validates the spawn count and agent IDs match expectations.

Reference: M010/S01 - AutonomousSwarm.initialize() spawns all agents
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.supervisor import ActorSupervisor


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_channel_registry():
    """Create mock channel registry."""
    registry = MagicMock()
    registry.get_subscriptions.return_value = []
    registry.get_nats_subject.return_value = "test.subject"
    registry.record_message.return_value = None
    registry.record_error.return_value = None
    return registry


@pytest.fixture
def mock_group_registry():
    """Create mock group registry."""
    registry = MagicMock()
    return registry


@pytest.fixture
def mock_memory():
    """Create mock dual-tier memory."""
    memory = MagicMock()
    memory.initialize = AsyncMock()
    memory.run_maintenance = AsyncMock()
    return memory


@pytest.fixture
def mock_rag():
    """Create mock RAG pipeline."""
    rag = MagicMock()
    rag.shutdown = AsyncMock()
    return rag


@pytest.fixture
def mock_consensus():
    """Create mock MAKER consensus engine."""
    consensus = MagicMock()
    return consensus


@pytest.fixture
def mock_event_mesh():
    """Create mock NATS event mesh with JetStream."""
    mesh = MagicMock()
    mesh.connect = AsyncMock()
    mesh.disconnect = AsyncMock()
    mesh.initialize_jetstream = AsyncMock(return_value=True)
    mesh.publish = AsyncMock()
    mesh.subscribe = AsyncMock()
    return mesh


@pytest.fixture
def mock_mcp_tools():
    """Create mock MCP tools."""
    tools = MagicMock()
    tools.get_registry.return_value = MagicMock(list_tools=MagicMock(return_value=[]))
    return tools


@pytest.fixture
def mock_supervisor():
    """Create mock actor supervisor with spawn tracking."""
    supervisor = MagicMock()
    supervisor.actors = {}
    supervisor.spawn_actor = AsyncMock()
    supervisor.terminate_all = AsyncMock()
    supervisor.terminate_actor = AsyncMock()
    supervisor.restart_actor = AsyncMock()
    supervisor.terminate = AsyncMock()
    return supervisor


@pytest.fixture
def swarm_config():
    """Create test configuration for autonomous swarm."""
    return {
        "nats_servers": ["nats://localhost:4222"],
        "health_check_interval": 30,
        "loop_interval": 1,
        "consciousness_interval": 5,
        "memory_maintenance_interval": 300,
        "scaling_interval": 60,
        "ephemeral": {"ttl_seconds": 3600},
        "persistent": {
            "connection_string": "postgresql://test:test@localhost/test_db",
        },
        "rag": {
            "embedding_provider": "openai",
            "collection_name": "test_documents",
        },
        "consensus": {
            "ahead_by_k": 2,
            "min_votes": 3,
            "red_flag_threshold": 0.3,
        },
    }


@pytest.fixture
async def swarm_with_mocks(
    swarm_config,
    mock_supervisor,
    mock_channel_registry,
    mock_group_registry,
    mock_memory,
    mock_rag,
    mock_consensus,
    mock_event_mesh,
    mock_mcp_tools,
):
    """
    Create AutonomousSwarm instance with all initialization components mocked.
    
    This fixture patches the module-level imports and sets up all dependencies
    so that initialize() can be called without connecting to real services.
    """
    from heretek_swarm.runtime.main_loop import AutonomousSwarm

    swarm = AutonomousSwarm(config=swarm_config)

    # Set mocked components directly (bypassing initialization)
    swarm.supervisor = mock_supervisor
    swarm.channel_registry = mock_channel_registry
    swarm.group_registry = mock_group_registry
    swarm.memory = mock_memory
    swarm.rag = mock_rag
    swarm.consensus = mock_consensus
    swarm.event_mesh = mock_event_mesh
    swarm.mcp_tools = mock_mcp_tools

    yield swarm


# ============================================================================
# Test Cases
# ============================================================================


class TestAutonomousSwarmSpawnAgents:
    """Test AutonomousSwarm agent spawning functionality."""

    @pytest.mark.asyncio
    async def test_initialize_spawns_all_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that initialize() spawns exactly 23 agents."""
        # Call _spawn_all_actors directly (components already mocked)
        await swarm_with_mocks._spawn_all_actors()

        # Verify spawn_actor was called exactly 23 times (matching the actors list)
        assert mock_supervisor.spawn_actor.call_count == 23, (
            f"Expected 23 spawn_actor calls, got {mock_supervisor.spawn_actor.call_count}"
        )

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier1_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 1 Core Triad agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        # Get all agent IDs passed to spawn_actor
        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [
            call_args[0][1]  # (actor_class, agent_id, ...)
            for call_args in call_args_list
        ]

        # Verify Tier 1 agents
        tier1_agents = ["steward", "alpha", "beta", "charlie"]
        for agent_id in tier1_agents:
            assert agent_id in spawned_ids, f"Tier 1 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier2_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 2 Support agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # Verify Tier 2 agents
        tier2_agents = ["historian", "metis", "empath", "perceiver", "echo"]
        for agent_id in tier2_agents:
            assert agent_id in spawned_ids, f"Tier 2 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier3_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 3 Exploration agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # Verify Tier 3 agents
        tier3_agents = ["explorer", "examiner", "dreamer", "coder"]
        for agent_id in tier3_agents:
            assert agent_id in spawned_ids, f"Tier 3 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier4_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 4 Safety agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # Verify Tier 4 agents
        tier4_agents = ["sentinel", "sentinel-prime", "arbiter"]
        for agent_id in tier4_agents:
            assert agent_id in spawned_ids, f"Tier 4 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier5_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 5 Coordination agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # Verify Tier 5 agents
        tier5_agents = ["coordinator", "nexus", "catalyst", "chronos"]
        for agent_id in tier5_agents:
            assert agent_id in spawned_ids, f"Tier 5 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_initialize_spawns_tier6_agents(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that Tier 6 Enhancement agents are spawned."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # Verify Tier 6 agents
        tier6_agents = ["prism", "habit-forge", "perceiver-plus"]
        for agent_id in tier6_agents:
            assert agent_id in spawned_ids, f"Tier 6 agent {agent_id} not spawned"

    @pytest.mark.asyncio
    async def test_all_23_agents_spawned(self, swarm_with_mocks, mock_supervisor):
        """Comprehensive test that all 23 agents are spawned with correct IDs."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list
        spawned_ids = [call_args[0][1] for call_args in call_args_list]

        # All expected agent IDs (23 total)
        expected_agents = [
            # Tier 1: Core Triad (4)
            "steward",
            "alpha",
            "beta",
            "charlie",
            # Tier 2: Support (5)
            "historian",
            "metis",
            "empath",
            "perceiver",
            "echo",
            # Tier 3: Exploration (4)
            "explorer",
            "examiner",
            "dreamer",
            "coder",
            # Tier 4: Safety (3)
            "sentinel",
            "sentinel-prime",
            "arbiter",
            # Tier 5: Coordination (4)
            "coordinator",
            "nexus",
            "catalyst",
            "chronos",
            # Tier 6: Enhancement (3)
            "prism",
            "habit-forge",
            "perceiver-plus",
        ]

        # Verify count
        assert len(spawned_ids) == 23, f"Expected 23 agents, got {len(spawned_ids)}"

        # Verify each expected agent is present
        missing_agents = set(expected_agents) - set(spawned_ids)
        assert not missing_agents, f"Missing agents: {missing_agents}"

        # Verify no duplicates
        duplicates = [aid for aid in spawned_ids if spawned_ids.count(aid) > 1]
        assert not duplicates, f"Duplicate agents found: {duplicates}"

    @pytest.mark.asyncio
    async def test_spawn_actor_receives_correct_agent_classes(
        self, swarm_with_mocks, mock_supervisor
    ):
        """Test that spawn_actor is called with correct actor classes."""
        await swarm_with_mocks._spawn_all_actors()

        call_args_list = mock_supervisor.spawn_actor.call_args_list

        # Create mapping of agent_id to actor class
        agent_id_to_class = {}
        for call_args in call_args_list:
            actor_class = call_args[0][0]
            agent_id = call_args[0][1]
            agent_id_to_class[agent_id] = actor_class

        # Verify key agents have correct classes
        from heretek_swarm.actors.triad import StewardAgent, AlphaAgent
        from heretek_swarm.actors.historian import HistorianAgent
        from heretek_swarm.actors.sentinel import SentinelAgent

        assert agent_id_to_class["steward"] == StewardAgent
        assert agent_id_to_class["alpha"] == AlphaAgent
        assert agent_id_to_class["historian"] == HistorianAgent
        assert agent_id_to_class["sentinel"] == SentinelAgent

    @pytest.mark.asyncio
    async def test_get_tier_returns_correct_tier(self, swarm_with_mocks):
        """Test that _get_tier returns correct tier names."""
        # Test a few agent IDs
        assert "Tier 1 (Core Triad)" == swarm_with_mocks._get_tier("steward")
        assert "Tier 2 (Support)" == swarm_with_mocks._get_tier("historian")
        assert "Tier 3 (Exploration)" == swarm_with_mocks._get_tier("explorer")
        assert "Tier 4 (Safety)" == swarm_with_mocks._get_tier("sentinel")
        assert "Tier 5 (Coordination)" == swarm_with_mocks._get_tier("coordinator")
        assert "Tier 6 (Enhancement)" == swarm_with_mocks._get_tier("prism")

    @pytest.mark.asyncio
    async def test_spawn_continues_on_failure(
        self, swarm_config, mock_supervisor
    ):
        """Test that spawning continues even if one agent fails to spawn."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        # Make first spawn call raise an error, rest succeed
        call_count = 0

        async def spawn_that_fails_once(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated spawn failure")
            return MagicMock()

        mock_supervisor.spawn_actor = spawn_that_fails_once

        swarm = AutonomousSwarm(config=swarm_config)
        swarm.supervisor = mock_supervisor

        # Should not raise - should continue on failure
        await swarm._spawn_all_actors()

        # All 23 agents should have been attempted (first failed, remaining 22 succeeded)
        assert call_count == 23, f"Expected 23 spawn attempts, got {call_count}"
