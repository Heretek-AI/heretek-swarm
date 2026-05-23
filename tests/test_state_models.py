"""
Tests for state models — snapshot roundtrip, diff detection,
full state restore, and conversation lineage integration.

Addresses M001/S01/T02 mismatches:
- M1: create_snapshot stores full AgentState.__dict__ (was only working_memory)
- M2: rollback_to_snapshot restores working_memory/context/metadata
- M3: rollback_to_snapshot creates fully populated AgentState (was bare)
- M4: ConversationState + LineageTracker + StateManager compound workflow
"""

import asyncio
from uuid import uuid4

import pytest

from heretek_swarm.state.models import (

    AgentState,
    ConversationState,
    LineageTracker,
    SnapshotManager,
    StateManager,
    StateStatus,
    StateSnapshot,
    SystemState,
)

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _run(coro):
    """Run an async coroutine synchronously for test convenience."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# M1 & M2: Snapshot roundtrip — full AgentState fields preserved
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_snapshot_stores_full_agent_state():
    """M1: create_snapshot must store all AgentState fields, not just working_memory."""
    mgr = SnapshotManager()

    agent = AgentState(
        agent_id="a1",
        agent_type="coordinator",
        status=StateStatus.ACTIVE,
        working_memory={"key": "value", "counter": 42},
        context={"session": "abc"},
        metadata={"priority": 1},
    )

    snap = _run(mgr.create_snapshot(
        agent_states={"a1": agent},
        trigger="test",
        description="full-state snapshot",
    ))

    stored = snap.state["agents"]["a1"]
    assert stored["agent_id"] == "a1"
    assert stored["agent_type"] == "coordinator"
    assert stored["status"] == "active"
    assert stored["working_memory"] == {"key": "value", "counter": 42}
    assert stored["context"] == {"session": "abc"}
    assert stored["metadata"] == {"priority": 1}


@pytest.mark.unit
def test_rollback_restores_working_memory_context_metadata():
    """M2/M3: rollback_to_snapshot restores working_memory, context, metadata."""
    mgr = StateManager()

    # Register an agent and add rich state
    agent = _run(mgr.register_agent("a1", "worker"))
    _run(mgr.update_state("a1",
        working_memory={"task": "analyze"},
        context={"thread": "t1"},
        metadata={"origin": "ui"},
    ))
    agent.status = StateStatus.SUSPENDED
    agent.version = 3

    # Snapshot
    snap = _run(mgr.create_snapshot(trigger="pre-rollback"))

    # Mutate state
    _run(mgr.update_state("a1",
        working_memory={"task": "overwritten"},
        context={},
        metadata={},
    ))
    agent.status = StateStatus.ACTIVE
    agent.version = 99

    # Rollback
    ok = _run(mgr.rollback_to_snapshot(snap.snapshot_id))
    assert ok

    restored = mgr.get_state("a1")
    assert restored is not None
    assert restored.working_memory == {"task": "analyze"}
    assert restored.context == {"thread": "t1"}
    assert restored.metadata == {"origin": "ui"}
    assert restored.status == StateStatus.SUSPENDED
    assert restored.version == 3


@pytest.mark.unit
def test_rollback_to_nonexistent_snapshot_returns_false():
    """Rollback with a bogus snapshot_id must return False gracefully."""
    mgr = StateManager()
    ok = _run(mgr.rollback_to_snapshot(uuid4()))
    assert ok is False


# ---------------------------------------------------------------------------
# Diff detection
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_diff_added_agent():
    """compute_diff should detect an agent added in the second snapshot."""
    mgr = SnapshotManager()

    agent_a = AgentState(agent_id="a", working_memory={"phase": 1})
    agent_b = AgentState(agent_id="b", working_memory={"phase": 1})

    snap1 = _run(mgr.create_snapshot(agent_states={"a": agent_a}, trigger="base"))
    snap2 = _run(mgr.create_snapshot(agent_states={"a": agent_a, "b": agent_b}, trigger="added"))

    diff = _run(mgr.compute_diff(snap1.snapshot_id, snap2.snapshot_id))
    assert "b" in diff["added"]
    assert "b" not in diff["removed"]
    assert "b" not in diff["changed"]


@pytest.mark.unit
def test_diff_removed_agent():
    """compute_diff should detect an agent removed in the second snapshot."""
    mgr = SnapshotManager()

    agent_a = AgentState(agent_id="a", working_memory={"phase": 1})
    agent_b = AgentState(agent_id="b", working_memory={"phase": 2})

    snap1 = _run(mgr.create_snapshot(agent_states={"a": agent_a, "b": agent_b}, trigger="both"))
    snap2 = _run(mgr.create_snapshot(agent_states={"a": agent_a}, trigger="removed"))

    diff = _run(mgr.compute_diff(snap1.snapshot_id, snap2.snapshot_id))
    assert "b" in diff["removed"]


@pytest.mark.unit
def test_diff_changed_agent():
    """compute_diff should detect a changed agent between snapshots."""
    mgr = SnapshotManager()

    agent_v1 = AgentState(agent_id="a", working_memory={"counter": 1})
    agent_v2 = AgentState(agent_id="a", working_memory={"counter": 2})

    snap1 = _run(mgr.create_snapshot(agent_states={"a": agent_v1}, trigger="v1"))
    snap2 = _run(mgr.create_snapshot(agent_states={"a": agent_v2}, trigger="v2"))

    diff = _run(mgr.compute_diff(snap1.snapshot_id, snap2.snapshot_id))
    assert "a" in diff["changed"]


@pytest.mark.unit
def test_diff_missing_snapshots():
    """compute_diff returns error dict when either snapshot is missing."""
    mgr = SnapshotManager()
    diff = _run(mgr.compute_diff(uuid4(), uuid4()))
    assert "error" in diff


# ---------------------------------------------------------------------------
# M4: Compound workflow — ConversationState + LineageTracker + StateManager
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_conversation_lineage_snapshot_roundtrip():
    """M4: Full compound workflow exercising ConversationState, LineageTracker,
    and StateManager in one end-to-end flow."""
    mgr = StateManager()

    # 1. Register agents
    _run(mgr.register_agent("agent-x", "worker"))
    _run(mgr.register_agent("agent-y", "worker"))

    # 2. Start conversation
    conv = _run(mgr.start_conversation(
        initiator_agent_id="agent-x",
        participant_ids=["agent-x", "agent-y"],
        topic="snapshot-test",
    ))

    # 3. Record messages and build lineage
    msg1 = _run(mgr.record_message(
        conversation_id=conv.conversation_id,
        sender_agent_id="agent-x",
        content="Hello, this is the root message.",
    ))
    msg2 = _run(mgr.record_message(
        conversation_id=conv.conversation_id,
        sender_agent_id="agent-y",
        content="Response to root.",
        parent_message_id=msg1.message_id,
    ))

    # Verify lineage depth
    assert msg1.depth == 0
    assert msg2.depth == 1
    assert msg2.root_message_id == msg1.message_id

    # 4. Snapshot current state
    snap = _run(mgr.create_snapshot(trigger="mid-conversation"))

    # 5. Mutate state — add more messages, change agent state
    _run(mgr.update_state("agent-x", working_memory={"last": "mutated"}))
    _run(mgr.record_message(
        conversation_id=conv.conversation_id,
        sender_agent_id="agent-x",
        content="This message should disappear after rollback.",
        parent_message_id=msg2.message_id,
    ))

    # 6. Rollback
    ok = _run(mgr.rollback_to_snapshot(snap.snapshot_id))
    assert ok

    # 7. Verify agent state restored
    agent_x = mgr.get_state("agent-x")
    assert agent_x is not None
    assert agent_x.working_memory == {}

    # 8. Verify conversation still exists
    assert conv.conversation_id in mgr._conversations


# ---------------------------------------------------------------------------
# AgentState.compute_hash
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_agent_state_compute_hash():
    """compute_hash is deterministic for identical working_memory."""
    a1 = AgentState(agent_id="x", working_memory={"a": 1})
    a2 = AgentState(agent_id="x", working_memory={"a": 1})
    assert a1.compute_hash() == a2.compute_hash()

    a3 = AgentState(agent_id="x", working_memory={"a": 2})
    assert a1.compute_hash() != a3.compute_hash()
