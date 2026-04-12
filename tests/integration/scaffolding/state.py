"""
Integration test scaffolding for state rollback.

Agent Gamma - QA and Validation Lead
Provides test infrastructure for state management and rollback testing.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import pytest

# ============== STATE MODELS ==============

@dataclass
class StateCheckpoint:
    """Checkpoint of agent state."""
    checkpoint_id: str
    agent_id: str
    state: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    parent_checkpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "timestamp": self.timestamp,
            "parent_checkpoint_id": self.parent_checkpoint_id,
        }


@dataclass
class StateDelta:
    """Delta between two states."""
    checkpoint_from: str
    checkpoint_to: str
    additions: dict[str, Any] = field(default_factory=dict)
    modifications: dict[str, Any] = field(default_factory=dict)
    deletions: list[str] = field(default_factory=list)

    def apply(self, state: dict[str, Any]) -> dict[str, Any]:
        """Apply delta to a state."""
        new_state = state.copy()
        new_state.update(self.additions)
        new_state.update(self.modifications)
        for key in self.deletions:
            new_state.pop(key, None)
        return new_state


# ============== MOCK STATE MANAGER ==============

class MockStateManager:
    """
    Mock state manager for rollback testing.

    Simulates the state management layer without requiring
    actual infrastructure (Redis, PostgreSQL, etc.).
    """

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._checkpoints: dict[str, list[StateCheckpoint]] = {}
        self._deltas: dict[str, list[StateDelta]] = {}
        self._checkpoint_counter = 0
        self._rollback_count = 0
        self._latency_simulator: float = 0.0  # Simulated latency in ms

    async def initialize_agent(self, agent_id: str, initial_state: dict[str, Any] | None = None) -> None:
        """Initialize state for an agent."""
        self._states[agent_id] = initial_state or {"status": "initialized"}
        self._checkpoints[agent_id] = []
        self._deltas[agent_id] = []

    async def get_state(self, agent_id: str) -> dict[str, Any] | None:
        """Get current state for an agent."""
        if self._latency_simulator > 0:
            await asyncio.sleep(self._latency_simulator / 1000)
        return self._states.get(agent_id)

    async def update_state(
        self,
        agent_id: str,
        updates: dict[str, Any],
        create_checkpoint: bool = True,
    ) -> StateCheckpoint | None:
        """
        Update agent state.

        Args:
            agent_id: Agent to update.
            updates: State updates to apply.
            create_checkpoint: Whether to create a checkpoint before update.

        Returns:
            Checkpoint if created, None otherwise.
        """
        if agent_id not in self._states:
            return None

        checkpoint = None
        if create_checkpoint:
            checkpoint = await self.create_checkpoint(agent_id)

        # Apply updates
        old_state = self._states[agent_id].copy()
        self._states[agent_id].update(updates)

        # Record delta
        delta = self._compute_delta(old_state, self._states[agent_id], checkpoint)
        if delta:
            self._deltas[agent_id].append(delta)

        if self._latency_simulator > 0:
            await asyncio.sleep(self._latency_simulator / 1000)

        return checkpoint

    async def create_checkpoint(
        self,
        agent_id: str,
        parent_id: str | None = None,
    ) -> StateCheckpoint:
        """
        Create a checkpoint of current state.

        Args:
            agent_id: Agent to checkpoint.
            parent_id: Optional parent checkpoint ID.

        Returns:
            Created checkpoint.
        """
        self._checkpoint_counter += 1
        checkpoint = StateCheckpoint(
            checkpoint_id=f"checkpoint-{self._checkpoint_counter:06d}",
            agent_id=agent_id,
            state=self._states.get(agent_id, {}).copy(),
            parent_checkpoint_id=parent_id,
        )

        if agent_id not in self._checkpoints:
            self._checkpoints[agent_id] = []
        self._checkpoints[agent_id].append(checkpoint)

        if self._latency_simulator > 0:
            await asyncio.sleep(self._latency_simulator / 1000)

        return checkpoint

    async def rollback(
        self,
        agent_id: str,
        checkpoint_id: str,
    ) -> bool:
        """
        Rollback agent state to a checkpoint.

        Args:
            agent_id: Agent to rollback.
            checkpoint_id: Checkpoint to rollback to.

        Returns:
            True if rollback successful.
        """
        start_time = time.perf_counter()

        checkpoints = self._checkpoints.get(agent_id, [])
        target_checkpoint = None

        for cp in checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                target_checkpoint = cp
                break

        if not target_checkpoint:
            return False

        # Restore state
        self._states[agent_id] = target_checkpoint.state.copy()

        # Remove checkpoints after the target
        checkpoint_index = checkpoints.index(target_checkpoint)
        self._checkpoints[agent_id] = checkpoints[:checkpoint_index + 1]

        # Record rollback
        self._rollback_count += 1

        if self._latency_simulator > 0:
            await asyncio.sleep(self._latency_simulator / 1000)

        (time.perf_counter() - start_time) * 1000
        return True

    async def rollback_to_last(self, agent_id: str) -> bool:
        """Rollback to the most recent checkpoint."""
        checkpoints = self._checkpoints.get(agent_id, [])
        if len(checkpoints) < 2:
            return False

        # Get second-to-last checkpoint (last is current state)
        target_checkpoint = checkpoints[-2]
        return await self.rollback(agent_id, target_checkpoint.checkpoint_id)

    def get_checkpoints(self, agent_id: str) -> list[StateCheckpoint]:
        """Get all checkpoints for an agent."""
        return self._checkpoints.get(agent_id, []).copy()

    def get_rollback_count(self) -> int:
        """Get total number of rollbacks performed."""
        return self._rollback_count

    def set_latency_simulator(self, latency_ms: float) -> None:
        """Set simulated latency for operations."""
        self._latency_simulator = latency_ms

    def _compute_delta(
        self,
        old_state: dict[str, Any],
        new_state: dict[str, Any],
        checkpoint: StateCheckpoint | None,
    ) -> StateDelta | None:
        """Compute delta between two states."""
        additions = {}
        modifications = {}
        deletions = []

        for key, value in new_state.items():
            if key not in old_state:
                additions[key] = value
            elif old_state[key] != value:
                modifications[key] = value

        for key in old_state:
            if key not in new_state:
                deletions.append(key)

        if not additions and not modifications and not deletions:
            return None

        return StateDelta(
            checkpoint_from=checkpoint.checkpoint_id if checkpoint else "initial",
            checkpoint_to="current",
            additions=additions,
            modifications=modifications,
            deletions=deletions,
        )

    def reset(self) -> None:
        """Reset state manager."""
        self._states.clear()
        self._checkpoints.clear()
        self._deltas.clear()
        self._checkpoint_counter = 0
        self._rollback_count = 0


# ============== STATE ROLLBACK TEST SCENARIOS ==============

class StateRollbackScenario:
    """Base class for state rollback test scenarios."""

    def __init__(self, state_manager: MockStateManager) -> None:
        self.state_manager = state_manager
        self.results: dict[str, Any] = {}

    async def setup(self) -> None:
        """Set up the scenario."""

    async def teardown(self) -> None:
        """Tear down the scenario."""
        self.state_manager.reset()

    async def run(self) -> dict[str, Any]:
        """Run the scenario and return results."""
        raise NotImplementedError


class SimpleRollbackScenario(StateRollbackScenario):
    """Simple rollback to previous state."""

    async def run(self) -> dict[str, Any]:
        """Run simple rollback scenario."""
        agent_id = "test-agent"

        await self.state_manager.initialize_agent(
            agent_id,
            {"status": "initial", "counter": 0},
        )

        # Create initial checkpoint
        cp1 = await self.state_manager.create_checkpoint(agent_id)

        # Make changes
        await self.state_manager.update_state(
            agent_id,
            {"status": "modified", "counter": 5},
            create_checkpoint=True,
        )

        # Verify state changed
        state_before = await self.state_manager.get_state(agent_id)

        # Rollback
        start_time = time.perf_counter()
        success = await self.state_manager.rollback(agent_id, cp1.checkpoint_id)
        rollback_latency_ms = (time.perf_counter() - start_time) * 1000

        # Verify state restored
        state_after = await self.state_manager.get_state(agent_id)

        return {
            "success": success,
            "state_before_rollback": state_before,
            "state_after_rollback": state_after,
            "rollback_latency_ms": rollback_latency_ms,
            "state_restored": state_after == cp1.state,
        }


class MultiStepRollbackScenario(StateRollbackScenario):
    """Rollback through multiple state changes."""

    async def run(self) -> dict[str, Any]:
        """Run multi-step rollback scenario."""
        agent_id = "test-agent"

        await self.state_manager.initialize_agent(
            agent_id,
            {"step": 0, "data": "initial"},
        )

        # Create series of state changes
        checkpoints = []
        for i in range(1, 6):
            cp = await self.state_manager.create_checkpoint(agent_id)
            checkpoints.append(cp)
            await self.state_manager.update_state(
                agent_id,
                {"step": i, "data": f"step-{i}"},
                create_checkpoint=False,
            )

        # Get current state
        await self.state_manager.get_state(agent_id)

        # Rollback to step 2
        start_time = time.perf_counter()
        success = await self.state_manager.rollback(
            agent_id,
            checkpoints[1].checkpoint_id,  # Step 2
        )
        rollback_latency_ms = (time.perf_counter() - start_time) * 1000

        # Verify state
        rolled_back_state = await self.state_manager.get_state(agent_id)

        return {
            "success": success,
            "initial_step": 0,
            "final_step_before_rollback": 5,
            "rolled_back_to_step": 2,
            "rollback_latency_ms": rollback_latency_ms,
            "state_matches_checkpoint": rolled_back_state == checkpoints[1].state,
        }


class MultiAgentRollbackScenario(StateRollbackScenario):
    """Coordinated rollback across multiple agents."""

    async def run(self) -> dict[str, Any]:
        """Run multi-agent rollback scenario."""
        agent_ids = ["agent-1", "agent-2", "agent-3"]

        # Initialize all agents
        for agent_id in agent_ids:
            await self.state_manager.initialize_agent(
                agent_id,
                {"status": "ready", "task": None},
            )

        # Create coordinated checkpoint
        checkpoints = {}
        for agent_id in agent_ids:
            checkpoints[agent_id] = await self.state_manager.create_checkpoint(agent_id)

        # Update all agents
        for agent_id in agent_ids:
            await self.state_manager.update_state(
                agent_id,
                {"status": "working", "task": f"task-{agent_id}"},
                create_checkpoint=True,
            )

        # Simulate failure - rollback all agents
        start_time = time.perf_counter()
        rollback_results = {}
        for agent_id in agent_ids:
            rollback_results[agent_id] = await self.state_manager.rollback(
                agent_id,
                checkpoints[agent_id].checkpoint_id,
            )
        total_rollback_latency_ms = (time.perf_counter() - start_time) * 1000

        # Verify all agents rolled back
        all_rolled_back = all(rollback_results.values())
        states_after = {}
        for agent_id in agent_ids:
            states_after[agent_id] = await self.state_manager.get_state(agent_id)

        return {
            "success": all_rolled_back,
            "agents": agent_ids,
            "rollback_results": rollback_results,
            "total_rollback_latency_ms": total_rollback_latency_ms,
            "avg_rollback_latency_ms": total_rollback_latency_ms / len(agent_ids),
            "states_after_rollback": states_after,
        }


class TaskFailureRollbackScenario(StateRollbackScenario):
    """Automatic rollback on task failure."""

    async def run(self) -> dict[str, Any]:
        """Run task failure rollback scenario."""
        agent_id = "worker-agent"

        await self.state_manager.initialize_agent(
            agent_id,
            {"status": "idle", "current_task": None, "progress": 0},
        )

        # Create checkpoint before task
        pre_task_checkpoint = await self.state_manager.create_checkpoint(agent_id)

        # Simulate task execution with progress updates
        for progress in [25, 50, 75]:
            await self.state_manager.update_state(
                agent_id,
                {"status": "executing", "progress": progress},
                create_checkpoint=False,
            )

        # Simulate task failure at 75%
        state_at_failure = await self.state_manager.get_state(agent_id)

        # Automatic rollback on failure
        start_time = time.perf_counter()
        success = await self.state_manager.rollback(
            agent_id,
            pre_task_checkpoint.checkpoint_id,
        )
        rollback_latency_ms = (time.perf_counter() - start_time) * 1000

        # Verify state restored to pre-task
        state_after_rollback = await self.state_manager.get_state(agent_id)

        return {
            "success": success,
            "state_at_failure": state_at_failure,
            "state_after_rollback": state_after_rollback,
            "rollback_latency_ms": rollback_latency_ms,
            "task_can_be_retried": state_after_rollback == pre_task_checkpoint.state,
        }


# ============== PYTEST FIXTURES ==============

@pytest.fixture
def state_manager() -> MockStateManager:
    """Create a mock state manager."""
    return MockStateManager()


@pytest.fixture
def simple_rollback_scenario(state_manager: MockStateManager) -> SimpleRollbackScenario:
    """Create a simple rollback scenario."""
    return SimpleRollbackScenario(state_manager)


@pytest.fixture
def multi_step_rollback_scenario(state_manager: MockStateManager) -> MultiStepRollbackScenario:
    """Create a multi-step rollback scenario."""
    return MultiStepRollbackScenario(state_manager)


@pytest.fixture
def multi_agent_rollback_scenario(state_manager: MockStateManager) -> MultiAgentRollbackScenario:
    """Create a multi-agent rollback scenario."""
    return MultiAgentRollbackScenario(state_manager)


@pytest.fixture
def task_failure_rollback_scenario(state_manager: MockStateManager) -> TaskFailureRollbackScenario:
    """Create a task failure rollback scenario."""
    return TaskFailureRollbackScenario(state_manager)
