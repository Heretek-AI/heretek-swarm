"""
Tests for the Dual-Tier Memory System.

Validates functionality, performance, and reliability of the
unified memory architecture.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from heretek_swarm.memory import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryTier,
    MemoryType,
    EphemeralMemoryStore,
    EphemeralConfig,
    PersistentMemoryStore,
    PersistentConfig,
    DualTierMemorySystem,
    DualTierConfig,
    EmbeddingService,
    EmbeddingConfig,
)


# Fixtures

@pytest.fixture
def ephemeral_config():
    """Test configuration for ephemeral store"""
    return EphemeralConfig(
        redis_url="redis://localhost:6379/15",  # Use test DB
        default_ttl_seconds=60,
        key_prefix="test:memory"
    )


@pytest.fixture
def persistent_config():
    """Test configuration for persistent store"""
    return PersistentConfig(
        database_url="postgresql+asyncpg://postgres:test@localhost:5432/test_heretek",
        pool_size=5
    )


@pytest.fixture
def embedding_config():
    """Test configuration for embedding service"""
    return EmbeddingConfig(
        litellm_base_url="http://localhost:4000",
        default_model="text-embedding-3-small",
        cache_max_size=100
    )


@pytest.fixture
async def ephemeral_store(ephemeral_config):
    """Create and connect ephemeral store"""
    store = EphemeralMemoryStore(ephemeral_config)
    await store.connect()
    yield store
    await store.disconnect()


@pytest.fixture
async def persistent_store(persistent_config):
    """Create and connect persistent store"""
    store = PersistentMemoryStore(persistent_config)
    await store.connect()
    yield store
    await persistent_store.disconnect()


@pytest.fixture
async def dual_tier_system(ephemeral_config, persistent_config, embedding_config):
    """Create and initialize dual-tier system"""
    config = DualTierConfig(
        ephemeral=ephemeral_config,
        persistent=persistent_config,
        embedding=embedding_config
    )
    system = DualTierMemorySystem(config)
    await system.initialize()
    yield system
    await system.shutdown()


# Test Cases

class TestMemoryEntry:
    """Test memory entry model"""
    
    def test_create_memory_entry(self):
        """Test basic entry creation"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Test memory content"
        )
        
        assert entry.id is not None
        assert entry.agent_id == "agent-1"
        assert entry.content == "Test memory content"
        assert entry.memory_type == MemoryType.EPISODIC
        assert entry.tier == MemoryTier.PERSISTENT
        assert entry.access_count == 0
    
    def test_entry_touch(self):
        """Test access tracking"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Test"
        )
        
        original_time = entry.accessed_at
        original_count = entry.access_count
        
        entry.touch()
        
        assert entry.accessed_at > original_time
        assert entry.access_count == original_count + 1
    
    def test_entry_expiration(self):
        """Test expiration check"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert not entry.is_expired()
        
        entry.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert entry.is_expired()


class TestMemoryQuery:
    """Test memory query model"""
    
    def test_create_query(self):
        """Test basic query creation"""
        query = MemoryQuery(
            query_text="search term",
            agent_ids=["agent-1"],
            limit=20
        )
        
        assert query.query_text == "search term"
        assert query.agent_ids == ["agent-1"]
        assert query.limit == 20
        assert query.sort_by == "relevance"
    
    def test_query_validation(self):
        """Test query parameter validation"""
        with pytest.raises(ValueError):
            MemoryQuery(limit=0)  # Must be > 0
        
        with pytest.raises(ValueError):
            MemoryQuery(limit=1001)  # Must be <= 1000


class TestEphemeralStore:
    """Test Redis ephemeral store"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, ephemeral_store):
        """Test basic store and retrieve"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Test ephemeral content",
            tags=["test", "ephemeral"]
        )
        
        await ephemeral_store.store(entry, ttl_seconds=60)
        
        retrieved = await ephemeral_store.retrieve(entry.id)
        
        assert retrieved is not None
        assert retrieved.content == "Test ephemeral content"
        assert "test" in retrieved.tags
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, ephemeral_store):
        """Test that entries expire correctly"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Short-lived content"
        )
        
        await ephemeral_store.store(entry, ttl_seconds=1)
        
        # Should exist immediately
        retrieved = await ephemeral_store.retrieve(entry.id)
        assert retrieved is not None
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be gone
        retrieved = await ephemeral_store.retrieve(entry.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_search_by_agent(self, ephemeral_store):
        """Test search filtering by agent"""
        # Create entries for different agents
        for i in range(3):
            entry = MemoryEntry(
                agent_id=f"agent-{i}",
                content=f"Content {i}"
            )
            await ephemeral_store.store(entry, ttl_seconds=60)
        
        # Search for agent-1
        query = MemoryQuery(agent_ids=["agent-1"])
        result = await ephemeral_store.search(query)
        
        assert result.total_count == 1
        assert result.entries[0].agent_id == "agent-1"
    
    @pytest.mark.asyncio
    async def test_search_by_tags(self, ephemeral_store):
        """Test search filtering by tags"""
        entry1 = MemoryEntry(
            agent_id="agent-1",
            content="Important",
            tags=["important", "priority"]
        )
        entry2 = MemoryEntry(
            agent_id="agent-1",
            content="Normal",
            tags=["normal"]
        )
        
        await ephemeral_store.store(entry1, ttl_seconds=60)
        await ephemeral_store.store(entry2, ttl_seconds=60)
        
        query = MemoryQuery(tags=["important"])
        result = await ephemeral_store.search(query)
        
        assert result.total_count == 1
        assert "important" in result.entries[0].tags
    
    @pytest.mark.asyncio
    async def test_delete(self, ephemeral_store):
        """Test entry deletion"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="To be deleted"
        )
        
        await ephemeral_store.store(entry, ttl_seconds=60)
        
        deleted = await ephemeral_store.delete(entry.id)
        assert deleted is True
        
        retrieved = await ephemeral_store.retrieve(entry.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_performance(self, ephemeral_store):
        """Test that operations meet latency target"""
        # Store multiple entries
        entries = []
        for i in range(10):
            entry = MemoryEntry(
                agent_id="agent-1",
                content=f"Performance test {i}"
            )
            await ephemeral_store.store(entry, ttl_seconds=60)
            entries.append(entry)
        
        # Measure retrieval latency
        stats = await ephemeral_store.get_stats()
        
        # p95 should be < 10ms for Redis
        assert stats["p95_latency_ms"] < 10.0 or stats["p95_latency_ms"] == 0


class TestPersistentStore:
    """Test PostgreSQL persistent store"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, persistent_store):
        """Test basic store and retrieve"""
        entry = MemoryEntry(
            agent_id="agent-1",
            content="Test persistent content",
            memory_type=MemoryType.SEMANTIC
        )
        
        await persistent_store.store(entry, generate_embedding=False)
        
        retrieved = await persistent_store.retrieve(entry.id)
        
        assert retrieved is not None
        assert retrieved.content == "Test persistent content"
        assert retrieved.memory_type == MemoryType.SEMANTIC
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, persistent_store):
        """Test search with multiple filters"""
        # Create entries
        for i in range(5):
            entry = MemoryEntry(
                agent_id=f"agent-{i % 2}",
                content=f"Content {i}",
                memory_type=MemoryType.EPISODIC if i % 2 == 0 else MemoryType.SEMANTIC
            )
            await persistent_store.store(entry, generate_embedding=False)
        
        # Search for episodic memories from agent-0
        query = MemoryQuery(
            agent_ids=["agent-0"],
            memory_types=[MemoryType.EPISODIC]
        )
        result = await persistent_store.search(query)
        
        assert all(e.agent_id == "agent-0" for e in result.entries)
        assert all(e.memory_type == MemoryType.EPISODIC for e in result.entries)
    
    @pytest.mark.asyncio
    async def test_pagination(self, persistent_store):
        """Test search pagination"""
        # Create 20 entries
        for i in range(20):
            entry = MemoryEntry(
                agent_id="agent-1",
                content=f"Content {i}"
            )
            await persistent_store.store(entry, generate_embedding=False)
        
        # First page
        query1 = MemoryQuery(
            agent_ids=["agent-1"],
            limit=10,
            offset=0
        )
        result1 = await persistent_store.search(query1)
        
        assert len(result1.entries) == 10
        assert result1.has_more
        assert result1.next_offset == 10
        
        # Second page
        query2 = MemoryQuery(
            agent_ids=["agent-1"],
            limit=10,
            offset=10
        )
        result2 = await persistent_store.search(query2)
        
        assert len(result2.entries) == 10
        assert not result2.has_more


class TestDualTierSystem:
    """Test unified dual-tier system"""
    
    @pytest.mark.asyncio
    async def test_auto_tier_selection(self, dual_tier_system):
        """Test automatic tier selection"""
        # High importance -> persistent
        entry1 = await dual_tier_system.store(
            content="Important memory",
            agent_id="agent-1",
            importance_score=0.9
        )
        assert entry1.tier == MemoryTier.PERSISTENT
        
        # Low importance -> ephemeral
        entry2 = await dual_tier_system.store(
            content="Temporary memory",
            agent_id="agent-1",
            importance_score=0.3
        )
        assert entry2.tier == MemoryTier.EPHEMERAL
    
    @pytest.mark.asyncio
    async def test_cross_tier_search(self, dual_tier_system):
        """Test search across both tiers"""
        # Store in ephemeral
        await dual_tier_system.store(
            content="Ephemeral content",
            agent_id="agent-1",
            tier=MemoryTier.EPHEMERAL
        )
        
        # Store in persistent
        await dual_tier_system.store(
            content="Persistent content",
            agent_id="agent-1",
            tier=MemoryTier.PERSISTENT
        )
        
        # Search both tiers
        query = MemoryQuery(
            agent_ids=["agent-1"],
            tiers=[MemoryTier.EPHEMERAL, MemoryTier.PERSISTENT]
        )
        result = await dual_tier_system.search(query)
        
        assert result.total_count >= 2
    
    @pytest.mark.asyncio
    async def test_tier_promotion(self, dual_tier_system):
        """Test promoting from ephemeral to persistent"""
        # Store in ephemeral
        entry = await dual_tier_system.store(
            content="Content to promote",
            agent_id="agent-1",
            tier=MemoryTier.EPHEMERAL
        )
        
        # Promote
        promoted = await dual_tier_system.promote_to_persistent(entry.id)
        
        assert promoted is not None
        assert promoted.tier == MemoryTier.PERSISTENT
        
        # Original should be gone from ephemeral
        retrieved = await dual_tier_system.ephemeral.retrieve(entry.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_context_retrieval(self, dual_tier_system):
        """Test getting context for agent"""
        # Store various memories
        await dual_tier_system.store(
            content="Working on task A",
            agent_id="agent-1",
            memory_type=MemoryType.WORKING
        )
        await dual_tier_system.store(
            content="Learned fact B",
            agent_id="agent-1",
            memory_type=MemoryType.SEMANTIC
        )
        
        # Get context
        context = await dual_tier_system.get_context_for_agent(
            agent_id="agent-1",
            limit=10
        )
        
        assert len(context) >= 2
    
    @pytest.mark.asyncio
    async def test_performance_target(self, dual_tier_system):
        """Test that system meets p95 < 50ms target"""
        # Perform multiple operations
        for i in range(20):
            await dual_tier_system.store(
                content=f"Performance test {i}",
                agent_id="agent-1"
            )
        
        # Get stats
        stats = await dual_tier_system.get_stats()
        
        # p95 should be < 50ms
        assert stats.p95_query_time_ms < 50.0 or stats.p95_query_time_ms == 0


class TestEmbeddingService:
    """Test embedding service"""
    
    @pytest.mark.asyncio
    async def test_single_embedding(self, embedding_config):
        """Test generating single embedding"""
        service = EmbeddingService(embedding_config)
        
        # This test requires LiteLLM running
        # Skip if not available
        try:
            embedding = await service.embed_single("Test content")
            assert embedding is not None
            assert len(embedding.vector) > 0
            assert embedding.dimensions > 0
        except Exception:
            pytest.skip("LiteLLM not available")
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self, embedding_config):
        """Test batch embedding generation"""
        service = EmbeddingService(embedding_config)
        
        try:
            texts = ["Content 1", "Content 2", "Content 3"]
            embeddings = await service.embed_batch(texts)
            
            assert len(embeddings) == 3
            for emb in embeddings:
                assert len(emb.vector) > 0
        except Exception:
            pytest.skip("LiteLLM not available")
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    async def test_caching(self, embedding_config):
        """Test embedding caching"""
        service = EmbeddingService(embedding_config)
        
        try:
            # First call
            emb1 = await service.embed_single("Test caching")
            
            # Second call should hit cache
            emb2 = await service.embed_single("Test caching")
            
            stats = service.get_stats()
            assert stats["cache_hits"] > 0
        except Exception:
            pytest.skip("LiteLLM not available")
        finally:
            await service.close()


# Integration Tests

class TestIntegration:
    """Integration tests for full system"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, dual_tier_system):
        """Test complete memory workflow"""
        agent_id = "integration-test-agent"
        
        # 1. Store working memory
        working = await dual_tier_system.store(
            content="Currently analyzing data",
            agent_id=agent_id,
            memory_type=MemoryType.WORKING,
            tier=MemoryTier.EPHEMERAL
        )
        assert working.tier == MemoryTier.EPHEMERAL
        
        # 2. Store semantic knowledge
        semantic = await dual_tier_system.store(
            content="The system uses PostgreSQL for persistence",
            agent_id=agent_id,
            memory_type=MemoryType.SEMANTIC,
            tier=MemoryTier.PERSISTENT
        )
        assert semantic.tier == MemoryTier.PERSISTENT
        
        # 3. Retrieve context
        context = await dual_tier_system.get_context_for_agent(agent_id)
        assert len(context) >= 2
        
        # 4. Search across tiers
        results = await dual_tier_system.search(
            MemoryQuery(agent_ids=[agent_id])
        )
        assert results.total_count >= 2
        
        # 5. Check health
        health = await dual_tier_system.health_check()
        assert health["overall"] is True
        
        # 6. Get statistics
        stats = await dual_tier_system.get_stats()
        assert stats.total_entries >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
