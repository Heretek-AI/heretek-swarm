"""
Tests for MCP Tool Registry

Validates MCP tool registration, discovery, and execution.
"""

import pytest

from heretek_swarm.mcp.registry import (
    MCPToolMetadata,
    MCPToolRegistry,
    MCPServerRegistry,
    ToolProviderType,
)


class TestMCPToolRegistry:
    """Test MCP tool registry functionality."""

    @pytest.fixture
    def registry(self):
        """Create test registry."""
        return MCPToolRegistry()

    @pytest.fixture
    def sample_metadata(self):
        """Sample tool metadata."""
        return MCPToolMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            },
            category="test",
            version="1.0.0",
        )

    def test_register_tool(self, registry, sample_metadata):
        """Test registering a tool."""
        async def handler(args, ctx):
            return {"result": args["input"]}

        registry.register_tool(sample_metadata, handler)

        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_register_duplicate_tool(self, registry, sample_metadata):
        """Test that registering duplicate tool raises error."""
        async def handler(args, ctx):
            return {}

        registry.register_tool(sample_metadata, handler)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_tool(sample_metadata, handler)

    def test_unregister_tool(self, registry, sample_metadata):
        """Test unregistering a tool."""
        async def handler(args, ctx):
            return {}

        registry.register_tool(sample_metadata, handler)
        assert registry.get_tool("test_tool") is not None

        result = registry.unregister_tool("test_tool")
        assert result is True
        assert registry.get_tool("test_tool") is None

    def test_unregister_nonexistent_tool(self, registry):
        """Test unregistering nonexistent tool returns False."""
        result = registry.unregister_tool("nonexistent")
        assert result is False

    def test_list_tools(self, registry):
        """Test listing tools."""
        metadata1 = MCPToolMetadata(
            name="tool1",
            description="First tool",
            input_schema={},
            category="category1",
        )
        metadata2 = MCPToolMetadata(
            name="tool2",
            description="Second tool",
            input_schema={},
            category="category2",
        )

        registry.register_tool(metadata1, lambda a, b: None)
        registry.register_tool(metadata2, lambda a, b: None)

        tools = registry.list_tools()
        assert len(tools) == 2

    def test_list_tools_by_category(self, registry):
        """Test filtering tools by category."""
        metadata1 = MCPToolMetadata(
            name="tool1",
            description="First tool",
            input_schema={},
            category="memory",
        )
        metadata2 = MCPToolMetadata(
            name="tool2",
            description="Second tool",
            input_schema={},
            category="system",
        )

        registry.register_tool(metadata1, lambda a, b: None)
        registry.register_tool(metadata2, lambda a, b: None)

        memory_tools = registry.list_tools(category="memory")
        assert len(memory_tools) == 1
        assert memory_tools[0].name == "tool1"

    def test_list_tools_enabled_only(self, registry):
        """Test filtering enabled tools only."""
        metadata1 = MCPToolMetadata(
            name="enabled_tool",
            description="Enabled tool",
            input_schema={},
            enabled=True,
        )
        metadata2 = MCPToolMetadata(
            name="disabled_tool",
            description="Disabled tool",
            input_schema={},
            enabled=False,
        )

        registry.register_tool(metadata1, lambda a, b: None)
        registry.register_tool(metadata2, lambda a, b: None)

        all_tools = registry.list_tools(enabled_only=False)
        assert len(all_tools) == 2

        enabled_tools = registry.list_tools(enabled_only=True)
        assert len(enabled_tools) == 1
        assert enabled_tools[0].name == "enabled_tool"

    def test_list_tool_summaries(self, registry):
        """Test listing tools in MCP format."""
        metadata = MCPToolMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            category="test",
            version="1.0.0",
            provider=ToolProviderType.LOCAL,
            enabled=True,
        )

        registry.register_tool(metadata, lambda a, b: None)

        summaries = registry.list_tool_summaries()
        assert len(summaries) == 1
        assert summaries[0]["name"] == "test_tool"
        assert summaries[0]["category"] == "test"
        assert summaries[0]["provider"] == "local"

    def test_get_stats(self, registry):
        """Test getting tool statistics."""
        metadata = MCPToolMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={},
        )

        registry.register_tool(metadata, lambda a, b: None)

        stats = registry.get_stats("test_tool")
        assert stats is not None
        assert stats["calls"] == 0
        assert stats["errors"] == 0

    def test_get_stats_nonexistent(self, registry):
        """Test getting stats for nonexistent tool."""
        stats = registry.get_stats("nonexistent")
        assert stats is None


class TestMCPToolInvocation:
    """Test tool invocation."""

    @pytest.fixture
    def registry(self):
        """Create test registry."""
        return MCPToolRegistry()

    def test_invoke_success(self, registry):
        """Test successful tool invocation."""
        metadata = MCPToolMetadata(
            name="echo",
            description="Echo input back",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            },
        )

        async def handler(args, ctx):
            return {"echoed": args["message"]}

        registry.register_tool(metadata, handler)

        result = registry.invoke_sync("echo", {"message": "hello"})

        assert result["success"] is True
        assert result["result"]["echoed"] == "hello"

    def test_invoke_not_found(self, registry):
        """Test invoking nonexistent tool."""
        result = registry.invoke_sync("nonexistent", {})

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_invoke_disabled_tool(self, registry):
        """Test invoking disabled tool."""
        metadata = MCPToolMetadata(
            name="disabled_tool",
            description="A disabled tool",
            input_schema={},
            enabled=False,
        )

        registry.register_tool(metadata, lambda a, b: None)

        result = registry.invoke_sync("disabled_tool", {})

        assert result["success"] is False
        assert "disabled" in result["error"]

    def test_invoke_validation_failure(self, registry):
        """Test invocation with invalid arguments."""
        metadata = MCPToolMetadata(
            name="strict_tool",
            description="A strict tool",
            input_schema={
                "type": "object",
                "properties": {
                    "required_field": {"type": "string"}
                },
                "required": ["required_field"]
            },
        )

        registry.register_tool(metadata, lambda a, b: None)

        result = registry.invoke_sync("strict_tool", {})

        assert result["success"] is False
        assert "Invalid arguments" in result["error"]

    def test_invoke_handler_exception(self, registry):
        """Test invocation when handler raises exception."""
        metadata = MCPToolMetadata(
            name="failing_tool",
            description="A failing tool",
            input_schema={},
        )

        async def handler(args, ctx):
            raise ValueError("Handler error")

        registry.register_tool(metadata, handler)

        result = registry.invoke_sync("failing_tool", {})

        assert result["success"] is False
        assert "Handler error" in result["error"]


class TestMCPServerRegistry:
    """Test MCP server registry."""

    @pytest.fixture
    def server_registry(self):
        """Create test server registry."""
        return MCPServerRegistry()

    def test_register_server(self, server_registry):
        """Test registering a server."""
        server_registry.register_server(
            server_id="test-server",
            name="Test Server",
            base_url="http://localhost:8080",
            auth_token="secret",
        )

        server = server_registry.get_server("test-server")
        assert server is not None
        assert server["name"] == "Test Server"
        assert server["base_url"] == "http://localhost:8080"
        assert server["status"] == "disconnected"

    def test_register_duplicate_server(self, server_registry):
        """Test that registering duplicate server raises error."""
        server_registry.register_server(
            server_id="test-server",
            name="Test Server",
            base_url="http://localhost:8080",
        )

        with pytest.raises(ValueError, match="already registered"):
            server_registry.register_server(
                server_id="test-server",
                name="Another Server",
                base_url="http://localhost:9090",
            )

    def test_unregister_server(self, server_registry):
        """Test unregistering a server."""
        server_registry.register_server(
            server_id="test-server",
            name="Test Server",
            base_url="http://localhost:8080",
        )

        result = server_registry.unregister_server("test-server")
        assert result is True
        assert server_registry.get_server("test-server") is None

    def test_list_servers(self, server_registry):
        """Test listing servers."""
        server_registry.register_server(
            server_id="server1",
            name="Server 1",
            base_url="http://localhost:8080",
        )
        server_registry.register_server(
            server_id="server2",
            name="Server 2",
            base_url="http://localhost:8081",
        )

        servers = server_registry.list_servers()
        assert len(servers) == 2

    def test_update_server_status(self, server_registry):
        """Test updating server status."""
        server_registry.register_server(
            server_id="test-server",
            name="Test Server",
            base_url="http://localhost:8080",
        )

        server_registry.update_server_status("test-server", "connected")
        server = server_registry.get_server("test-server")
        assert server["status"] == "connected"


class TestToolMetadata:
    """Test tool metadata."""

    def test_tool_metadata_creation(self):
        """Test creating tool metadata."""
        metadata = MCPToolMetadata(
            name="test",
            description="Test tool",
            input_schema={"type": "object"},
            category="test",
            version="2.0.0",
            provider=ToolProviderType.EXTERNAL,
            server_id="external-server",
            tags=["external", "api"],
        )

        assert metadata.name == "test"
        assert metadata.category == "test"
        assert metadata.version == "2.0.0"
        assert metadata.provider == ToolProviderType.EXTERNAL
        assert metadata.server_id == "external-server"
        assert metadata.tags == ["external", "api"]

    def test_tool_provider_type_enum(self):
        """Test provider type enum values."""
        assert ToolProviderType.LOCAL.value == "local"
        assert ToolProviderType.EXTERNAL.value == "external"
        assert ToolProviderType.PROXIED.value == "proxied"
