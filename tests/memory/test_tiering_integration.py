"""
Integration Tests for Memory Tier Migration

End-to-end tests for the tier migration system:
1. End-to-end tier migration
2. Data integrity after migration
3. Access pattern tracking during migration
"""

import asyncio
from datetime import datetime, timedelta, timezone

from src.heretek_swarm.memory.tiering import (
    MemoryTier,
    MemoryTieringSystem,
    MigrationTrigger,
    TieredMemory,
    TierMigrationStatus,
)


class TestEndToEndTierMigration:
    """End-to-end tests for complete tier migration lifecycle."""

    def test_full_lifecycle_hot_to_warm_to_cold(self):
        """Test complete migration lifecycle through all tiers."""
        tiering = MemoryTieringSystem()

        # Store in hot tier
        original_data = {"content": "test content", "value": 123}
        original_metadata = {
            "user": "test_user",
            "priority": 0.9,
            "tags": ["important"],
        }

        memory = tiering.store(
            memory_id="lifecycle_1",
            data=original_data,
            metadata=original_metadata,
            target_tier=MemoryTier.L1_HOT,
        )

        # Verify initial state
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        assert len(hot_memories) == 1
        assert hot_memories[0].memory_id == "lifecycle_1"

        # Migrate hot -> warm
        async def migrate_hot_to_warm():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="Low recency - lifecycle test",
            )

        record1 = asyncio.run(migrate_hot_to_warm())
        assert record1.status == TierMigrationStatus.COMPLETED

        # Verify after first migration
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert len(warm_memories) == 1
        assert warm_memories[0].memory_id == "lifecycle_1"
        assert warm_memories[0].data == original_data
        assert warm_memories[0].metadata == original_metadata

        # Migrate warm -> cold
        async def migrate_warm_to_cold():
            return await tiering._migrate_memory(
                memory=warm_memories[0],
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="Very low recency - lifecycle test",
            )

        record2 = asyncio.run(migrate_warm_to_cold())
        assert record2.status == TierMigrationStatus.COMPLETED

        # Verify final state
        cold_memories = tiering.get_memories_by_tier(MemoryTier.L3_COLD)
        assert len(cold_memories) == 1

        final_memory = cold_memories[0]
        assert final_memory.memory_id == "lifecycle_1"
        assert final_memory.data == original_data
        assert final_memory.metadata == original_metadata

        # Verify tier history
        assert len(final_memory.tier_history) >= 3  # created + 2 migrations

        # Verify no memory in other tiers
        hot_count = len(tiering.get_memories_by_tier(MemoryTier.L1_HOT))
        warm_count = len(tiering.get_memories_by_tier(MemoryTier.L2_WARM))
        assert hot_count == 0
        assert warm_count == 0

    def test_promotion_cold_to_warm_to_hot(self):
        """Test promotion path from cold to hot tier."""
        tiering = MemoryTieringSystem()

        # Start in cold tier
        memory = tiering.store(
            memory_id="promotion_1",
            data={"content": "frequently accessed"},
            metadata={"access_pattern": "high_frequency"},
            target_tier=MemoryTier.L3_COLD,
        )

        # Cold -> Warm
        async def migrate_cold_to_warm():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="High frequency detected - promotion test",
            )

        record1 = asyncio.run(migrate_cold_to_warm())
        assert record1.status == TierMigrationStatus.COMPLETED

        # Warm -> Hot
        async def migrate_warm_to_hot():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L1_HOT,
                trigger=MigrationTrigger.ACCESS_PATTERN,
                reason="Very high frequency - promotion test",
            )

        record2 = asyncio.run(migrate_warm_to_hot())
        assert record2.status == TierMigrationStatus.COMPLETED

        # Verify final state in hot tier
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        assert len(hot_memories) == 1
        assert hot_memories[0].memory_id == "promotion_1"

    def test_migration_with_automatic_policy(self):
        """Test migration using automatic policy evaluation."""
        tiering = MemoryTieringSystem(enable_auto_migration=False)

        # Create memory that would trigger hot->warm policy
        memory = tiering.store(
            memory_id="policy_test_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Manually set old access time to trigger demotion
        old_time = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
        memory.last_accessed = old_time
        memory.access_count = 1

        # Run policy evaluation
        async def evaluate():
            return await tiering._evaluate_and_migrate()

        migrated_count = asyncio.run(evaluate())

        # Should have migrated based on recency policy
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert len(warm_memories) == 1
        assert warm_memories[0].memory_id == "policy_test_1"


class TestDataIntegrityAfterMigration:
    """Test data integrity is maintained after migrations."""

    def test_data_integrity_after_multiple_migrations(self):
        """Test data survives multiple migrations unchanged."""
        tiering = MemoryTieringSystem()

        # Complex data structure
        complex_data = {
            "strings": ["a", "b", "c"],
            "numbers": [1, 2, 3],
            "nested": {
                "deep": {
                    "value": "test",
                    "array": [4, 5, 6],
                }
            },
            "mixed": [
                {"type": "object"},
                [1, 2, 3],
                "string",
                42,
                True,
            ],
        }

        memory = tiering.store(
            memory_id="integrity_1",
            data=complex_data,
            metadata={"checksum": "abc123"},
            target_tier=MemoryTier.L1_HOT,
        )

        # Migrate through all tiers
        async def migrate_all():
            # Hot -> Warm
            await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Integrity test 1",
            )

            # Warm -> Cold
            await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.MANUAL,
                reason="Integrity test 2",
            )

            # Cold -> Warm
            await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Integrity test 3",
            )

            # Warm -> Hot
            await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L1_HOT,
                trigger=MigrationTrigger.MANUAL,
                reason="Integrity test 4",
            )

        asyncio.run(migrate_all())

        # Verify data integrity
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        final_memory = hot_memories[0]

        assert final_memory.data == complex_data
        assert final_memory.metadata["checksum"] == "abc123"

    def test_size_tracking_after_migration(self):
        """Test that size_bytes is tracked correctly after migration."""
        tiering = MemoryTieringSystem()

        large_data = {"items": [f"item_{i}" for i in range(1000)]}
        expected_size = len(str(large_data))

        memory = tiering.store(
            memory_id="size_tracking_1",
            data=large_data,
            metadata={},
            target_tier=MemoryTier.L1_HOT,
            size_bytes=expected_size,
        )

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.MANUAL,
                reason="Size tracking test",
            )

        asyncio.run(migrate())

        # Verify size is preserved
        cold_memories = tiering.get_memories_by_tier(MemoryTier.L3_COLD)
        assert cold_memories[0].size_bytes == expected_size

    def test_compression_state_after_migration(self):
        """Test that compression state is preserved during migration."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="compression_1",
            data={"compressed": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Set compression state
        memory.compressed = True
        memory.compression_ratio = 0.65

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L3_COLD,
                trigger=MigrationTrigger.MANUAL,
                reason="Compression state test",
            )

        asyncio.run(migrate())

        # Verify compression state preserved
        cold_memories = tiering.get_memories_by_tier(MemoryTier.L3_COLD)
        assert cold_memories[0].compressed is True
        assert abs(cold_memories[0].compression_ratio - 0.65) < 0.001


class TestAccessPatternTracking:
    """Test access pattern tracking during and after migration."""

    def test_access_count_preserved_during_migration(self):
        """Test that access count is preserved during migration."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="access_count_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Simulate accesses
        memory.access_count = 500

        # Migrate
        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Access count test",
            )

        asyncio.run(migrate())

        # Verify access count preserved
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert warm_memories[0].access_count == 500

    def test_last_accessed_updated_on_get(self):
        """Test that last_accessed is updated when memory is accessed."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="access_time_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        original_accessed = memory.last_accessed

        # Wait a bit
        import time
        time.sleep(0.1)

        # Access memory
        accessed_memory = tiering.get_memory("access_time_1")

        # Verify last_accessed was updated
        assert accessed_memory.last_accessed >= original_accessed
        assert accessed_memory.access_count == 1

    def test_access_pattern_triggers_migration(self):
        """Test that access patterns correctly trigger migrations."""
        tiering = MemoryTieringSystem(enable_auto_migration=False)

        # Create memory with low recency (very old access time)
        tiering.store(
            memory_id="pattern_trigger_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        # Get the memory from storage and set old access time
        # This ensures we're modifying the actual stored reference
        memory = tiering.get_memory("pattern_trigger_1")

        # Set very old access time to trigger demotion (hot_to_warm threshold is 0.3)
        # Need recency score below 0.3, which requires age > ~48 hours
        # Use 10 days to be safe - this will trigger both hot->warm and warm->cold
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        memory.last_accessed = old_time

        # Evaluate policies
        async def evaluate():
            return await tiering._evaluate_and_migrate()

        migrated_count = asyncio.run(evaluate())

        # Check all tiers for the memory
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        cold_memories = tiering.get_memories_by_tier(MemoryTier.L3_COLD)

        # Memory should be in exactly one tier (no data loss)
        total_count = len(warm_memories) + len(hot_memories) + len(cold_memories)
        assert total_count == 1, f"Memory should be in exactly one tier, but found {total_count} total"

        # Migration should have happened (memory moved from hot)
        assert migrated_count >= 1, "Expected at least one migration to occur"

        # Memory should NOT be in hot tier anymore (it was demoted)
        assert len(hot_memories) == 0, "Memory should have been demoted from hot tier"

        # Memory should be in warm or cold tier (depending on how many policies triggered)
        # With very low recency, it may go all the way to cold
        assert len(warm_memories) + len(cold_memories) == 1

        # Verify the memory is the correct one
        if warm_memories:
            assert warm_memories[0].memory_id == "pattern_trigger_1"
        else:
            assert cold_memories[0].memory_id == "pattern_trigger_1"

    def test_concurrent_access_during_migration(self):
        """Test that concurrent access during migration is handled."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="concurrent_access_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Concurrent access test",
            )

        async def access_during_migration():
            # Simulate access during migration
            await asyncio.sleep(0.01)
            return tiering.get_memory("concurrent_access_1")

        async def run_concurrent():
            # Start migration
            migrate_task = asyncio.create_task(migrate())

            # Access during migration - must await the coroutine
            await asyncio.sleep(0.005)
            accessed = await access_during_migration()

            # Wait for migration
            record = await migrate_task

            return record, accessed

        record, accessed = asyncio.run(run_concurrent())

        # Migration should complete
        assert record.status == TierMigrationStatus.COMPLETED

        # Memory should be accessible in target tier
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert len(warm_memories) == 1


class TestMigrationStatistics:
    """Test migration statistics and reporting."""

    def test_statistics_after_full_lifecycle(self):
        """Test statistics tracking through full migration lifecycle."""
        tiering = MemoryTieringSystem()

        # Create and migrate multiple memories
        for i in range(5):
            memory = tiering.store(
                memory_id=f"stats_lifecycle_{i}",
                data={"index": i},
                metadata={},
                target_tier=MemoryTier.L1_HOT,
            )

            # Migrate to warm
            async def migrate():
                return await tiering._migrate_memory(
                    memory=memory,
                    target_tier=MemoryTier.L2_WARM,
                    trigger=MigrationTrigger.MANUAL,
                    reason="Stats test",
                )

            asyncio.run(migrate())

        # Get statistics
        stats = tiering.get_statistics()

        # Verify statistics
        assert stats.migrations_total == 5
        assert stats.migrations_successful == 5
        assert stats.migrations_failed == 0
        assert stats.memories_per_tier.get("l2_warm", 0) == 5
        assert stats.memories_per_tier.get("l1_hot", 0) == 0

    def test_report_generation(self):
        """Test comprehensive report generation."""
        tiering = MemoryTieringSystem()

        # Create and migrate some memories
        for i in range(3):
            memory = tiering.store(
                memory_id=f"report_{i}",
                data={"index": i},
                metadata={},
                target_tier=MemoryTier.L1_HOT,
            )

            async def migrate():
                return await tiering._migrate_memory(
                    memory=memory,
                    target_tier=MemoryTier.L2_WARM,
                    trigger=MigrationTrigger.MANUAL,
                    reason="Report test",
                )

            asyncio.run(migrate())

        # Generate report
        report = tiering.generate_report()

        # Verify report structure
        assert "statistics" in report
        assert "tier_utilization" in report
        assert "recent_migrations" in report
        assert "policy_effectiveness" in report
        assert "recommendations" in report

        # Verify statistics in report
        assert report["statistics"]["migrations"]["total"] == 3
        assert report["statistics"]["migrations"]["successful"] == 3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_migration_to_same_tier_fails(self):
        """Test that migrating to the same tier fails gracefully."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="edge_same_tier_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        async def migrate_same():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L1_HOT,  # Same tier
                trigger=MigrationTrigger.MANUAL,
                reason="Should fail",
            )

        record = asyncio.run(migrate_same())

        # Should fail with appropriate error
        assert record.status == TierMigrationStatus.FAILED
        assert "same tier" in record.error.lower()

        # Memory should still be in hot tier (rollback)
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        assert len(hot_memories) == 1

    def test_migration_of_nonexistent_memory_fails(self):
        """Test that migrating non-existent memory fails gracefully."""
        tiering = MemoryTieringSystem()

        # Create fake memory object
        fake_memory = TieredMemory(
            memory_id="nonexistent",
            current_tier=MemoryTier.L1_HOT,
            data={"test": "data"},
        )

        async def migrate_fake():
            return await tiering._migrate_memory(
                memory=fake_memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Should fail",
            )

        record = asyncio.run(migrate_fake())

        # Should fail
        assert record.status == TierMigrationStatus.FAILED

        # Should be rolled back
        assert record.rolled_back is True

    def test_migration_with_empty_metadata(self):
        """Test migration with empty metadata."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="edge_empty_meta_1",
            data={"test": "data"},
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="Empty metadata test",
            )

        record = asyncio.run(migrate())

        # Should succeed
        assert record.status == TierMigrationStatus.COMPLETED

        # Verify empty metadata preserved
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert warm_memories[0].metadata == {}

    def test_migration_with_none_data(self):
        """Test migration with None data value."""
        tiering = MemoryTieringSystem()

        memory = tiering.store(
            memory_id="edge_none_data_1",
            data=None,
            metadata={},
            target_tier=MemoryTier.L1_HOT,
        )

        async def migrate():
            return await tiering._migrate_memory(
                memory=memory,
                target_tier=MemoryTier.L2_WARM,
                trigger=MigrationTrigger.MANUAL,
                reason="None data test",
            )

        record = asyncio.run(migrate())

        # Should succeed
        assert record.status == TierMigrationStatus.COMPLETED

        # Verify None data preserved
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        assert warm_memories[0].data is None
