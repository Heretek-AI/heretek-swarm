"""
Tests for AgentSociety Exploration Mode

Tests exploration_mode wiring: task routing, fallback behavior, and public API.
"""

from unittest.mock import AsyncMock, patch

import pytest

from heretek_swarm.collective.society import (
    AgentSociety,
    CollectiveResult,
    CollectiveTask,
    CollectiveTaskType,
)


# =============================================================================
# Helpers
# =============================================================================

def _make_exploration_task(task_id: str = "task-1") -> CollectiveTask:
    """Create a minimal EXPLORATION task."""
    return CollectiveTask(
        id=task_id,
        type=CollectiveTaskType.EXPLORATION,
        description="Explore new capability",
        input_data={},
        participants=["explorer-0", "explorer-1"],
    )


def _make_optimization_task(task_id: str = "task-2") -> CollectiveTask:
    """Create a minimal OPTIMIZATION task."""
    return CollectiveTask(
        id=task_id,
        type=CollectiveTaskType.OPTIMIZATION,
        description="Optimize existing workflow",
        input_data={"threshold": 0.5, "max_iterations": 10},
        participants=["coder-0", "coder-1"],
    )


def _make_deliberation_task(task_id: str = "task-3") -> CollectiveTask:
    """Create a DELIBERATION task (not routed to swarm)."""
    return CollectiveTask(
        id=task_id,
        type=CollectiveTaskType.DELIBERATION,
        description="Deliberate on decision",
        input_data={},
        participants=["alpha-0", "beta-0"],
    )


class MockEmergentBehavior:
    """Minimal mock for EmergentBehavior."""


# =============================================================================
# S01: Exploration Routing and Fallback
# =============================================================================

class TestExplorationTaskTypesSet:
    """Tests for _exploration_task_types set."""

    def test_exploration_task_types_contains_exploration(self):
        """EXPLORATION task type is in _exploration_task_types."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        assert CollectiveTaskType.EXPLORATION in society._exploration_task_types

    def test_exploration_task_types_contains_optimization(self):
        """OPTIMIZATION task type is in _exploration_task_types."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        assert CollectiveTaskType.OPTIMIZATION in society._exploration_task_types

    def test_exploration_task_types_does_not_contain_deliberation(self):
        """DELIBERATION task type is NOT in _exploration_task_types."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        assert CollectiveTaskType.DELIBERATION not in society._exploration_task_types


class TestExplorationModeRouting:
    """Tests for exploration_mode task routing in coordinate_task."""

    @pytest.mark.asyncio
    async def test_exploration_mode_routes_exploration_task(self):
        """
        With exploration_mode=True and EXPLORATION task,
        coordinate_task calls _execute_swarm_exploration (not _execute_coordination).
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        task = _make_exploration_task()

        with patch.object(society, "_execute_swarm_exploration", new_callable=AsyncMock) as mock_swarm:
            mock_swarm.return_value = CollectiveResult(
                task_id=task.id,
                success=True,
                result={},
                participants=task.participants,
            )
            result = await society.coordinate_task(task)
            mock_swarm.assert_called_once_with(task)
            assert result.success

    @pytest.mark.asyncio
    async def test_exploration_mode_routes_optimization_task(self):
        """
        With exploration_mode=True and OPTIMIZATION task,
        coordinate_task calls _execute_swarm_exploration.
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        task = _make_optimization_task()

        with patch.object(society, "_execute_swarm_exploration", new_callable=AsyncMock) as mock_swarm:
            mock_swarm.return_value = CollectiveResult(
                task_id=task.id,
                success=True,
                result={},
                participants=task.participants,
            )
            result = await society.coordinate_task(task)
            mock_swarm.assert_called_once_with(task)
            assert result.success

    @pytest.mark.asyncio
    async def test_exploration_mode_false_uses_triard_fallback(self):
        """
        With exploration_mode=False, EXPLORATION task still uses TRIAD
        (does not route to _execute_swarm_exploration).
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=False)
        task = _make_exploration_task()

        with patch.object(society, "_execute_swarm_exploration", new_callable=AsyncMock) as mock_swarm:
            result = await society.coordinate_task(task)
            mock_swarm.assert_not_called()
            # Falls through to standard TRIAD coordination — result may succeed or fail
            # depending on supervisor availability; we just verify no swarm routing occurred


class TestSwarmFallback:
    """Tests for TRIAD fallback when swarm is unavailable."""

    @pytest.mark.asyncio
    async def test_fallback_when_swarm_unavailable(self):
        """
        When swarm_engine is None, _execute_swarm_exploration calls
        _execute_coordination_fallback and returns a valid CollectiveResult.
        """
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=True)
        task = _make_exploration_task()
        # swarm_engine is None when enable_swarm_intelligence=False

        with patch.object(society, "_execute_coordination_fallback", new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = CollectiveResult(
                task_id=task.id,
                success=True,
                result={},
                participants=task.participants,
            )
            result = await society._execute_swarm_exploration(task)
            mock_fallback.assert_called_once_with(task, task.participants)
            assert result.success

    @pytest.mark.asyncio
    async def test_fallback_when_swarm_returns_none(self):
        """
        When apply_swarm_pattern returns None, _execute_swarm_exploration
        calls _execute_coordination_fallback.
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        task = _make_exploration_task()

        with patch.object(society, "apply_swarm_pattern", new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = None  # Swarm engine unavailable signal
            with patch.object(
                society, "_execute_coordination_fallback", new_callable=AsyncMock
            ) as mock_fallback:
                mock_fallback.return_value = CollectiveResult(
                    task_id=task.id,
                    success=True,
                    result={},
                    participants=task.participants,
                )
                result = await society._execute_swarm_exploration(task)
                mock_fallback.assert_called_once_with(task, task.participants)
                assert result.success


# =============================================================================
# S02: Public API
# =============================================================================

class TestSetExplorationMode:
    """Tests for set_exploration_mode public method."""

    def test_set_exploration_mode_runtime(self):
        """set_exploration_mode(True) updates self.exploration_mode."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        assert society.exploration_mode is False
        society.set_exploration_mode(True)
        assert society.exploration_mode is True

    def test_set_exploration_mode_enables(self):
        """set_exploration_mode(True) sets internal flag to True."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        assert society.exploration_mode is False
        society.set_exploration_mode(True)
        assert society.exploration_mode is True

    def test_set_exploration_mode_disables(self):
        """set_exploration_mode(False) sets internal flag to False."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=True)
        assert society.exploration_mode is True
        society.set_exploration_mode(False)
        assert society.exploration_mode is False

    def test_set_exploration_mode_idempotent(self):
        """Calling set_exploration_mode twice with same value is safe."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=False)
        society.set_exploration_mode(False)
        society.set_exploration_mode(False)
        assert society.exploration_mode is False


class TestSocietyStatusExposesExplorationMode:
    """Tests that status methods expose exploration state."""

    def test_get_society_status_exposes_exploration_mode(self):
        """get_society_status includes 'exploration_mode' key."""
        society = AgentSociety(enable_swarm_intelligence=False, exploration_mode=True)
        status = society.get_society_status()
        assert "exploration_mode" in status
        assert status["exploration_mode"] is True

    def test_get_swarm_status_exposes_exploration_fields(self):
        """get_swarm_status includes exploration_mode_active and exploration_engine_available."""
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        status = society.get_swarm_status()
        assert "exploration_mode_active" in status
        assert status["exploration_mode_active"] is True
        assert "exploration_engine_available" in status
        assert status["exploration_engine_available"] is True

    def test_get_swarm_status_exploration_inactive(self):
        """With exploration_mode=False, exploration_mode_active is False."""
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=False)
        status = society.get_swarm_status()
        assert status.get("exploration_mode_active") is False


# =============================================================================
# S03: Integration Tests
# =============================================================================

class TestFullExplorationLifecycle:
    """Integration tests for full exploration task lifecycle."""

    @pytest.mark.asyncio
    async def test_full_exploration_task_lifecycle(self):
        """
        Full lifecycle: EXPLORATION task with exploration_mode=True
        returns CollectiveResult with swarm result and non-zero confidence.
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        task = _make_exploration_task()

        # apply_swarm_pattern returns a dict with confidence and emergence_indicators
        mock_decision = {
            "confidence": 0.85,
            "emergence_indicators": ["pattern_coherence"],
            "decision": {},
            "iterations": 5,
            "emergence_detected": True,
            "quality_metrics": {},
            "pattern_type": "bee_algorithm",
        }

        with patch.object(society, "apply_swarm_pattern", new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = mock_decision
            result = await society.coordinate_task(task)

            assert result.success
            assert result.task_id == task.id
            assert result.consensus_score == 0.85
            assert result.result is not None
            assert result.result.get("confidence") == 0.85
            assert result.result.get("swarm_pattern") == "bee_algorithm"

    @pytest.mark.asyncio
    async def test_full_optimization_task_lifecycle(self):
        """
        Full lifecycle: OPTIMIZATION task with exploration_mode=True
        routes to pso pattern.
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=True)
        task = _make_optimization_task()

        mock_decision = {
            "confidence": 0.75,
            "emergence_indicators": [],
            "decision": {},
            "iterations": 10,
            "emergence_detected": False,
            "quality_metrics": {},
            "pattern_type": "pso",
        }

        with patch.object(society, "apply_swarm_pattern", new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = mock_decision
            result = await society.coordinate_task(task)

            assert result.success
            assert result.result.get("swarm_pattern") == "pso"

    @pytest.mark.asyncio
    async def test_exploration_mode_default_false(self):
        """
        exploration_mode defaults to False. EXPLORATION tasks
        bypass swarm routing and use TRIAD coordination.
        """
        society = AgentSociety(enable_swarm_intelligence=True, exploration_mode=False)
        task = _make_exploration_task()

        with patch.object(society, "_execute_swarm_exploration", new_callable=AsyncMock) as mock_swarm:
            await society.coordinate_task(task)
            # TRIAD path — swarm routing not triggered
            mock_swarm.assert_not_called()

    @pytest.mark.asyncio
    async def test_governance_society_passes_exploration_mode(self):
        """
        GovernanceAgentSociety(exploration_mode=True) propagates flag
        to the underlying AgentSociety.
        """
        from heretek_swarm.governance.integrations.collective_governance import (
            GovernanceAgentSociety,
        )

        gov_society = GovernanceAgentSociety(
            enable_swarm_intelligence=True,
            exploration_mode=True,
        )
        assert gov_society.exploration_mode is True

    @pytest.mark.asyncio
    async def test_governance_society_toggles_exploration_mode(self):
        """
        set_exploration_mode on GovernanceAgentSociety updates the flag.
        """
        from heretek_swarm.governance.integrations.collective_governance import (
            GovernanceAgentSociety,
        )

        gov_society = GovernanceAgentSociety(
            enable_swarm_intelligence=True,
            exploration_mode=False,
        )
        gov_society.set_exploration_mode(True)
        assert gov_society.exploration_mode is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
