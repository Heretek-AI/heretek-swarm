"""
Tests for Tool Registry.

Validates tool registration, retrieval, and listing functionality.
"""

import pytest

from heretek_swarm.tools import (
    ToolContext,
    ToolRegistry,
    ToolRegistryConfig,
    ToolStatus,
)
from heretek_swarm.tools.base import SimpleTool
from heretek_swarm.tools.examples import (
    ConsensusVoteTool,
    HealthCheckTool,
    MemorySearchTool,
)


@pytest.fixture
def registry_config():
    """Test registry configuration"""
    return ToolRegistryConfig(
        auto_register=False,
        validate_on_register=False,
        max_tools=100
    )


@pytest.fixture
def registry(registry_config):
    """Create test registry"""
    return ToolRegistry(registry_config)


class TestToolRegistry:
    """Test tool registry functionality"""

    def test_register(self, registry):
        """Test tool registration"""
        tool = MemorySearchTool()
        registry.register(tool)

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0] == "memory_search"

    def test_register_multiple(self, registry):
        """Test registering multiple tools"""
        tools = [
            MemorySearchTool(),
            HealthCheckTool(),
            ConsensusVoteTool()
        ]

        for tool in tools:
            registry.register(tool)

        registered = registry.list_tools()
        assert len(registered) == 3

    def test_list_tools_by_category(self, registry):
        """Test filtering tools by category"""
        registry.register(MemorySearchTool())
        registry.register(HealthCheckTool())
        registry.register(ConsensusVoteTool())

        # Filter by memory category
        memory_tools = registry.list_tools(category="memory")
        assert len(memory_tools) == 1
        assert "memory_search" in memory_tools

        # Filter by system category
        system_tools = registry.list_tools(category="system")
        assert len(system_tools) == 1
        assert "health_check" in system_tools

    def test_get_tool(self, registry):
        """Test retrieving a tool by name"""
        tool = MemorySearchTool()
        registry.register(tool)

        retrieved = registry.get("memory_search")

        assert retrieved is not None
        assert retrieved.metadata.name == "memory_search"

    def test_get_nonexistent_tool(self, registry):
        """Test retrieving a tool that doesn't exist"""
        tool = registry.get("nonexistent_tool")
        assert tool is None

    def test_unregister_tool(self, registry):
        """Test unregistering a tool"""
        tool = MemorySearchTool()
        registry.register(tool)

        result = registry.unregister("memory_search")
        assert result is True

        # Verify tool is gone
        assert registry.get("memory_search") is None

    def test_unregister_nonexistent(self, registry):
        """Test unregistering a non-existent tool"""
        result = registry.unregister("nonexistent_tool")
        assert result is False

    def test_get_metadata(self, registry):
        """Test getting tool metadata"""
        tool = MemorySearchTool()
        registry.register(tool)

        metadata = registry.get_metadata("memory_search")
        assert metadata is not None
        assert metadata.name == "memory_search"

    def test_get_metadata_nonexistent(self, registry):
        """Test getting metadata for non-existent tool"""
        metadata = registry.get_metadata("nonexistent_tool")
        assert metadata is None


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

        context = ToolContext(agent_id="test", session_id="test-session")
        result = await tool.execute(context, a=5, b=3)

        assert result.status == ToolStatus.SUCCESS
        assert result.output == 8

    @pytest.mark.asyncio
    async def test_simple_tool_with_kwargs(self):
        """Test SimpleTool that uses kwargs"""
        def add_with_multiplier(a: int, b: int, multiplier: int = 1) -> int:
            return (a + b) * multiplier

        tool = SimpleTool(
            name="add_with_multiplier",
            description="Add and multiply",
            func=add_with_multiplier
        )

        context = ToolContext(agent_id="test", session_id="test-session")
        result = await tool.execute(context, a=3, b=5, multiplier=2)

        assert result.status == ToolStatus.SUCCESS
        assert result.output == 16

    @pytest.mark.asyncio
    async def test_simple_tool_error(self):
        """Test SimpleTool with error"""
        def bad_function():
            raise ValueError("test error")

        tool = SimpleTool(
            name="bad_function",
            description="A function that fails",
            func=bad_function
        )

        context = ToolContext(agent_id="test", session_id="test-session")
        result = await tool.execute(context)

        assert result.status == ToolStatus.FAILED
        assert "test error" in result.error.lower()


class TestToolRegistryIntegration:
    """Integration tests for tool registry"""

    def test_full_workflow(self, registry):
        """Test complete tool workflow"""
        # 1. Register tools
        tools = [
            MemorySearchTool(),
            HealthCheckTool(),
            ConsensusVoteTool()
        ]

        for tool in tools:
            registry.register(tool)

        # 2. List tools
        all_tools = registry.list_tools()
        assert len(all_tools) == 3

        # 3. Get tool
        health_tool = registry.get("health_check")
        assert health_tool is not None

        # 4. Get metadata
        metadata = registry.get_metadata("consensus_vote")
        assert metadata is not None

        # 5. Unregister
        result = registry.unregister("consensus_vote")
        assert result is True

        # 6. Verify unregistered
        remaining = registry.list_tools()
        assert len(remaining) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])