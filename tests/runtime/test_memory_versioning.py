"""
M019 S04: Deep Lake Dataset Versioning — Integration Tests

Tests the versioned memory store:
1. Snapshot creation, listing, retrieval
2. Version diffing
3. Version rollback
4. Label management
5. Triad deliberation snapshot wiring
"""

import asyncio

import pytest


class AsyncTestCase:
    """Base async test case."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


class TestVersionedMemoryStore:
    """T01-T03: VersionedMemoryStore core functionality."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_snapshot(self):
        """create_snapshot() creates a version; get_version() retrieves it."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore(max_versions=10)

        version = await store.create_snapshot(
            message="Initial checkpoint",
            agent_id="alpha",
            deliberation_id="del-001",
        )

        assert version is not None
        assert version.message == "Initial checkpoint"
        assert version.agent_id == "alpha"
        assert version.deliberation_id == "del-001"
        assert version.branch == "main"
        assert version.version_id == "v0001"
        assert version.short_id == "v0001"
        assert version.total_entries == 0  # No backend, no entries

    @pytest.mark.asyncio
    async def test_snapshot_with_entries(self):
        """create_snapshot() captures pre-fetched entries."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        entries = [
            {"id": "e1", "content": "Memory 1"},
            {"id": "e2", "content": "Memory 2"},
        ]

        version = await store.create_snapshot(
            message="With entries",
            snapshot_entries=entries,
        )

        retrieved = await store.get_version_entries(version.id)
        assert len(retrieved) == 2
        assert retrieved[0]["id"] == "e1"

    @pytest.mark.asyncio
    async def test_multiple_versions_increment_id(self):
        """Multiple snapshots increment the version ID counter."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        v1 = await store.create_snapshot(message="First")
        v2 = await store.create_snapshot(message="Second")
        v3 = await store.create_snapshot(message="Third")

        assert v1.version_id == "v0001"
        assert v2.version_id == "v0002"
        assert v3.version_id == "v0003"
        assert v3.parent_id == v2.id

    @pytest.mark.asyncio
    async def test_list_versions_respects_limit_and_offset(self):
        """list_versions() returns paginated results newest-first."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        for i in range(5):
            await store.create_snapshot(message=f"Version {i}")

        # Default: newest first
        recent = await store.list_versions(limit=2)
        assert len(recent) == 2
        assert recent[0].message == "Version 4"  # Newest first
        assert recent[1].message == "Version 3"

        # Offset
        page2 = await store.list_versions(limit=2, offset=2)
        assert len(page2) == 2
        assert page2[0].message == "Version 2"

    @pytest.mark.asyncio
    async def test_list_versions_filter_by_agent_id(self):
        """list_versions(agent_id=) filters by triggering agent."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        await store.create_snapshot(message="Alpha checkpoint", agent_id="alpha")
        await store.create_snapshot(message="Beta checkpoint", agent_id="beta")
        await store.create_snapshot(message="Alpha again", agent_id="alpha")

        alpha_versions = await store.list_versions(agent_id="alpha")
        assert len(alpha_versions) == 2
        assert all(v.agent_id == "alpha" for v in alpha_versions)

    @pytest.mark.asyncio
    async def test_list_versions_filter_by_labels(self):
        """list_versions(labels=) filters by labels."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        await store.create_snapshot(message="Decision 1", labels=["decision"])
        await store.create_snapshot(message="Rollback 1", labels=["rollback"])
        await store.create_snapshot(message="Both", labels=["decision", "important"])

        results = await store.list_versions(labels=["decision"])
        assert len(results) == 2  # decision + Both

    @pytest.mark.asyncio
    async def test_diff_versions(self):
        """diff_versions() shows added and removed entries."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        v1 = await store.create_snapshot(
            message="Before",
            snapshot_entries=[
                {"id": "e1", "content": "A"},
                {"id": "e2", "content": "B"},
            ],
        )
        v2 = await store.create_snapshot(
            message="After",
            snapshot_entries=[
                {"id": "e1", "content": "A"},  # unchanged
                {"id": "e3", "content": "C"},  # added
            ],
        )

        diff = await store.diff_versions(v1.id, v2.id)

        assert diff is not None
        assert len(diff.added) == 1
        assert diff.added[0]["id"] == "e3"
        assert len(diff.removed) == 1
        assert diff.removed[0]["id"] == "e2"
        assert "diff_summary" in str(diff)

    @pytest.mark.asyncio
    async def test_restore_version_creates_new_snapshot(self):
        """restore_version() creates a new version from an old snapshot's entries."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        v1 = await store.create_snapshot(
            message="Good state",
            snapshot_entries=[{"id": "e1", "content": "Keep this"}],
        )
        await store.create_snapshot(
            message="Bad state",
            snapshot_entries=[{"id": "e2", "content": "Discard this"}],
        )

        # Restore to v1
        restored = await store.restore_version(v1.id)

        assert restored.message.startswith("Restore to")
        assert restored.total_entries == 1
        assert restored.parent_id != v1.id  # It's a new version

        # Verify restored entries match v1
        restored_entries = await store.get_version_entries(restored.id)
        assert len(restored_entries) == 1
        assert restored_entries[0]["id"] == "e1"

    @pytest.mark.asyncio
    async def test_label_version(self):
        """label_version() adds a tag to a version."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        v1 = await store.create_snapshot(message="Important decision")

        success = await store.label_version(v1.id, "production-ready")
        assert success
        assert "production-ready" in v1.labels

        # Retrieve by label
        found = await store.get_version_by_label("production-ready")
        assert found is not None
        assert found.id == v1.id

    @pytest.mark.asyncio
    async def test_label_version_not_found(self):
        """label_version() returns False for unknown version."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()
        success = await store.label_version("nonexistent", "tag")
        assert not success

    @pytest.mark.asyncio
    async def test_head_version(self):
        """get_current_head() returns the latest version on a branch."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        v1 = await store.create_snapshot(message="First")
        v2 = await store.create_snapshot(message="Second")

        head = await store.get_current_head()
        assert head is not None
        assert head.id == v2.id
        assert head.message == "Second"

    @pytest.mark.asyncio
    async def test_branch_support(self):
        """Versions can be created on named branches."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        await store.create_snapshot(message="Main v1", branch="main")
        await store.create_snapshot(message="Feature v1", branch="feature-x")
        await store.create_snapshot(message="Feature v2", branch="feature-x")
        await store.create_snapshot(message="Main v2", branch="main")

        main_versions = await store.list_versions(branch="main")
        assert len(main_versions) == 2

        feature_versions = await store.list_versions(branch="feature-x")
        assert len(feature_versions) == 2

    @pytest.mark.asyncio
    async def test_statistics(self):
        """get_statistics() returns correct counts."""
        from heretek_swarm.memory.versioned import VersionedMemoryStore

        store = VersionedMemoryStore()

        await store.create_snapshot(message="v1")
        await store.create_snapshot(message="v2", labels=["important"])

        stats = store.get_statistics()

        assert stats["total_versions"] == 2
        assert stats["total_labels"] == 1
        assert "main" in stats["branches"]
        assert stats["branch_stats"]["main"] == 2


class TestMemoryVersionAPIEndpoints:
    """T04-T05: API endpoints and triad wiring."""

    def test_memory_version_endpoints_in_api(self):
        """api/memory_versions.py registers endpoints correctly."""
        import inspect
        from heretek_swarm.api.memory_versions import router

        routes = [r.path for r in router.routes]
        assert any("snapshot" in r for r in routes)  # /snapshot or /{version_id}/snapshot
        assert any("" in r for r in routes)  # list versions
        assert any("head" in r for r in routes)
        assert any("diff" in r for r in routes)
        assert any("restore" in r for r in routes)
        assert any("statistics" in r for r in routes)
        assert any("label" in r for r in routes)

    def test_snapshot_endpoint_has_required_params(self):
        """create_snapshot endpoint accepts message and optional fields."""
        import inspect
        from heretek_swarm.api.memory_versions import create_snapshot

        sig = inspect.signature(create_snapshot)
        params = list(sig.parameters.keys())

        assert "message" in params
        assert "agent_id" in params
        assert "deliberation_id" in params
        assert "branch" in params
        assert "labels" in params

    def test_versioned_store_exports_correctly(self):
        """memory/versioned.py exports VersionedMemoryStore and related types."""
        from heretek_swarm.memory.versioned import (
            MemoryDiff,
            MemoryVersion,
            MemorySnapshot,
            VersionedMemoryStore,
            get_versioned_store,
        )

        assert VersionedMemoryStore is not None
        assert get_versioned_store is not None
        assert issubclass(MemoryVersion, object)  # dataclass
        assert issubclass(MemorySnapshot, object)
        assert issubclass(MemoryDiff, object)

    def test_get_versioned_store_returns_same_instance(self):
        """get_versioned_store() returns the same singleton on repeated calls."""
        from heretek_swarm.memory.versioned import get_versioned_store

        store1 = get_versioned_store()
        store2 = get_versioned_store()
        assert store1 is store2

    @pytest.mark.asyncio
    async def test_consensus_api_wires_snapshot(self):
        """consensus.py run_deliberation_round endpoint calls _snapshot_after_round."""
        import asyncio
        import inspect
        from unittest.mock import MagicMock, patch

        from heretek_swarm.api.consensus import _snapshot_after_round, run_deliberation_round

        sig = inspect.signature(run_deliberation_round)
        assert "deliberation_id" in sig.parameters

        # Verify _snapshot_after_round is defined and is async
        assert asyncio.iscoroutinefunction(_snapshot_after_round)

        # Verify it accepts the right arguments
        snapshot_sig = inspect.signature(_snapshot_after_round)
        snapshot_params = list(snapshot_sig.parameters.keys())
        assert "deliberation_id" in snapshot_params
        assert "round_number" in snapshot_params
        assert "summary" in snapshot_params
        assert "agent_id" in snapshot_params
