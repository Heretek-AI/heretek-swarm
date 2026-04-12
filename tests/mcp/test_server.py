"""
Tests for MCP Server

Validates MCP server endpoints and functionality.
"""

import pytest

from heretek_swarm.mcp.registry import MCPToolRegistry
from heretek_swarm.mcp.server import MCPServer, get_registry, set_registry


class TestMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def server(self):
        """Create test server."""
        return MCPServer()

    @pytest.fixture
    def registry(self):
        """Create test registry."""
        return MCPToolRegistry()

    def test_server_creation(self, server):
        """Test server creation."""
        assert server.registry is not None
        assert server.is_running is False

    def test_register_tool(self, server):
        """Test registering a tool."""
        async def echo_handler(args, ctx):
            return {"echo": args.get("message", "")}

        server.register_tool(
            name="echo",
            description="Echo a message",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            },
            handler=echo_handler,
            category="utility",
        )

        tool = server.registry.get_tool("echo")
        assert tool is not None
        assert tool.name == "echo"
        assert tool.category == "utility"

    def test_register_tool_with_all_params(self, server):
        """Test registering tool with all parameters."""
        async def handler(args, ctx):
            return {}

        server.register_tool(
            name="full_tool",
            description="Tool with all params",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            handler=handler,
            category="test",
            version="1.0.0",
            tags=["tag1", "tag2"],
        )

        tool = server.registry.get_tool("full_tool")
        assert tool.version == "1.0.0"
        assert tool.tags == ["tag1", "tag2"]
        assert tool.output_schema == {"type": "object"}


class TestRegistryGlobalAccess:
    """Test global registry access."""

    def test_get_set_registry(self):
        """Test setting and getting global registry."""
        registry = MCPToolRegistry()
        set_registry(registry)

        retrieved = get_registry()
        assert retrieved is registry

    def test_get_registry_when_not_set(self):
        """Test getting registry when not set creates new one."""
        # Reset global
        import heretek_swarm.mcp.server as server_module
        server_module._registry = None

        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, MCPToolRegistry)


class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    @pytest.fixture
    def server(self):
        """Create test server with tools."""
        srv = MCPServer()

        async def add_handler(args, ctx):
            a = args.get("a", 0)
            b = args.get("b", 0)
            return {"result": a + b}

        async def multiply_handler(args, ctx):
            a = args.get("a", 0)
            b = args.get("b", 0)
            return {"result": a * b}

        srv.register_tool(
            name="add",
            description="Add two numbers",
            input_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                }
            },
            handler=add_handler,
            category="math",
        )

        srv.register_tool(
            name="multiply",
            description="Multiply two numbers",
            input_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                }
            },
            handler=multiply_handler,
            category="math",
        )

        set_registry(srv.registry)
        return srv

    @pytest.mark.asyncio
    async def test_server_start_stop(self, server):
        """Test server start and stop."""
        await server.start()
        assert server.is_running is True

        await server.stop()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_tool_invocation(self, server):
        """Test tool invocation through server registry."""
        await server.start()

        result = await server.registry.invoke("add", {"a": 5, "b": 3})

        assert result["success"] is True
        assert result["result"]["result"] == 8

    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test listing all registered tools."""
        await server.start()

        tools = server.registry.list_tools()
        assert len(tools) == 2

        summaries = server.registry.list_tool_summaries()
        assert len(summaries) == 2

    @pytest.mark.asyncio
    async def test_filter_by_category(self, server):
        """Test filtering tools by category."""
        await server.start()

        math_tools = server.registry.list_tools(category="math")
        assert len(math_tools) == 2

        other_tools = server.registry.list_tools(category="other")
        assert len(other_tools) == 0
