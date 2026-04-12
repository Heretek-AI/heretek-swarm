"""
Tests for MCP Client

Validates external MCP server connection and tool proxying.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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

    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """Test successful connection."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"name": "test-server"})

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.connect()

            assert result is True
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.connect()

            assert result is False
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnect."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"name": "test-server"})

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await client.connect()
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_list_tools(self, client):
        """Test listing tools."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "tools": [
                {"name": "tool1", "description": "First tool"},
                {"name": "tool2", "description": "Second tool"},
            ]
        })

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await client.connect()
            tools = await client.list_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"

    @pytest.mark.asyncio
    async def test_call_tool(self, client):
        """Test calling a tool."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "success": True,
            "result": {"echo": "hello"}
        })

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await client.connect()
            result = await client.call_tool("echo", {"message": "hello"})

            assert result["success"] is True
            assert result["result"]["echo"] == "hello"

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await client.connect()
            health = await client.health_check()

            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_not_connected_error(self, client):
        """Test error when client not connected."""
        with pytest.raises(RuntimeError, match="not connected"):
            await client.list_tools()


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
