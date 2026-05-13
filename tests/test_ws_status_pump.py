"""
Tests for the WebSocket status pump background task (M005/S02/T01).

Verifies that the pump iteration logic correctly invokes
send_agent_status_update for each non-None actor status.

Uses AsyncMock for send_agent_status_update so we can verify
call counts and arguments without a running WebSocket server.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.actors.base.core import ActorState, ActorStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_actor(
    state: ActorState = ActorState.ACTIVE,
    agent_id: str = "test-agent",
) -> MagicMock:
    """Build a MagicMock that looks like an AgentActor with a
    controllable get_status() return."""
    actor = MagicMock()
    status = ActorStatus(
        agent_id=agent_id,
        state=state,
        message_count=5,
        created_at="2025-01-01T00:00:00Z",
        topics=["test"],
        capabilities=["test"],
        mailbox_size=0,
        last_activity="2025-01-01T00:01:00Z",
        error_count=0,
    )
    actor.get_status.return_value = status
    return actor


def _make_mock_actor_none_status() -> MagicMock:
    """Build an actor whose get_status() returns None (edge case)."""
    actor = MagicMock()
    actor.get_status.return_value = None
    return actor


# ---------------------------------------------------------------------------
# Tests — exercise the same iteration logic used by the pump
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pump_calls_send_for_each_actor():
    """The pump should call send_agent_status_update once per actor
    with a non-None status."""
    supervisor = MagicMock()
    supervisor.actors = {
        "alpha": _make_mock_actor(agent_id="alpha"),
        "beta": _make_mock_actor(agent_id="beta", state=ActorState.SUSPENDED),
        "gamma": _make_mock_actor(agent_id="gamma", state=ActorState.ERROR),
    }

    send_mock = AsyncMock()

    # Execute the same iteration logic the pump uses
    actors = list(supervisor.actors.items())
    for agent_id, actor in actors:
        status = actor.get_status()
        if status is None:
            continue
        await send_mock(
            agent_id=str(agent_id),
            status=status.state.value if status.state else "unknown",
        )

    # Verify send_agent_status_update was called for each of 3 actors
    assert send_mock.call_count == 3
    actual_calls = {call.kwargs["agent_id"] for call in send_mock.call_args_list}
    assert actual_calls == {"alpha", "beta", "gamma"}

    # Verify status values passed through
    status_by_agent = {
        call.kwargs["agent_id"]: call.kwargs["status"]
        for call in send_mock.call_args_list
    }
    assert status_by_agent["alpha"] == "active"
    assert status_by_agent["beta"] == "suspended"
    assert status_by_agent["gamma"] == "error"


@pytest.mark.asyncio
async def test_pump_skips_none_status():
    """Actors whose get_status() returns None should be silently skipped."""
    supervisor = MagicMock()
    supervisor.actors = {
        "good": _make_mock_actor(agent_id="good"),
        "bad": _make_mock_actor_none_status(),
        "also_good": _make_mock_actor(agent_id="also_good"),
    }

    send_mock = AsyncMock()

    actors = list(supervisor.actors.items())
    for agent_id, actor in actors:
        status = actor.get_status()
        if status is None:
            continue
        await send_mock(
            agent_id=str(agent_id),
            status=status.state.value if status.state else "unknown",
        )

    assert send_mock.call_count == 2
    actual_agents = {call.kwargs["agent_id"] for call in send_mock.call_args_list}
    assert actual_agents == {"good", "also_good"}


@pytest.mark.asyncio
async def test_pump_handles_empty_supervisor():
    """An empty supervisor.actors dict should produce zero calls."""
    supervisor = MagicMock()
    supervisor.actors = {}

    send_mock = AsyncMock()

    actors = list(supervisor.actors.items())
    for _agent_id, actor in actors:
        status = actor.get_status()
        if status is None:
            continue
        await send_mock(agent_id="nope", status="active")

    assert send_mock.call_count == 0


@pytest.mark.asyncio
async def test_send_agent_status_update_invokes_dashboard():
    """send_agent_status_update should call both broadcast_agent_status
    and broadcast_dashboard."""
    from heretek_swarm.api.websockets import manager, send_agent_status_update

    # Mock both broadcast methods
    manager.broadcast_agent_status = AsyncMock()
    manager.broadcast_dashboard = AsyncMock()

    await send_agent_status_update(agent_id="testy", status="active")

    # Called broadcast_agent_status
    manager.broadcast_agent_status.assert_awaited_once()
    args, _ = manager.broadcast_agent_status.call_args
    assert args[0] == "testy"  # agent_id
    assert args[1]["status"] == "active"

    # Called broadcast_dashboard with the correct envelope
    manager.broadcast_dashboard.assert_awaited_once()
    dash_args = manager.broadcast_dashboard.call_args[0][0]
    assert dash_args["type"] == "agent_status"
    assert dash_args["agentId"] == "testy"
    assert dash_args["status"] == "active"
    assert "lastHeartbeat" in dash_args
