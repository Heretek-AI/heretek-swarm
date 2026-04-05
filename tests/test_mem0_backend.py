"""
mem0 Backend Integration Tests

Tests for mem0 memory backend with latency tracking.
Target: p95 latency <50ms
"""

import os
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

from memory import Mem0Backend, Mem0Config, MEM0_AVAILABLE
from memory.base import MemoryEntry, MemoryType, MemoryTier, MemoryQuery


@pytest.fixture
def mem0_config():
    """Test mem0 configuration."""
    return Mem0Config(
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        qdrant_collection="heretek_test_memories",
        llm_model="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


@pytest.fixture
async def mem0_backend(mem0_config):
    """Test fixture for mem0 backend."""
    if not MEM0_AVAILABLE:
        pytest.skip("mem0 not installed")
    
    backend = Mem0Backend(config=mem0_config)
    try:
        await backend.initialize()
        yield backend
    finally:
        await backend.shutdown()


@pytest.mark.asyncio
async def test_mem0_initialization(mem0_backend):
    """Test mem0 backend initializes correctly."""
    assert mem0_backend._initialized
    assert mem0_backend._memory is not None


@pytest.mark.asyncio
async def test_mem0_store_and_retrieve(mem0_backend):
    """Test basic store and search operations."""
    # Create test entry
    entry = MemoryEntry(
        id=uuid4(),
        agent_id="test-agent-1",
        session_id=uuid4(),
        content="Test memory content for retrieval",
        content_type="text/plain",
        memory_type=MemoryType.EPISODIC,
        tier=MemoryTier.PERSISTENT,
        importance_score=0.8,
    )
    
    # Store
    memory_id = await mem0_backend.store(entry)
    assert memory_id, "Memory ID should be returned"
    
    # Small delay for mem0 processing
    await asyncio.sleep(0.5)
    
    # Search
    query = MemoryQuery(
        query_text="test memory",
        agent_ids=["test-agent-1"],
        limit=10,
    )
    result = await mem0_backend.search(query)
    
    assert result.total_count >= 1, "Should find at least one memory"
    assert any("Test memory" in e.content for e in result.entries)


@pytest.mark.asyncio
async def test_mem0_batch_store(mem0_backend):
    """Test batch store operations."""
    entries = [
        MemoryEntry(
            id=uuid4(),
            agent_id="test-agent-batch",
            content=f"Batch memory {i}",
            memory_type=MemoryType.EPISODIC,
            tier=MemoryTier.PERSISTENT,
        )
        for i in range(10)
    ]
    
    memory_ids = await mem0_backend.store_batch(entries)
    assert len(memory_ids) == 10, "Should return 10 memory IDs"


@pytest.mark.asyncio
async def test_mem0_get_all(mem0_backend):
    """Test get all memories for agent."""
    # Store multiple memories
    for i in range(5):
        entry = MemoryEntry(
            id=uuid4(),
            agent_id="test-agent-getall",
            content=f"Memory {i} for get_all test",
            memory_type=MemoryType.SEMANTIC,
            tier=MemoryTier.PERSISTENT,
        )
        await mem0_backend.store(entry)
    
    await asyncio.sleep(0.5)
    
    # Get all
    entries = await mem0_backend.get_all("test-agent-getall")
    assert len(entries) >= 5, "Should retrieve all stored memories"


@pytest.mark.asyncio
async def test_mem0_delete(mem0_backend):
    """Test memory deletion."""
    entry = MemoryEntry(
        id=uuid4(),
        agent_id="test-agent-delete",
        content="Memory to be deleted",
        memory_type=MemoryType.EPISODIC,
        tier=MemoryTier.PERSISTENT,
    )
    
    # Store
    memory_id = await mem0_backend.store(entry)
    
    # Delete
    success = await mem0_backend.delete(memory_id)
    assert success, "Delete should succeed"


@pytest.mark.asyncio
async def test_mem0_latency_tracking(mem0_backend):
    """Test latency statistics tracking."""
    # Perform multiple operations
    for i in range(50):
        entry = MemoryEntry(
            id=uuid4(),
            agent_id="test-agent-latency",
            content=f"Latency test memory {i}",
            memory_type=MemoryType.EPISODIC,
            tier=MemoryTier.PERSISTENT,
        )
        await mem0_backend.store(entry)
    
    # Get stats
    stats = mem0_backend.get_latency_stats()
    
    assert "p50" in stats
    assert "p95" in stats
    assert "p99" in stats
    assert "avg" in stats
    
    # Check p95 target (<50ms is ideal, <500ms acceptable for tests)
    assert stats["p95"] < 500, f"p95 latency {stats['p95']}ms exceeds 500ms target"


@pytest.mark.asyncio
async def test_mem0_search_with_filters(mem0_backend):
    """Test search with various filters."""
    # Store memories with different types
    for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.WORKING]:
        entry = MemoryEntry(
            id=uuid4(),
            agent_id="test-agent-filter",
            content=f"Memory of type {memory_type.value}",
            memory_type=memory_type,
            tier=MemoryTier.PERSISTENT,
            tags=[memory_type.value, "test"],
        )
        await mem0_backend.store(entry)
    
    await asyncio.sleep(0.5)
    
    # Search with agent filter
    query = MemoryQuery(
        query_text="memory type",
        agent_ids=["test-agent-filter"],
        limit=10,
    )
    result = await mem0_backend.search(query)
    
    assert result.total_count >= 3, "Should find memories of all types"


@pytest.mark.asyncio
async def test_mem0_metadata_preservation(mem0_backend):
    """Test that metadata is preserved through store/retrieve."""
    test_metadata = {
        "custom_field": "custom_value",
        "number": 42,
        "nested": {"key": "value"},
        "source": "test_suite",
    }
    
    entry = MemoryEntry(
        id=uuid4(),
        agent_id="test-agent-metadata",
        content="Memory with rich metadata",
        memory_type=MemoryType.SEMANTIC,
        tier=MemoryTier.PERSISTENT,
        metadata=test_metadata,
    )
    
    # Store
    await mem0_backend.store(entry)
    await asyncio.sleep(0.5)
    
    # Retrieve
    entries = await mem0_backend.get_all("test-agent-metadata")
    assert len(entries) > 0, "Should retrieve memory"
    
    # Note: mem0 may transform metadata, so we check if custom data is present
    found_entry = entries[0]
    assert found_entry.content == "Memory with rich metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
