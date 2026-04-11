"""
Gateway Tests - EventMesh and A2A Protocol

Test coverage for gateway components.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.gateway import A2AServer, EventMesh

# =============================================================================
# EventMesh Tests
# =============================================================================

class TestEventMesh:
    """Test EventMesh connection manager."""

    @pytest.fixture
    def event_mesh(self):
        return EventMesh()

    @pytest.mark.asyncio
    async def test_register_client(self, _event_mesh):
        """Test client registration."""
        _mock_ws = AsyncMock()
        await event_mesh.register("test-client", mock_ws)

        assert "test-client" in event_mesh.clients
        assert event_mesh.client_count == 1

    @pytest.mark.asyncio
    async def test_unregister_client(self, _event_mesh):
        """Test client unregistration."""
        _mock_ws = AsyncMock()
        await event_mesh.register("test-client", mock_ws)
        await event_mesh.unregister("test-client")

        assert "test-client" not in event_mesh.clients
        assert event_mesh.client_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_clients(self, _event_mesh):
        """Test broadcast with null safety."""
        # Add mock clients
        _mock_ws1 = AsyncMock()
        _mock_ws2 = AsyncMock()
        await event_mesh.register("client-1", mock_ws1)
        await event_mesh.register("client-2", mock_ws2)

        # Broadcast
        _result = await event_mesh.broadcast(b"test message")

        assert result["sent"] == 2
        assert result["failed"] == 0
        mock_ws1.send_bytes.assert_called_once()
        mock_ws2.send_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_handles_failures(self, _event_mesh):
        """Test broadcast handles failed sends."""
        # Add one working and one failing client
        _mock_ws1 = AsyncMock()
        mock_ws1.client_state = MagicMock()
        mock_ws1.client_state.disconnecting = False

        # For failing client, we need to set up client_state BEFORE the side_effect
        # because broadcast checks _is_disconnecting() before calling send_bytes
        _mock_ws2 = AsyncMock()
        mock_ws2.client_state = MagicMock()
        mock_ws2.client_state.disconnecting = False
        mock_ws2.send_bytes = AsyncMock(side_effect=Exception("Connection lost"))

        await event_mesh.register("client-1", mock_ws1)
        await event_mesh.register("client-2", mock_ws2)

        _result = await event_mesh.broadcast(b"test")

        assert result["sent"] == 1
        assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_send_to_specific_client(self, _event_mesh):
        """Test targeted send."""
        _mock_ws = AsyncMock()
        await event_mesh.register("target-client", mock_ws)

        _success = await event_mesh.send_to("target-client", b"direct message")

        assert success is True
        mock_ws.send_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_client(self, _event_mesh):
        """Test send to unknown client fails gracefully."""
        _success = await event_mesh.send_to("unknown", b"message")
        assert success is False

    @pytest.mark.asyncio
    async def test_close_all_clients(self, _event_mesh):
        """Test closing all connections."""
        _mock_ws1 = AsyncMock()
        _mock_ws2 = AsyncMock()
        await event_mesh.register("client-1", mock_ws1)
        await event_mesh.register("client-2", mock_ws2)

        await event_mesh.close_all()

        assert event_mesh.client_count == 0
        mock_ws1.close.assert_called()
        mock_ws2.close.assert_called()


# =============================================================================
# A2A Server Tests
# =============================================================================

class TestA2AServer:
    """Test A2A Protocol server."""

    @pytest.fixture
    def a2a_server(self):
        event_mesh = EventMesh()
        return A2AServer(event_mesh)

    @pytest.mark.asyncio
    async def test_server_initialization(self, _a2a_server):
        """Test server initializes correctly."""
        assert a2a_server.agents == {}
        assert a2a_server.event_mesh is not None

    @pytest.mark.asyncio
    async def test_discovery_returns_agents(self, _a2a_server):
        """Test agent discovery."""
        # Add mock agents
        a2a_server.agents["agent-1"] = MagicMock(
            _id = "agent-1",
            _status = "idle",
            _connected_at = "2026-04-07T00:00:00Z",
            _last_activity = "2026-04-07T00:00:00Z"
        )

        # Mock event mesh send
        a2a_server.event_mesh.send_to_json = AsyncMock()

        await a2a_server._handle_discovery("requesting-agent", {})

        a2a_server.event_mesh.send_to_json.assert_called_once()
        call_args = a2a_server.event_mesh.send_to_json.call_args[0][1]
        assert call_args["type"] == "discovery"
        assert len(call_args["agents"]) == 1

    @pytest.mark.asyncio
    async def test_message_broadcast(self, _a2a_server):
        """Test message broadcast to all agents."""
        a2a_server.event_mesh.broadcast_json = AsyncMock()

        await a2a_server._handle_message_broadcast(
            "sender-agent",
            {"content": "Hello swarm!"}
        )

        a2a_server.event_mesh.broadcast_json.assert_called_once()
        _call_args = a2a_server.event_mesh.broadcast_json.call_args[0][0]
        assert call_args["type"] == "message"
        assert call_args["from"] == "sender-agent"

    @pytest.mark.asyncio
    async def test_proposal_creation(self, _a2a_server):
        """Test consensus proposal."""
        a2a_server.event_mesh.broadcast_json = AsyncMock()

        await a2a_server._handle_proposal(
            "proposer-agent",
            {"action": "deploy", "details": {"target": "production"}}
        )

        a2a_server.event_mesh.broadcast_json.assert_called_once()
        _call_args = a2a_server.event_mesh.broadcast_json.call_args[0][0]
        assert call_args["type"] == "proposal"
        assert call_args["from"] == "proposer-agent"

    @pytest.mark.asyncio
    async def test_vote_casting(self, _a2a_server):
        """Test consensus voting."""
        a2a_server.event_mesh.broadcast_json = AsyncMock()

        await a2a_server._handle_vote(
            "voter-agent",
            {"proposal_id": "prop-123", "vote": "yes", "reason": "Looks good"}
        )

        a2a_server.event_mesh.broadcast_json.assert_called_once()
        _call_args = a2a_server.event_mesh.broadcast_json.call_args[0][0]
        assert call_args["type"] == "vote"
        assert call_args["vote"] == "yes"

    def test_get_statistics(self, _a2a_server):
        """Test server statistics."""
        _stats = a2a_server.get_statistics()

        assert "connected_agents" in stats
        assert "agent_ids" in stats
        assert "message_log_size" in stats
        assert stats["uptime"] == "active"


# =============================================================================
# Authentication Tests
# =============================================================================

class TestAuthentication:
    """Test authentication layer."""

    def test_generate_api_key(self):
        """Test API key generation."""
        from heretek_swarm.gateway.auth import generate_api_key

        _key1 = generate_api_key()
        _key2 = generate_api_key()

        assert key1.startswith("htsk_")
        assert key2.startswith("htsk_")
        assert key1 != key2  # Keys should be unique

    def test_get_api_key_from_env(self):
        """Test environment variable retrieval."""
        import os

        from heretek_swarm.gateway.auth import get_api_key_from_env

        # Set test key
        os.environ["HERETEK_API_KEY"] = "htsk_test_key"

        _key = get_api_key_from_env()
        assert key == "htsk_test_key"

        # Cleanup
        del os.environ["HERETEK_API_KEY"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
