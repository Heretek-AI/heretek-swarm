"""
Tests for mem0 backend integration.

These tests verify the mem0 integration works correctly with the
Heretek Swarm memory system.
"""

from uuid import uuid4

import pytest

from heretek_swarm.memory import (
    MEM0_AVAILABLE,
    Mem0Backend,
    Mem0Config,
    MemoryEntry,
    MemoryQuery,
    MemoryTier,
    MemoryType,
)


@pytest.fixture
def mem0_config():
    """Create test configuration for mem0"""
    return Mem0Config(
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection="test_heretek_memories",
        llm_model="gpt-4o-mini",
        embedder_model="text-embedding-3-small",
    )


@pytest.fixture
def sample_entry():
    """Create a sample memory entry for testing"""
    return MemoryEntry(
        id=uuid4(),
        agent_id="test_agent",
        content="This is a test memory about agent preferences",
        content_type="text/plain",
        metadata={"test": True, "category": "preferences"},
        memory_type=MemoryType.SEMANTIC,
        tier=MemoryTier.PERSISTENT,
        tags=["test", "preferences"],
        importance_score=0.8,
    )


@pytest.mark.skipif(not MEM0_AVAILABLE, reason="mem0ai not installed")
@pytest.mark.asyncio
async def test_mem0_backend_initialization(mem0_config):
    """Test that mem0 backend initializes correctly"""
    backend = Mem0Backend(config=mem0_config)

    assert not backend._initialized

    await backend.initialize()

    assert backend._initialized
    assert backend._memory is not None

    await backend.shutdown()

    assert not backend._initialized


@pytest.mark.skipif(not MEM0_AVAILABLE, reason="mem0ai not installed")
@pytest.mark.asyncio
async def test_mem0_store_and_search(mem0_config, sample_entry):
    """Test storing and searching memories"""
    backend = Mem0Backend(config=mem0_config)
    await backend.initialize()

    try:
        # Store memory
        memory_id = await backend.store(sample_entry)
        assert memory_id is not None
        assert len(memory_id) > 0

        # Search for the memory
        query = MemoryQuery(
            query_text="agent preferences",
            agent_ids=["test_agent"],
            limit=10,
        )
        result = await backend.search(query)

        assert result.total_count >= 1
        assert len(result.entries) >= 1

        # Check that we got the right memory
        found = False
        for entry in result.entries:
            if "preferences" in entry.content.lower():
                found = True
                break

        assert found, "Should find memory about preferences"

    finally:
        await backend.shutdown()


@pytest.mark.skipif(not MEM0_AVAILABLE, reason="mem0ai not installed")
@pytest.mark.asyncio
async def test_mem0_get_all(mem0_config, sample_entry):
    """Test getting all memories for an agent"""
    backend = Mem0Backend(config=mem0_config)
    await backend.initialize()

    try:
        # Store a memory
        await backend.store(sample_entry)

        # Get all memories
        entries = await backend.get_all("test_agent")

        assert len(entries) >= 1

    finally:
        await backend.shutdown()


@pytest.mark.skipif(not MEM0_AVAILABLE, reason="mem0ai not installed")
@pytest.mark.asyncio
async def test_mem0_delete(mem0_config, sample_entry):
    """Test deleting a memory"""
    backend = Mem0Backend(config=mem0_config)
    await backend.initialize()

    try:
        # Store memory
        memory_id = await backend.store(sample_entry)

        # Delete it
        deleted = await backend.delete(memory_id)
        assert deleted is True

    finally:
        await backend.shutdown()


@pytest.mark.skipif(not MEM0_AVAILABLE, reason="mem0ai not installed")
@pytest.mark.asyncio
async def test_mem0_latency_tracking(mem0_config, sample_entry):
    """Test that latency is tracked correctly"""
    backend = Mem0Backend(config=mem0_config)
    await backend.initialize()

    try:
        # Perform some operations
        await backend.store(sample_entry)

        query = MemoryQuery(
            query_text="test",
            agent_ids=["test_agent"],
            limit=10,
        )
        await backend.search(query)

        # Check stats
        stats = backend.get_latency_stats()

        assert "p50" in stats
        assert "p95" in stats
        assert "p99" in stats
        assert "avg" in stats

    finally:
        await backend.shutdown()


def test_mem0_config_to_dict():
    """Test Mem0Config serialization"""
    config = Mem0Config(
        qdrant_host="test-host",
        qdrant_port=6333,
        qdrant_collection="test-collection",
        llm_model="gpt-4o",
        openai_api_key="test-key",
    )

    result = config.get_mem0_config()

    assert result["vector_store"]["provider"] == "qdrant"
    assert result["vector_store"]["config"]["host"] == "test-host"
    assert result["llm"]["config"]["model"] == "gpt-4o"
    assert result["embedder"]["provider"] == "openai"


def test_mem0_not_available():
    """Test behavior when mem0 is not installed"""
    # This test documents expected behavior when mem0ai is not installed
    if not MEM0_AVAILABLE:
        assert Mem0Backend is None
        assert Mem0Config is None
