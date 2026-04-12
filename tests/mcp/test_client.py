"""
Tests for MCP Client

Validates external MCP server connection and tool proxying.
"""

import pytest

from heretek_swarm.mcp.client import MCPClient, MCPClientManager
from heretek_swarm.mcp.registry import MCPToolRegistry, ToolProviderType


class TestMCPClient:
    """Test MCP client functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return MCPClient(
            server_id="test-server",
            base_url="http://localhost:8080",
            auth_token="secret",
            timeout=10.0,
        )

    def test_client_creation(self, client):
        """Test client creation."""
        assert client.server_id == "test-server"
        assert client.base_url == "http://localhost:8080"
        assert client.is_connected is False

    def test_client_headers_without_token(self):
        """Test client headers without auth token."""
        client = MCPClient(
            server_id="test",
            base_url="http://localhost:8080",
        )
        headers = client._get_headers()
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_client_headers_with_token(self, client):
        """Test client headers with auth token."""
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer secret"
        assert headers["Content-Type"] == "application/json"

    def test_client_not_connected_by_default(self, client):
        """Test client is not connected by default."""
        assert client.is_connected is False

    def test_client_base_url_strips_trailing_slash(self):
        """Test client strips trailing slash from base URL."""
        client = MCPClient(
            server_id="test",
            base_url="http://localhost:8080/",
        )
        assert client.base_url == "http://localhost:8080"


class TestMCPClientManager:
    """Test MCP client manager."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return MCPClientManager(MCPToolRegistry())

    def test_manager_creation(self, manager):
        """Test manager creation."""
        assert manager.server_registry is not None
        assert manager.list_servers() == []

    def test_list_proxied_tools_empty(self, manager):
        """Test listing proxied tools when none exist."""
        tools = manager.list_proxied_tools()
        assert tools == []

    def test_list_proxied_tools_with_filter(self, manager):
        """Test listing proxied tools with server filter."""
        # Add mock proxied tools
        manager._proxied_tools["tool1"] = "server1"
        manager._proxied_tools["tool2"] = "server1"
        manager._proxied_tools["tool3"] = "server2"

        server1_tools = manager.list_proxied_tools(server_id="server1")
        assert len(server1_tools) == 2

        server2_tools = manager.list_proxied_tools(server_id="server2")
        assert len(server2_tools) == 1

        all_tools = manager.list_proxied_tools()
        assert len(all_tools) == 3

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_server(self, manager):
        """Test disconnecting nonexistent server."""
        result = await manager.disconnect_server("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_server_health_not_connected(self, manager):
        """Test getting health for unconnected server."""
        health = await manager.get_server_health("nonexistent")
        assert health["status"] == "not_connected"

    def test_server_registry_access(self, manager):
        """Test accessing server registry."""
        assert manager.server_registry is not None
        assert hasattr(manager.server_registry, "register_server")
        assert hasattr(manager.server_registry, "list_servers")
