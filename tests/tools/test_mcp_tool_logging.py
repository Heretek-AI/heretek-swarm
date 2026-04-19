"""
Tests for MCP Tool Logging

Validates that MCPToolRegistry.invoke() creates ExternalCallLog entries
for all tool invocations with proper encryption and error handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.tools.mcp_tools import (
    MCPToolDefinition,
    MCPToolRegistry,
    _create_log_entry_sync,
)


class TestMCPToolLogging:
    """Test ExternalCallLog creation in MCP tool invocations."""

    @pytest.fixture
    def registry(self):
        """Create a fresh MCPToolRegistry instance."""
        return MCPToolRegistry()

    @pytest.fixture
    def mock_encryptor(self):
        """Mock the encryption module to avoid key requirements."""
        mock_result = {"encrypted": "fake_encrypted_data"}
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.encrypt.return_value = mock_result
            mock_encryptor.is_available = True
            mock_get_encryptor.return_value = mock_encryptor
            yield mock_get_encryptor

    async def test_invoke_calls_external_call_log_creation(
        self, registry, mock_encryptor
    ):
        """Test that invoke() creates an ExternalCallLog entry after tool execution."""
        tool_name = "test_tool"

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            result = await registry.invoke(
                tool_name,
                {"input": "test"},
                context={"agent_id": "test-agent"}
            )

            # Verify the tool executed successfully
            assert result["success"] is True

            # Verify _create_log_entry_sync was called
            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["tool_name"] == tool_name
            assert call_kwargs["error"] is None

    async def test_agent_id_from_context_captured_in_log_entry(
        self, registry, mock_encryptor
    ):
        """Test that agent_id from context dict is captured in the log entry."""
        tool_name = "test_tool"
        expected_agent_id = "agent-123"
        expected_agent_type = "mcp_agent"

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            await registry.invoke(
                tool_name,
                {},
                context={"agent_id": expected_agent_id, "agent_type": expected_agent_type}
            )

            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["agent_id"] == expected_agent_id
            assert call_kwargs["agent_type"] == expected_agent_type

    async def test_tool_name_correctly_recorded(self, registry, mock_encryptor):
        """Test that tool_name is correctly recorded in the log entry."""
        tool_name = "specific_tool_name"

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            await registry.invoke(tool_name, {})

            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["tool_name"] == tool_name

    async def test_arguments_encrypted_in_log_entry(self, registry, mock_encryptor):
        """Test that arguments are encrypted in the log entry."""
        tool_name = "test_tool"
        test_arguments = {"key1": "value1", "key2": 123, "nested": {"a": "b"}}

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            await registry.invoke(tool_name, test_arguments)

            call_kwargs = mock_create_log.call_args.kwargs
            # Arguments should be passed to the log entry creator
            assert call_kwargs["arguments"] == test_arguments

    async def test_result_encrypted_in_log_entry(self, registry, mock_encryptor):
        """Test that result is encrypted in the log entry."""
        tool_name = "test_tool"
        expected_result = {"status": "ok", "data": {"id": 1, "name": "test"}}

        async def handler(args, ctx):
            return expected_result

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            await registry.invoke(tool_name, {})

            call_kwargs = mock_create_log.call_args.kwargs
            # Result should be passed to the log entry creator
            assert call_kwargs["result"] == expected_result

    async def test_tool_not_found_creates_log_entry_with_error(
        self, registry, mock_encryptor
    ):
        """Test that tool not found error creates ExternalCallLog with error_message."""
        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            result = await registry.invoke("nonexistent_tool", {})

            # Verify the tool execution failed
            assert result["success"] is False
            assert "not found" in result["error"]

            # Verify log entry was created with error
            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["error"] is not None
            assert "not found" in call_kwargs["error"]
            assert call_kwargs["tool_name"] == "nonexistent_tool"

    async def test_schema_validation_failed_creates_log_entry_with_error(
        self, registry, mock_encryptor
    ):
        """Test that schema validation failure creates ExternalCallLog with error_message."""
        tool_name = "strict_tool"
        schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"}
            },
            "required": ["required_field"]
        }

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Strict tool",
            input_schema=schema,
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            # Call without the required field
            result = await registry.invoke(tool_name, {})

            # Verify the tool execution failed due to validation
            assert result["success"] is False
            assert "Invalid arguments" in result["error"]

            # Verify log entry was created with error
            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["error"] is not None
            assert "Invalid arguments" in call_kwargs["error"]

    async def test_logging_failure_does_not_prevent_tool_execution(
        self, registry, mock_encryptor
    ):
        """Test that logging failures do not prevent tool execution."""
        tool_name = "test_tool"

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        # Make _create_log_entry_sync raise an exception
        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync",
            side_effect=Exception("DB write failed")
        ):
            result = await registry.invoke(tool_name, {})

            # Tool execution should still succeed
            assert result["success"] is True
            assert result["result"] == {"result": "success"}

    async def test_logging_failure_does_not_prevent_error_handling(
        self, registry, mock_encryptor
    ):
        """Test that logging failures don't prevent error case handling."""
        tool_name = "test_tool"

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name=tool_name,
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        # Make _create_log_entry_sync raise an exception on error path too
        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync",
            side_effect=Exception("DB write failed")
        ):
            result = await registry.invoke("nonexistent_tool", {})

            # Error should still be returned
            assert result["success"] is False
            assert "not found" in result["error"]


class TestCreateLogEntrySync:
    """Test the _create_log_entry_sync helper function."""

    def test_creates_external_call_log_with_correct_fields(self):
        """Test that _create_log_entry_sync creates ExternalCallLog with correct fields."""
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.encrypt.return_value = {"encrypted": "test_data"}
            mock_get_encryptor.return_value = mock_encryptor

            log_entry = _create_log_entry_sync(
                agent_id="test-agent",
                agent_type="mcp_agent",
                tool_name="test_tool",
                arguments={"input": "value"},
                result={"status": "ok"},
                error=None,
                duration_ms=100.5,
            )

            assert log_entry.agent_id == "test-agent"
            assert log_entry.agent_type == "mcp_agent"
            assert log_entry.call_type == "mcp"
            assert log_entry.url == "mcp://tool/test_tool"
            assert log_entry.method == "INVOKE"
            assert log_entry.tool_name == "test_tool"
            assert log_entry.error_message is None
            assert log_entry.duration_ms == 100.5

    def test_creates_external_call_log_with_error(self):
        """Test that _create_log_entry_sync creates ExternalCallLog with error_message."""
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.encrypt.return_value = {"encrypted": "test_data"}
            mock_get_encryptor.return_value = mock_encryptor

            log_entry = _create_log_entry_sync(
                agent_id="test-agent",
                agent_type="mcp_agent",
                tool_name="test_tool",
                arguments={"input": "value"},
                result={},
                error="Tool execution failed",
                duration_ms=50.0,
            )

            assert log_entry.agent_id == "test-agent"
            assert log_entry.error_message == "Tool execution failed"

    def test_encrypts_arguments_and_result(self):
        """Test that arguments and result are encrypted via encryptor."""
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.encrypt.side_effect = [
                {"encrypted": "encrypted_args"},
                {"encrypted": "encrypted_result"},
            ]
            mock_get_encryptor.return_value = mock_encryptor

            log_entry = _create_log_entry_sync(
                agent_id="test-agent",
                agent_type="mcp_agent",
                tool_name="test_tool",
                arguments={"secret": "value"},
                result={"response": "data"},
                error=None,
                duration_ms=100.0,
            )

            # Verify encryptor was called for both arguments and result
            assert mock_encryptor.encrypt.call_count == 2
            assert log_entry.request_body_encrypted == "encrypted_args"
            assert log_entry.response_body_encrypted == "encrypted_result"

    def test_handles_missing_encryption_key(self):
        """Test that encryption works even when key is not set."""
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.is_available = False
            mock_encryptor.encrypt.return_value = {"encrypted": "unencrypted_data"}
            mock_get_encryptor.return_value = mock_encryptor

            log_entry = _create_log_entry_sync(
                agent_id="test-agent",
                agent_type="mcp_agent",
                tool_name="test_tool",
                arguments={"input": "value"},
                result={"status": "ok"},
                error=None,
                duration_ms=100.0,
            )

            # Should still create log entry
            assert log_entry.request_body_encrypted is not None
            assert log_entry.response_body_encrypted is not None

    def test_extracts_status_code_from_result(self):
        """Test that status_code is extracted from result dict."""
        with patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        ) as mock_get_encryptor:
            mock_encryptor = MagicMock()
            mock_encryptor.encrypt.return_value = {"encrypted": "test"}
            mock_get_encryptor.return_value = mock_encryptor

            log_entry = _create_log_entry_sync(
                agent_id="test-agent",
                agent_type="mcp_agent",
                tool_name="test_tool",
                arguments={},
                result={"status_code": 200},
                error=None,
                duration_ms=100.0,
            )

            assert log_entry.status_code == 200


class TestMCPToolLoggingEdgeCases:
    """Test edge cases for MCP tool logging."""

    async def test_disabled_tool_creates_log_entry(self):
        """Test that invoking a disabled tool creates log entry with error."""
        # Create a fresh mock for this test
        mock_encryptor_patch = patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        )
        mock_get_encryptor = mock_encryptor_patch.start()
        mock_encryptor = MagicMock()
        mock_encryptor.encrypt.return_value = {"encrypted": "test"}
        mock_get_encryptor.return_value = mock_encryptor

        registry = MCPToolRegistry()

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name="disabled_tool",
            description="Disabled tool",
            input_schema={},
            handler=handler,
            enabled=False,  # Disabled
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            result = await registry.invoke("disabled_tool", {})

            assert result["success"] is False
            assert "disabled" in result["error"]

            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert "disabled" in call_kwargs["error"]

        mock_encryptor_patch.stop()

    async def test_tool_with_nested_context(self):
        """Test that nested context values are properly extracted."""
        mock_encryptor_patch = patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        )
        mock_get_encryptor = mock_encryptor_patch.start()
        mock_encryptor = MagicMock()
        mock_encryptor.encrypt.return_value = {"encrypted": "test"}
        mock_get_encryptor.return_value = mock_encryptor

        registry = MCPToolRegistry()

        async def handler(args, ctx):
            return {"result": "success"}

        tool = MCPToolDefinition(
            name="test_tool",
            description="Test tool",
            input_schema={},
            handler=handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            context = {
                "agent_id": "agent-with-session",
                "agent_type": "worker",
                "session_id": "session-123",
                "custom_field": "custom_value",
            }
            await registry.invoke("test_tool", {"key": "value"}, context=context)

            call_kwargs = mock_create_log.call_args.kwargs
            # Should extract agent_id and agent_type
            assert call_kwargs["agent_id"] == "agent-with-session"
            assert call_kwargs["agent_type"] == "worker"
            # Custom fields are not extracted but should not cause errors
            assert call_kwargs["tool_name"] == "test_tool"

        mock_encryptor_patch.stop()

    async def test_handler_exception_creates_log_entry_with_error(self):
        """Test that handler exceptions create log entry with error_message."""
        mock_encryptor_patch = patch(
            "heretek_swarm.tools.mcp_tools._get_encryptor"
        )
        mock_get_encryptor = mock_encryptor_patch.start()
        mock_encryptor = MagicMock()
        mock_encryptor.encrypt.return_value = {"encrypted": "test"}
        mock_get_encryptor.return_value = mock_encryptor

        registry = MCPToolRegistry()

        async def failing_handler(args, ctx):
            raise RuntimeError("Handler execution failed")

        tool = MCPToolDefinition(
            name="failing_tool",
            description="Tool that fails",
            input_schema={},
            handler=failing_handler,
        )
        registry.register(tool)

        with patch(
            "heretek_swarm.tools.mcp_tools._create_log_entry_sync"
        ) as mock_create_log:
            result = await registry.invoke("failing_tool", {})

            assert result["success"] is False
            assert "Handler execution failed" in result["error"]

            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert "Handler execution failed" in call_kwargs["error"]

        mock_encryptor_patch.stop()
