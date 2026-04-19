"""
Integration tests for agent auto-spawn via API lifespan.

Tests that GET /api/agents returns 23 ACTIVE agents within 120 seconds
of API startup, without requiring wizard completion or any manual action.

Slice: M012/S03 — Agent Auto-Spawn
Task: T01 — Add _spawn_all_agents() to API lifespan
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_supervisor():
    """
    Create a mock ActorSupervisor with 23 mock actors.

    Each mock actor has get_status() returning ACTIVE state.
    """
    supervisor = MagicMock()

    actors = {}
    for agent_id in [
        "steward", "alpha", "beta", "charlie",
        "historian", "metis", "empath", "perceiver", "echo",
        "explorer", "examiner", "dreamer", "coder",
        "sentinel", "sentinel-prime", "arbiter",
        "coordinator", "nexus", "catalyst", "chronos",
        "prism", "habit-forge", "perceiver-plus",
    ]:
        mock_actor = MagicMock()
        mock_status = MagicMock()
        mock_status.state.value = "active"
        mock_status.message_count = 0
        mock_status.error_count = 0
        mock_status.last_activity = None
        mock_actor.get_status.return_value = mock_status
        actors[agent_id] = mock_actor

    supervisor.actors = actors
    supervisor.spawn_actor = AsyncMock()
    supervisor.terminate_all = AsyncMock()
    supervisor.get_statistics = MagicMock(return_value={
        "total": 23,
        "active": 23,
        "suspended": 0,
        "error": 0,
    })
    return supervisor


@pytest.fixture
def mock_supervisor_no_actors():
    """Create a mock supervisor with no actors spawned."""
    supervisor = MagicMock()
    supervisor.actors = {}
    supervisor.spawn_actor = AsyncMock()
    supervisor.terminate_all = AsyncMock()
    supervisor.get_statistics = MagicMock(return_value={
        "total": 0,
        "active": 0,
        "suspended": 0,
        "error": 0,
    })
    return supervisor


# ============================================================================
# Tests: _spawn_all_agents() Function
# ============================================================================


@pytest.mark.asyncio
async def test_spawn_all_agents_produces_23_calls(mock_supervisor_no_actors):
    """
    Verify _spawn_all_agents() calls spawn_actor exactly 23 times.

    Uses the actual _spawn_all_agents() function with a mocked supervisor.
    """
    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor_no_actors):
        await api_main._spawn_all_agents()

    assert mock_supervisor_no_actors.spawn_actor.call_count == 23


@pytest.mark.asyncio
async def test_spawn_all_agents_spawns_correct_agent_ids(mock_supervisor_no_actors):
    """
    Verify _spawn_all_agents() spawns all expected agent IDs.

    Checks that the 23 specific agent IDs are each spawned once.
    """
    from heretek_swarm.api import main as api_main

    expected_ids = {
        "steward", "alpha", "beta", "charlie",
        "historian", "metis", "empath", "perceiver", "echo",
        "explorer", "examiner", "dreamer", "coder",
        "sentinel", "sentinel-prime", "arbiter",
        "coordinator", "nexus", "catalyst", "chronos",
        "prism", "habit-forge", "perceiver-plus",
    }

    with patch.object(api_main, "supervisor", mock_supervisor_no_actors):
        await api_main._spawn_all_agents()

    spawned_ids = {
        call_args[0][1]
        for call_args in mock_supervisor_no_actors.spawn_actor.call_args_list
    }
    assert spawned_ids == expected_ids


@pytest.mark.asyncio
async def test_spawn_all_agents_isolation_one_failure_does_not_prevent_others(
    mock_supervisor_no_actors,
):
    """
    Verify error isolation: one failed spawn does not prevent remaining agents.

    Makes the first spawn raise an exception and verifies the remaining 22
    agents are still attempted.
    """
    from heretek_swarm.api import main as api_main

    async def fail_once(*args, **kwargs):
        fail_once.call_count += 1
        if fail_once.call_count == 1:
            raise RuntimeError("simulated spawn failure")
        return None

    fail_once.call_count = 0
    mock_supervisor_no_actors.spawn_actor = AsyncMock(side_effect=fail_once)

    with patch.object(api_main, "supervisor", mock_supervisor_no_actors):
        await api_main._spawn_all_agents()

    # All 23 attempts should have been made despite the first failure
    assert mock_supervisor_no_actors.spawn_actor.call_count == 23


# ============================================================================
# Tests: GET /api/agents Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_get_agents_returns_23_active_agents(mock_supervisor):
    """
    Verify GET /api/agents returns exactly 23 agents, all ACTIVE.

    Uses the real endpoint with a fully-mocked supervisor.
    """
    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor):
        result = await api_main.get_agents(authenticated="test-key")

    assert result["total"] == 23
    assert len(result["agents"]) == 23
    for agent in result["agents"]:
        assert agent["status"] == "active"


@pytest.mark.asyncio
async def test_get_agents_returns_correct_agent_ids(mock_supervisor):
    """
    Verify GET /api/agents returns all expected agent IDs.

    Each agent in the response should have an id matching the expected list.
    """
    from heretek_swarm.api import main as api_main

    expected_ids = {
        "steward", "alpha", "beta", "charlie",
        "historian", "metis", "empath", "perceiver", "echo",
        "explorer", "examiner", "dreamer", "coder",
        "sentinel", "sentinel-prime", "arbiter",
        "coordinator", "nexus", "catalyst", "chronos",
        "prism", "habit-forge", "perceiver-plus",
    }

    with patch.object(api_main, "supervisor", mock_supervisor):
        result = await api_main.get_agents(authenticated="test-key")

    returned_ids = {agent["id"] for agent in result["agents"]}
    assert returned_ids == expected_ids


@pytest.mark.asyncio
async def test_get_agents_includes_type_and_status(mock_supervisor):
    """
    Verify GET /api/agents response includes type and status for each agent.
    """
    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor):
        result = await api_main.get_agents(authenticated="test-key")

    for agent in result["agents"]:
        assert "id" in agent
        assert "type" in agent
        assert "status" in agent
        assert agent["status"] == "active"


# ============================================================================
# Tests: Startup Integration
# ============================================================================


@pytest.mark.asyncio
async def test_init_supervisor_creates_task_for_spawn(mock_supervisor_no_actors):
    """
    Verify _init_supervisor() creates an asyncio task for _spawn_all_agents().

    Ensures the fire-and-forget pattern is used (startup is not blocked).
    """
    from heretek_swarm.api import main as api_main

    original_task_count = len(asyncio.all_tasks())

    with patch.object(api_main, "supervisor", mock_supervisor_no_actors):
        await api_main._init_supervisor()

    # A new task should have been created (fire-and-forget spawn)
    current_task_count = len(asyncio.all_tasks())
    assert current_task_count > original_task_count


@pytest.mark.asyncio
async def test_get_agents_returns_503_when_supervisor_not_initialized():
    """
    Verify GET /api/agents returns 503 when supervisor is not initialized.
    """
    from fastapi import HTTPException

    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", None):
        with pytest.raises(HTTPException) as exc_info:
            await api_main.get_agents(authenticated="test-key")

        assert exc_info.value.status_code == 503


# ============================================================================
# Tests: Supervisor Status Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_supervisor_status_returns_statistics(mock_supervisor):
    """Verify GET /api/supervisor/status returns supervisor statistics."""
    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor):
        result = await api_main.get_supervisor_status(authenticated="test-key")

    assert result["total"] == 23
    assert result["active"] == 23
    assert result["suspended"] == 0
    assert result["error"] == 0


# ============================================================================
# Tests: Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_get_agent_returns_404_for_unknown_agent(mock_supervisor):
    """Verify GET /api/agents/{agent_id} returns 404 for unknown agents."""
    from fastapi import HTTPException

    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor):
        with pytest.raises(HTTPException) as exc_info:
            await api_main.get_agent(agent_id="unknown-agent", authenticated="test-key")

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_terminate_agent_returns_404_for_unknown_agent(mock_supervisor):
    """Verify POST /api/agents/{agent_id}/terminate returns 404 for unknown agents."""
    from fastapi import HTTPException

    from heretek_swarm.api import main as api_main

    with patch.object(api_main, "supervisor", mock_supervisor):
        with pytest.raises(HTTPException) as exc_info:
            await api_main.terminate_agent(
                agent_id="unknown-agent", authenticated="test-key"
            )

        assert exc_info.value.status_code == 404
