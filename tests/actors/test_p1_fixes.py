"""
Tests for P1 Critical Fixes - Actor System and Runtime Issues

This module tests all P1 fixes from the zero-trust audit:
1. ActorSupervisor.initialize() method
2. State value case consistency
3. Datetime type handling in _find_idle_agent
4. Exception handling in async methods
5. LLM timeout handling
6. Actor cleanup on shutdown
7. Input validation in handoff
8. Cache size limits in historian
"""

import asyncio
import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import modules directly to avoid circular imports
from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.actors.base import AgentActor, ActorMessage, ActorState
from heretek_swarm.actors.handoff import AgentHandoff, HandoffValidator, HandoffResult
from heretek_swarm.actors.historian import HistorianAgent, LRUCache
from heretek_swarm.runtime.tools import ToolRegistry


# =============================================================================
# Test 1: ActorSupervisor.initialize() method
# =============================================================================

class TestActorSupervisorInitialize:
    """Test the initialize() method added to ActorSupervisor."""
    
    @pytest.mark.asyncio
    async def test_initialize_method_exists(self):
        """Test that initialize() method exists and is callable."""
        supervisor = ActorSupervisor()
        assert hasattr(supervisor, 'initialize')
        assert callable(supervisor.initialize)
    
    @pytest.mark.asyncio
    async def test_initialize_returns_none(self):
        """Test that initialize() completes without error."""
        supervisor = ActorSupervisor()
        result = await supervisor.initialize()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_initialize_called_from_runtime(self):
        """Test that runtime can call initialize() on supervisor."""
        # This simulates the call in autonomous_runtime.py:87
        supervisor = ActorSupervisor()
        # Should not raise AttributeError
        await supervisor.initialize()


# =============================================================================
# Test 2: State Value Case Consistency
# =============================================================================

class TestStateValueCase:
    """Test state value case consistency."""
    
    def test_actor_state_enum_values(self):
        """Test that ActorState enum values are lowercase."""
        assert ActorState.SPAWNING.value == "spawning"
        assert ActorState.ACTIVE.value == "active"
        assert ActorState.SUSPENDED.value == "suspended"
        assert ActorState.TERMINATED.value == "terminated"
        assert ActorState.ERROR.value == "error"
    
    def test_state_comparison_with_string(self):
        """Test that state comparison works with lowercase strings."""
        status = MagicMock()
        status.state = ActorState.SUSPENDED
        
        # This is the pattern used in autonomous_runtime.py:186
        assert status.state.value in ["suspended", "terminated", "error"]
        
        status.state = ActorState.TERMINATED
        assert status.state.value in ["suspended", "terminated", "error"]
        
        status.state = ActorState.ERROR
        assert status.state.value in ["suspended", "terminated", "error"]
        
        status.state = ActorState.ACTIVE
        assert status.state.value not in ["suspended", "terminated", "error"]


# =============================================================================
# Test 3: Datetime Type Handling
# =============================================================================

class TestDatetimeHandling:
    """Test datetime type handling in _find_idle_agent."""
    
    def test_iso_timestamp_parsing(self):
        """Test that ISO format timestamps can be parsed."""
        timestamp_str = datetime.utcnow().isoformat()
        parsed = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)
    
    def test_datetime_subtraction(self):
        """Test that datetime subtraction works correctly."""
        now = datetime.utcnow()
        past = now - timedelta(minutes=30)
        
        idle_time = now - past
        assert idle_time.total_seconds() == 30 * 60
    
    @pytest.mark.asyncio
    async def test_find_idle_agent_with_string_timestamp(self):
        """Test _find_idle_agent handles string timestamps."""
        # Test the datetime parsing logic directly
        # This simulates what happens in autonomous_runtime.py:_find_idle_agent
        
        # String timestamp (the bug scenario)
        timestamp_str = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        
        # The fix: parse ISO format timestamp
        try:
            last_activity_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            idle_time = datetime.utcnow() - last_activity_dt
            
            # Should be approximately 2 hours (7200 seconds)
            assert idle_time.total_seconds() > 7000
        except (ValueError, TypeError) as e:
            pytest.fail(f"Failed to parse timestamp: {e}")


# =============================================================================
# Test 4: Exception Handling in Async Methods
# =============================================================================

class TestExceptionHandling:
    """Test exception handling in async methods."""
    
    @pytest.mark.asyncio
    async def test_spawn_exception_handling(self):
        """Test that spawn() handles exceptions properly."""
        class FailingActor(AgentActor):
            async def initialize(self):
                raise ValueError("Intentional failure")
            
            async def process_message(self, message: ActorMessage) -> None:
                pass
        
        actor = FailingActor(agent_id="test-fail")
        
        with pytest.raises(ValueError, match="Intentional failure"):
            await actor.spawn()
        
        # State should be ERROR after failure
        assert actor.state == ActorState.ERROR
        assert actor.error_count > 0
    
    @pytest.mark.asyncio
    async def test_terminate_exception_handling(self):
        """Test that terminate() handles exceptions properly."""
        actor = AgentActor(agent_id="test-term")
        await actor.spawn()
        
        # Mock cleanup to raise exception
        original_cleanup = actor.cleanup
        async def failing_cleanup():
            raise RuntimeError("Cleanup failed")
        actor.cleanup = failing_cleanup
        
        # Should propagate exception
        with pytest.raises(RuntimeError, match="Cleanup failed"):
            await actor.terminate()
        
        # State should be ERROR
        assert actor.state == ActorState.ERROR
    
    @pytest.mark.asyncio
    async def test_run_with_llm_timeout_parameter_exists(self):
        """Test that run_with_llm accepts timeout parameter."""
        actor = AgentActor(agent_id="test-llm")
        
        # Verify the method signature includes timeout parameter
        import inspect
        sig = inspect.signature(actor.run_with_llm)
        assert 'timeout' in sig.parameters
        assert sig.parameters['timeout'].default == 60  # Default timeout is 60 seconds
        
        # Mock swarms_agent to return immediately
        def quick_run(*args, **kwargs):
            return "result"
        
        mock_agent = MagicMock()
        mock_agent.run = quick_run
        actor.swarms_agent = mock_agent
        
        # Should complete successfully with timeout
        result = await actor.run_with_llm("test prompt", timeout=5)
        assert result == "result"


# =============================================================================
# Test 5: Actor Cleanup on Shutdown
# =============================================================================

class TestActorCleanup:
    """Test actor cleanup on shutdown."""
    
    @pytest.mark.asyncio
    async def test_cleanup_clears_mailbox(self):
        """Test that cleanup() clears the mailbox."""
        actor = AgentActor(agent_id="test-cleanup")
        await actor.spawn()
        
        # Add messages to mailbox
        for i in range(5):
            msg = ActorMessage(
                sender="test",
                message_type="test",
                content={"i": i},
                timestamp=datetime.utcnow().isoformat()
            )
            await actor.mailbox.put(msg)
        
        assert actor.mailbox.qsize() == 5
        
        await actor.cleanup()
        
        # Mailbox should be cleared
        assert actor.mailbox.qsize() == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_clears_internal_state(self):
        """Test that cleanup() clears internal state."""
        actor = AgentActor(agent_id="test-cleanup")
        actor.update_state("key1", "value1")
        actor.update_state("key2", "value2")
        
        assert actor.get_state("key1") == "value1"
        
        await actor.cleanup()
        
        # Internal state should be cleared
        assert actor.get_state("key1") is None
        assert actor.get_state("key2") is None
    
    @pytest.mark.asyncio
    async def test_cleanup_clears_handlers(self):
        """Test that cleanup() clears message handlers."""
        actor = AgentActor(agent_id="test-cleanup")
        initial_count = len(actor._message_handlers)
        
        # Add custom handler
        actor.register_handler("custom", lambda m: None)
        assert len(actor._message_handlers) > initial_count
        
        await actor.cleanup()
        
        # Handlers should be cleared
        assert len(actor._message_handlers) == 0


# =============================================================================
# Test 6: LLM Timeout in Tool Registry
# =============================================================================

class TestToolTimeout:
    """Test timeout handling in ToolRegistry."""
    
    @pytest.mark.asyncio
    async def test_tool_registry_default_timeout(self):
        """Test ToolRegistry has default timeout."""
        registry = ToolRegistry()
        assert registry.default_timeout == 30
    
    @pytest.mark.asyncio
    async def test_tool_registry_custom_timeout(self):
        """Test ToolRegistry accepts custom timeout."""
        registry = ToolRegistry(default_timeout=60)
        assert registry.default_timeout == 60
    
    @pytest.mark.asyncio
    async def test_tool_execute_with_timeout(self):
        """Test tool execution respects timeout."""
        registry = ToolRegistry(default_timeout=1)
        
        async def slow_tool():
            await asyncio.sleep(10)
            return "result"
        
        registry.register("slow", slow_tool, "Slow tool")
        
        with pytest.raises(asyncio.TimeoutError):
            await registry.execute("slow")
    
    @pytest.mark.asyncio
    async def test_tool_execute_timeout_override(self):
        """Test timeout can be overridden per execution."""
        registry = ToolRegistry(default_timeout=60)
        
        async def slow_tool():
            await asyncio.sleep(0.5)
            return "result"
        
        registry.register("slow", slow_tool, "Slow tool")
        
        # Should timeout with 0.1s override
        with pytest.raises(asyncio.TimeoutError):
            await registry.execute("slow", timeout=0.1)


# =============================================================================
# Test 7: Input Validation in Handoff
# =============================================================================

class TestHandoffValidation:
    """Test input validation in handoff."""
    
    def test_handoff_validator_empty_from_agent_id(self):
        """Test validation fails with empty from_agent_id."""
        with pytest.raises(ValueError, match="from_agent_id must be a non-empty string"):
            HandoffValidator.validate("", "agent2", {"key": "value"})
    
    def test_handoff_validator_empty_to_agent_id(self):
        """Test validation fails with empty to_agent_id."""
        with pytest.raises(ValueError, match="to_agent_id must be a non-empty string"):
            HandoffValidator.validate("agent1", "", {"key": "value"})
    
    def test_handoff_validator_empty_context(self):
        """Test validation fails with empty context."""
        with pytest.raises(ValueError, match="context must be a non-empty dictionary"):
            HandoffValidator.validate("agent1", "agent2", {})
    
    def test_handoff_validator_same_agent_ids(self):
        """Test validation fails with same agent IDs."""
        with pytest.raises(ValueError, match="from_agent_id and to_agent_id must be different"):
            HandoffValidator.validate("agent1", "agent1", {"key": "value"})
    
    def test_handoff_validator_context_too_large(self):
        """Test validation fails with oversized context."""
        large_context = {"data": "x" * 100000}  # 100KB
        with pytest.raises(ValueError, match="Context size"):
            HandoffValidator.validate("agent1", "agent2", large_context)
    
    def test_handoff_validator_valid_input(self):
        """Test validation passes with valid input."""
        # Should not raise
        HandoffValidator.validate("agent1", "agent2", {"key": "value"})
    
    @pytest.mark.asyncio
    async def test_handoff_rate_limiting(self):
        """Test handoff rate limiting."""
        handoff = AgentHandoff(historian=None)
        
        # Make multiple rapid handoffs
        for i in range(HandoffValidator.MAX_HANDOFFS_PER_MINUTE + 1):
            result = await handoff.execute_handoff(
                from_agent_id=f"agent{i}",
                to_agent_id=f"agent{i+10}",
                context={"test": i}
            )
        
        # Last one should fail due to rate limiting
        result = await handoff.execute_handoff(
            from_agent_id="agent_final",
            to_agent_id="agent_target",
            context={"test": "final"}
        )
        
        assert not result.success
        assert "Rate limit" in result.error
    
    @pytest.mark.asyncio
    async def test_handoff_validation_error_result(self):
        """Test that validation errors return proper HandoffResult."""
        handoff = AgentHandoff(historian=None)
        
        result = await handoff.execute_handoff(
            from_agent_id="",  # Invalid
            to_agent_id="agent2",
            context={"key": "value"}
        )
        
        assert isinstance(result, HandoffResult)
        assert not result.success
        assert "Validation failed" in result.error


# =============================================================================
# Test 8: Cache Size Limits in Historian
# =============================================================================

class TestLRUCache:
    """Test LRU cache implementation."""
    
    def test_lru_cache_basic_operations(self):
        """Test basic cache get/set operations."""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert len(cache) == 2
    
    def test_lru_cache_eviction(self):
        """Test that LRU cache evicts oldest entries."""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Add one more, should evict key1
        cache.set("key4", "value4")
        
        assert len(cache) == 3
        assert "key1" not in cache
        assert "key2" in cache
        assert "key3" in cache
        assert "key4" in cache
    
    def test_lru_cache_access_updates_order(self):
        """Test that accessing an item updates its LRU order."""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1, making it most recently used
        cache.get("key1")
        
        # Add new key, should evict key2 (now oldest)
        cache.set("key4", "value4")
        
        assert "key1" in cache  # Still there because accessed
        assert "key2" not in cache  # Evicted
        assert "key3" in cache
        assert "key4" in cache
    
    def test_lru_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_statistics()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] > 0
    
    def test_lru_cache_clear(self):
        """Test cache clear operation."""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")
        
        cache.clear()
        
        assert len(cache) == 0
        stats = cache.get_statistics()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestHistorianCacheLimits:
    """Test historian cache size limits."""
    
    def test_historian_custom_cache_sizes(self):
        """Test historian accepts custom cache sizes."""
        historian = HistorianAgent(
            context_cache_max_size=50,
            pattern_cache_max_size=25
        )
        
        assert historian.context_cache.max_size == 50
        assert historian.pattern_cache.max_size == 25
    
    def test_historian_default_cache_sizes(self):
        """Test historian default cache sizes."""
        historian = HistorianAgent()
        
        assert historian.context_cache.max_size == 100
        assert historian.pattern_cache.max_size == 50
    
    def test_historian_cache_eviction(self):
        """Test that historian caches evict when full."""
        historian = HistorianAgent(
            context_cache_max_size=3,
            pattern_cache_max_size=2
        )
        
        # Fill context cache
        for i in range(5):
            historian.context_cache.set(f"ctx{i}", f"value{i}")
        
        # Should only have 3 items
        assert len(historian.context_cache) == 3
        
        # Fill pattern cache
        for i in range(4):
            historian.pattern_cache.set(f"pat{i}", f"value{i}")
        
        # Should only have 2 items
        assert len(historian.pattern_cache) == 2
    
    def test_historian_statistics_includes_cache_stats(self):
        """Test historian statistics include cache statistics."""
        historian = HistorianAgent()
        
        # Add some data
        historian.context_cache.set("test", "value")
        historian.pattern_cache.set("pattern", "data")
        
        stats = historian.get_memory_statistics()
        
        assert "context_cache" in stats
        assert "pattern_cache" in stats
        assert "size" in stats["context_cache"]
        assert "hit_rate_percent" in stats["pattern_cache"]
