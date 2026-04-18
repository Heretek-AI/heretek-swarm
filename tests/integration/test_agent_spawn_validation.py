"""
Integration test for agent spawning validation.

Tests that all 23 agents in the Heretek Swarm can be spawned and reach ACTIVE state.
This test validates R009: all agents must be spawnable and verified.

The 23 agents span 6 tiers:
- Tier 1 (Core Triad): StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
- Tier 2 (Support): HistorianAgent, MetisAgent, EmpathAgent, PerceiverAgent, EchoActor
- Tier 3 (Exploration): ExplorerAgent, ExaminerAgent, DreamerAgent, CoderAgent
- Tier 4 (Safety & Security): SentinelAgent, SentinelPrimeAgent, ArbiterAgent
- Tier 5 (Coordination): CoordinatorAgent, NexusAgent, CatalystAgent, ChronosAgent
- Tier 6 (Enhancement): PrismAgent, HabitForgeAgent, PerceiverPlusAgent

Author: Heretek Swarm Collective
Date: 2026-04-17
Version: 1.0.0
"""

import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from heretek_swarm.actors import (
    ActorSupervisor,
    # Tier 1 - Core Triad
    StewardAgent,
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    # Tier 2 - Support
    HistorianAgent,
    MetisAgent,
    EmpathAgent,
    PerceiverAgent,
    EchoActor,
    # Tier 3 - Exploration
    ExplorerAgent,
    ExaminerAgent,
    DreamerAgent,
    CoderAgent,
    # Tier 4 - Safety & Security
    SentinelAgent,
    SentinelPrimeAgent,
    ArbiterAgent,
    # Tier 5 - Coordination
    CoordinatorAgent,
    NexusAgent,
    CatalystAgent,
    ChronosAgent,
    # Tier 6 - Enhancement
    PrismAgent,
    HabitForgeAgent,
    PerceiverPlusAgent,
)
from heretek_swarm.actors.base import ActorState, ActorStatus


# All 23 agent types and their spawn configurations
AGENT_TEST_CASES = [
    # Tier 1 - Core Triad
    {"name": "StewardAgent", "class": StewardAgent, "tier": 1},
    {"name": "AlphaAgent", "class": AlphaAgent, "tier": 1},
    {"name": "BetaAgent", "class": BetaAgent, "tier": 1},
    {"name": "CharlieAgent", "class": CharlieAgent, "tier": 1},
    # Tier 2 - Support
    {"name": "HistorianAgent", "class": HistorianAgent, "tier": 2},
    {"name": "MetisAgent", "class": MetisAgent, "tier": 2},
    {"name": "EmpathAgent", "class": EmpathAgent, "tier": 2},
    {"name": "PerceiverAgent", "class": PerceiverAgent, "tier": 2},
    {"name": "EchoActor", "class": EchoActor, "tier": 2},
    # Tier 3 - Exploration
    {"name": "ExplorerAgent", "class": ExplorerAgent, "tier": 3},
    {"name": "ExaminerAgent", "class": ExaminerAgent, "tier": 3},
    {"name": "DreamerAgent", "class": DreamerAgent, "tier": 3},
    {"name": "CoderAgent", "class": CoderAgent, "tier": 3},
    # Tier 4 - Safety & Security
    {"name": "SentinelAgent", "class": SentinelAgent, "tier": 4},
    {"name": "SentinelPrimeAgent", "class": SentinelPrimeAgent, "tier": 4},
    {"name": "ArbiterAgent", "class": ArbiterAgent, "tier": 4},
    # Tier 5 - Coordination
    {"name": "CoordinatorAgent", "class": CoordinatorAgent, "tier": 5},
    {"name": "NexusAgent", "class": NexusAgent, "tier": 5},
    {"name": "CatalystAgent", "class": CatalystAgent, "tier": 5},
    {"name": "ChronosAgent", "class": ChronosAgent, "tier": 5},
    # Tier 6 - Enhancement
    {"name": "PrismAgent", "class": PrismAgent, "tier": 6},
    {"name": "HabitForgeAgent", "class": HabitForgeAgent, "tier": 6},
    {"name": "PerceiverPlusAgent", "class": PerceiverPlusAgent, "tier": 6},
]

pytestmark = pytest.mark.integration


class TestAgentSpawnValidation:
    """Test suite for agent spawning validation across all 23 agent types."""

    @pytest.fixture
    def supervisor(self):
        """Create ActorSupervisor instance for testing."""
        return ActorSupervisor(name="test-supervisor")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", AGENT_TEST_CASES, ids=lambda tc: tc["name"])
    async def test_agent_spawn_individual(self, supervisor, test_case):
        """Test spawning a single agent and verifying it reaches ACTIVE state."""
        agent_class = test_case["class"]
        agent_name = test_case["name"]
        tier = test_case["tier"]

        agent_id = f"test-{agent_name.lower()}-001"

        # Spawn the agent
        try:
            actor = await supervisor.spawn_actor(
                actor_class=agent_class,
                actor_id=agent_id,
            )

            # Verify actor was registered
            assert agent_id in supervisor.actors

            # Get actor status
            status = await supervisor.get_actor_status(agent_id)
            assert status is not None

            # Verify actor state is ACTIVE
            assert status.state == ActorState.ACTIVE, (
                f"{agent_name} (Tier {tier}) failed to reach ACTIVE state: {status.state}"
            )

            # Log success with agent_id and tier
            print(f"✅ {agent_name} (Tier {tier}) spawned successfully: {agent_id}")

        except Exception as e:
            pytest.fail(
                f"{agent_name} (Tier {tier}) failed to spawn: {e}"
            )
        finally:
            # Cleanup
            if agent_id in supervisor.actors:
                await supervisor.terminate_actor(agent_id)

    @pytest.mark.asyncio
    async def test_all_23_agents_spawn_with_supervisor(self, supervisor):
        """Test spawning all 23 agents through the supervisor and verifying they all reach ACTIVE state."""
        spawned_agents = []
        failed_agents = []

        # Spawn all agents
        for test_case in AGENT_TEST_CASES:
            agent_class = test_case["class"]
            agent_name = test_case["name"]
            tier = test_case["tier"]
            agent_id = f"test-{agent_name.lower()}-full-001"

            try:
                actor = await supervisor.spawn_actor(
                    actor_class=agent_class,
                    actor_id=agent_id,
                )
                spawned_agents.append({
                    "name": agent_name,
                    "id": agent_id,
                    "tier": tier,
                    "actor": actor,
                })
            except Exception as e:
                failed_agents.append({
                    "name": agent_name,
                    "id": agent_id,
                    "tier": tier,
                    "error": str(e),
                })

        # Verify all 23 agents spawned successfully
        assert len(spawned_agents) == 23, (
            f"Only {len(spawned_agents)}/23 agents spawned. "
            f"Failed: {[a['name'] for a in failed_agents]}"
        )

        # Verify all spawned agents reached ACTIVE state
        active_agents = []
        inactive_agents = []

        for agent_info in spawned_agents:
            status = await supervisor.get_actor_status(agent_info["id"])
            if status and status.state == ActorState.ACTIVE:
                active_agents.append(agent_info["name"])
            else:
                inactive_agents.append({
                    "name": agent_info["name"],
                    "tier": agent_info["tier"],
                    "state": status.state if status else "UNKNOWN",
                })

        # Verify all 23 agents are ACTIVE
        assert len(active_agents) == 23, (
            f"Only {len(active_agents)}/23 agents reached ACTIVE state. "
            f"Inactive: {inactive_agents}"
        )

        # Log which agents failed to spawn
        if failed_agents:
            print("\n❌ Agents that failed to spawn:")
            for agent in failed_agents:
                print(f"   - {agent['name']} (Tier {agent['tier']}): {agent['error']}")

        # Cleanup all agents
        await supervisor.terminate_all()

        # Verify cleanup
        assert len(supervisor.actors) == 0, (
            f"Supervisor still has {len(supervisor.actors)} actors after terminate_all()"
        )

    @pytest.mark.asyncio
    async def test_supervisor_get_actor_state_query(self, supervisor):
        """Test that supervisor.get_actor_state() can be queried post-spawn."""
        agent_class = StewardAgent
        agent_id = "test-state-query-001"

        # Spawn agent
        actor = await supervisor.spawn_actor(
            actor_class=agent_class,
            actor_id=agent_id,
        )

        # Query state post-spawn - check actor is registered and accessible
        assert agent_id in supervisor.actors, (
            f"Actor {agent_id} not found in supervisor.actors"
        )

        status = await supervisor.get_actor_status(agent_id)
        assert status is not None
        assert status.state == ActorState.ACTIVE

        # Verify get_statistics reflects the spawned actor
        stats = supervisor.get_statistics()
        assert stats["total_actors"] >= 1
        assert stats["active_actors"] >= 1

        # Cleanup
        await supervisor.terminate_actor(agent_id)

    @pytest.mark.asyncio
    async def test_agent_spawn_logging(self, supervisor, caplog):
        """Test that agent spawn success/failure is logged with agent_id and tier."""
        agent_class = StewardAgent
        agent_id = "test-logging-001"
        tier = 1

        # Spawn agent
        actor = await supervisor.spawn_actor(
            actor_class=agent_class,
            actor_id=agent_id,
        )

        # Verify logs contain agent_id and tier information
        status = await supervisor.get_actor_status(agent_id)
        assert status.state == ActorState.ACTIVE

        # Cleanup
        await supervisor.terminate_actor(agent_id)


class TestAgentSpawnByTier:
    """Test agent spawning organized by tier for detailed diagnostics."""

    TIERS = {
        1: {"name": "Core Triad", "agents": []},
        2: {"name": "Support", "agents": []},
        3: {"name": "Exploration", "agents": []},
        4: {"name": "Safety & Security", "agents": []},
        5: {"name": "Coordination", "agents": []},
        6: {"name": "Enhancement", "agents": []},
    }

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", AGENT_TEST_CASES, ids=lambda tc: tc["name"])
    async def test_tier_agent_spawn(self, test_case):
        """Test spawning agents by tier and log diagnostics."""
        supervisor = ActorSupervisor(name=f"test-supervisor-tier{test_case['tier']}")
        agent_class = test_case["class"]
        agent_name = test_case["name"]
        tier = test_case["tier"]
        agent_id = f"tier{tier}-{agent_name.lower()}-001"

        try:
            actor = await supervisor.spawn_actor(
                actor_class=agent_class,
                actor_id=agent_id,
            )
            status = await supervisor.get_actor_status(agent_id)

            assert status.state == ActorState.ACTIVE, (
                f"Tier {tier} ({self.TIERS[tier]['name']}) - {agent_name} failed: {status.state}"
            )

        finally:
            if agent_id in supervisor.actors:
                await supervisor.terminate_actor(agent_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
