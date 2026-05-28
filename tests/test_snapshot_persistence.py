"""Test T04: Verify SnapshotManager persistence (initialize / shutdown).

Validates that:
- SnapshotManager.initialize() creates the storage directory
- create_snapshot() persists to disk immediately
- Snapshots survive manager restart (re-init loads from disk)
- shutdown() flushes all snapshots and cancels cleanup task
- File system errors are handled gracefully (no crash)
- Pruning removes oldest snapshots when max_snapshots is exceeded
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from heretek_swarm.state.models import SnapshotConfig, SnapshotManager, StateSnapshot, SystemState

pytestmark = [pytest.mark.unit]

# Helpers

def _snapshot_json_count(storage_path: Path) -> int:
    """Count .json files in the storage directory."""
    return len(list(storage_path.glob("*.json")))


def _snapshot_on_disk(storage_path: Path, snapshot_id: uuid.UUID) -> dict[str, object] | None:
    """Read a snapshot JSON from disk by ID, or None."""
    path = storage_path / f"{snapshot_id}.json"
    if not path.exists():
        return None
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return data


# Fixtures


@pytest.fixture
def tmp_storage_path(tmp_path: Path) -> Path:
    """Provide a fresh storage directory path per test."""
    return tmp_path / "snapshots"


@pytest.fixture
def config(tmp_storage_path: Path) -> SnapshotConfig:
    """SnapshotConfig pointed at a temp directory."""
    return SnapshotConfig(
        storage_path=str(tmp_storage_path),
        max_snapshots=50,
        auto_cleanup_enabled=True,
    )


@pytest.fixture
def manager(config: SnapshotConfig) -> SnapshotManager:
    """Create a fresh SnapshotManager with no initialized state."""
    return SnapshotManager(config=config)


# Tests: initialize  # noqa: ERA001


@pytest.mark.asyncio
async def test_initialize_creates_storage_dir(
    manager: SnapshotManager, config: SnapshotConfig
) -> None:
    """initialize() creates the storage directory."""
    resolved = Path(config.storage_path).expanduser().resolve()  # noqa: ASYNC240
    assert not resolved.exists()

    await manager.initialize()

    assert resolved.exists()
    assert resolved.is_dir()
    # Cleanup the background task so test exits cleanly
    await manager.shutdown()


@pytest.mark.asyncio
async def test_initialize_loads_existing_snapshots(
    manager: SnapshotManager, config: SnapshotConfig
) -> None:
    """initialize() loads pre-existing snapshot JSON files from disk."""
    resolved = Path(config.storage_path).expanduser().resolve()  # noqa: ASYNC240
    resolved.mkdir(parents=True, exist_ok=True)

    # Write two snapshot files manually (simulating prior session)
    snap_a_id = uuid.uuid4()
    snap_b_id = uuid.uuid4()
    snap_a = StateSnapshot(
        snapshot_id=snap_a_id,
        trigger="test_a",
        description="first",
        version=1,
    )
    snap_b = StateSnapshot(
        snapshot_id=snap_b_id,
        trigger="test_b",
        description="second",
        version=2,
    )
    for snap in (snap_a, snap_b):
        (resolved / f"{snap.snapshot_id}.json").write_text(
            json.dumps(snap.to_dict(), indent=2, default=str), encoding="utf-8"
        )

    await manager.initialize()

    loaded = await manager.list_snapshots()
    loaded_ids = {str(s.snapshot_id) for s in loaded}
    assert str(snap_a_id) in loaded_ids
    assert str(snap_b_id) in loaded_ids

    # Verify one field is correctly deserialized
    assert any(s.description == "first" for s in loaded)
    assert any(s.trigger == "test_b" for s in loaded)

    await manager.shutdown()


@pytest.mark.asyncio
async def test_initialize_handles_malformed_json(
    manager: SnapshotManager, config: SnapshotConfig
) -> None:
    """initialize() skips malformed JSON files without crashing."""
    resolved = Path(config.storage_path).expanduser().resolve()  # noqa: ASYNC240
    resolved.mkdir(parents=True, exist_ok=True)

    # Write a valid snapshot AND a broken file
    good_id = uuid.uuid4()
    snap = StateSnapshot(snapshot_id=good_id, trigger="good")
    (resolved / f"{good_id}.json").write_text(
        json.dumps(snap.to_dict(), indent=2, default=str), encoding="utf-8"
    )
    (resolved / "corrupt.json").write_text("--- not json ---", encoding="utf-8")

    await manager.initialize()

    loaded = await manager.list_snapshots()
    loaded_ids = {str(s.snapshot_id) for s in loaded}
    assert str(good_id) in loaded_ids
    # Corrupt file should be skipped, not crash

    await manager.shutdown()


# Tests: create_snapshot persistence


@pytest.mark.asyncio
async def test_create_snapshot_persists_to_disk(
    manager: SnapshotManager, tmp_storage_path: Path
) -> None:
    """create_snapshot() writes the snapshot to disk immediately."""
    await manager.initialize()

    snap = await manager.create_snapshot(
        trigger="manual",
        description="test snapshot",
        system_state=SystemState(active_agents=3),
    )

    # Should now exist on disk
    disk_data = _snapshot_on_disk(tmp_storage_path, snap.snapshot_id)
    assert disk_data is not None
    assert disk_data["trigger"] == "manual"
    assert disk_data["description"] == "test snapshot"
    assert disk_data["system_state"]["active_agents"] == 3  # type: ignore[index]

    await manager.shutdown()


@pytest.mark.asyncio
async def test_create_snapshot_increments_disk_count(
    manager: SnapshotManager, tmp_storage_path: Path
) -> None:
    """Each call to create_snapshot adds one file to disk."""
    await manager.initialize()

    for i in range(3):
        await manager.create_snapshot(trigger=f"step_{i}", description=f"snap {i}")

    assert _snapshot_json_count(tmp_storage_path) == 3
    await manager.shutdown()


# Tests: restart (survive re-init)


@pytest.mark.asyncio
async def test_snapshots_survive_restart(tmp_storage_path: Path) -> None:
    """Snapshots persist across manager instances (full restart cycle).

    Creates snapshots with one manager, shuts it down, then creates a
    fresh manager pointed at the same directory to confirm they reload.
    """
    config = SnapshotConfig(storage_path=str(tmp_storage_path), max_snapshots=50)

    # First session
    mgr1 = SnapshotManager(config=config)
    await mgr1.initialize()
    snap1 = await mgr1.create_snapshot(trigger="before_restart", description="persisted")
    snap2 = await mgr1.create_snapshot(trigger="second", description="also persisted")
    await mgr1.shutdown()

    assert _snapshot_json_count(tmp_storage_path) == 2

    # Second session — fresh manager
    mgr2 = SnapshotManager(config=config)
    await mgr2.initialize()

    loaded = await mgr2.list_snapshots()
    loaded_ids = {str(s.snapshot_id) for s in loaded}
    assert str(snap1.snapshot_id) in loaded_ids
    assert str(snap2.snapshot_id) in loaded_ids
    assert len(loaded) == 2

    # Verify content survived round-trip
    loaded_snap1 = await mgr2.get_snapshot(snap1.snapshot_id)
    assert loaded_snap1 is not None
    assert loaded_snap1.trigger == "before_restart"
    assert loaded_snap1.description == "persisted"

    await mgr2.shutdown()


# Tests: shutdown  # noqa: ERA001


@pytest.mark.asyncio
async def test_shutdown_flushes_all_snapshots(tmp_storage_path: Path) -> None:
    """shutdown() flushes all in-memory snapshots to disk."""
    config = SnapshotConfig(storage_path=str(tmp_storage_path), max_snapshots=50)
    mgr = SnapshotManager(config=config)

    await mgr.initialize()
    for i in range(5):
        await mgr.create_snapshot(trigger=f"flush_{i}")

    await mgr.shutdown()

    assert _snapshot_json_count(tmp_storage_path) == 5


@pytest.mark.asyncio
async def test_shutdown_cancels_cleanup_task(manager: SnapshotManager) -> None:
    """shutdown() cancels the background cleanup task."""
    await manager.initialize()

    assert manager._cleanup_task is not None
    assert not manager._cleanup_task.done()

    await manager.shutdown()

    assert manager._cleanup_task is None
    # The original task should be done (cancelled)
    # No exception here = success


# -- Tests: pruning --


@pytest.mark.asyncio
async def test_prune_removes_oldest_snapshots(tmp_storage_path: Path) -> None:
    """When max_snapshots is exceeded, oldest snapshots are pruned."""
    config = SnapshotConfig(storage_path=str(tmp_storage_path), max_snapshots=3)
    mgr = SnapshotManager(config=config)

    await mgr.initialize()

    # Create 5 snapshots — only 3 should survive pruning
    snap_ids = []
    for i in range(5):
        snap = await mgr.create_snapshot(
            trigger=f"keep_{i}",
            description=f"snapshot {i}",
            system_state=SystemState(active_agents=i),
        )
        snap_ids.append(snap.snapshot_id)

    assert _snapshot_json_count(tmp_storage_path) == 5

    await mgr._prune_old_snapshots()

    remaining = await mgr.list_snapshots()
    assert len(remaining) == 3

    remaining_ids = {s.snapshot_id for s in remaining}
    # Oldest 2 should be gone
    assert snap_ids[0] not in remaining_ids
    assert snap_ids[1] not in remaining_ids
    # Newest 3 survive
    assert snap_ids[2] in remaining_ids
    assert snap_ids[3] in remaining_ids
    assert snap_ids[4] in remaining_ids

    assert _snapshot_json_count(tmp_storage_path) == 3

    await mgr.shutdown()


@pytest.mark.asyncio
async def test_prune_noop_when_under_limit(tmp_storage_path: Path) -> None:
    """Pruning is a no-op when count <= max_snapshots."""
    config = SnapshotConfig(storage_path=str(tmp_storage_path), max_snapshots=50)
    mgr = SnapshotManager(config=config)

    await mgr.initialize()
    for _ in range(5):
        await mgr.create_snapshot(trigger="under_limit")

    await mgr._prune_old_snapshots()

    assert len(await mgr.list_snapshots()) == 5
    await mgr.shutdown()


# Tests: error handling


@pytest.mark.asyncio
async def test_persist_without_initialize_does_not_crash(
    tmp_storage_path: Path,
) -> None:
    """Calling create_snapshot before initialize() should not crash.

    The _persist_snapshot helper early-returns when _storage_path is None.
    """
    config = SnapshotConfig(storage_path=str(tmp_storage_path), max_snapshots=50)
    mgr = SnapshotManager(config=config)

    # No initialize() call — _storage_path is None
    snap = await mgr.create_snapshot(trigger="no_init")
    assert snap.snapshot_id is not None
    # Should NOT have written to disk because storage_path was None
    assert _snapshot_json_count(tmp_storage_path) == 0


@pytest.mark.asyncio
async def test_shutdown_handles_missing_storage_dir(
    manager: SnapshotManager, config: SnapshotConfig
) -> None:
    """shutdown() does not crash if the storage directory was deleted externally."""
    await manager.initialize()

    resolved = Path(config.storage_path).expanduser().resolve()  # noqa: ASYNC240
    # Delete the directory after initialize
    for f in resolved.glob("*.json"):
        f.unlink()
    resolved.rmdir()

    # Should not raise
    await manager.shutdown()


# Tests: round-trip serialization


def test_state_snapshot_to_dict_round_trip() -> None:
    """StateSnapshot.to_dict() → from_dict() is lossless."""
    original = StateSnapshot(
        snapshot_id=uuid.uuid4(),
        agent_id="agent-42",
        state={"key": "value", "nested": {"a": 1}},
        version=7,
        trigger="automated",
        description="a test snapshot",
        system_state=SystemState(
            system_id="sys-1",
            active_agents=5,
            total_messages=100,
            uptime_seconds=3600.0,
        ),
        agent_states={"a1": {"status": "active"}},
        metadata={"foo": "bar"},
    )

    serialized = original.to_dict()
    restored = StateSnapshot.from_dict(serialized)

    assert restored.snapshot_id == original.snapshot_id
    assert restored.agent_id == original.agent_id
    assert restored.state == original.state
    assert restored.version == original.version
    assert restored.trigger == original.trigger
    assert restored.description == original.description
    assert restored.system_state is not None
    assert restored.system_state.system_id == "sys-1"
    assert restored.system_state.active_agents == 5
    assert restored.agent_states == original.agent_states
    assert restored.metadata == original.metadata
