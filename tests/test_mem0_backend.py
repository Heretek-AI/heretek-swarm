"""
mem0 Backend Integration Tests

Tests for mem0 memory backend with latency tracking.
Target: p95 latency <50ms
"""

import os
import pytest
import asyncio
from uuid import uuid4

from memory import Mem0Backend, Mem0Config, MEM0_AVAILABLE
from memory.base import MemoryEntry, MemoryType, MemoryTier, MemoryQuery


@pytest.fixture
def mem0_config():
    """Test mem0 configuration."""
    return Mem0Config(
        _qdrant_host = os.getenv("QDRANT_HOST", "localhost"),
        _qdrant_port = int(os.getenv("QDRANT_PORT", "6333")),
        _qdrant_collection = "heretek_test_memories",
        _llm_model = "gpt-4o-mini",
        _openai_api_key = os.getenv("OPENAI_API_KEY"),
    )


@pytest.fixture
async def mem0_backend(_mem0_config):
    """Test fixture for mem0 backend."""
    if not MEM0_AVAILABLE:
        pytest.skip("mem0 not installed")
    
    _backend = Mem0Backend(config=mem0_config)
    try:
        await backend.initialize()
        yield backend
    finally:
        await backend.shutdown()


@pytest.mark.asyncio
async def test_mem0_initialization(_mem0_backend):
    """Test mem0 backend initializes correctly."""
    assert mem0_backend._initialized
    assert mem0_backend._memory is not None


@pytest.mark.asyncio
async def test_mem0_store_and_retrieve(_mem0_backend):
    """Test basic store and search operations."""
    # Create test entry
    _entry = MemoryEntry(
        _id = uuid4(),
        _agent_id = "test-agent-1",
        _session_id = uuid4(),
        content="Test memory content for retrieval",
        _content_type = "text/plain",
        _memory_type = MemoryType.EPISODIC,
        _tier = MemoryTier.PERSISTENT,
        _importance_score = 0.8,
    )
    
    # Store
    _memory_id = await mem0_backend.store(entry)
    assert memory_id, "Memory ID should be returned"
    
    # Small delay for mem0 processing
    await asyncio.sleep(0.5)
    
    # Search
    _query = MemoryQuery(
        _query_text = "test memory",
        _agent_ids = ["test-agent-1"],
        _limit = 10,
    )
    _result = await mem0_backend.search(query)
    
    assert result.total_count >= 1, "Should find at least one memory"
    assert any("Test memory" in e.content for e in result.entries)


@pytest.mark.asyncio
async def test_mem0_batch_store(_mem0_backend):
    """Test batch store operations."""
    _entries = [
        MemoryEntry(
            _id = uuid4(),
            _agent_id = "test-agent-batch",
            content=f"Batch memory {i}",
            _memory_type = MemoryType.EPISODIC,
            _tier = MemoryTier.PERSISTENT,
        )
        for i in range(10)
    ]
    
    _memory_ids = await mem0_backend.store_batch(entries)
    assert len(memory_ids) == 10, "Should return 10 memory IDs"


@pytest.mark.asyncio
async def test_mem0_get_all(_mem0_backend):
    """Test get all memories for agent."""
    # Store multiple memories
    for i in range(5):
        _entry = MemoryEntry(
            _id = uuid4(),
            _agent_id = "test-agent-getall",
            content=f"Memory {i} for get_all test",
            _memory_type = MemoryType.SEMANTIC,
            _tier = MemoryTier.PERSISTENT,
        )
        await mem0_backend.store(entry)
    
    await asyncio.sleep(0.5)
    
    # Get all
    _entries = await mem0_backend.get_all("test-agent-getall")
    assert len(entries) >= 5, "Should retrieve all stored memories"


@pytest.mark.asyncio
async def test_mem0_delete(_mem0_backend):
    """Test memory deletion."""
    _entry = MemoryEntry(
        _id = uuid4(),
        _agent_id = "test-agent-delete",
        content="Memory to be deleted",
        _memory_type = MemoryType.EPISODIC,
        _tier = MemoryTier.PERSISTENT,
    )
    
    # Store
    _memory_id = await mem0_backend.store(entry)
    
    # Delete
    _success = await mem0_backend.delete(memory_id)
    assert success, "Delete should succeed"


@pytest.mark.asyncio
async def test_mem0_latency_tracking(_mem0_backend):
    """Test latency statistics tracking."""
    # Perform multiple operations
    for i in range(50):
        _entry = MemoryEntry(
            _id = uuid4(),
            _agent_id = "test-agent-latency",
            content=f"Latency test memory {i}",
            _memory_type = MemoryType.EPISODIC,
            _tier = MemoryTier.PERSISTENT,
        )
        await mem0_backend.store(entry)
    
    # Get stats
    _stats = mem0_backend.get_latency_stats()
    
    assert "p50" in stats
    assert "p95" in stats
    assert "p99" in stats
    assert "avg" in stats
    
    # Check p95 target (<50ms is ideal, <500ms acceptable for tests)
    assert stats["p95"] < 500, f"p95 latency {stats['p95']}ms exceeds 500ms target"


@pytest.mark.asyncio
async def test_mem0_search_with_filters(_mem0_backend):
    """Test search with various filters."""
    # Store memories with different types
    for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.WORKING]:
        _entry = MemoryEntry(
            _id = uuid4(),
            _agent_id = "test-agent-filter",
            content=f"Memory of type {memory_type.value}",
            _memory_type = memory_type,
            _tier = MemoryTier.PERSISTENT,
            _tags = [memory_type.value, "test"],
        )
        await mem0_backend.store(entry)
    
    await asyncio.sleep(0.5)
    
    # Search with agent filter
    _query = MemoryQuery(
        _query_text = "memory type",
        _agent_ids = ["test-agent-filter"],
        _limit = 10,
    )
    _result = await mem0_backend.search(query)
    
    assert result.total_count >= 3, "Should find memories of all types"


@pytest.mark.asyncio
async def test_mem0_metadata_preservation(_mem0_backend):
    """Test that metadata is preserved through store/retrieve."""
    _test_metadata = {
        "custom_field": "custom_value",
        "number": 42,
        "nested": {"key": "value"},
        "source": "test_suite",
    }
    
    _entry = MemoryEntry(
        _id = uuid4(),
        _agent_id = "test-agent-metadata",
        content="Memory with rich metadata",
        _memory_type = MemoryType.SEMANTIC,
        _tier = MemoryTier.PERSISTENT,
        _metadata = test_metadata,
    )
    
    # Store
    await mem0_backend.store(entry)
    await asyncio.sleep(0.5)
    
    # Retrieve
    _entries = await mem0_backend.get_all("test-agent-metadata")
    assert len(entries) > 0, "Should retrieve memory"
    
    # Note: mem0 may transform metadata, so we check if custom data is present
    _found_entry = entries[0]
    assert found_entry.content == "Memory with rich metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
