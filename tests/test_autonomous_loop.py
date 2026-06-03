"""Tests for the autonomous main loop — goal pipeline wiring and periodic analysis.

Verifies that the fix for the dangling ``_run_goal_pipeline_cycle`` call
does not crash when invoked with mock actors and a temp file goal store.
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from heretek_swarm.goals.models import Goal
from heretek_swarm.runtime.main_loop import AutonomousSwarm


@pytest.mark.asyncio
async def test_goal_pipeline_wiring_does_not_crash(
    tmp_path: Path,
) -> None:
    """Validate the goal pipeline wiring (in _run_goal_pipeline) does
    not crash when invoked with mock actors and a temp file goal store.

    The test:
    1. Creates an AutonomousSwarm in no_infra mode
    2. Sets up a minimal supervisor with mock metis/historian actors
    3. Provides a consensus engine
    4. Calls _run_goal_pipeline directly
    5. Asserts no exception is raised
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)

    # --- Wire the minimum components needed by _run_goal_pipeline ------
    from heretek_swarm.consensus.maker import MAKERConsensus

    swarm.consensus = MAKERConsensus(
        ahead_by_k=2,
        min_votes=3,
        confidence_threshold=0.3,
    )

    # Create a minimal supervisor stub with just actors
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # --- Mock metis: return a valid Goal proposal ----------------------
    goal = Goal(
        id="test_goal_001",
        title="Test strategic goal",
        description="A test goal for verifying pipeline wiring.",
        success_criteria=["Criterion 1", "Criterion 2"],
    )
    mock_metis = AsyncMock()
    mock_metis.generate_goal_proposal = AsyncMock(return_value={"goal": goal})
    supervisor.actors["metis"] = mock_metis

    # --- Mock historian: no-op -----------------------------------------
    mock_historian = AsyncMock()
    mock_historian.log_event = AsyncMock()
    supervisor.actors["historian"] = mock_historian

    # --- Point the goal store at a temp file ---------------------------
    from heretek_swarm.goals.store import FileGoalStore

    goal_store_path = tmp_path / "goals.json"
    swarm._goal_store = FileGoalStore(store_path=goal_store_path)

    # --- Execute — should NOT raise ------------------------------------
    await swarm._run_goal_pipeline(
        metis=mock_metis,
        historian=mock_historian,
    )

    # --- Verify the goal was persisted to the store --------------------
    goals = swarm._goal_store.load_all()
    assert len(goals) == 1, "Expected exactly one goal to be persisted"
    assert goals[0].id == "test_goal_001"
    assert goals[0].status == "proposed"

    # --- Verify metis was consulted ------------------------------------
    mock_metis.generate_goal_proposal.assert_awaited_once()

    # --- Verify historian was called -----------------------------------
    found_proposed_event = any(
        call.args[0] == "goal_proposed"
        for call in mock_historian.log_event.call_args_list
    )
    assert found_proposed_event, (
        "Expected historian.log_event to be called with event_type='goal_proposed'"
    )


@pytest.mark.asyncio
async def test_goal_pipeline_handles_missing_metis_gracefully(
    tmp_path: Path,
) -> None:
    """When metis is None, _run_goal_pipeline should not crash."""
    swarm = AutonomousSwarm(config={}, no_infra=True)

    from heretek_swarm.consensus.maker import MAKERConsensus

    swarm.consensus = MAKERConsensus(
        ahead_by_k=2,
        min_votes=3,
        confidence_threshold=0.3,
    )
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    mock_historian = AsyncMock()
    supervisor.actors["historian"] = mock_historian

    from heretek_swarm.goals.store import FileGoalStore

    goal_store_path = tmp_path / "goals-missing-metis.json"
    swarm._goal_store = FileGoalStore(store_path=goal_store_path)

    # metis is None — should not crash
    await swarm._run_goal_pipeline(metis=None, historian=mock_historian)

    # No goals should have been created
    assert swarm._goal_store.count() == 0


@pytest.mark.asyncio
async def test_goal_pipeline_skipped_without_consensus() -> None:
    """When consensus is None, _run_goal_pipeline should short-circuit."""
    swarm = AutonomousSwarm(config={}, no_infra=True)
    swarm.consensus = None

    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # Should not crash when consensus is None
    await swarm._run_goal_pipeline(
        metis=MagicMock(),
        historian=MagicMock(),
    )
    # No assertion needed — we just need no crash


@pytest.mark.asyncio
async def test_response_collection_subscribes_to_topics() -> None:
    """Verify _collect_responses subscribes to both analysis response topics."""
    from heretek_swarm.actors.stubs import StubEventMesh

    swarm = AutonomousSwarm(config={}, no_infra=True)
    swarm.event_mesh = StubEventMesh()
    await swarm.event_mesh.connect()

    # Start _collect_responses as a background task; it subscribes on startup,
    # then blocks on asyncio.Event().wait().  We let subscriptions register and
    # then cancel the task.
    task = asyncio.create_task(swarm._collect_responses())
    await asyncio.sleep(0.02)

    sub_ids = swarm.event_mesh.get_subscription_ids()
    assert len(sub_ids) == 2, f"Expected 2 subscriptions, got {len(sub_ids)}"

    subjects = list(swarm.event_mesh._subscriptions.keys())
    assert "swarm.analysis.metis.response" in subjects
    assert "swarm.analysis.empath.response" in subjects

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_response_collection_callback_queues_message() -> None:
    """Verify the _on_response callback puts a message into _response_queue."""
    from heretek_swarm.actors.stubs import StubEventMesh

    swarm = AutonomousSwarm(config={}, no_infra=True)
    swarm.event_mesh = StubEventMesh()
    await swarm.event_mesh.connect()

    task = asyncio.create_task(swarm._collect_responses())
    await asyncio.sleep(0.02)

    # Retrieve the callback handler from StubEventMesh subscriptions
    metis_subs = swarm.event_mesh._subscriptions.get(
        "swarm.analysis.metis.response", []
    )
    assert len(metis_subs) == 1, "Expected one subscription for metis.response"
    handler = metis_subs[0]["handler"]

    await handler(
        None,  # mesh_or_none — ignored by _on_response
        "swarm.analysis.metis.response",
        {"message_type": "analysis_result", "analysis": "test_strategy"},
    )

    assert not swarm._response_queue.empty()
    item = swarm._response_queue.get_nowait()
    assert item["subject"] == "swarm.analysis.metis.response"
    assert item["data"]["message_type"] == "analysis_result"
    assert item["data"]["analysis"] == "test_strategy"
    assert "timestamp" in item

    # Also test the empath subscription callback
    empath_subs = swarm.event_mesh._subscriptions.get(
        "swarm.analysis.empath.response", []
    )
    assert len(empath_subs) == 1
    handler2 = empath_subs[0]["handler"]

    await handler2(
        None,
        "swarm.analysis.empath.response",
        {"message_type": "sentiment_result", "sentiment": "positive"},
    )

    item2 = swarm._response_queue.get_nowait()
    assert item2["subject"] == "swarm.analysis.empath.response"
    assert item2["data"]["sentiment"] == "positive"

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_response_drain_resets_latest_analysis_on_cycle_30() -> None:
    """Verify the drain logic in _process_cycle populates _latest_analysis.

    We can't fully exercise _process_cycle here (it needs a live supervisor
    with actors), so we test the drain logic directly:  queue items, then
    exercise the same drain loop that _process_cycle would run.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)

    # Enqueue two fake response items
    await swarm._response_queue.put({
        "subject": "swarm.analysis.metis.response",
        "data": {"message_type": "analysis_result"},
        "timestamp": "2026-01-01T00:00:00Z",
    })
    await swarm._response_queue.put({
        "subject": "swarm.analysis.empath.response",
        "data": {"message_type": "sentiment_result"},
        "timestamp": "2026-01-01T00:00:01Z",
    })

    # Exercise the same drain logic from _process_cycle()
    drained: list[dict[str, Any]] = []
    while not swarm._response_queue.empty():
        item = swarm._response_queue.get_nowait()
        drained.append(item)

    assert len(drained) == 2

    # This is what _process_cycle does after draining
    swarm._latest_analysis = {
        "responses": drained,
        "collected_at": "2026-01-01T00:00:00Z",
    }

    assert len(swarm._latest_analysis["responses"]) == 2
    assert (
        swarm._latest_analysis["responses"][0]["subject"]
        == "swarm.analysis.metis.response"
    )
    assert (
        swarm._latest_analysis["responses"][1]["subject"]
        == "swarm.analysis.empath.response"
    )
    assert swarm._response_queue.empty()


@pytest.mark.asyncio
async def test_response_queue_empty_when_no_responses() -> None:
    """Verify _response_queue is empty before any responses are published."""
    swarm = AutonomousSwarm(config={}, no_infra=True)
    assert swarm._response_queue.empty()
    assert swarm._latest_analysis == {}


@pytest.mark.asyncio
async def test_process_cycle_drains_responses_at_cycle_30() -> None:
    """Verify _process_cycle drains responses when the cycle counter reaches 30.

    Full-flow integration test:
    1. Pre-seed _response_queue with two analysis response items
    2. Set _analysis_cycle_count to 29 so the next call triggers periodic analysis
    3. Provide a minimal supervisor with empty actors dict (methods degrade gracefully)
    4. Call _process_cycle
    5. Verify cycle counter reset, drain into _latest_analysis, queue empty
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)

    # Minimal supervisor with empty actors dict -> internal methods log warnings
    # and short-circuit gracefully
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # Pre-seed the response queue with two analysis response items
    await swarm._response_queue.put({
        "subject": "swarm.analysis.metis.response",
        "data": {"message_type": "analysis_result", "analysis": "focus on scaling"},
        "timestamp": "2026-01-01T00:00:00Z",
    })
    await swarm._response_queue.put({
        "subject": "swarm.analysis.empath.response",
        "data": {"message_type": "sentiment_result", "sentiment": "positive"},
        "timestamp": "2026-01-01T00:00:01Z",
    })

    # Set cycle count to 29 -> the next call triggers periodic analysis + drain
    swarm._analysis_cycle_count = 29

    # Call _process_cycle
    await swarm._process_cycle()

    # 1. Cycle counter was reset to 0
    assert swarm._analysis_cycle_count == 0

    # 2. Response queue was drained into _latest_analysis
    assert len(swarm._latest_analysis["responses"]) == 2
    assert swarm._response_queue.empty()

    # 3. Responses are correctly stored with subject and data
    assert (
        swarm._latest_analysis["responses"][0]["subject"]
        == "swarm.analysis.metis.response"
    )
    assert (
        swarm._latest_analysis["responses"][1]["subject"]
        == "swarm.analysis.empath.response"
    )
    assert "collected_at" in swarm._latest_analysis


@pytest.mark.asyncio
async def test_process_cycle_skips_drain_below_cycle_30() -> None:
    """Verify _process_cycle does NOT trigger drain below the 30-cycle threshold.

    Negative test: with _analysis_cycle_count < 29, the periodic analysis
    block (including the drain) should not execute, and queued responses
    should remain in _response_queue.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)

    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # Pre-seed the response queue
    await swarm._response_queue.put({
        "subject": "swarm.analysis.metis.response",
        "data": {"message_type": "analysis_result"},
        "timestamp": "2026-01-01T00:00:00Z",
    })

    # Set cycle count to 5 -> well below the drain threshold
    swarm._analysis_cycle_count = 5

    await swarm._process_cycle()

    # Cycle counter should increment but NOT reset (didn't hit 30)
    assert swarm._analysis_cycle_count == 6

    # Response queue should NOT have been drained (drain is inside the >=30 block)
    assert not swarm._response_queue.empty()

    # _latest_analysis should remain empty (never populated outside drain)
    assert swarm._latest_analysis == {}


@pytest.mark.asyncio
async def test_cooldown_suppresses_second_dispatch() -> None:
    """Verify _request_analysis sets cooldown and suppresses a second dispatch.

    Under cooldown, the second condition set is coalesced into
    _pending_event_conditions rather than dispatched immediately.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # First call should trigger dispatch and set cooldown
    await swarm._request_analysis([{"type": "test"}])
    assert swarm._cooldown_until is not None, "Cooldown should be set after first dispatch"

    # Second call while cooldown is active should coalesce, not dispatch
    await swarm._request_analysis([{"type": "test2"}])
    assert len(swarm._pending_event_conditions) == 1, (
        "Expected one coalesced event condition"
    )
    assert swarm._pending_event_conditions[0]["type"] == "test2"


@pytest.mark.asyncio
async def test_cooldown_expired_dispatches_coalesced_events() -> None:
    """Verify that after cooldown expires, pending + new events are dispatched
    and _pending_event_conditions is cleared.

    Simulates cooldown expiry by resetting _cooldown_until to a past timestamp.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # First dispatch triggers cooldown
    await swarm._request_analysis([{"type": "event1"}])
    assert swarm._cooldown_until is not None

    # Coalesce a second event during cooldown
    await swarm._request_analysis([{"type": "event2"}])
    assert len(swarm._pending_event_conditions) == 1

    # Simulate cooldown expiry by setting timestamp to the past
    swarm._cooldown_until = 0.0
    assert not swarm._is_in_cooldown(), "Expected cooldown to be expired"

    # Third dispatch should merge pending (event2) + new (event3) and dispatch
    await swarm._request_analysis([{"type": "event3"}])

    # _pending_event_conditions should be empty (merged into dispatch)
    assert len(swarm._pending_event_conditions) == 0, (
        "Expected pending events to be cleared after dispatch"
    )


@pytest.mark.asyncio
async def test_is_in_cooldown_returns_false_when_none() -> None:
    """Verify _is_in_cooldown returns False before any analysis is requested."""
    swarm = AutonomousSwarm(config={}, no_infra=True)
    assert not swarm._is_in_cooldown()


@pytest.mark.asyncio
async def test_pending_event_conditions_empty_initially() -> None:
    """Verify _pending_event_conditions is an empty list at construction."""
    swarm = AutonomousSwarm(config={}, no_infra=True)
    assert swarm._pending_event_conditions == []


@pytest.mark.asyncio
async def test_event_driven_dispatch_still_drains_responses() -> None:
    """Integration test: verify that event-driven dispatch via _request_analysis
    does not interfere with the response queue drain in _process_cycle.

    Triggers event-driven analysis, then runs _process_cycle at cycle 29
    to verify the periodic heartbeat drain still collects responses.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # Pre-seed the response queue
    await swarm._response_queue.put({
        "subject": "swarm.analysis.metis.response",
        "data": {"message_type": "analysis_result"},
        "timestamp": "2026-01-01T00:00:00Z",
    })
    await swarm._response_queue.put({
        "subject": "swarm.analysis.empath.response",
        "data": {"message_type": "sentiment_result"},
        "timestamp": "2026-01-01T00:00:01Z",
    })

    # Trigger event-driven analysis first
    await swarm._request_analysis([{"type": "event"}])

    # Set cycle count to 29 so _process_cycle fires periodic heartbeat + drain
    swarm._analysis_cycle_count = 29

    # Call _process_cycle -- should increment to 30, fire heartbeat, drain queue
    await swarm._process_cycle()

    # Cycle counter should be reset (heartbeat fired)
    assert swarm._analysis_cycle_count == 0

    # Response queue should be drained
    assert swarm._response_queue.empty()

    # _latest_analysis should have both responses
    assert len(swarm._latest_analysis["responses"]) == 2
    assert (
        swarm._latest_analysis["responses"][0]["subject"]
        == "swarm.analysis.metis.response"
    )
    assert (
        swarm._latest_analysis["responses"][1]["subject"]
        == "swarm.analysis.empath.response"
    )


@pytest.mark.asyncio
async def test_fallback_heartbeat_fires_at_30_cycles() -> None:
    """Verify the fallback periodic heartbeat fires when _analysis_cycle_count
    reaches 30, even without pending_event_conditions.

    Sets _analysis_cycle_count to 29, calls _process_cycle, and asserts
    the counter is reset to 0 (heartbeat fired) with no errors.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # No pending events, no cooldown
    swarm._pending_event_conditions = []
    swarm._cooldown_until = None
    swarm._analysis_cycle_count = 29

    await swarm._process_cycle()

    # Heartbeat should have fired, resetting the counter
    assert swarm._analysis_cycle_count == 0, (
        "Expected cycle counter to reset after heartbeat at 30"
    )


@pytest.mark.asyncio
async def test_fallback_heartbeat_not_fired_when_pending_events_available() -> None:
    """Verify that when pending_event_conditions are present and cooldown is
    expired, the event-driven path fires first. The periodic heartbeat still
    runs after event dispatch since the counter hits 30.

    Both _pending_event_conditions should be drained (by event path)
    and _analysis_cycle_count should be reset (by heartbeat path).
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor

    # Set pending events and expired cooldown
    swarm._pending_event_conditions = [{"type": "test"}]
    swarm._cooldown_until = 0.0  # Expired
    swarm._analysis_cycle_count = 29

    await swarm._process_cycle()

    # Event path should have drained pending events
    assert len(swarm._pending_event_conditions) == 0, (
        "Expected pending events to be drained by event-driven path"
    )
    # Heartbeat path should have reset the counter
    assert swarm._analysis_cycle_count == 0, (
        "Expected cycle counter to reset after heartbeat at 30"
    )


@pytest.mark.asyncio
async def test_monitor_error_rate_detects_errors() -> None:
    """Verify _monitor_error_rate detects an actor in error state and
    dispatches an error_spike condition via _request_analysis.

    Sets up a mock actor that returns state='error', runs one iteration
    of the monitor, and verifies that _request_analysis was triggered
    (cooldown_until is set, indicating dispatch occurred).
    """
    import os

    os.environ["HERETEK_ANALYSIS_ERROR_THRESHOLD"] = "0"

    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor
    swarm._running = True
    swarm._health_check_interval = 0.01

    # Create a mock actor whose get_status() returns state = "error"
    mock_actor = MagicMock()
    mock_actor.get_status.return_value.state.value = "error"
    supervisor.actors["test_agent"] = mock_actor

    # Run the monitor as a background task for one iteration
    task = asyncio.create_task(swarm._monitor_error_rate())
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    # After one iteration with 0 threshold and 1 error agent,
    # _request_analysis should have been called and set cooldown
    assert swarm._cooldown_until is not None, (
        "Expected cooldown to be set after error spike dispatch"
    )


@pytest.mark.asyncio
async def test_monitor_agent_state_detects_changes() -> None:
    """Verify _monitor_agent_state detects a state transition and
    dispatches an agent_state_change condition via _request_analysis.

    Runs the monitor for two iterations: first records the initial state
    ('active'), second detects the transition to 'suspended' and dispatches.
    """
    swarm = AutonomousSwarm(config={}, no_infra=True)
    supervisor = MagicMock()
    supervisor.actors = {}
    swarm.supervisor = supervisor
    swarm._running = True
    swarm._health_check_interval = 0.01

    # Mock actor starts in 'active' state
    mock_actor = MagicMock()
    mock_actor.get_status.return_value.state.value = "active"
    supervisor.actors["test_agent"] = mock_actor

    # Run the monitor; first iteration records 'active' in last_states
    task = asyncio.create_task(swarm._monitor_agent_state())
    await asyncio.sleep(0.05)

    # Change actor state to 'suspended' for the second iteration
    mock_actor.get_status.return_value.state.value = "suspended"
    await asyncio.sleep(0.05)

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    # After two iterations with a state transition, _request_analysis
    # should have been called and set cooldown
    assert swarm._cooldown_until is not None, (
        "Expected cooldown to be set after state change dispatch"
    )


@pytest.mark.asyncio
async def test_chronos_bulk_schedule_adjust_creates_task() -> None:
    """Verify bulk_schedule_adjust create operation schedules a new task."""
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from heretek_swarm.actors.chronos import ChronosAgent

    agent = ChronosAgent(agent_id="test_chronos_create", config={})
    mock_send = AsyncMock()
    agent.send = mock_send

    msg = SimpleNamespace(
        sender="requester",
        message_type="bulk_schedule_adjust",
        content={
            "operations": [
                {
                    "op": "create",
                    "operation_id": "c1",
                    "task_id": "created_task",
                    "name": "Created via bulk",
                    "scheduled_at": "2026-06-04T00:00:00Z",
                },
            ]
        },
        timestamp=datetime.now(UTC).isoformat(),
    )

    await agent._handle_bulk_schedule_adjust(msg)

    assert "created_task" in agent._tasks
    assert agent._tasks["created_task"].name == "Created via bulk"
    assert mock_send.called
    content = mock_send.call_args.kwargs["content"]
    assert content["total"] == 1
    assert content["succeeded"] == 1


@pytest.mark.asyncio
async def test_chronos_bulk_schedule_adjust_cancels_task() -> None:
    """Verify bulk_schedule_adjust cancel operation cancels an existing task."""
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from heretek_swarm.actors.chronos import ChronosAgent
    from heretek_swarm.actors.chronos.types import ScheduledTask, ScheduleStatus

    agent = ChronosAgent(agent_id="test_chronos_cancel", config={})
    mock_send = AsyncMock()
    agent.send = mock_send

    agent._tasks["task_to_cancel"] = ScheduledTask(
        task_id="task_to_cancel",
        name="To Cancel",
        description="",
        scheduled_at=datetime(2026, 6, 4, tzinfo=UTC),
    )

    msg = SimpleNamespace(
        sender="requester",
        message_type="bulk_schedule_adjust",
        content={
            "operations": [
                {
                    "op": "cancel",
                    "operation_id": "x1",
                    "task_id": "task_to_cancel",
                },
            ]
        },
        timestamp=datetime.now(UTC).isoformat(),
    )

    await agent._handle_bulk_schedule_adjust(msg)

    assert agent._tasks["task_to_cancel"].status == ScheduleStatus.CANCELLED
    content = mock_send.call_args.kwargs["content"]
    assert content["succeeded"] == 1


@pytest.mark.asyncio
async def test_chronos_bulk_schedule_adjust_updates_priority() -> None:
    """Verify bulk_schedule_adjust update_priority operation changes priority."""
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from heretek_swarm.actors.chronos import ChronosAgent
    from heretek_swarm.actors.chronos.types import Priority, ScheduledTask

    agent = ChronosAgent(agent_id="test_chronos_priority", config={})
    mock_send = AsyncMock()
    agent.send = mock_send

    agent._tasks["priority_task"] = ScheduledTask(
        task_id="priority_task",
        name="Priority Task",
        description="",
        scheduled_at=datetime(2026, 6, 4, tzinfo=UTC),
    )

    msg = SimpleNamespace(
        sender="requester",
        message_type="bulk_schedule_adjust",
        content={
            "operations": [
                {
                    "op": "update_priority",
                    "operation_id": "p1",
                    "task_id": "priority_task",
                    "new_priority": 5,
                },
            ]
        },
        timestamp=datetime.now(UTC).isoformat(),
    )

    await agent._handle_bulk_schedule_adjust(msg)

    assert agent._tasks["priority_task"].priority == Priority.CRITICAL
    content = mock_send.call_args.kwargs["content"]
    assert content["succeeded"] == 1


@pytest.mark.asyncio
async def test_chronos_bulk_schedule_adjust_retries_failed_operations() -> None:
    """Verify bulk_schedule_adjust retries failed operations once.

    A 'create' operation targeting a task_id that already exists will fail on
    both the initial attempt and the retry, proving the retry mechanism fires
    without crashing.
    """
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from heretek_swarm.actors.chronos import ChronosAgent
    from heretek_swarm.actors.chronos.types import ScheduledTask

    agent = ChronosAgent(agent_id="test_chronos_retry", config={})
    mock_send = AsyncMock()
    agent.send = mock_send

    agent._tasks["existing"] = ScheduledTask(
        task_id="existing",
        name="Existing",
        description="",
        scheduled_at=datetime(2026, 6, 4, tzinfo=UTC),
    )

    msg = SimpleNamespace(
        sender="requester",
        message_type="bulk_schedule_adjust",
        content={
            "operations": [
                {
                    "op": "create",
                    "operation_id": "r1",
                    "task_id": "existing",
                    "name": "Should Fail",
                },
            ]
        },
        timestamp=datetime.now(UTC).isoformat(),
    )

    await agent._handle_bulk_schedule_adjust(msg)

    content = mock_send.call_args.kwargs["content"]
    assert content["failed"] >= 1
    assert "already exists" in content["results"][0]["error"]
    assert content["total"] == 1
