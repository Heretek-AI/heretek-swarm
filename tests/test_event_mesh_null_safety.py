"""
EventMesh Null Safety Verification Test

This test verifies that the EventMesh implementation properly handles:
- Null/disconnected clients
- Failed send operations
- Automatic cleanup of failed connections

Reference: src/heretek_swarm/gateway/event_mesh.py
"""

import asyncio
import pytest
from unittest.mock import Mock

from heretek_swarm.gateway.event_mesh import EventMesh


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self, _should_fail, _disconnecting):
        self.should_fail = should_fail
        self.client_state = type('obj', (object,), {
            'disconnecting': disconnecting
        })()
        self.sent_messages = []
        self.closed = False
    
    async def send_bytes(self, _data: bytes):
        """Mock send_bytes that can fail"""
        if self.should_fail:
            raise Exception("Connection lost")
        if self.closed:
            raise Exception("Connection closed")
        self.sent_messages.append(data)
    
    async def close(self):
        """Mock close"""
        self.closed = True


@pytest.mark.asyncio
async def test_event_mesh_null_safety_with_disconnected_clients():
    """Test that EventMesh cleans up disconnected clients before broadcast"""
    _mesh = EventMesh()
    
    # Register clients
    _good_client = MockWebSocket(should_fail=False, disconnecting=False)
    _bad_client = MockWebSocket(should_fail=False, disconnecting=True)
    
    await mesh.register("good", good_client)
    await mesh.register("bad", bad_client)
    
    # Broadcast should only send to non-disconnecting clients
    _result = await mesh.broadcast(b"test message")
    
    # Should only send to good client
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert len(good_client.sent_messages) == 1
    assert len(bad_client.sent_messages) == 0
    
    # Bad client should be cleaned up
    assert "good" in mesh.clients
    assert "bad" not in mesh.clients  # Disconnected client cleaned up


@pytest.mark.asyncio
async def test_event_mesh_null_safety_with_failed_sends():
    """Test that EventMesh handles failed send operations"""
    _mesh = EventMesh()
    
    # Register clients
    _good_client = MockWebSocket(should_fail=False, disconnecting=False)
    _bad_client = MockWebSocket(should_fail=True, disconnecting=False)
    
    await mesh.register("good", good_client)
    await mesh.register("bad", bad_client)
    
    # Broadcast should handle failures
    _result = await mesh.broadcast(b"test message")
    
    # Should send to good client and fail for bad client
    assert result["sent"] == 1
    assert result["failed"] == 1
    assert len(good_client.sent_messages) == 1
    assert len(bad_client.sent_messages) == 0
    
    # Bad client should be cleaned up
    assert "good" in mesh.clients
    assert "bad" not in mesh.clients


@pytest.mark.asyncio
async def test_event_mesh_null_safety_with_null_clients():
    """Test that EventMesh handles null clients in the registry"""
    _mesh = EventMesh()
    
    # Manually add a null client to test robustness
    mesh.clients["null_client"] = None
    mesh.clients["good_client"] = MockWebSocket(should_fail=False, disconnecting=False)
    
    # Broadcast should filter out null clients
    _result = await mesh.broadcast(b"test message")
    
    # Should only send to good client
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert "good_client" in mesh.clients
    assert "null_client" not in mesh.clients  # Null client should be filtered out


@pytest.mark.asyncio
async def test_event_mesh_empty_broadcast():
    """Test that EventMesh handles broadcast with no clients"""
    _mesh = EventMesh()
    
    # Broadcast with no clients
    _result = await mesh.broadcast(b"test message")
    
    # Should return zeros
    assert result["sent"] == 0
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_event_mesh_client_count():
    """Test that client_count property works correctly"""
    _mesh = EventMesh()
    
    # Initially no clients
    assert mesh.client_count == 0
    
    # Register clients
    await mesh.register("client1", MockWebSocket())
    await mesh.register("client2", MockWebSocket())
    
    assert mesh.client_count == 2
    
    # Unregister one client
    await mesh.unregister("client1")
    
    assert mesh.client_count == 1


@pytest.mark.asyncio
async def test_event_mesh_register_unregister():
    """Test client registration and unregistration"""
    _mesh = EventMesh()
    client = MockWebSocket()
    
    # Register client
    await mesh.register("test_client", client)
    assert "test_client" in mesh.clients
    assert mesh.client_count == 1
    
    # Unregister client
    await mesh.unregister("test_client")
    assert "test_client" not in mesh.clients
    assert mesh.client_count == 0
    
    # Unregister non-existent client should not raise
    await mesh.unregister("non_existent")
    assert mesh.client_count == 0


@pytest.mark.asyncio
async def test_event_mesh_concurrent_broadcasts():
    """Test that EventMesh handles concurrent broadcasts safely"""
    _mesh = EventMesh()
    
    # Register multiple clients
    for i in range(5):
        await mesh.register(f"client{i}", MockWebSocket())
    
    # Send concurrent broadcasts
    _tasks = [mesh.broadcast(f"message{i}".encode()) for i in range(10)]
    _results = await asyncio.gather(*tasks)
    
    # All broadcasts should succeed
    for result in results:
        assert result["sent"] == 5
        assert result["failed"] == 0


@pytest.mark.asyncio
async def test_event_mesh_failed_client_cleanup():
    """Test that failed clients are properly cleaned up"""
    _mesh = EventMesh()
    
    # Register clients that will fail
    _failing_clients = [f"bad{i}" for i in range(5)]
    for client_id in failing_clients:
        await mesh.register(client_id, MockWebSocket(should_fail=True))
    
    # Register one good client
    await mesh.register("good", MockWebSocket(should_fail=False))
    
    # Broadcast should clean up all failing clients
    _result = await mesh.broadcast(b"test message")
    
    assert result["sent"] == 1
    assert result["failed"] == 5
    assert "good" in mesh.clients
    
    # All failing clients should be cleaned up
    for client_id in failing_clients:
        assert client_id not in mesh.clients


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
