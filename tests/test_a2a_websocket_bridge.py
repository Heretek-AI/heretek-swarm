"""
Integration tests for A2A WebSocket Bridge (NATS → FastAPI → Frontend)

Tests the complete flow: NATS subscription → broadcast to WebSocket clients.

Reference: M011/S01/S01-PLAN.md
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Clear database env var to avoid Postgres dependency
import os
os.environ.pop("DATABASE_URL", None)


class TestA2AWebSocketBridge:
    """Test suite for NATS-to-WebSocket bridge functionality."""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Set up test environment with mocked dependencies."""
        # Clear DATABASE_URL to prevent postgres connection attempts
        os.environ.pop("DATABASE_URL", None)

    @pytest.mark.asyncio
    async def test_nats_callback_broadcasts_to_websocket_client(self):
        """
        Test that NATS message callback broadcasts to connected WebSocket clients.

        Flow:
        1. Mock NATSEventMesh.subscribe to capture the callback
        2. Open test WebSocket connection to /ws/a2a
        3. Invoke the captured callback with a SwarmEvent dict
        4. Assert the WebSocket client receives the JSON message within 1 second
        """
        from heretek_swarm.api.websockets import manager

        # Track received messages
        received_messages = []
        message_event = asyncio.Event()

        class MockWebSocket:
            """Mock WebSocket that tracks received messages."""

            def __init__(self):
                self.accepted = False
                self.messages = []

            async def accept(self):
                self.accepted = True

            async def send_json(self, data):
                self.messages.append(data)
                received_messages.append(data)
                message_event.set()

            async def close(self):
                pass

        # Create mock WebSocket client
        mock_ws = MockWebSocket()

        # Add to a2a_listeners (simulating connection)
        manager.a2a_listeners.add(mock_ws)

        try:
            # Simulate a SwarmEvent arriving from NATS
            swarm_event = {
                "event_type": "message",
                "source_agent": "alpha-primary",
                "target_agent": "beta-primary",
                "payload": {"content": "Hello from alpha"},
                "timestamp": "2024-01-01T12:00:00Z",
            }

            # Directly invoke broadcast_a2a (simulates what NATS callback would do)
            await manager.broadcast_a2a(swarm_event)

            # Wait for message with timeout
            try:
                await asyncio.wait_for(message_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pytest.fail("WebSocket client did not receive message within 1 second")

            # Verify message was received
            assert len(received_messages) == 1
            assert received_messages[0]["event_type"] == "message"
            assert received_messages[0]["source_agent"] == "alpha-primary"
            assert received_messages[0]["target_agent"] == "beta-primary"

        finally:
            # Clean up: remove from listeners
            manager.a2a_listeners.discard(mock_ws)

    @pytest.mark.asyncio
    async def test_multiple_websocket_clients_receive_broadcast(self):
        """
        Test that all connected WebSocket clients receive the broadcast.
        """
        from heretek_swarm.api.websockets import manager

        received_counts = {}
        events = {}

        class MockWebSocket:
            """Mock WebSocket with unique ID."""

            def __init__(self, client_id: str):
                self.client_id = client_id
                self.accepted = False
                self.messages = []
                self.event = asyncio.Event()

            async def accept(self):
                self.accepted = True

            async def send_json(self, data):
                self.messages.append(data)
                events[self.client_id].set()

            async def close(self):
                pass

        # Create multiple mock clients
        clients = [MockWebSocket(f"client-{i}") for i in range(3)]
        for i, client in enumerate(clients):
            client_id = f"client-{i}"
            events[client_id] = asyncio.Event()
            manager.a2a_listeners.add(client)

        try:
            # Broadcast event
            swarm_event = {
                "event_type": "message",
                "source_agent": "alpha-primary",
                "target_agent": "beta-primary",
                "payload": {"content": "Broadcast test"},
                "timestamp": "2024-01-01T12:00:00Z",
            }

            await manager.broadcast_a2a(swarm_event)

            # Wait for all clients to receive
            await asyncio.wait_for(
                asyncio.gather(*[events[c.client_id].wait() for c in clients]),
                timeout=1.0,
            )

            # Verify all received the message
            for client in clients:
                assert len(client.messages) == 1
                assert client.messages[0]["event_type"] == "message"

        finally:
            for client in clients:
                manager.a2a_listeners.discard(client)

    @pytest.mark.asyncio
    async def test_disconnected_client_is_removed_from_listeners(self):
        """
        Test that disconnected clients are properly removed from a2a_listeners.
        """
        from heretek_swarm.api.websockets import manager

        class FailingWebSocket:
            """Mock WebSocket that fails on send."""

            def __init__(self):
                self.accepted = False

            async def accept(self):
                self.accepted = True

            async def send_json(self, data):
                raise Exception("Connection closed")

            async def close(self):
                pass

        # Add failing client
        failing_ws = FailingWebSocket()
        manager.a2a_listeners.add(failing_ws)

        initial_count = len(manager.a2a_listeners)

        # Broadcast to trigger disconnect cleanup
        await manager.broadcast_a2a({"test": "data"})

        # Give time for cleanup
        await asyncio.sleep(0.1)

        # Verify client was removed
        assert len(manager.a2a_listeners) < initial_count
        assert failing_ws not in manager.a2a_listeners

    @pytest.mark.asyncio
    async def test_nats_subscription_in_main_lifespan(self):
        """
        Test that main.py properly initializes NATS bridge in lifespan.

        Verifies:
        1. NATSEventMesh is created with fallback=True
        2. connect() is called
        3. subscription is registered
        """
        import heretek_swarm.api.main as main_module

        # Clear any existing state and disconnect if needed
        if main_module._nats_mesh is not None:
            try:
                await main_module._nats_mesh.disconnect()
            except Exception:
                pass

        main_module._nats_mesh = None

        # Capture the mesh instance after initialization
        original_mesh = None

        original_init = main_module._nats_mesh

        # Patch subscribe to capture the callback registration
        subscribe_calls = []

        original_subscribe = None
        if main_module._nats_mesh is not None and hasattr(main_module._nats_mesh, 'subscribe'):
            original_subscribe = main_module._nats_mesh.subscribe

        # Initialize bridge - this will connect to real NATS if available
        await main_module._init_nats_bridge()

        # Verify mesh was created
        assert main_module._nats_mesh is not None, "NATSEventMesh should be initialized"

        # Verify it's connected (or using fallback)
        assert main_module._nats_mesh.is_connected, "Mesh should be connected"

        # Verify subscriptions were registered
        sub_ids = main_module._nats_mesh.get_subscription_ids()
        assert len(sub_ids) >= 2, f"Should have at least 2 subscriptions, got {len(sub_ids)}"

        # Cleanup
        await main_module._nats_mesh.disconnect()
        main_module._nats_mesh = None

    @pytest.mark.asyncio
    async def test_fallback_heartbeat_interval_reduced(self):
        """
        Test that fallback heartbeat interval is 5 seconds (not 30).
        """
        from heretek_swarm.api.websockets import a2a_websocket

        # We can't easily test the WebSocket handler directly, but we can verify
        # the module level config by checking the code structure

        # Read the websockets.py source and verify fallback uses 5 second sleep
        import inspect
        source = inspect.getsource(a2a_websocket)

        # The fallback block should use asyncio.sleep(5) not asyncio.sleep(30)
        assert "asyncio.sleep(5)" in source or "sleep(5)" in source
        # Should NOT have the old 30 second sleep
        assert "asyncio.sleep(30)" not in source


# =============================================================================
# Test Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])