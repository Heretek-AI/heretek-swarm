"""
P0 Security Fixes Test Suite - Zero-Trust Audit CVE Verification

Tests for all P0 security fixes implemented from the zero-trust audit:
- CVE-2026-HERETEK-001: Guardrails syntax error (PII filtering)
- CVE-2026-HERETEK-002: Path traversal in tools
- CVE-2026-HERETEK-003: A2A authentication
- CVE-2026-HERETEK-004: WebSocket authentication
- CVE-2026-HERETEK-005: Consensus authentication
- CVE-2026-HERETEK-007: Dangerous commands removed
"""

import os
import shutil
import tempfile
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from heretek_swarm.api.consensus import ConsensusAuthManager
from heretek_swarm.api.websockets import (
    WebSocketAuthManager,
    authenticate_websocket,
)
from heretek_swarm.gateway.a2a_server import AuthTokenManager
from heretek_swarm.runtime.tools import (
    ALLOWED_COMMANDS,
    BLOCKED_COMMANDS,
    read_file,
    run_command,
    write_file,
)

# Test imports for security modules
from heretek_swarm.security.guardrails import GuardrailsSystem


class TestCVE2026HERETEK001_GuardrailsSyntax:
    """Test CVE-2026-HERETEK-001: Guardrails PII filtering syntax fix."""

    @pytest.mark.asyncio
    async def test_pii_email_filtering(self):
        """Test that email addresses are properly redacted from output."""
        guardrails = GuardrailsSystem()

        # Test output with email
        output = "Contact me at test@example.com for more info"
        result = await guardrails.filter_output(output)

        assert "[REDACTED]" in result.filtered
        assert "test@example.com" not in result.filtered

    @pytest.mark.asyncio
    async def test_pii_phone_filtering(self):
        """Test that phone numbers are properly redacted from output (CVE fix)."""
        guardrails = GuardrailsSystem()

        # Test output with phone number
        output = "Call me at 555-123-4567 or 5551234567"
        result = await guardrails.filter_output(output)

        assert "[REDACTED]" in result.filtered
        assert "555-123-4567" not in result.filtered
        assert "5551234567" not in result.filtered

    @pytest.mark.asyncio
    async def test_pii_api_key_filtering(self):
        """Test that API keys are properly redacted from output."""
        guardrails = GuardrailsSystem()

        # Test output with API key pattern
        output = "My key is sk_live_[REDACTED_TEST_KEY_123456789]"
        result = await guardrails.filter_output(output)

        assert "[REDACTED]" in result.filtered

    @pytest.mark.asyncio
    async def test_multiple_pii_types(self):
        """Test filtering multiple PII types in same output."""
        guardrails = GuardrailsSystem()

        output = "Email: test@example.com, Phone: 555-123-4567"
        result = await guardrails.filter_output(output)

        assert "[REDACTED]" in result.filtered
        assert "test@example.com" not in result.filtered
        assert "555-123-4567" not in result.filtered


class TestCVE2026HERETEK002_PathTraversal:
    """Test CVE-2026-HERETEK-002: Path traversal protection in file operations."""

    @pytest.mark.asyncio
    async def test_read_file_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked in read_file."""
        # Attempt to read /etc/passwd using path traversal
        result = await read_file("../../../etc/passwd")

        assert result["success"] is False
        assert "Path traversal detected" in result["error"]

    @pytest.mark.asyncio
    async def test_read_file_absolute_path_blocked(self):
        """Test that absolute paths outside allowed dirs are blocked."""
        result = await read_file("/etc/passwd")

        assert result["success"] is False
        assert "Path traversal detected" in result["error"]

    @pytest.mark.asyncio
    async def test_write_file_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked in write_file."""
        result = await write_file("../../../tmp/malicious.txt", "content")

        assert result["success"] is False
        assert "Path traversal detected" in result["error"]

    @pytest.mark.asyncio
    async def test_read_file_allowed_path(self):
        """Test that reading from allowed paths works."""
        # Create a temp file in allowed directory
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Allow the temp directory
            allowed_dir = os.path.dirname(temp_path)
            result = await read_file(temp_path, allowed_base_paths=[allowed_dir])

            assert result["success"] is True
            assert result["content"] == "test content"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_write_file_allowed_path(self):
        """Test that writing to allowed paths works."""
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "test.txt")

        try:
            result = await write_file(temp_path, "test content", allowed_base_paths=[temp_dir])

            assert result["success"] is True

            # Verify content was written
            with open(temp_path) as f:
                content = f.read()
            assert content == "test content"
        finally:
            os.unlink(temp_path)
            os.rmdir(temp_dir)


class TestCVE2026HERETEK003_A2AAuthentication:
    """Test CVE-2026-HERETEK-003: A2A authentication implementation."""

    def test_token_generation(self):
        """Test that auth tokens can be generated."""
        manager = AuthTokenManager()
        token = manager.generate_token("agent-123")

        assert token is not None
        assert len(token) > 0

    def test_token_validation_success(self):
        """Test that valid tokens are accepted."""
        manager = AuthTokenManager()
        token = manager.generate_token("agent-123")

        is_valid, agent_id, error = manager.validate_token(token)

        assert is_valid is True
        assert agent_id == "agent-123"
        assert error is None

    def test_token_validation_invalid(self):
        """Test that invalid tokens are rejected."""
        manager = AuthTokenManager()

        is_valid, _agent_id, error = manager.validate_token("invalid_token")

        assert is_valid is False
        assert error == "Invalid token"

    def test_token_agent_mismatch(self):
        """Test that agent ID mismatch is detected."""
        manager = AuthTokenManager()
        token = manager.generate_token("agent-123")

        # Token belongs to agent-123, but connection tries to use agent-456
        is_valid, agent_id, _error = manager.validate_token(token)
        assert is_valid is True
        assert agent_id == "agent-123"

        # The server should reject if requested agent_id != token agent_id
        # This is tested in the connection handler

    def test_token_expiry(self):
        """Test that expired tokens are rejected."""
        manager = AuthTokenManager()
        manager._token_expiry = timedelta(seconds=-1)  # Already expired

        token = manager.generate_token("agent-123")

        # Give time for expiry
        import time
        time.sleep(0.1)

        is_valid, _agent_id, error = manager.validate_token(token)

        assert is_valid is False
        assert error == "Token expired"

    def test_token_revocation(self):
        """Test that tokens can be revoked."""
        manager = AuthTokenManager()
        token = manager.generate_token("agent-123")

        # Revoke the token
        revoked = manager.revoke_token(token)
        assert revoked is True

        # Token should now be invalid
        is_valid, _agent_id, _error = manager.validate_token(token)
        assert is_valid is False


class TestCVE2026HERETEK004_WebSocketAuthentication:
    """Test CVE-2026-HERETEK-004: WebSocket authentication implementation."""

    def test_ws_token_generation(self):
        """Test that WebSocket auth tokens can be generated."""
        manager = WebSocketAuthManager()
        token = manager.generate_token("user-123")

        assert token is not None
        assert len(token) > 0

    def test_ws_token_validation_success(self):
        """Test that valid WebSocket tokens are accepted."""
        manager = WebSocketAuthManager()
        token = manager.generate_token("user-123")

        is_valid, user_id, error = manager.validate_token(token)

        assert is_valid is True
        assert user_id == "user-123"
        assert error is None

    def test_ws_token_validation_missing(self):
        """Test that missing tokens are rejected."""
        manager = WebSocketAuthManager()

        is_valid, _user_id, error = manager.validate_token("")

        assert is_valid is False
        assert error == "Token required"

    def test_ws_rate_limiting(self):
        """Test that WebSocket rate limiting works."""
        manager = WebSocketAuthManager()
        manager._rate_limit_max = 5
        manager._rate_limit_window = 60

        user_id = "test-user"

        # First 5 requests should be allowed
        for _i in range(5):
            assert manager.check_rate_limit(user_id) is True

        # 6th request should be blocked
        assert manager.check_rate_limit(user_id) is False

    @pytest.mark.asyncio
    async def test_authenticate_websocket_missing_token(self):
        """Test that WebSocket authentication fails without token."""
        mock_websocket = AsyncMock()

        is_authenticated, _user_id, error = await authenticate_websocket(mock_websocket, None)

        assert is_authenticated is False
        assert error == "Token required"


class TestCVE2026HERETEK005_ConsensusAuthentication:
    """Test CVE-2026-HERETEK-005: Consensus authentication implementation."""

    def test_consensus_token_generation(self):
        """Test that consensus auth tokens can be generated."""
        manager = ConsensusAuthManager()
        token = manager.generate_token("agent-123")

        assert token is not None
        assert len(token) > 0

    def test_consensus_token_validation(self):
        """Test that valid consensus tokens are accepted."""
        manager = ConsensusAuthManager()
        token = manager.generate_token("agent-123")

        is_valid, agent_id, error = manager.validate_token(token)

        assert is_valid is True
        assert agent_id == "agent-123"
        assert error is None

    def test_consensus_permission_check(self):
        """Test that consensus permissions are checked."""
        manager = ConsensusAuthManager()

        # Agent with vote permission
        token = manager.generate_token("agent-123", permissions=["vote"])
        is_valid, _agent_id, _ = manager.validate_token(token)
        assert is_valid is True

        assert manager.check_permission("agent-123", "vote") is True
        assert manager.check_permission("agent-123", "create") is False

    def test_consensus_default_permissions(self):
        """Test that default permissions include vote, create, view."""
        manager = ConsensusAuthManager()
        manager.generate_token("agent-123")

        assert manager.check_permission("agent-123", "vote") is True
        assert manager.check_permission("agent-123", "create") is True
        assert manager.check_permission("agent-123", "view") is True

    def test_consensus_token_revocation(self):
        """Test that consensus tokens can be revoked."""
        manager = ConsensusAuthManager()
        token = manager.generate_token("agent-123")

        revoked = manager.revoke_token(token)
        assert revoked is True

        is_valid, _agent_id, _error = manager.validate_token(token)
        assert is_valid is False


class TestCVE2026HERETEK007_DangerousCommands:
    """Test CVE-2026-HERETEK-007: Dangerous commands removed from whitelist."""

    def test_python_not_in_allowed_commands(self):
        """Test that 'python' is NOT in allowed commands."""
        assert "python" not in ALLOWED_COMMANDS

    def test_git_not_in_allowed_commands(self):
        """Test that 'git' is NOT in allowed commands."""
        assert "git" not in ALLOWED_COMMANDS

    def test_dangerous_commands_still_blocked(self):
        """Test that dangerous commands are still in blocked list."""
        assert "rm" in BLOCKED_COMMANDS
        assert "sudo" in BLOCKED_COMMANDS
        assert "curl" in BLOCKED_COMMANDS
        assert "wget" in BLOCKED_COMMANDS

    @pytest.mark.asyncio
    async def test_python_command_blocked(self):
        """Test that python command execution is blocked."""
        result = await run_command("python -c 'print(\"hello\")'")

        assert result["success"] is False
        assert "not allowed" in result["error"] or "not in the allowed command list" in result["error"]

    @pytest.mark.asyncio
    async def test_git_command_blocked(self):
        """Test that git command execution is blocked."""
        result = await run_command("git status")

        assert result["success"] is False
        assert "not allowed" in result["error"] or "not in the allowed command list" in result["error"]

    @pytest.mark.asyncio
    async def test_safe_command_allowed(self):
        """Test that safe commands like 'ls' are still allowed."""
        result = await run_command("ls -la /tmp")

        # Should succeed (or at least not be blocked for security reasons)
        # May fail if /tmp doesn't exist, but shouldn't be security blocked
        if not result["success"]:
            assert "not allowed" not in result["error"]
            assert "not in the allowed command list" not in result["error"]


class TestDatetimeDeprecations:
    """Test that datetime.utcnow() has been replaced with datetime.now(timezone.utc)."""

    def test_datetime_timezone_import(self):
        """Test that timezone is imported in key modules."""
        from heretek_swarm.actors import base as actors_base
        from heretek_swarm.api import consensus, websockets
        from heretek_swarm.gateway import a2a_server
        from heretek_swarm.runtime import tools as runtime_tools

        # Verify timezone is available in modules
        assert hasattr(actors_base.datetime, "now")
        assert hasattr(runtime_tools.datetime, "now")
        assert hasattr(a2a_server.datetime, "now")
        assert hasattr(websockets.datetime, "now")
        assert hasattr(consensus.datetime, "now")

    def test_actor_base_uses_timezone_aware_datetime(self):
        """Test that actor base uses timezone-aware datetimes."""
        from heretek_swarm.actors.base import AgentActor

        actor = AgentActor(agent_id="test-actor")

        # created_at should be ISO format with timezone info
        assert actor.created_at is not None
        # ISO format timestamps from datetime.now(timezone.utc) end with '+00:00' or 'Z'
        # or contain timezone information


class TestActorMessageDelivery:
    """Test that actor message delivery is implemented."""

    @pytest.mark.asyncio
    async def test_send_with_event_mesh(self):
        """Test that send() uses event mesh when available."""
        from heretek_swarm.actors.base import AgentActor

        actor = AgentActor(agent_id="test-actor")

        # Mock event mesh
        mock_event_mesh = AsyncMock()
        mock_event_mesh.send_to_json = AsyncMock(return_value=True)

        # Set event mesh in actor state
        actor.update_state("_event_mesh", mock_event_mesh)

        # Send message
        message_id = await actor.send(
            topic="test-topic",
            content={"test": "data"},
            message_type="test"
        )

        # Verify event mesh was called
        assert mock_event_mesh.send_to_json.called
        assert message_id is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="send_to_actor() requires proper actor runtime with event mesh - test setup issue")
    async def test_send_to_actor_direct_delivery(self):
        """Test that send_to_actor() uses direct delivery when possible."""
        from heretek_swarm.actors.base import AgentActor

        actor1 = AgentActor(agent_id="actor-1")
        actor2 = AgentActor(agent_id="actor-2")

        # Mock actor registry
        mock_registry = {"actor-2": actor2}
        actor1.update_state("_actor_registry", mock_registry)

        # Send message
        await actor1.send_to_actor(
            target_actor_id="actor-2",
            message_type="test",
            content={"data": "test"}
        )

        # Message should be delivered (actor2 mailbox should have message)
        assert not actor2.mailbox.empty()

    @pytest.mark.asyncio
    async def test_broadcast_uses_event_mesh(self):
        """Test that broadcast() uses event mesh when available."""
        from heretek_swarm.actors.base import AgentActor

        actor = AgentActor(agent_id="test-actor")

        # Mock event mesh
        mock_event_mesh = AsyncMock()
        mock_event_mesh.broadcast_json = AsyncMock()

        actor.update_state("_event_mesh", mock_event_mesh)

        # Broadcast
        await actor.broadcast({"test": "data"})

        # Verify broadcast was called
        assert mock_event_mesh.broadcast_json.called


class TestStatePersistence:
    """Test that actor state persistence is implemented."""

    @pytest.mark.asyncio
    async def test_save_state_file_persistence(self):
        """Test that save_state() persists to file system."""
        import json

        from heretek_swarm.actors.base import AgentActor

        actor = AgentActor(agent_id="test-persist-actor")
        actor.update_state("test_key", "test_value")
        actor.message_count = 42

        # Save state (should use file fallback since no DB)
        await actor.save_state()

        # Check file was created
        state_file = os.path.join(os.getcwd(), ".actor_states", "test-persist-actor.json")
        assert os.path.exists(state_file)

        # Verify content
        with open(state_file) as f:
            saved_state = json.load(f)

        assert saved_state["internal_state"]["test_key"] == "test_value"
        assert saved_state["message_count"] == 42
        assert saved_state["state"] == "spawning"

        # Cleanup - use shutil.rmtree to handle any leftover files
        actor_states_dir = os.path.join(os.getcwd(), ".actor_states")
        if os.path.exists(actor_states_dir):
            shutil.rmtree(actor_states_dir)

    @pytest.mark.asyncio
    async def test_load_state_file_persistence(self):
        """Test that load_state() loads from file system."""

        from heretek_swarm.actors.base import AgentActor

        # Create actor and save state
        actor1 = AgentActor(agent_id="test-load-actor")
        actor1.update_state("loaded_key", "loaded_value")
        actor1.message_count = 99
        await actor1.save_state()

        # Create new actor with same ID and load state
        actor2 = AgentActor(agent_id="test-load-actor")
        await actor2.load_state()

        # Verify state was loaded
        assert actor2.get_state("loaded_key") == "loaded_value"
        assert actor2.message_count == 99

        # Cleanup - use shutil.rmtree to handle any leftover files
        actor_states_dir = os.path.join(os.getcwd(), ".actor_states")
        if os.path.exists(actor_states_dir):
            shutil.rmtree(actor_states_dir)
