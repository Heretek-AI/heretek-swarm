"""Tests for Goal persistence — FileGoalStore and Goal data model.

Verifies that:
- Goal.from_dict / to_dict round-trips correctly
- Vote serialization is lossless
- FileGoalStore CRUD operations (save, load, load_all, update_status,
  add_vote, delete, exists, count) work correctly
- Atomic writes produce valid JSON with no .tmp leftovers
- Corrupt/missing files are handled gracefully
- Thread safety under concurrent reads
"""

from __future__ import annotations

import json
import threading
import time
from typing import TYPE_CHECKING

import pytest


pytestmark = [pytest.mark.unit]

from heretek_swarm.goals.models import Goal, Vote
from heretek_swarm.goals.store import FileGoalStore

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_store_path(tmp_path: Path) -> Path:
    """Provide a fresh temp file path for each test."""
    return tmp_path / "goals.json"


@pytest.fixture
def store(tmp_store_path: Path) -> FileGoalStore:
    """Create a FileGoalStore backed by a temp file."""
    return FileGoalStore(store_path=tmp_store_path)


@pytest.fixture
def sample_goal() -> Goal:
    """A minimal but valid Goal object."""
    return Goal(
        id="goal-001",
        title="Improve Agent Communication",
        description=(
            "Optimize internal agent-to-agent messaging to reduce latency "
            "and improve reliability across the swarm."
        ),
        success_criteria=[
            "P99 message latency < 50ms",
            "Zero dropped messages over 24h",
        ],
        status="proposed",
    )


@pytest.fixture
def second_goal() -> Goal:
    """A second goal for multi-goal tests."""
    return Goal(
        id="goal-002",
        title="Add Monitoring Dashboard",
        description="Build a real-time monitoring dashboard for swarm health.",
        success_criteria=["Dashboard shows agent status within 1s of change"],
        status="proposed",
        estimated_node_types=["agent", "tool", "output"],
    )


# ---------------------------------------------------------------------------
# Goal model tests
# ---------------------------------------------------------------------------


class TestGoalModel:
    """Unit tests for Goal and Vote data model serialization."""

    def test_goal_to_dict_round_trip(self, sample_goal: Goal):
        """to_dict -> from_dict is lossless."""
        data = sample_goal.to_dict()
        restored = Goal.from_dict(data)
        assert restored.id == sample_goal.id
        assert restored.title == sample_goal.title
        assert restored.description == sample_goal.description
        assert restored.success_criteria == sample_goal.success_criteria
        assert restored.status == sample_goal.status
        assert restored.votes == sample_goal.votes

    def test_goal_auto_populates_timestamps(self):
        """Timestamps are auto-populated on creation."""
        goal = Goal(id="g-1", title="T", description="D")
        assert goal.created_at
        assert goal.updated_at
        assert "T" in goal.created_at

    def test_goal_from_dict_missing_optional_fields(self):
        """from_dict gracefully handles missing optional keys."""
        minimal = {"id": "g-min", "title": "Min", "description": "Minimal goal"}
        goal = Goal.from_dict(minimal)
        assert goal.id == "g-min"
        assert goal.success_criteria == []
        assert goal.status == "proposed"
        assert goal.votes == []
        assert goal.estimated_node_types == []
        assert goal.execution_results is None

    def test_goal_add_vote(self, sample_goal: Goal):
        """add_vote appends a Vote and bumps updated_at."""
        old_updated = sample_goal.updated_at
        time.sleep(0.001)
        vote = Vote(
            agent_id="alpha",
            decision="approve",
            confidence=0.85,
            rationale="Solid strategy",
        )
        sample_goal.add_vote(vote)
        assert len(sample_goal.votes) == 1
        assert sample_goal.votes[0]["agent_id"] == "alpha"
        assert sample_goal.updated_at != old_updated

    def test_vote_auto_populates_timestamp(self):
        """Vote auto-populates timestamp."""
        vote = Vote(agent_id="beta", decision="reject", confidence=0.2)
        assert vote.timestamp
        assert "T" in vote.timestamp

    def test_vote_respects_explicit_timestamp(self):
        """Vote preserves an explicit timestamp."""
        vote = Vote(
            agent_id="delta",
            decision="abstain",
            confidence=0.5,
            timestamp="2025-01-15T12:00:00Z",
        )
        assert vote.timestamp == "2025-01-15T12:00:00Z"

    def test_goal_default_status_is_proposed(self):
        """New goals default to 'proposed' status."""
        goal = Goal(id="g-2", title="X", description="Y")
        assert goal.status == "proposed"


# ---------------------------------------------------------------------------
# FileGoalStore unit tests
# ---------------------------------------------------------------------------


class TestFileGoalStore:
    """Unit tests for FileGoalStore CRUD."""

    def test_save_and_load(self, store, sample_goal):
        """save() persists and load() retrieves the same Goal."""
        store.save(sample_goal)
        loaded = store.load("goal-001")
        assert loaded is not None
        assert loaded.id == "goal-001"
        assert loaded.title == "Improve Agent Communication"
        assert loaded.status == "proposed"
        assert len(loaded.success_criteria) == 2

    def test_load_nonexistent(self, store):
        """load() returns None for unknown IDs."""
        assert store.load("does-not-exist") is None

    def test_save_updates_metadata(self, store, sample_goal):
        """Saving twice preserves created_at but refreshes updated_at."""
        store.save(sample_goal)
        first = store.load("goal-001")
        assert first is not None

        sample_goal.title = "Renamed Goal"
        sample_goal.status = "voting"
        store.save(sample_goal)
        second = store.load("goal-001")
        assert second is not None

        assert first.created_at == second.created_at
        assert second.title == "Renamed Goal"
        assert second.status == "voting"

    def test_load_all(self, store, sample_goal, second_goal):
        """load_all() returns every persisted goal, sorted by created_at."""
        store.save(sample_goal)
        store.save(second_goal)
        all_goals = store.load_all()
        assert len(all_goals) == 2
        ids = {g.id for g in all_goals}
        assert "goal-001" in ids
        assert "goal-002" in ids

    def test_update_status(self, store, sample_goal):
        """update_status changes status atomically."""
        store.save(sample_goal)
        updated = store.update_status("goal-001", "voting")
        assert updated is not None
        assert updated.status == "voting"

        reloaded = store.load("goal-001")
        assert reloaded is not None
        assert reloaded.status == "voting"

    def test_update_status_nonexistent(self, store):
        """update_status returns None for unknown goal IDs."""
        assert store.update_status("ghost", "accepted") is None

    def test_add_vote(self, store, sample_goal):
        """add_vote atomically appends a Vote."""
        store.save(sample_goal)
        vote = Vote(
            agent_id="alpha",
            decision="approve",
            confidence=0.9,
            rationale="Makes sense",
        )
        updated = store.add_vote("goal-001", vote)
        assert updated is not None
        assert len(updated.votes) == 1
        assert updated.votes[0]["agent_id"] == "alpha"

    def test_add_vote_nonexistent(self, store):
        """add_vote returns None for unknown goal IDs."""
        vote = Vote(agent_id="zeta", decision="abstain", confidence=0.5)
        assert store.add_vote("ghost", vote) is None

    def test_delete(self, store, sample_goal):
        """delete removes the goal and returns True."""
        store.save(sample_goal)
        assert store.delete("goal-001") is True
        assert store.load("goal-001") is None

    def test_delete_nonexistent(self, store):
        """delete returns False for unknown IDs."""
        assert store.delete("nope") is False

    def test_exists(self, store, sample_goal):
        """exists reflects presence accurately."""
        assert store.exists("goal-001") is False
        store.save(sample_goal)
        assert store.exists("goal-001") is True

    def test_count(self, store, sample_goal, second_goal):
        """count returns the number of persisted goals."""
        assert store.count() == 0
        store.save(sample_goal)
        assert store.count() == 1
        store.save(second_goal)
        assert store.count() == 2

    def test_atomic_write_produces_valid_json(self, store, sample_goal):
        """The on-disk file is valid JSON after save."""
        store.save(sample_goal)
        raw = store._path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "goal-001" in data

    def test_no_tmp_file_left_behind(self, store, sample_goal):
        """Atomic write cleans up the .tmp file."""
        store.save(sample_goal)
        tmp = store._path.with_suffix(".json.tmp")
        assert not tmp.exists()

    def test_empty_file_returns_empty_list(self, tmp_store_path):
        """Corrupt file is handled gracefully."""
        tmp_store_path.write_text("not valid json", encoding="utf-8")
        store = FileGoalStore(store_path=tmp_store_path)
        assert store.load_all() == []

    def test_missing_file_returns_empty_list(self, tmp_store_path):
        """Missing file means no goals persisted yet."""
        store = FileGoalStore(store_path=tmp_store_path)
        assert store.load_all() == []
        assert store.count() == 0

    def test_missing_directory_auto_created(self, tmp_path):
        """Store creates parent directories automatically."""
        deep_path = tmp_path / "a" / "b" / "goals.json"
        store = FileGoalStore(store_path=deep_path)
        goal = Goal(id="g-deep", title="Deep", description="Nested dirs")
        store.save(goal)
        assert deep_path.exists()


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------


class TestFileGoalStoreConcurrency:
    """Thread-safety tests for FileGoalStore."""

    def test_concurrent_saves_no_corruption(self, store):
        """Multiple threads saving concurrently should not corrupt the file."""
        errors: list[Exception] = []

        def save_goal(i: int) -> None:
            try:
                goal = Goal(
                    id=f"goal-{i:03d}",
                    title=f"Goal {i}",
                    description=f"Concurrent goal #{i}",
                )
                store.save(goal)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=save_goal, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent saves raised errors: {errors}"
        all_goals = store.load_all()
        assert len(all_goals) == 10

    def test_concurrent_reads(self, store, sample_goal):
        """Concurrent reads should not interfere."""
        store.save(sample_goal)
        results: list[Goal | None] = []

        def read_goal() -> None:
            results.append(store.load("goal-001"))

        threads = [threading.Thread(target=read_goal) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r is not None for r in results)
        assert all(r.id == "goal-001" for r in results)  # type: ignore[union-attr]
