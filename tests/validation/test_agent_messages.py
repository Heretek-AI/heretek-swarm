"""
Tests for Agent Message Validation

This module contains comprehensive tests for the agent message validation
functionality, ensuring all message types are properly validated.
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from heretek_swarm.validation.agent_messages import (
    ActorMessage,
    StateUpdate,
    ToolRequest,
    ToolResponse,
    CoordinationRequest,
    ConsensusProposal,
    ConsensusVote,
    ErrorMessage,
    TaskMessage,
    CodeExecutionRequest,
    MessagePriority,
    MessageType,
    validate_message,
    create_actor_message,
    create_state_update,
    create_tool_request,
    create_tool_response,
    MESSAGE_TYPES,
)


class TestMessageTypes:
    """Tests for MessageType enum."""
    
    def test_actor_message_types(self):
        """Test actor message types are defined."""
        assert MessageType.ACTOR_MESSAGE.value == "actor_message"
        assert MessageType.STATE_UPDATE.value == "state_update"
        assert MessageType.STATE_REQUEST.value == "state_request"
    
    def test_tool_message_types(self):
        """Test tool-related message types are defined."""
        assert MessageType.TOOL_REQUEST.value == "tool_request"
        assert MessageType.TOOL_RESPONSE.value == "tool_response"
        assert MessageType.TOOL_ERROR.value == "tool_error"
    
    def test_coordination_message_types(self):
        """Test coordination message types are defined."""
        assert MessageType.COORDINATION_REQUEST.value == "coordination_request"
        assert MessageType.COORDINATION_RESPONSE.value == "coordination_response"
        assert MessageType.HANDOFF_REQUEST.value == "handoff_request"
        assert MessageType.HANDOFF_ACCEPTED.value == "handoff_accepted"
        assert MessageType.HANDOFF_REJECTED.value == "handoff_rejected"
    
    def test_task_message_types(self):
        """Test task message types are defined."""
        assert MessageType.TASK_CREATED.value == "task_created"
        assert MessageType.TASK_UPDATED.value == "task_updated"
        assert MessageType.TASK_COMPLETED.value == "task_completed"
        assert MessageType.TASK_FAILED.value == "task_failed"
    
    def test_consensus_message_types(self):
        """Test consensus message types are defined."""
        assert MessageType.CONSENSUS_PROPOSAL.value == "consensus_proposal"
        assert MessageType.CONSENSUS_VOTE.value == "consensus_vote"
        assert MessageType.CONSENSUS_RESULT.value == "consensus_result"
    
    def test_error_message_types(self):
        """Test error message types are defined."""
        assert MessageType.ERROR.value == "error"
        assert MessageType.WARNING.value == "warning"
    
    def test_status_message_types(self):
        """Test status message types are defined."""
        assert MessageType.STATUS_UPDATE.value == "status_update"
        assert MessageType.HEALTH_CHECK.value == "health_check"
        assert MessageType.HEARTBEAT.value == "heartbeat"
    
    def test_nexus_message_types(self):
        """Test Nexus-specific message types are defined."""
        assert MessageType.CONNECTION_CREATED.value == "connection_created"
        assert MessageType.CONNECTION_UPDATED.value == "connection_updated"
        assert MessageType.CONNECTION_DELETED.value == "connection_deleted"
        assert MessageType.WEBHOOK_REGISTERED.value == "webhook_registered"
        assert MessageType.WEBHOOK_UNREGISTERED.value == "webhook_unregistered"
    
    def test_coder_message_types(self):
        """Test Coder-specific message types are defined."""
        assert MessageType.CODE_GENERATED.value == "code_generated"
        assert MessageType.CODE_REVIEWED.value == "code_reviewed"
        assert MessageType.CODE_DEBUGGED.value == "code_debugged"
        assert MessageType.TESTS_GENERATED.value == "tests_generated"


class TestMessagePriority:
    """Tests for MessagePriority enum."""
    
    def test_priority_levels(self):
        """Test all priority levels exist."""
        assert MessagePriority.CRITICAL.value == "critical"
        assert MessagePriority.HIGH.value == "high"
        assert MessagePriority.NORMAL.value == "normal"
        assert MessagePriority.LOW.value == "low"


class TestActorMessage:
    """Tests for ActorMessage model."""
    
    def test_valid_actor_message(self):
        """Test creating a valid actor message."""
        msg = ActorMessage(
            content={"text": "Hello"},
            sender_id="agent1"
        )
        assert msg.sender_id == "agent1"
        assert msg.content == {"text": "Hello"}
        assert msg.message_id is not None
    
    def test_actor_message_with_dangerous_content_fails(self):
        """Test that dangerous content in actor message fails."""
        with pytest.raises(ValidationError) as exc_info:
            ActorMessage(
                content={"code": "eval(user_input)"},
                sender_id="agent1"
            )
        assert "Unsafe content" in str(exc_info.value)
    
    def test_actor_message_with_nested_dangerous_content_fails(self):
        """Test that nested dangerous content fails."""
        with pytest.raises(ValidationError):
            ActorMessage(
                content={
                    "data": {
                        "nested": {
                            "dangerous": "__import__('os')"
                        }
                    }
                },
                sender_id="agent1"
            )
    
    def test_actor_message_with_list_content(self):
        """Test actor message with list content."""
        msg = ActorMessage(
            content={"items": ["safe", "content"]},
            sender_id="agent1"
        )
        assert msg.content["items"] == ["safe", "content"]
    
    def test_actor_message_with_dangerous_list_item_fails(self):
        """Test that dangerous content in list fails."""
        with pytest.raises(ValidationError):
            ActorMessage(
                content={"items": ["safe", "eval(x)"]},
                sender_id="agent1"
            )


class TestStateUpdate:
    """Tests for StateUpdate model."""
    
    def test_valid_state_update(self):
        """Test creating a valid state update."""
        update = StateUpdate(
            state_key="user.name",
            state_value="John",
            sender_id="agent1"
        )
        assert update.state_key == "user.name"
        assert update.state_value == "John"
        assert update.operation == "set"
    
    def test_state_update_invalid_key_format(self):
        """Test that invalid state key format fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="123invalid",
                state_value="value",
                sender_id="agent1"
            )
    
    def test_state_update_with_dangerous_value_fails(self):
        """Test that dangerous state values fail."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="config.callback",
                state_value="eval(user_input)",
                sender_id="agent1"
            )
    
    def test_state_update_with_exec_fails(self):
        """Test that exec in state value fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="config.code",
                state_value="exec(malicious_code)",
                sender_id="agent1"
            )
    
    def test_state_update_with_getattr_fails(self):
        """Test that getattr in state value fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="config.accessor",
                state_value="getattr(obj, 'attr')",
                sender_id="agent1"
            )
    
    def test_state_update_with_globals_fails(self):
        """Test that globals() in state value fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="config.namespace",
                state_value="globals()",
                sender_id="agent1"
            )
    
    def test_state_update_invalid_operation(self):
        """Test that invalid operation fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="counter",
                state_value=1,
                sender_id="agent1",
                operation="invalid_op"
            )
    
    def test_state_update_valid_operations(self):
        """Test all valid operations."""
        for op in ["set", "append", "delete", "merge", "increment", "decrement"]:
            update = StateUpdate(
                state_key="counter",
                state_value=1,
                sender_id="agent1",
                operation=op
            )
            assert update.operation == op
    
    def test_state_update_nested_dict_safe(self):
        """Test state update with safe nested dict."""
        update = StateUpdate(
            state_key="config",
            state_value={"nested": {"safe": "value"}},
            sender_id="agent1"
        )
        assert update.state_value["nested"]["safe"] == "value"
    
    def test_state_update_nested_dict_dangerous_fails(self):
        """Test state update with dangerous nested dict fails."""
        with pytest.raises(ValidationError):
            StateUpdate(
                state_key="config",
                state_value={"nested": {"dangerous": "locals()"}},
                sender_id="agent1"
            )


class TestToolRequest:
    """Tests for ToolRequest model."""
    
    def test_valid_tool_request(self):
        """Test creating a valid tool request."""
        request = ToolRequest(
            tool_name="calculator",
            arguments={"operation": "add", "a": 1, "b": 2},
            sender_id="agent1"
        )
        assert request.tool_name == "calculator"
        assert request.arguments["operation"] == "add"
    
    def test_tool_request_invalid_name_format(self):
        """Test that invalid tool name format fails."""
        with pytest.raises(ValidationError):
            ToolRequest(
                tool_name="123invalid",
                arguments={},
                sender_id="agent1"
            )
    
    def test_tool_request_dangerous_tool_name_fails(self):
        """Test that dangerous tool names fail."""
        dangerous_tools = ["eval", "exec", "compile", "__import__", "getattr", "setattr", "delattr", "hasattr", "globals", "locals", "vars", "dir", "open", "input"]
        for tool in dangerous_tools:
            with pytest.raises(ValidationError) as exc_info:
                ToolRequest(
                    tool_name=tool,
                    arguments={},
                    sender_id="agent1"
                )
            assert "Dangerous tool name" in str(exc_info.value)
    
    def test_tool_request_dangerous_arguments_fails(self):
        """Test that dangerous tool arguments fail."""
        with pytest.raises(ValidationError):
            ToolRequest(
                tool_name="executor",
                arguments={"code": "eval(x)"},
                sender_id="agent1"
            )
    
    def test_tool_request_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        request = ToolRequest(
            tool_name="calculator",
            arguments={},
            sender_id="agent1",
            timeout=60
        )
        assert request.timeout == 60
        
        # Timeout too low
        with pytest.raises(ValidationError):
            ToolRequest(
                tool_name="calculator",
                arguments={},
                sender_id="agent1",
                timeout=0
            )
        
        # Timeout too high
        with pytest.raises(ValidationError):
            ToolRequest(
                tool_name="calculator",
                arguments={},
                sender_id="agent1",
                timeout=500
            )


class TestToolResponse:
    """Tests for ToolResponse model."""
    
    def test_valid_tool_response_success(self):
        """Test creating a valid successful tool response."""
        response = ToolResponse(
            execution_id="exec_123",
            success=True,
            result={"value": 42},
            sender_id="agent1"
        )
        assert response.success is True
        assert response.result["value"] == 42
    
    def test_valid_tool_response_error(self):
        """Test creating a valid error tool response."""
        response = ToolResponse(
            execution_id="exec_123",
            success=False,
            error="Tool execution failed",
            sender_id="agent1"
        )
        assert response.success is False
        assert "failed" in response.error.lower()
    
    def test_tool_response_sanitizes_error_message(self):
        """Test that error messages are sanitized."""
        # Error messages should be sanitized, not rejected
        response = ToolResponse(
            execution_id="exec_123",
            success=False,
            error="Error in eval() call at line 10",
            sender_id="agent1"
        )
        # Should be created but sanitized
        assert response.error is not None


class TestCoordinationRequest:
    """Tests for CoordinationRequest model."""
    
    def test_valid_coordination_request(self):
        """Test creating a valid coordination request."""
        request = CoordinationRequest(
            request_type="delegation",
            description="Need help with task",
            sender_id="agent1"
        )
        assert request.request_type == "delegation"
        assert "help" in request.description.lower()
    
    def test_coordination_request_dangerous_description_fails(self):
        """Test that dangerous description fails."""
        with pytest.raises(ValidationError):
            CoordinationRequest(
                request_type="delegation",
                description="Use eval() to process this",
                sender_id="agent1"
            )
    
    def test_coordination_request_dangerous_payload_fails(self):
        """Test that dangerous payload fails."""
        with pytest.raises(ValidationError):
            CoordinationRequest(
                request_type="delegation",
                description="Need help",
                sender_id="agent1",
                payload={"callback": "exec(code)"}
            )
    
    def test_coordination_request_description_too_long(self):
        """Test that description over limit fails."""
        with pytest.raises(ValidationError):
            CoordinationRequest(
                request_type="delegation",
                description="x" * 3000,
                sender_id="agent1"
            )


class TestConsensusProposal:
    """Tests for ConsensusProposal model."""
    
    def test_valid_consensus_proposal(self):
        """Test creating a valid consensus proposal."""
        proposal = ConsensusProposal(
            title="New Feature",
            description="Implement new feature X",
            proposer_id="agent1",
            sender_id="agent1"
        )
        assert proposal.title == "New Feature"
        assert proposal.proposer_id == "agent1"
    
    def test_consensus_proposal_dangerous_title_fails(self):
        """Test that dangerous title fails."""
        with pytest.raises(ValidationError):
            ConsensusProposal(
                title="Use eval() for processing",
                description="Safe description",
                proposer_id="agent1"
            )
    
    def test_consensus_proposal_dangerous_description_fails(self):
        """Test that dangerous description fails."""
        with pytest.raises(ValidationError):
            ConsensusProposal(
                title="Safe Title",
                description="We should use __import__('os') for this",
                proposer_id="agent1"
            )
    
    def test_consensus_proposal_title_too_long(self):
        """Test that title over limit fails."""
        with pytest.raises(ValidationError):
            ConsensusProposal(
                title="x" * 300,
                description="Safe description",
                proposer_id="agent1"
            )


class TestConsensusVote:
    """Tests for ConsensusVote model."""
    
    def test_valid_consensus_vote(self):
        """Test creating a valid consensus vote."""
        vote = ConsensusVote(
            proposal_id="prop_123",
            vote="yes",
            sender_id="agent1"
        )
        assert vote.proposal_id == "prop_123"
        assert vote.vote == "yes"
        assert vote.confidence == 1.0
    
    def test_consensus_vote_with_reasoning(self):
        """Test vote with reasoning."""
        vote = ConsensusVote(
            proposal_id="prop_123",
            vote="yes",
            sender_id="agent1",
            reasoning="This is a good proposal",
            confidence=0.9
        )
        assert vote.reasoning == "This is a good proposal"
        assert vote.confidence == 0.9
    
    def test_consensus_vote_dangerous_reasoning_fails(self):
        """Test that dangerous reasoning fails."""
        with pytest.raises(ValidationError):
            ConsensusVote(
                proposal_id="prop_123",
                vote="yes",
                sender_id="agent1",
                reasoning="Because eval() is useful here"
            )
    
    def test_consensus_vote_confidence_range(self):
        """Test confidence must be in range."""
        # Valid confidence
        vote = ConsensusVote(
            proposal_id="prop_123",
            vote="yes",
            sender_id="agent1",
            confidence=0.5
        )
        assert vote.confidence == 0.5
        
        # Confidence too low
        with pytest.raises(ValidationError):
            ConsensusVote(
                proposal_id="prop_123",
                vote="yes",
                sender_id="agent1",
                confidence=-0.1
            )
        
        # Confidence too high
        with pytest.raises(ValidationError):
            ConsensusVote(
                proposal_id="prop_123",
                vote="yes",
                sender_id="agent1",
                confidence=1.5
            )


class TestErrorMessage:
    """Tests for ErrorMessage model."""
    
    def test_valid_error_message(self):
        """Test creating a valid error message."""
        error = ErrorMessage(
            error_code="ERR001",
            error_message="Something went wrong",
            sender_id="agent1"
        )
        assert error.error_code == "ERR001"
        assert "went wrong" in error.error_message
    
    def test_error_message_sanitizes_stack_trace(self):
        """Test that stack traces are sanitized."""
        # Error messages should be sanitized, not rejected
        error = ErrorMessage(
            error_code="ERR001",
            error_message="Error occurred",
            stack_trace="File 'test.py', line 10, in eval_func\n    eval(x)",
            sender_id="agent1"
        )
        assert error.stack_trace is not None


class TestTaskMessage:
    """Tests for TaskMessage model."""
    
    def test_valid_task_message(self):
        """Test creating a valid task message."""
        msg = TaskMessage(
            message_type=MessageType.TASK_CREATED.value,
            task_id="task_123",
            sender_id="agent1"
        )
        assert msg.task_id == "task_123"
        assert msg.task_status == "pending"
    
    def test_task_message_dangerous_data_fails(self):
        """Test that dangerous task data fails."""
        with pytest.raises(ValidationError):
            TaskMessage(
                message_type=MessageType.TASK_CREATED.value,
                task_id="task_123",
                sender_id="agent1",
                task_data={"code": "eval(x)"}
            )
    
    def test_task_message_nested_dangerous_data_fails(self):
        """Test that nested dangerous task data fails."""
        with pytest.raises(ValidationError):
            TaskMessage(
                message_type=MessageType.TASK_CREATED.value,
                task_id="task_123",
                sender_id="agent1",
                task_data={"config": {"nested": {"dangerous": "exec(code)"}}}
            )


class TestCodeExecutionRequest:
    """Tests for CodeExecutionRequest model."""
    
    def test_valid_code_execution_request(self):
        """Test creating a valid code execution request."""
        request = CodeExecutionRequest(
            code="print('Hello, World!')",
            sender_id="agent1"
        )
        assert "print" in request.code
        assert request.language == "python"
        assert request.sandbox is True
    
    def test_code_execution_request_with_eval_fails(self):
        """Test that code with eval fails."""
        with pytest.raises(ValidationError) as exc_info:
            CodeExecutionRequest(
                code="eval(user_input)",
                sender_id="agent1"
            )
        assert "Unsafe code" in str(exc_info.value)
    
    def test_code_execution_request_with_exec_fails(self):
        """Test that code with exec fails."""
        with pytest.raises(ValidationError):
            CodeExecutionRequest(
                code="exec(malicious_code)",
                sender_id="agent1"
            )
    
    def test_code_execution_request_with_import_fails(self):
        """Test that code with __import__ fails."""
        with pytest.raises(ValidationError):
            CodeExecutionRequest(
                code="__import__('os').system('ls')",
                sender_id="agent1"
            )
    
    def test_code_execution_request_with_subprocess_fails(self):
        """Test that code with subprocess fails."""
        with pytest.raises(ValidationError):
            CodeExecutionRequest(
                code="subprocess.run(['ls'])",
                sender_id="agent1"
            )
    
    def test_code_execution_request_empty_code_fails(self):
        """Test that empty code fails."""
        with pytest.raises(ValidationError):
            CodeExecutionRequest(
                code="",
                sender_id="agent1"
            )
    
    def test_code_execution_request_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        request = CodeExecutionRequest(
            code="print('hello')",
            sender_id="agent1",
            timeout=60
        )
        assert request.timeout == 60
        
        # Timeout too low
        with pytest.raises(ValidationError):
            CodeExecutionRequest(
                code="print('hello')",
                sender_id="agent1",
                timeout=0
            )


class TestValidateMessage:
    """Tests for validate_message function."""
    
    def test_validate_known_message_type(self):
        """Test validation of known message type."""
        result = validate_message(
            "actor_message",
            {"content": {"text": "hello"}, "sender_id": "agent1"}
        )
        assert result.valid is True
    
    def test_validate_unknown_message_type(self):
        """Test validation of unknown message type."""
        result = validate_message(
            "unknown_type",
            {"key": "value"}
        )
        # Should do basic structured validation
        assert result.valid is True
    
    def test_validate_known_message_type_with_dangerous_content(self):
        """Test validation of known message type with dangerous content."""
        result = validate_message(
            "actor_message",
            {"content": {"code": "eval(x)"}, "sender_id": "agent1"}
        )
        assert result.valid is False
    
    def test_validate_state_update_message(self):
        """Test validation of state update message."""
        result = validate_message(
            "state_update",
            {
                "state_key": "user.name",
                "state_value": "John",
                "sender_id": "agent1"
            }
        )
        assert result.valid is True


class TestCreateFunctions:
    """Tests for message creation helper functions."""
    
    def test_create_actor_message(self):
        """Test create_actor_message function."""
        msg = create_actor_message(
            content={"text": "hello"},
            sender_id="agent1",
            priority=MessagePriority.HIGH
        )
        assert msg.priority == MessagePriority.HIGH
        assert msg.content == {"text": "hello"}
    
    def test_create_state_update(self):
        """Test create_state_update function."""
        update = create_state_update(
            state_key="counter",
            state_value=42,
            sender_id="agent1",
            operation="increment"
        )
        assert update.state_key == "counter"
        assert update.state_value == 42
        assert update.operation == "increment"
    
    def test_create_tool_request(self):
        """Test create_tool_request function."""
        request = create_tool_request(
            tool_name="calculator",
            arguments={"op": "add"},
            sender_id="agent1",
            timeout=60
        )
        assert request.tool_name == "calculator"
        assert request.timeout == 60
    
    def test_create_tool_response(self):
        """Test create_tool_response function."""
        response = create_tool_response(
            execution_id="exec_123",
            success=True,
            sender_id="agent1",
            result={"value": 42}
        )
        assert response.execution_id == "exec_123"
        assert response.success is True


class TestMessageTypesRegistry:
    """Tests for MESSAGE_TYPES registry."""
    
    def test_registered_message_types(self):
        """Test that expected message types are registered."""
        assert "actor_message" in MESSAGE_TYPES
        assert "state_update" in MESSAGE_TYPES
        assert "tool_request" in MESSAGE_TYPES
        assert "tool_response" in MESSAGE_TYPES
        assert "coordination_request" in MESSAGE_TYPES
        assert "consensus_proposal" in MESSAGE_TYPES
        assert "consensus_vote" in MESSAGE_TYPES
        assert "error" in MESSAGE_TYPES
    
    def test_message_type_mapping(self):
        """Test that message types map to correct classes."""
        from heretek_swarm.validation.agent_messages import (
            ActorMessage,
            StateUpdate,
            ToolRequest,
        )
        assert MESSAGE_TYPES["actor_message"] == ActorMessage
        assert MESSAGE_TYPES["state_update"] == StateUpdate
        assert MESSAGE_TYPES["tool_request"] == ToolRequest
