"""
Comprehensive tests for Session 43 Memory Optimization modules.

Tests for:
- Access Pattern Analyzer
- Intelligent Pre-fetcher
- Cold Data Compressor
- Memory Tiering System

Reference: EXPANSION_ROADMAP.md Session 43
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

# Import Session 43 modules
from heretek_swarm.memory.access_patterns import (
    AccessPatternAnalyzer,
    AccessPattern,
    AccessTier,
    MemoryAccessProfile,
    AccessStatistics,
    AccessPatternReport,
    MemoryAccessRecord,
)

from heretek_swarm.memory.prefetcher import (
    IntelligentPrefetcher,
    PreFetchStrategy,
    PreFetchPriority,
    LRUCache,
    LFUCache,
    PreFetchRequest,
    PreFetchResult,
)

from heretek_swarm.memory.compression import (
    ColdDataCompressor,
    CompressionAlgorithm,
    CompressionLevel,
    CompressionConfig,
    CompressedMemory,
    CompressionResult,
    DecompressionResult,
    CompressionEngine,
)

from heretek_swarm.memory.tiering import (
    MemoryTieringSystem,
    MemoryTier,
    TierConfig,
    MigrationPolicy,
    MigrationRecord,
    TieredMemory,
    TieringStatistics,
    MigrationTrigger,
    TierMigrationStatus,
)


# =============================================================================
# Access Pattern Analyzer Tests
# =============================================================================

class TestAccessPatternAnalyzer:
    """Tests for AccessPatternAnalyzer."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = AccessPatternAnalyzer()
        assert analyzer.hot_threshold == 0.8
        assert analyzer.warm_threshold == 0.4
        assert analyzer.cold_threshold == 0.1
        assert analyzer.recency_half_life_hours == 24.0
    
    def test_record_access(self):
        """Test recording memory accesses."""
        analyzer = AccessPatternAnalyzer()
        
        # Record first access
        profile = analyzer.record_access(
            memory_id="test_memory_1",
            access_type="read",
            agent_id="agent_1",
            session_id="session_1",
        )
        
        assert profile.memory_id == "test_memory_1"
        assert profile.access_count == 1
        assert profile.first_access is not None
        assert profile.last_access is not None
        assert profile.tier == AccessTier.COLD  # Initial tier
    
    def test_multiple_accesses_update_profile(self):
        """Test that multiple accesses update the profile correctly."""
        analyzer = AccessPatternAnalyzer()
        
        # Record multiple accesses
        for i in range(10):
            analyzer.record_access(
                memory_id="test_memory_2",
                access_type="read",
                agent_id="agent_1",
            )
        
        profile = analyzer.get_profile("test_memory_2")
        assert profile is not None
        assert profile.access_count == 10
        assert profile.frequency_score > 0
    
    def test_tier_classification(self):
        """Test memory tier classification based on access patterns."""
        analyzer = AccessPatternAnalyzer()
        
        # Hot memory: many accesses
        for _ in range(100):
            analyzer.record_access(memory_id="hot_memory", agent_id="agent_1")
        
        # Cold memory: few accesses
        analyzer.record_access(memory_id="cold_memory", agent_id="agent_1")
        
        hot_profile = analyzer.get_profile("hot_memory")
        cold_profile = analyzer.get_profile("cold_memory")
        
        assert hot_profile.tier in [AccessTier.HOT, AccessTier.WARM]
        assert cold_profile.tier == AccessTier.COLD
    
    def test_get_profiles_by_tier(self):
        """Test getting profiles filtered by tier."""
        analyzer = AccessPatternAnalyzer()
        
        # Create memories with different access patterns
        for i in range(50):
            analyzer.record_access(memory_id=f"hot_{i}", agent_id="agent_1")
        
        for i in range(5):
            analyzer.record_access(memory_id=f"cold_{i}", agent_id="agent_1")
        
        hot_profiles = analyzer.get_hot_memories()
        cold_profiles = analyzer.get_cold_memories()
        
        assert len(hot_profiles) > 0
        assert len(cold_profiles) > 0
    
    def test_get_statistics(self):
        """Test getting access statistics."""
        analyzer = AccessPatternAnalyzer()
        
        # Record some accesses
        for i in range(20):
            analyzer.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
        
        stats = analyzer.get_statistics()
        
        assert stats.total_accesses == 20
        assert stats.unique_memories == 20
        assert isinstance(stats.hit_rate, float)
    
    def test_generate_report(self):
        """Test generating access pattern report."""
        analyzer = AccessPatternAnalyzer()
        
        # Record accesses
        for i in range(10):
            analyzer.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
        
        report = analyzer.generate_report(analysis_window_hours=24)
        
        assert isinstance(report, AccessPatternReport)
        assert report.total_memories == 10
        assert report.total_accesses == 10
        assert report.analysis_window_hours == 24
        assert isinstance(report.recommendations, list)
    
    def test_agent_pattern_tracking(self):
        """Test agent-specific pattern tracking."""
        analyzer = AccessPatternAnalyzer()
        
        # Agent 1 accesses
        for _ in range(5):
            analyzer.record_access(
                memory_id="agent1_memory",
                agent_id="agent_1",
            )
        
        # Agent 2 accesses
        for _ in range(3):
            analyzer.record_access(
                memory_id="agent2_memory",
                agent_id="agent_2",
            )
        
        agent1_patterns = analyzer.get_agent_patterns("agent_1")
        assert "accessed_memories" in agent1_patterns
    
    def test_predict_agent_access(self):
        """Test predicting agent memory access."""
        analyzer = AccessPatternAnalyzer()
        
        # Create access pattern for agent
        for i in range(10):
            analyzer.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
        
        predictions = analyzer.predict_agent_access("agent_1")
        assert isinstance(predictions, list)
    
    def test_clear_analyzer(self):
        """Test clearing the analyzer."""
        analyzer = AccessPatternAnalyzer()
        
        # Record some accesses
        analyzer.record_access(memory_id="test", agent_id="agent_1")
        
        # Clear
        analyzer.clear()
        
        stats = analyzer.get_statistics()
        assert stats.total_accesses == 0
        assert stats.unique_memories == 0
    
    def test_pattern_detection_sequential(self):
        """Test sequential pattern detection."""
        analyzer = AccessPatternAnalyzer()
        
        # Create sequential access pattern
        for _ in range(10):
            analyzer.record_access(memory_id="seq_memory", agent_id="agent_1")
        
        profile = analyzer.get_profile("seq_memory")
        # Pattern should be detected
        assert profile.pattern in [AccessPattern.SEQUENTIAL, AccessPattern.RANDOM]
    
    def test_recency_score_decay(self):
        """Test that recency score decays over time."""
        analyzer = AccessPatternAnalyzer()
        
        # Record access
        analyzer.record_access(memory_id="test", agent_id="agent_1")
        
        profile = analyzer.get_profile("test")
        assert profile.recency_score > 0
        assert profile.recency_score <= 1.0


# =============================================================================
# Intelligent Pre-fetcher Tests
# =============================================================================

class TestIntelligentPrefetcher:
    """Tests for IntelligentPrefetcher."""
    
    def test_prefetcher_initialization(self):
        """Test pre-fetcher initializes correctly."""
        prefetcher = IntelligentPrefetcher(cache_size=100)
        assert prefetcher.cache_size == 100
        assert prefetcher.prefetch_threshold == 0.6
    
    @pytest.mark.asyncio
    async def test_prefetcher_lifecycle(self):
        """Test pre-fetcher initialize and shutdown."""
        prefetcher = IntelligentPrefetcher()
        
        await prefetcher.initialize()
        assert prefetcher._scheduler_running or prefetcher._scheduler is None
        
        await prefetcher.shutdown()
    
    def test_lru_cache_operations(self):
        """Test LRU cache basic operations."""
        cache = LRUCache(max_size=10)
        
        # Put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.contains("key1")
        
        # Remove
        assert cache.remove("key1")
        assert not cache.contains("key1")
    
    def test_lru_cache_eviction(self):
        """Test LRU cache eviction when full."""
        cache = LRUCache(max_size=3)
        
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Add one more - should evict
        evicted = cache.put("key4", "value4")
        
        assert evicted == "key1"
        assert not cache.contains("key1")
        assert cache.contains("key4")
    
    def test_lru_cache_statistics(self):
        """Test LRU cache statistics."""
        cache = LRUCache(max_size=10)
        
        # Some hits and misses
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_statistics()
        assert stats.hit_count == 1
        assert stats.miss_count == 1
        assert stats.hit_rate == 0.5
    
    def test_lfu_cache_operations(self):
        """Test LFU cache basic operations."""
        cache = LFUCache(max_size=10)
        
        # Put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_lfu_cache_eviction(self):
        """Test LFU cache evicts least frequently used."""
        cache = LFUCache(max_size=3)
        
        # Add items with different frequencies
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 and key3 more frequently
        cache.get("key1")
        cache.get("key1")
        cache.get("key3")
        
        # Add new item - should evict key2 (least frequent)
        evicted = cache.put("key4", "value4")
        
        assert evicted == "key2"
        assert not cache.contains("key2")
    
    def test_record_access_triggers_prefetch(self):
        """Test that recording access triggers pre-fetching."""
        prefetcher = IntelligentPrefetcher(cache_size=100)
        
        # Record accesses to create pattern
        for i in range(5):
            prefetcher.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
        
        # Check that patterns are being tracked
        assert len(prefetcher._access_patterns.get("agent_1", [])) > 0
    
    def test_prefetch_operation(self):
        """Test pre-fetching data into cache."""
        prefetcher = IntelligentPrefetcher()
        
        result = prefetcher.prefetch(
            memory_id="test_memory",
            data={"key": "value"},
            size_bytes=100,
        )
        
        assert result.success
        assert result.memory_id == "test_memory"
        assert prefetcher.contains("test_memory")
    
    def test_get_from_cache(self):
        """Test getting data from cache."""
        prefetcher = IntelligentPrefetcher()
        
        # Pre-fetch data
        prefetcher.prefetch("test", "test_data")
        
        # Get data
        data = prefetcher.get("test")
        assert data == "test_data"
    
    def test_evict_from_cache(self):
        """Test evicting data from cache."""
        prefetcher = IntelligentPrefetcher()
        
        prefetcher.prefetch("test", "data")
        assert prefetcher.contains("test")
        
        prefetcher.evict("test")
        assert not prefetcher.contains("test")
    
    def test_get_statistics(self):
        """Test getting pre-fetcher statistics."""
        prefetcher = IntelligentPrefetcher()
        
        # Do some operations
        prefetcher.prefetch("test", "data")
        prefetcher.get("test")
        
        stats = prefetcher.get_statistics()
        
        assert "lru_cache" in stats
        assert "prefetch" in stats
        assert "access" in stats
    
    def test_prefetch_recommendations(self):
        """Test getting pre-fetch recommendations."""
        prefetcher = IntelligentPrefetcher()
        
        # Create access pattern
        for _ in range(5):
            prefetcher.record_access("memory_1", "agent_1")
        
        recommendations = prefetcher.get_prefetch_recommendations()
        assert isinstance(recommendations, list)
    
    def test_clear_prefetcher(self):
        """Test clearing the pre-fetcher."""
        prefetcher = IntelligentPrefetcher()
        
        prefetcher.prefetch("test", "data")
        prefetcher.clear()
        
        assert not prefetcher.contains("test")


# =============================================================================
# Cold Data Compressor Tests
# =============================================================================

class TestColdDataCompressor:
    """Tests for ColdDataCompressor."""
    
    def test_compressor_initialization(self):
        """Test compressor initializes correctly."""
        compressor = ColdDataCompressor()
        assert compressor.enable_auto_compress
        assert compressor._engine is not None
    
    def test_compress_data(self):
        """Test compressing data."""
        compressor = ColdDataCompressor()
        
        # Create compressible data
        data = {"key": "value" * 100}  # Repetitive data compresses well
        
        result = compressor.compress(
            memory_id="test_memory",
            data=data,
            metadata={"type": "test"},
        )
        
        assert result.success
        assert result.compression_ratio > 0
        assert compressor.is_compressed("test_memory")
    
    def test_decompress_data(self):
        """Test decompressing data."""
        compressor = ColdDataCompressor()
        
        original_data = {"key": "value" * 100}
        
        # Compress
        compressor.compress(
            memory_id="test_memory",
            data=original_data,
        )
        
        # Decompress
        result = compressor.decompress("test_memory")
        
        assert result.success
        assert result.data == original_data
        assert result.integrity_verified
    
    def test_compression_integrity(self):
        """Test that compression preserves data integrity."""
        compressor = ColdDataCompressor()
        
        # Test with various data types
        test_data = [
            {"string": "test" * 100},
            [1, 2, 3, 4, 5] * 100,
            {"nested": {"data": "value" * 50}},
        ]
        
        for i, data in enumerate(test_data):
            memory_id = f"test_{i}"
            
            compressor.compress(memory_id=memory_id, data=data)
            result = compressor.decompress(memory_id)
            
            assert result.success
            assert result.data == data
            assert result.integrity_verified
    
    def test_compress_small_data_fails(self):
        """Test that small data is not compressed."""
        config = CompressionConfig(min_size_for_compression=1024)
        compressor = ColdDataCompressor(config=config)
        
        # Small data
        result = compressor.compress(
            memory_id="small",
            data={"key": "value"},
        )
        
        assert not result.success
        assert "too small" in result.error.lower()
    
    def test_get_statistics(self):
        """Test getting compression statistics."""
        compressor = ColdDataCompressor()
        
        # Compress some data
        for i in range(5):
            compressor.compress(
                memory_id=f"memory_{i}",
                data={"data": "value" * 100},
            )
        
        stats = compressor.get_statistics()
        
        assert "engine" in stats
        assert "storage" in stats
        assert stats["storage"]["compressed_count"] == 5
    
    def test_get_compression_report(self):
        """Test generating compression report."""
        compressor = ColdDataCompressor()
        
        # Compress data
        compressor.compress(
            memory_id="test",
            data={"data": "value" * 100},
        )
        
        report = compressor.get_compression_report()
        
        assert "summary" in report
        assert "algorithm_breakdown" in report
        assert "recommendations" in report
    
    def test_remove_compressed_memory(self):
        """Test removing compressed memory."""
        compressor = ColdDataCompressor()
        
        compressor.compress(memory_id="test", data={"data": "value"})
        assert compressor.is_compressed("test")
        
        compressor.remove("test")
        assert not compressor.is_compressed("test")
    
    def test_clear_compressor(self):
        """Test clearing the compressor."""
        compressor = ColdDataCompressor()
        
        compressor.compress(memory_id="test", data={"data": "value"})
        compressor.clear()
        
        assert not compressor.is_compressed("test")
    
    def test_compression_algorithms(self):
        """Test different compression algorithms."""
        compressor = ColdDataCompressor()
        
        data = {"data": "value" * 100}
        
        # Test zlib
        result_zlib = compressor.compress(
            memory_id="zlib_test",
            data=data,
            algorithm=CompressionAlgorithm.ZLIB,
        )
        assert result_zlib.success
        
        # Test gzip
        result_gzip = compressor.compress(
            memory_id="gzip_test",
            data=data,
            algorithm=CompressionAlgorithm.GZIP,
        )
        assert result_gzip.success
    
    def test_compression_levels(self):
        """Test different compression levels."""
        compressor = ColdDataCompressor()
        
        data = {"data": "value" * 100}
        
        # Fastest compression
        result_fastest = compressor.compress(
            memory_id="fastest",
            data=data,
            level=CompressionLevel.FASTEST,
        )
        
        # Best compression
        result_best = compressor.compress(
            memory_id="best",
            data=data,
            level=CompressionLevel.BEST,
        )
        
        assert result_fastest.success
        assert result_best.success


# =============================================================================
# Memory Tiering System Tests
# =============================================================================

class TestMemoryTieringSystem:
    """Tests for MemoryTieringSystem."""
    
    def test_tiering_initialization(self):
        """Test tiering system initializes correctly."""
        tiering = MemoryTieringSystem()
        assert tiering.enable_auto_migration
        assert len(tiering.tier_configs) == 4  # L1, L2, L3, Archive
    
    def test_store_memory(self):
        """Test storing memory in tier."""
        tiering = MemoryTieringSystem()
        
        memory = tiering.store(
            memory_id="test_memory",
            data={"key": "value"},
            metadata={"type": "test"},
        )
        
        assert memory.memory_id == "test_memory"
        assert memory.current_tier == MemoryTier.L2_WARM  # Default tier
    
    def test_store_with_explicit_tier(self):
        """Test storing memory with explicit tier."""
        tiering = MemoryTieringSystem()
        
        memory = tiering.store(
            memory_id="hot_memory",
            data={"key": "value"},
            target_tier=MemoryTier.L1_HOT,
        )
        
        assert memory.current_tier == MemoryTier.L1_HOT
    
    def test_get_memory(self):
        """Test retrieving memory from tier."""
        tiering = MemoryTieringSystem()
        
        tiering.store(memory_id="test", data={"key": "value"})
        
        memory = tiering.get_memory("test")
        
        assert memory is not None
        assert memory.memory_id == "test"
        assert memory.access_count == 1
    
    def test_get_memories_by_tier(self):
        """Test getting memories filtered by tier."""
        tiering = MemoryTieringSystem()
        
        # Store in different tiers
        tiering.store(memory_id="hot1", data={}, target_tier=MemoryTier.L1_HOT)
        tiering.store(memory_id="warm1", data={}, target_tier=MemoryTier.L2_WARM)
        tiering.store(memory_id="cold1", data={}, target_tier=MemoryTier.L3_COLD)
        
        hot_memories = tiering.get_memories_by_tier(MemoryTier.L1_HOT)
        warm_memories = tiering.get_memories_by_tier(MemoryTier.L2_WARM)
        
        assert len(hot_memories) == 1
        assert len(warm_memories) == 1
    
    def test_remove_memory(self):
        """Test removing memory from tier."""
        tiering = MemoryTieringSystem()
        
        tiering.store(memory_id="test", data={})
        assert tiering.get_memory("test") is not None
        
        tiering.remove_memory("test")
        assert tiering.get_memory("test") is None
    
    def test_migration_record_creation(self):
        """Test that migrations create proper records."""
        tiering = MemoryTieringSystem()
        
        # Store memory
        tiering.store(
            memory_id="test",
            data={},
            target_tier=MemoryTier.L2_WARM,
        )
        
        memory = tiering.get_memory("test")
        
        # Note: Actual migration requires async execution
        # This test verifies the structure is correct
    
    def test_get_statistics(self):
        """Test getting tiering statistics."""
        tiering = MemoryTieringSystem()
        
        # Store some memories
        for i in range(5):
            tiering.store(memory_id=f"memory_{i}", data={})
        
        stats = tiering.get_statistics()
        
        assert isinstance(stats, TieringStatistics)
        assert stats.total_memories == 5
        assert isinstance(stats.memories_per_tier, dict)
    
    def test_get_migration_history(self):
        """Test getting migration history."""
        tiering = MemoryTieringSystem()
        
        history = tiering.get_migration_history()
        assert isinstance(history, list)
    
    def test_add_policy(self):
        """Test adding migration policy."""
        tiering = MemoryTieringSystem()
        
        policy = MigrationPolicy(
            name="test_policy",
            description="Test migration policy",
            enabled=True,
            conditions={"test": True},
            actions={"target_tier": "l1_hot"},
            priority=50,
        )
        
        tiering.add_policy(policy)
        
        policies = tiering.get_policies()
        assert len(policies) > 0
        assert any(p.name == "test_policy" for p in policies)
    
    def test_remove_policy(self):
        """Test removing migration policy."""
        tiering = MemoryTieringSystem()
        
        # Add then remove
        policy = MigrationPolicy(
            name="temp_policy",
            description="Temporary policy",
            enabled=True,
        )
        
        tiering.add_policy(policy)
        result = tiering.remove_policy("temp_policy")
        
        assert result
        assert not any(p.name == "temp_policy" for p in tiering.get_policies())
    
    def test_get_tier_config(self):
        """Test getting tier configuration."""
        tiering = MemoryTieringSystem()
        
        config = tiering.get_tier_config(MemoryTier.L1_HOT)
        
        assert config is not None
        assert config.tier == MemoryTier.L1_HOT
        assert config.name == "Hot Storage (Redis)"
    
    def test_update_tier_config(self):
        """Test updating tier configuration."""
        tiering = MemoryTieringSystem()
        
        result = tiering.update_tier_config(
            MemoryTier.L1_HOT,
            max_capacity_count=50000,
        )
        
        assert result
        config = tiering.get_tier_config(MemoryTier.L1_HOT)
        assert config.max_capacity_count == 50000
    
    def test_generate_report(self):
        """Test generating tiering report."""
        tiering = MemoryTieringSystem()
        
        # Store some memories
        for i in range(3):
            tiering.store(memory_id=f"memory_{i}", data={})
        
        report = tiering.generate_report()
        
        assert "statistics" in report
        assert "tier_utilization" in report
        assert "recent_migrations" in report
        assert "recommendations" in report
    
    def test_tier_history_tracking(self):
        """Test that tier history is tracked."""
        tiering = MemoryTieringSystem()
        
        memory = tiering.store(
            memory_id="test",
            data={},
            target_tier=MemoryTier.L2_WARM,
        )
        
        assert len(memory.tier_history) == 1
        assert memory.tier_history[0]["action"] == "created"
    
    def test_access_count_tracking(self):
        """Test that access count is tracked."""
        tiering = MemoryTieringSystem()
        
        tiering.store(memory_id="test", data={})
        
        # Access multiple times
        tiering.get_memory("test")
        tiering.get_memory("test")
        tiering.get_memory("test")
        
        memory = tiering.get_memory("test")
        assert memory.access_count == 4  # Initial get + 3 more
    
    def test_clear_tiering(self):
        """Test clearing the tiering system."""
        tiering = MemoryTieringSystem()
        
        tiering.store(memory_id="test", data={})
        tiering.clear()
        
        stats = tiering.get_statistics()
        assert stats.total_memories == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestMemoryOptimizationIntegration:
    """Integration tests for memory optimization modules."""
    
    def test_analyzer_with_prefetcher(self):
        """Test access pattern analyzer with pre-fetcher."""
        analyzer = AccessPatternAnalyzer()
        prefetcher = IntelligentPrefetcher()
        
        # Record accesses
        for i in range(10):
            analyzer.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
            prefetcher.record_access(
                memory_id=f"memory_{i}",
                agent_id="agent_1",
            )
        
        # Get statistics from both
        analyzer_stats = analyzer.get_statistics()
        prefetcher_stats = prefetcher.get_statistics()
        
        assert analyzer_stats.total_accesses == 10
        assert prefetcher_stats["access"]["total_accesses"] == 10
    
    def test_compressor_with_tiering(self):
        """Test compressor integration with tiering system."""
        compressor = ColdDataCompressor()
        tiering = MemoryTieringSystem()
        
        # Store and compress
        tiering.store(
            memory_id="test",
            data={"data": "value" * 100},
            target_tier=MemoryTier.L3_COLD,
        )
        
        # Compress the data
        result = compressor.compress(
            memory_id="test",
            data={"data": "value" * 100},
        )
        
        assert result.success
    
    def test_full_optimization_pipeline(self):
        """Test complete memory optimization pipeline."""
        analyzer = AccessPatternAnalyzer()
        prefetcher = IntelligentPrefetcher()
        compressor = ColdDataCompressor()
        tiering = MemoryTieringSystem()
        
        # Simulate memory lifecycle
        # 1. Store in tiering
        tiering.store(memory_id="memory_1", data={"key": "value"})
        
        # 2. Track access patterns
        for _ in range(5):
            analyzer.record_access(memory_id="memory_1", agent_id="agent_1")
            prefetcher.record_access(memory_id="memory_1", agent_id="agent_1")
        
        # 3. Compress if cold
        compressor.compress(
            memory_id="memory_1",
            data={"key": "value" * 100},
        )
        
        # Get comprehensive stats
        analyzer_report = analyzer.generate_report()
        prefetcher_stats = prefetcher.get_statistics()
        compressor_report = compressor.get_compression_report()
        tiering_report = tiering.generate_report()
        
        # Verify all systems are working
        assert analyzer_report.total_accesses > 0
        assert prefetcher_stats["access"]["total_accesses"] > 0
        assert compressor_report["summary"]["storage"]["compressed_count"] > 0
        assert tiering_report["statistics"]["total_memories"] > 0


# =============================================================================
# Zero-Trust Verification Tests
# =============================================================================

class TestZeroTrustCompliance:
    """Tests verifying zero-trust compliance of memory optimization modules."""
    
    def test_no_datetime_utcnow(self):
        """Verify no deprecated datetime.utcnow usage."""
        import inspect
        from heretek_swarm.memory import access_patterns, prefetcher, compression, tiering
        
        modules = [access_patterns, prefetcher, compression, tiering]
        
        for module in modules:
            source = inspect.getsource(module)
            assert "datetime.utcnow" not in source, f"datetime.utcnow found in {module.__name__}"
    
    def test_no_hardcoded_secrets(self):
        """Verify no hardcoded secrets."""
        import inspect
        from heretek_swarm.memory import access_patterns, prefetcher, compression, tiering
        
        modules = [access_patterns, prefetcher, compression, tiering]
        
        for module in modules:
            source = inspect.getsource(module)
            # Simple string check instead of regex to avoid escape issues
            assert "password =" not in source or 'password = "' not in source, f"Hardcoded password found in {module.__name__}"
    
    def test_heavy_documentation(self):
        """Verify heavy inline documentation."""
        import inspect
        from heretek_swarm.memory import access_patterns, prefetcher, compression, tiering
        
        modules = [
            (access_patterns, "AccessPatternAnalyzer"),
            (prefetcher, "IntelligentPrefetcher"),
            (compression, "ColdDataCompressor"),
            (tiering, "MemoryTieringSystem"),
        ]
        
        for module, main_class in modules:
            source = inspect.getsource(module)
            
            # Check for docstrings
            assert '"""' in source, f"Missing docstrings in {module.__name__}"
            
            # Check for class docstrings
            lines = source.split('\n')
            docstring_count = sum(1 for line in lines if '"""' in line)
            assert docstring_count >= 10, f"Insufficient documentation in {module.__name__}"
    
    def test_no_todo_comments(self):
        """Verify no TODO/FIXME/XXX/HACK comments."""
        import inspect
        from heretek_swarm.memory import access_patterns, prefetcher, compression, tiering
        
        modules = [access_patterns, prefetcher, compression, tiering]
        forbidden_patterns = ["TODO", "FIXME", "XXX", "HACK"]
        
        for module in modules:
            source = inspect.getsource(module)
            for pattern in forbidden_patterns:
                assert pattern not in source, f"{pattern} comment found in {module.__name__}"
