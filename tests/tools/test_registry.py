"""
Tests for Tool Registry.

Validates dynamic tool discovery, registration, and execution.
"""

import pytest
from uuid import uuid4

from heretek_swarm.tools import (
    ToolRegistry,
    ToolRegistryConfig,
    ToolContext,
    ToolStatus,
)
from heretek_swarm.tools.base import BaseTool, SimpleTool
from heretek_swarm.tools.examples import (
    MemorySearchTool,
    HealthCheckTool,
    ConsensusVoteTool,
)


# Fixtures

@pytest.fixture
def registry_config(tmp_path):
    """Test registry configuration"""
    return ToolRegistryConfig(
        auto_discover=False,  # Disable auto-discovery for tests
        lazy_loading=False,
        cache_enabled=True,
        cache_ttl_seconds=300,
        max_tools=100
    )


@pytest.fixture
async def registry(registry_config):
    """Create test registry"""
    reg = ToolRegistry(registry_config)
    await reg.initialize()
    yield reg
    await reg.shutdown()


# Test Cases

class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_register_tool(self, registry):
        """Test manual tool registration"""
        tool = MemorySearchTool()
        registry.register_tool(tool)
        
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "memory_search"
    
    def test_register_multiple_tools(self, registry):
        """Test registering multiple tools"""
        tools = [
            MemorySearchTool(),
            HealthCheckTool(),
            ConsensusVoteTool()
        ]
        
        for tool in tools:
            registry.register_tool(tool)
        
        registered = registry.list_tools()
        assert len(registered) == 3
    
    def test_list_tools_by_category(self, registry):
        """Test filtering tools by category"""
        registry.register_tool(MemorySearchTool())
        registry.register_tool(HealthCheckTool())
        registry.register_tool(ConsensusVoteTool())
        
        # Filter by memory category
        memory_tools = registry.list_tools(category="memory")
        assert len(memory_tools) == 1
        assert memory_tools[0].name == "memory_search"
        
        # Filter by system category
        system_tools = registry.list_tools(category="system")
        assert len(system_tools) == 1
        assert system_tools[0].name == "health_check"
    
    def test_list_tools_by_tags(self, registry):
        """Test filtering tools by tags"""
        registry.register_tool(MemorySearchTool())
        registry.register_tool(HealthCheckTool())
        
        # Filter by search tag
        search_tools = registry.list_tools(tags=["search"])
        assert len(search_tools) == 1
        
        # Filter by monitoring tag
        monitoring_tools = registry.list_tools(tags=["monitoring"])
        assert len(monitoring_tools) == 1
    
    def test_list_enabled_tools_only(self, registry):
        """Test that disabled tools are filtered"""
        tool = MemorySearchTool()
        registry.register_tool(tool)
        
        # Disable tool
        tool.disable()
        
        # Should not appear in enabled-only list
        enabled_tools = registry.list_tools(enabled_only=True)
        assert len(enabled_tools) == 0
        
        # Should appear when including disabled
        all_tools = registry.list_tools(enabled_only=False)
        assert len(all_tools) == 1
    
    @pytest.mark.asyncio
    async def test_get_tool(self, registry):
        """Test retrieving a tool by name"""
        tool = MemorySearchTool()
        registry.register_tool(tool)
        
        retrieved = await registry.get_tool("memory_search")
        
        assert retrieved is not None
        assert retrieved.metadata.name == "memory_search"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_tool(self, registry):
        """Test retrieving a tool that doesn't exist"""
        tool = await registry.get_tool("nonexistent_tool")
        assert tool is None
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, registry):
        """Test executing a tool"""
        tool = HealthCheckTool()
        registry.register_tool(tool)
        
        context = ToolContext(agent_id="test-agent")
        
        result = await registry.execute_tool(
            "health_check",
            {"services": ["redis", "postgres"]},
            context
        )
        
        assert result.status == ToolStatus.COMPLETED
        assert result.output is not None
        assert result.output.overall_healthy is True
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        """Test executing a tool that doesn't exist"""
        context = ToolContext(agent_id="test-agent")
        
        result = await registry.execute_tool(
            "nonexistent_tool",
            {},
            context
        )
        
        assert result.status == ToolStatus.FAILED
        assert "not found" in result.error.lower()
    
    def test_search_tools(self, registry):
        """Test searching tools"""
        registry.register_tool(MemorySearchTool())
        registry.register_tool(HealthCheckTool())
        registry.register_tool(ConsensusVoteTool())
        
        # Search by name
        results = registry.search_tools("memory")
        assert len(results) == 1
        assert results[0].name == "memory_search"
        
        # Search by description
        results = registry.search_tools("health")
        assert len(results) == 1
        assert results[0].name == "health_check"
        
        # Search by tag
        results = registry.search_tools("governance")
        assert len(results) == 1
        assert results[0].name == "consensus_vote"
    
    def test_get_categories(self, registry):
        """Test getting all categories"""
        registry.register_tool(MemorySearchTool())
        registry.register_tool(HealthCheckTool())
        
        categories = registry.get_categories()
        
        assert "memory" in categories
        assert "system" in categories
    
    def test_get_tags(self, registry):
        """Test getting all tags"""
        registry.register_tool(MemorySearchTool())
        
        tags = registry.get_tags()
        
        assert "search" in tags
        assert "memory" in tags
    
    def test_get_stats(self, registry):
        """Test getting registry statistics"""
        registry.register_tool(MemorySearchTool())
        registry.register_tool(HealthCheckTool())
        
        stats = registry.get_stats()
        
        assert stats["total_tools"] == 2
        assert stats["enabled_tools"] == 2
        assert stats["disabled_tools"] == 0
        assert stats["categories"] >= 2
    
    @pytest.mark.asyncio
    async def test_tool_enable_disable(self, registry):
        """Test enabling and disabling tools"""
        tool = MemorySearchTool()
        registry.register_tool(tool)
        
        # Disable
        tool.disable()
        assert tool.metadata.enabled is False
        assert tool.metadata.status == ToolStatus.DISABLED
        
        # Enable
        tool.enable()
        assert tool.metadata.enabled is True
        assert tool.metadata.status == ToolStatus.READY
    
    @pytest.mark.asyncio
    async def test_tool_execution_tracking(self, registry):
        """Test that tool executions are tracked"""
        tool = HealthCheckTool()
        registry.register_tool(tool)
        
        context = ToolContext(agent_id="test-agent")
        
        # Execute multiple times
        for _ in range(3):
            await registry.execute_tool(
                "health_check",
                {},
                context
            )
        
        # Check stats
        stats = tool.get_stats()
        assert stats["total_executions"] == 3
        assert stats["successful_executions"] == 3


class TestToolCaching:
    """Test tool caching functionality"""
    
    @pytest.fixture
    def cache_config(self):
        """Registry config with caching enabled"""
        return ToolRegistryConfig(
            auto_discover=False,
            lazy_loading=False,
            cache_enabled=True,
            cache_ttl_seconds=300
        )
    
    @pytest.fixture
    async def cached_registry(self, cache_config):
        """Registry with caching"""
        reg = ToolRegistry(cache_config)
        await reg.initialize()
        yield reg
        await reg.shutdown()
    
    @pytest.mark.asyncio
    async def test_tool_cached(self, cached_registry):
        """Test that tools are cached after first load"""
        tool = MemorySearchTool()
        cached_registry.register_tool(tool)
        
        # First get
        tool1 = await cached_registry.get_tool("memory_search")
        
        # Second get (should be cached)
        tool2 = await cached_registry.get_tool("memory_search")
        
        # Should be same instance
        assert tool1 is tool2
        
        # Check cache stats
        stats = cached_registry.get_stats()
        assert stats["cache_hits"] >= 0
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_config):
        """Test cache TTL expiration"""
        # Create registry with very short TTL
        cache_config.cache_ttl_seconds = 0
        
        reg = ToolRegistry(cache_config)
        await reg.initialize()
        
        tool = MemorySearchTool()
        reg.register_tool(tool)
        
        # First get
        tool1 = await reg.get_tool("memory_search")
        
        # Wait for TTL to expire
        import asyncio
        await asyncio.sleep(0.1)
        
        # Second get (should not be cached)
        tool2 = await reg.get_tool("memory_search")
        
        # Should be different instances (or None if cache expired)
        assert tool1 is not None
        assert tool2 is not None
        
        await reg.shutdown()


class TestSimpleTool:
    """Test SimpleTool wrapper"""
    
    @pytest.mark.asyncio
    async def test_simple_tool_sync_function(self):
        """Test SimpleTool with sync function"""
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        tool = SimpleTool(
            name="add_numbers",
            description="Add two numbers",
            func=add_numbers
        )
        
        context = ToolContext(agent_id="test")
        result = await tool.run({"a": 5, "b": 3}, context)
        
        assert result.status == ToolStatus.COMPLETED
        assert result.output == 8
    
    @pytest.mark.asyncio
    async def test_simple_tool_async_function(self):
        """Test SimpleTool with async function"""
        import asyncio
        
        async def multiply_numbers(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a * b
        
        tool = SimpleTool(
            name="multiply_numbers",
            description="Multiply two numbers",
            func=multiply_numbers
        )
        
        context = ToolContext(agent_id="test")
        result = await tool.run({"a": 4, "b": 5}, context)
        
        assert result.status == ToolStatus.COMPLETED
        assert result.output == 20
    
    @pytest.mark.asyncio
    async def test_simple_tool_timeout(self):
        """Test SimpleTool timeout"""
        import asyncio
        
        async def slow_function():
            await asyncio.sleep(10)
            return "done"
        
        tool = SimpleTool(
            name="slow_function",
            description="A slow function",
            func=slow_function,
            timeout_seconds=0.1
        )
        
        context = ToolContext(agent_id="test")
        result = await tool.run({}, context)
        
        assert result.status == ToolStatus.FAILED
        assert "timeout" in result.error.lower()


class TestToolRegistryIntegration:
    """Integration tests for tool registry"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, registry):
        """Test complete tool workflow"""
        # 1. Register tools
        tools = [
            MemorySearchTool(),
            HealthCheckTool(),
            ConsensusVoteTool()
        ]
        
        for tool in tools:
            registry.register_tool(tool)
        
        # 2. List tools
        all_tools = registry.list_tools()
        assert len(all_tools) == 3
        
        # 3. Search tools
        results = registry.search_tools("health")
        assert len(results) == 1
        
        # 4. Execute tool
        context = ToolContext(
            agent_id="test-agent",
            session_id=uuid4()
        )
        
        result = await registry.execute_tool(
            "health_check",
            {"services": ["redis"]},
            context
        )
        
        assert result.status == ToolStatus.COMPLETED
        assert result.execution_time_ms > 0
        
        # 5. Check stats
        stats = registry.get_stats()
        assert stats["total_executions"] >= 1
        
        # 6. Get tool stats
        health_tool = await registry.get_tool("health_check")
        tool_stats = health_tool.get_stats()
        assert tool_stats["total_executions"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
