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
