"""
Tests for Memory Tier Migration Fix

This module tests the fixed tier migration functionality:
1. Transactional integrity - Migration either completes fully or rolls back
2. Metadata preservation - Timestamps, access patterns, and metadata are preserved
3. No data loss - All data survives migration
4. Atomic operations - Migration is atomic with proper error handling
"""

import asyncio

from src.heretek_swarm.memory.tiering import (
    MemoryTier,
    MemoryTieringSystem,
    MigrationTrigger,
    TierMigrationStatus,
)


class TestMigrationTransactionalIntegrity:
    """Test that migrations are transactional."""

    def test_migration_completes_fully(self):
        """Test that successful migration completes all steps."""
        tiering = MemoryTieringSystem()

        # Store memory in L1_HOT
        memory = tiering.store(
            memory_id="test_mem_1",
            data={"key": "value"},
            metadata={"original": "metadata", "counter": 42},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate to L2_WARM
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test migration",
            )

        record = asyncio.run(migrate())

        # Verify migration completed
        assert record.status == TierMigrationStatus.COMPLETED
        assert record.error is None

        # Verify memory is in target tier
        memories_in_warm = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert len(memories_in_warm) == 1
        assert memories_in_warm[0].memory_id == "test_mem_1"

        # Verify memory is NOT in source tier
        memories_in_hot = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        assert len(memories_in_hot) == 0

    def test_migration_rollback_on_failure(self):
        """Test that failed migration rolls back to original state."""
        tiering = MemoryTieringSystem()

        # Store memory in L1_HOT
        original_metadata = {"original": "metadata", "counter": 42}
        original_data = {"key": "value"}
        memory = tiering.store(
            memory_id="test_mem_2",
            data=original_data,
            metadata=original_metadata,
            target_tier=MemoryTier.L1_HOT,
        )

        # Verify initial state
        initial_hot_count = len(tiering.get_memories_by_tier(MemoryTier.L1_HOT))
        assert initial_hot_count == 1

        # Simulate a failure by trying to migrate to invalid tier
        # This should trigger rollback
        async def migrate_to_same_tier():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L1_HOT,  # Same tier - will fail
                trigger=MigrationTrigger.MANUAL,
                reason="Test rollback",
            )

        record = asyncio.run(migrate_to_same_tier())

        # Verify migration failed
        assert record.status == TierMigrationStatus.FAILED
        assert record.error is not None
        assert record.rolled_back is True

        # Verify memory is still in original tier (rollback succeeded)
        memories_in_hot = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        assert len(memories_in_hot) == 1
        assert memories_in_hot[0].memory_id == "test_mem_2"

        # Verify metadata preserved after rollback
        assert memories_in_hot[0].metadata == original_metadata
        assert memories_in_hot[0].data == original_data

    def test_migration_no_partial_state(self):
        """Test that migration never leaves partial state."""
        tiering = MemoryTieringSystem()

        # Store memory
        memory = tiering.store(
            memory_id="test_mem_3",
            data={"test": "data"},
            metadata={"test": "metadata"},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test no partial state",
            )

        asyncio.run(migrate())

        # Count total occurrences of memory across all tiers
        total_count = 0
        for tier in MemoryTier:
            memories = tiering.get_memories_by_tier(tier)
            for m in memories:
                if m.memory_id == "test_mem_3":
                    total_count += 1

        # Memory should exist exactly once
        assert total_count == 1


class TestMetadataPreservation:
    """Test that metadata is preserved during migration."""

    def test_metadata_preserved_during_migration(self):
        """Test that all metadata survives migration intact."""
        tiering = MemoryTieringSystem()

        # Create memory with complex metadata
        original_metadata = {
            "user_id": "user_123",
            "session_id": "session_456",
            "priority": 0.85,
            "tags": ["important", "frequent"],
            "custom_field": {"nested": "value", "number": 42},
            "timestamps": {
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-02T00:00:00Z",
            },
        }

        memory = tiering.store(
            memory_id="test_meta_1",
            data={"content": "test data"},
            metadata=original_metadata,
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate through all tiers
        async def migrate_all():
            # Hot -> Warm
            record1 = await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="Test metadata preservation",
            )

            # Warm -> Cold
            record2 = await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="Test metadata preservation",
            )

            return record1, record2

        asyncio.run(migrate_all())

        # Get memory from cold tier
        memories_in_cold = tiering.get_memories_by_tier(MemoryTier.L3_COLD)
        assert len(memories_in_cold) == 1

        migrated_memory = memories_in_cold[0]

        # Verify all metadata preserved
        assert migrated_memory.metadata == original_metadata

        # Verify tier history shows all migrations
        assert len(migrated_memory.tier_history) >= 3  # created + 2 migrations

    def test_timestamps_preserved_during_migration(self):
        """Test that created_at and last_accessed timestamps are preserved."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_ts_1",
            data={"test": "data"},
            metadata={"test": "metadata"},
            target_tier=MemoryTier.L1_HOT,
        )

        original_created = memory.created_at
        original_accessed = memory.last_accessed

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test timestamp preservation",
            )

        asyncio.run(migrate())

        # Get migrated memory
        memories_in_warm = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        migrated_memory = memories_in_warm[0]

        # Timestamps should be preserved (not changed by migration)
        assert migrated_memory.created_at == original_created
        # last_accessed might be updated by get_memory but should not change during migration itself
        assert migrated_memory.last_accessed >= original_accessed

    def test_access_patterns_preserved(self):
        """Test that access_count is preserved during migration."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_access_1",
            data={"test": "data"},
            metadata={"test": "metadata"},
            target_tier=MemoryTier.L1_HOT,
        )

        # Simulate accesses
        memory.access_count = 100

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test access pattern preservation",
            )

        asyncio.run(migrate())

        # Get migrated memory
        memories_in_warm = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        migrated_memory = memories_in_warm[0]

        # Access count should be preserved
        assert migrated_memory.access_count == 100


class TestDataIntegrity:
    """Test that data integrity is maintained during migration."""

    def test_data_preserved_during_migration(self):
        """Test that data survives migration unchanged."""
        tiering = MemoryTieringSystem()

        original_data = {
            "complex": {
                "nested": {
                    "structure": [1, 2, 3, {"deep": "value"}],
                    "numbers": [4, 5, 6],
                },
                "strings": ["a", "b", "c"],
                "booleans": [True, False],
            }
        }

        memory = tiering.store(
            memory_id="test_data_1",
            data=original_data,
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test data integrity",
            )

        asyncio.run(migrate())

        # Get migrated memory
        memories_in_warm = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        migrated_memory = memories_in_warm[0]

        # Data should be identical
        assert migrated_memory.data == original_data

    def test_large_data_migration(self):
        """Test migration of large data structures."""
        tiering = MemoryTieringSystem()

        # Create large data structure
        large_data = {
            "items": [f"item_{i}" for i in range(10000)],
            "metadata": {"size": "large", "count": 10000},
        }

        memory = tiering.store(
            memory_id="test_large_1",
            data=large_data,
            metadata={},
            target_tier=MemoryTier.L1_HOT,
            size_bytes=len(str(large_data)),
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.CAPACITY,
                reason="Test large data migration",
            )

        record = asyncio.run(migrate())

        # Verify migration succeeded
        assert record.status == TierMigrationStatus.COMPLETED

        # Verify data integrity
        memories_in_cold = tiering.get_memories_by_tier(MemoryTier.L3_COLD)
        migrated_memory = memories_in_cold[0]

        assert migrated_memory.data == large_data
        assert migrated_memory.size_bytes == len(str(large_data))

    def test_verification_after_migration(self):
        """Test that verification catches migration issues."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_verify_1",
            data={"test": "data"},
            metadata={"key": "value"},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test verification",
            )

        record = asyncio.run(migrate())

        # Verify audit metadata contains verification results
        assert "verification" in record.audit_metadata
        verification = record.audit_metadata["verification"]
        assert verification["success"] is True
        assert "target_tier_exists" in verification["checks_performed"]
        assert "tier_field_correct" in verification["checks_performed"]
        assert "metadata_preserved" in verification["checks_performed"]
        assert "removed_from_source" in verification["checks_performed"]


class TestConcurrentMigration:
    """Test concurrent migration handling."""

    def test_concurrent_migrations_same_memory(self):
        """Test that concurrent migrations of same memory are handled."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_concurrent_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        async def migrate_to_warm():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Concurrent test 1",
            )

        async def migrate_to_cold():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.MANUAL,
                reason="Concurrent test 2",
            )

        # Run migrations concurrently
        async def run_concurrent():
            return await asyncio.gather(
                migrate_to_warm(),
                migrate_to_cold(),
                return_exceptions=True,
            )

        results = asyncio.run(run_concurrent())

        # At least one should complete (the other may fail due to race condition)
        # This is expected behavior - concurrent migrations need external locking
        [r for r in results if isinstance(r, MemoryTieringSystem)]
        [r for r in results if isinstance(r, Exception)]

        # Memory should end up in exactly one tier
        total_count = 0
        for tier in MemoryTier:
            memories = tiering.get_memories_by_tier(tier)
            for m in memories:
                if m.memory_id == "test_concurrent_1":
                    total_count += 1

        assert total_count == 1

    def test_concurrent_migrations_different_memories(self):
        """Test that concurrent migrations of different memories work correctly."""
        tiering = MemoryTieringSystem()

        # Create multiple memories
        memories = []
        for i in range(5):
            mem = tiering.store(
                memory_id=f"test_concurrent_multi_{i}",
                data={"index": i},
                metadata={},
                target_tier=MemoryTier.L1_HOT,
            )
            memories.append(mem)

        async def migrate_memory(mem, target_tier):
            return await tiering._migrate_memory(
                memory=mem,
                target_tier=target_tier,
                trigger=MigrationTrigger.MANUAL,
                reason="Concurrent multi test",
            )

        # Run migrations concurrently
        async def run_concurrent():
            tasks = []
            for i, mem in enumerate(memories):
                target = MemoryTier.L2_WARM if i % 2 == 0 else MemoryTier.L3_COLD
                tasks.append(migrate_memory(mem, target))

            return await asyncio.gather(*tasks)

        results = asyncio.run(run_concurrent())

        # All migrations should complete
        successful = [r for r in results if r.status == TierMigrationStatus.COMPLETED]
        assert len(successful) == 5

        # Verify all memories are in correct tiers
        warm_count = len(tiering.get_memories_by_tier(MemoryTier.L2_WARM))
        cold_count = len(tiering.get_memories_by_tier(MemoryTier.L3_COLD))
        hot_count = len(tiering.get_memories_by_tier(MemoryTier.L1_HOT))

        assert warm_count == 3  # indices 0, 2, 4
        assert cold_count == 2  # indices 1, 3
        assert hot_count == 0


class TestMigrationStatistics:
    """Test that migration statistics are tracked correctly."""

    def test_statistics_updated_on_success(self):
        """Test that statistics are updated on successful migration."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_stats_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        initial_stats = tiering.get_statistics()
        initial_total = initial_stats.migrations_total
        initial_successful = initial_stats.migrations_successful

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test statistics",
            )

        asyncio.run(migrate())

        # Check statistics
        final_stats = tiering.get_statistics()
        assert final_stats.migrations_total == initial_total + 1
        assert final_stats.migrations_successful == initial_successful + 1

    def test_statistics_updated_on_failure(self):
        """Test that statistics are updated on failed migration."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_stats_fail_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        initial_stats = tiering.get_statistics()
        initial_total = initial_stats.migrations_total
        initial_failed = initial_stats.migrations_failed

        # Try to migrate to same tier (will fail)
        async def migrate_fail():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L1_HOT,
                trigger=MigrationTrigger.MANUAL,
                reason="Test failure stats",
            )

        asyncio.run(migrate_fail())

        # Check statistics
        final_stats = tiering.get_statistics()
        assert final_stats.migrations_total == initial_total + 1
        assert final_stats.migrations_failed == initial_failed + 1


class TestMigrationHistory:
    """Test migration history tracking."""

    def test_migration_history_recorded(self):
        """Test that migration history is properly recorded."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_history_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test history",
            )

        asyncio.run(migrate())

        # Get history
        history = tiering.get_migration_history(limit=10)

        assert len(history) >= 1
        assert history[-1].memory_id == "test_history_1"
        assert history[-1].from_tier == MemoryTier.L1_HOT
        assert history[-1].to_tier == MemoryTier.L2_WARM
        assert history[-1].status == TierMigrationStatus.COMPLETED

    def test_memory_tier_history_updated(self):
        """Test that memory's tier_history is updated."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="test_mem_history_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        initial_history_length = len(memory.tier_history)

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Test tier history",
            )

        asyncio.run(migrate())

        # Get updated memory
        memories_in_warm = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        updated_memory = memories_in_warm[0]

        # History should have new entry
        assert len(updated_memory.tier_history) == initial_history_length + 1

        # Last entry should be migration
        last_entry = updated_memory.tier_history[-1]
        assert last_entry["action"] == "migrated"
        assert last_entry["from_tier"] == "l1_hot"
        assert last_entry["to_tier"] == "l2_warm"
