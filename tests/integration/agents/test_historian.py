"""
Integration tests for HistorianAgent.

Tier 2 (Support) - HistorianAgent manages dual-tier memory system with LRU caching and pattern matching.
"""

import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from src.heretek_swarm.actors.base import ActorMessage, ActorState
from src.heretek_swarm.actors.historian import HistorianAgent, LRUCache

_pytestmark = pytest.mark.integration


class TestLRUCache:
    """Tests for LRUCache utility."""

    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        _cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        _cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        _cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        _result = cache.invalidate("key1")
        assert result is True
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        _cache = LRUCache(max_size=10)

        cache.set("session:001", "data1")
        cache.set("session:002", "data2")
        cache.set("user:001", "data3")

        _count = cache.invalidate_pattern("session:*")
        assert count == 2
        assert cache.get("session:001") is None
        assert cache.get("session:002") is None
        assert cache.get("user:001") == "data3"

    def test_cache_clear(self):
        """Test cache clear."""
        _cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_statistics(self):
        """Test cache statistics."""
        _cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key1")
        cache.get("missing")

        _stats = cache.get_statistics()
        assert stats["size"] == 1
        assert stats["hits"] >= 2
        assert stats["misses"] >= 1


class TestHistorianAgentIntegration:
    """Integration tests for HistorianAgent."""

    @pytest_asyncio.fixture
    async def historian_agent(self, _mock_nats, _mock_llm, _mock_db):
        """Create HistorianAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.historian.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                with patch('src.heretek_swarm.actors.historian.get_db_pool', return_value=mock_db):
                    _agent = HistorianAgent(agent_id="historian-test-001")
                    yield agent
                    if agent._state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_historian(self, _historian_agent):
        """Create and spawn HistorianAgent."""
        await historian_agent.spawn()
        yield historian_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, _historian_agent):
        """Test agent spawning lifecycle."""
        assert historian_agent._state == ActorState.SPAWNING
        await historian_agent.spawn()
        assert historian_agent._state == ActorState.ACTIVE
        assert historian_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, _spawned_historian):
        """Test agent termination lifecycle."""
        assert spawned_historian._state == ActorState.ACTIVE
        await spawned_historian.terminate()
        assert spawned_historian._state == ActorState.TERMINATED
        assert not spawned_historian.is_alive

    @pytest.mark.asyncio
    async def test_handle_store_memory(self, _spawned_historian, _mock_nats, _sample_memory):
        """Test handling memory storage request."""
        # Create message
        _message = ActorMessage(
            _message_type = "store_memory",
            _content = sample_memory,
            _sender = "alpha",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_historian.process_message(message)

        # Verify memory stored
        _stats = spawned_historian.get_memory_statistics()
        assert stats["total_memories"] >= 1

    @pytest.mark.asyncio
    async def test_handle_retrieve_context(self, _spawned_historian, _mock_nats, _sample_memory):
        """Test handling context retrieval request."""
        # Store memory first
        await spawned_historian.store_memory(
            _content = sample_memory["content"],
            _metadata = sample_memory["metadata"],
            _memory_type = "decision"
        )

        # Create retrieval message
        _message = ActorMessage(
            _message_type = "retrieve_context",
            _content = {"query": "decision", "limit": 10},
            _sender = "beta",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_historian.process_message(message)

        # Verify context retrieved
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_query_history(self, _spawned_historian, _mock_nats):
        """Test handling history query request."""
        # Create message
        _message = ActorMessage(
            _message_type = "query_history",
            _content = {
                "query": "architecture decision",
                "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
            },
            _sender = "coordinator",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_historian.process_message(message)

        # Verify query executed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_track_lineage(self, _spawned_historian, _mock_nats):
        """Test handling lineage tracking request."""
        # Create message
        _message = ActorMessage(
            _message_type = "track_lineage",
            _content = {
                "decision_id": "dec-001",
                "parent_decisions": ["dec-parent-001"],
                "child_decisions": ["dec-child-001"],
            },
            _sender = "steward",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_historian.process_message(message)

        # Verify lineage tracked
        _lineage = await spawned_historian.get_lineage("dec-001")
        assert lineage is not None

    @pytest.mark.asyncio
    async def test_handle_pattern_match(self, _spawned_historian, _mock_nats):
        """Test handling pattern matching request."""
        # Store some memories first
        await spawned_historian.store_memory(
            _content = "Similar pattern A",
            _metadata = {"category": "pattern_a"},
            _memory_type = "pattern"
        )
        await spawned_historian.store_memory(
            _content = "Similar pattern A variant",
            _metadata = {"category": "pattern_a"},
            _memory_type = "pattern"
        )

        # Create pattern match message
        _message = ActorMessage(
            _message_type = "pattern_match",
            _content = {"input": "pattern A", "threshold": 0.5},
            _sender = "metis",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_historian.process_message(message)

        # Verify patterns matched
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_store_memory(self, _spawned_historian, _sample_memory):
        """Test storing memory directly."""
        _result = await spawned_historian.store_memory(
            _content = sample_memory["content"],
            _metadata = sample_memory["metadata"],
            _memory_type = "decision"
        )

        assert result is not None
        assert "id" in result

    @pytest.mark.asyncio
    async def test_retrieve_context(self, _spawned_historian, _sample_memory):
        """Test retrieving context."""
        # Store memory first
        await spawned_historian.store_memory(
            _content = sample_memory["content"],
            _metadata = sample_memory["metadata"],
            _memory_type = "decision"
        )

        # Retrieve
        _context = await spawned_historian.retrieve_context(
            _query = "decision",
            _limit = 10
        )

        assert context is not None
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_query_history(self, _spawned_historian, _sample_memory):
        """Test querying history."""
        # Store memory first
        await spawned_historian.store_memory(
            _content = sample_memory["content"],
            _metadata = sample_memory["metadata"],
            _memory_type = "decision"
        )

        # Query
        _results = await spawned_historian.query_history(
            _query = "decision",
            _limit = 10
        )

        assert results is not None

    @pytest.mark.asyncio
    async def test_track_decision_lineage(self, _spawned_historian):
        """Test tracking decision lineage."""
        # Track lineage
        await spawned_historian.track_decision_lineage(
            _decision_id = "dec-001",
            _parent_ids = ["dec-000"],
            _metadata = {"type": "architecture"}
        )

        # Get lineage
        _lineage = await spawned_historian.get_lineage("dec-001")
        assert lineage is not None

    @pytest.mark.asyncio
    async def test_match_patterns(self, _spawned_historian):
        """Test pattern matching."""
        # Store memories
        await spawned_historian.store_memory(
            _content = "Database scaling pattern",
            _metadata = {"type": "scaling"},
            _memory_type = "pattern"
        )

        # Match
        _matches = await spawned_historian.match_patterns(
            _input_text = "scaling database",
            _threshold = 0.3
        )

        assert matches is not None

    @pytest.mark.asyncio
    async def test_provide_deliberation_context(self, _spawned_historian, _sample_memory):
        """Test providing deliberation context."""
        # Store relevant memories
        await spawned_historian.store_memory(
            _content = sample_memory["content"],
            _metadata = sample_memory["metadata"],
            _memory_type = "deliberation"
        )

        # Provide context
        _context = await spawned_historian.provide_deliberation_context(
            _session_id = "delib-001",
            _problem = "architecture decision"
        )

        assert context is not None

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, _spawned_historian):
        """Test concurrent memory operations."""
        # Store multiple memories concurrently
        _tasks = []
        for i in range(10):
            _task = spawned_historian.store_memory(
                _content = f"Memory {i}",
                _metadata = {"index": i},
                _memory_type = "test"
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Verify all stored
        _stats = spawned_historian.get_memory_statistics()
        assert stats["total_memories"] >= 10

    @pytest.mark.asyncio
    async def test_cache_efficiency(self, _spawned_historian):
        """Test cache efficiency."""
        # Store and retrieve to build cache stats
        for i in range(20):
            await spawned_historian.store_memory(
                _content = f"Memory {i}",
                _metadata = {"index": i},
                _memory_type = "cache_test"
            )

        _stats = spawned_historian.get_memory_statistics()
        assert stats["cache_size"] > 0

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_historian, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        _message = ActorMessage(
            _message_type = "store_memory",
            _content = {"content": "test", "metadata": {}},
            _sender = "test",
            _recipient = "historian-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        _start = time.time()
        await spawned_historian.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "historian_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_historian, _mock_db):
        """Test agent state persistence."""
        # Store memory
        await spawned_historian.store_memory(
            _content = "Persistent memory",
            _metadata = {"test": "persist"},
            _memory_type = "test"
        )

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_historian.save_state()

        # Verify state saved
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, _historian_agent):
        """Test agent error recovery."""
        await historian_agent.spawn()
        historian_agent._state = ActorState.ERROR
        await historian_agent.resume()
        assert historian_agent._state == ActorState.ACTIVE
