"""
Agent Message Validation Module

This module provides Pydantic models for validating all types of agent messages
in the Heretek Swarm system. It ensures message structure integrity and content
safety before messages are processed or state updates are applied.

Author: Heretek Swarm Collective
Date: 2026-04-07
Version: 1.0.0
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError
from pydantic import validator as pydantic_validator

from heretek_swarm.validation.llm_output import (
    LLMOutputValidator,
    ValidationResult,
    ValidationSeverity,
)


class MessageType(str, Enum):
    """Standard message types in the swarm system."""
    # Actor base messages
    ACTOR_MESSAGE = "actor_message"
    STATE_UPDATE = "state_update"
    STATE_REQUEST = "state_request"

    # Tool-related messages
    TOOL_REQUEST = "tool_request"
    TOOL_RESPONSE = "tool_response"
    TOOL_ERROR = "tool_error"

    # Coordination messages
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    HANDOFF_REQUEST = "handoff_request"
    HANDOFF_ACCEPTED = "handoff_accepted"
    HANDOFF_REJECTED = "handoff_rejected"

    # Task-related messages
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Consensus messages
    CONSENSUS_PROPOSAL = "consensus_proposal"
    CONSENSUS_VOTE = "consensus_vote"
    CONSENSUS_RESULT = "consensus_result"

    # Error messages
    ERROR = "error"
    WARNING = "warning"

    # Status messages
    STATUS_UPDATE = "status_update"
    HEALTH_CHECK = "health_check"
    HEARTBEAT = "heartbeat"

    # Nexus-specific messages
    CONNECTION_CREATED = "connection_created"
    CONNECTION_UPDATED = "connection_updated"
    CONNECTION_DELETED = "connection_deleted"
    CONNECTION_STATUS = "connection_status"
    REQUEST_COMPLETED = "request_completed"
    WEBHOOK_REGISTERED = "webhook_registered"
    WEBHOOK_UNREGISTERED = "webhook_unregistered"
    WEBHOOK_VALIDATION = "webhook_validation"
    WEBHOOK_STATUS = "webhook_status"
    PROTOCOL_TRANSLATED = "protocol_translated"
    INTEGRATION_REPORT = "integration_report"

    # Coder-specific messages
    CODE_GENERATED = "code_generated"
    CODE_REVIEWED = "code_reviewed"
    CODE_DEBUGGED = "code_debugged"
    TESTS_GENERATED = "tests_generated"
    DOCS_GENERATED = "docs_generated"
    CODE_REFACTORED = "code_refactored"
    CODE_EXPLAINED = "code_explained"
    TASK_IMPLEMENTED = "task_implemented"


class MessagePriority(str, Enum):
    """Message priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AgentMessageBase(BaseModel):
    """Base class for all agent messages."""

    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    message_type: str = Field(..., description="Type of the message")
    sender_id: str = Field(..., description="ID of the sending agent")
    recipient_id: Optional[str] = Field(None, description="ID of the recipient agent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    correlation_id: Optional[str] = Field(None, description="ID to correlate related messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        extra = "allow"  # Allow extra fields for flexibility
        validate_assignment = True


class ActorMessage(AgentMessageBase):
    """
    Standard message between actors in the swarm.
    
    This is the primary message type used for inter-agent communication.
    """

    message_type: str = Field(default=MessageType.ACTOR_MESSAGE.value)
    content: Dict[str, Any] = Field(..., description="Message content payload")

    @pydantic_validator("content")
    def validate_content_safety(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that message content doesn't contain dangerous patterns."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=True)

        def check_value(value: Any, path: str = "") -> None:
            """Recursively check values for dangerous patterns."""
            if isinstance(value, str):
                result = validator.validate_text(value)
                if not result.valid:
                    raise ValueError(f"Unsafe content at path '{path}': {', '.join(result.errors)}")
            elif isinstance(value, dict):
                for key, val in value.items():
                    check_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{path}[{i}]")

        check_value(v)
        return v

    class Config:
        extra = "allow"


class StateUpdate(AgentMessageBase):
    """
    Message for updating agent or swarm state.
    
    State updates are critical and require strict validation before application.
    """

    message_type: str = Field(default=MessageType.STATE_UPDATE.value)
    state_key: str = Field(..., min_length=1, max_length=256, description="Key identifying the state to update")
    state_value: Any = Field(..., description="New value for the state")
    operation: str = Field(default="set", description="Operation to perform (set, append, delete, merge)")
    version: Optional[int] = Field(None, description="Expected version for optimistic locking")

    @pydantic_validator("state_key")
    def validate_state_key(cls, v: str) -> str:
        """Validate state key format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", v):
            raise ValueError(f"Invalid state key format: {v}")
        return v

    @pydantic_validator("state_value")
    def validate_state_value_safety(cls, v: Any) -> Any:
        """Validate that state value doesn't contain dangerous patterns."""
        validator = LLMOutputValidator(strict_mode=True)

        def check_value(value: Any, path: str = "") -> Any:
            """Recursively check and sanitize values."""
            if isinstance(value, str):
                result = validator.validate_text(value)
                if not result.valid:
                    raise ValueError(f"Unsafe state value at path '{path}': {', '.join(result.errors)}")
                # Return sanitized version if available
                return result.sanitized_content or value
            elif isinstance(value, dict):
                return {k: check_value(val, f"{path}.{k}" if path else k) for k, val in value.items()}
            elif isinstance(value, list):
                return [check_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
            return value

        return check_value(v)

    @pydantic_validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        valid_operations = {"set", "append", "delete", "merge", "increment", "decrement"}
        if v not in valid_operations:
            raise ValueError(f"Invalid operation: {v}. Must be one of {valid_operations}")
        return v

    class Config:
        extra = "forbid"


class ToolRequest(AgentMessageBase):
    """
    Request to execute a tool or function.
    
    Tool requests require validation of both the tool name and arguments.
    """

    message_type: str = Field(default=MessageType.TOOL_REQUEST.value)
    tool_name: str = Field(..., min_length=1, max_length=100, description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")

    @pydantic_validator("tool_name")
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid tool name format: {v}")

        # Block dangerous tool names
        dangerous_tools = {"eval", "exec", "compile", "__import__", "getattr", "setattr", "delattr", "hasattr", "globals", "locals", "vars", "dir", "open", "input"}
        if v.lower() in dangerous_tools:
            raise ValueError(f"Dangerous tool name not allowed: {v}")

        return v

    @pydantic_validator("arguments")
    def validate_arguments_safety(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that tool arguments don't contain dangerous patterns."""
        validator = LLMOutputValidator(strict_mode=True)

        for key, value in v.items():
            if isinstance(value, str):
                result = validator.validate_text(value)
                if not result.valid:
                    raise ValueError(f"Unsafe argument '{key}': {', '.join(result.errors)}")

        return v

    class Config:
        extra = "forbid"


class ToolResponse(AgentMessageBase):
    """
    Response from a tool execution.
    
    Contains the result or error from tool execution.
    """

    message_type: str = Field(default=MessageType.TOOL_RESPONSE.value)
    execution_id: str = Field(..., description="ID of the executed tool request")
    success: bool = Field(..., description="Whether the tool execution succeeded")
    result: Optional[Any] = Field(None, description="Result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: int = Field(default=0, ge=0, description="Execution time in milliseconds")

    @pydantic_validator("error")
    def validate_error_safety(cls, v: Optional[str]) -> Optional[str]:
        """Validate that error messages don't contain dangerous patterns."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=False)  # Sanitize errors instead of rejecting
        result = validator.validate_text(v)

        if not result.valid and result.sanitized_content:
            return result.sanitized_content

        return v

    class Config:
        extra = "forbid"


class CoordinationRequest(AgentMessageBase):
    """
    Request for coordination between agents.
    
    Used for inter-agent coordination and task delegation.
    """

    message_type: str = Field(default=MessageType.COORDINATION_REQUEST.value)
    request_type: str = Field(..., description="Type of coordination request")
    description: str = Field(..., max_length=2000, description="Description of the coordination needed")
    required_capabilities: List[str] = Field(default_factory=list, description="Required agent capabilities")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for the request")
    payload: Optional[Dict[str, Any]] = Field(None, description="Additional payload for the request")

    @pydantic_validator("description")
    def validate_description_safety(cls, v: str) -> str:
        """Validate description safety."""
        validator = LLMOutputValidator(strict_mode=True)
        result = validator.validate_text(v)
        if not result.valid:
            raise ValueError(f"Unsafe description: {', '.join(result.errors)}")
        return v

    @pydantic_validator("payload")
    def validate_payload_safety(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate payload safety."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=True)

        def check_value(value: Any, path: str = "") -> Any:
            if isinstance(value, str):
                result = validator.validate_text(value)
                if not result.valid:
                    raise ValueError(f"Unsafe payload at '{path}': {', '.join(result.errors)}")
                return result.sanitized_content or value
            elif isinstance(value, dict):
                return {k: check_value(val, f"{path}.{k}" if path else k) for k, val in value.items()}
            elif isinstance(value, list):
                return [check_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
            return value

        return check_value(v)

    class Config:
        extra = "forbid"


class ConsensusProposal(AgentMessageBase):
    """
    Proposal for consensus deliberation.
    
    Used in swarm consensus mechanisms for decision making.
    """

    message_type: str = Field(default=MessageType.CONSENSUS_PROPOSAL.value)
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:12]}")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the proposal")
    description: str = Field(..., max_length=5000, description="Detailed description of the proposal")
    options: List[str] = Field(default_factory=list, description="Available options for voting")
    proposer_id: str = Field(..., description="ID of the proposing agent")

    @pydantic_validator("title", "description")
    def validate_text_safety(cls, v: str) -> str:
        """Validate text safety."""
        validator = LLMOutputValidator(strict_mode=True)
        result = validator.validate_text(v)
        if not result.valid:
            raise ValueError(f"Unsafe text: {', '.join(result.errors)}")
        return v

    class Config:
        extra = "forbid"


class ConsensusVote(AgentMessageBase):
    """
    Vote in a consensus deliberation.
    """

    message_type: str = Field(default=MessageType.CONSENSUS_VOTE.value)
    proposal_id: str = Field(..., description="ID of the proposal being voted on")
    vote: str = Field(..., description="The vote value (option name or yes/no)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the vote (0-1)")
    reasoning: Optional[str] = Field(None, max_length=1000, description="Optional reasoning for the vote")

    @pydantic_validator("reasoning")
    def validate_reasoning_safety(cls, v: Optional[str]) -> Optional[str]:
        """Validate reasoning safety."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=True)
        result = validator.validate_text(v)
        if not result.valid:
            raise ValueError(f"Unsafe reasoning: {', '.join(result.errors)}")
        return v

    class Config:
        extra = "forbid"


class ErrorMessage(AgentMessageBase):
    """
    Error message from an agent.
    """

    message_type: str = Field(default=MessageType.ERROR.value)
    error_code: str = Field(..., description="Error code for categorization")
    error_message: str = Field(..., description="Human-readable error message")
    stack_trace: Optional[str] = Field(None, description="Optional stack trace")
    context: Optional[Dict[str, Any]] = Field(None, description="Context information about the error")

    @pydantic_validator("error_message", "stack_trace")
    def validate_error_safety(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize error messages."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=False)  # Sanitize instead of reject
        result = validator.validate_text(v)
        return result.sanitized_content or v

    class Config:
        extra = "forbid"


class TaskMessage(AgentMessageBase):
    """
    Message related to task management.
    """

    message_type: str = Field(..., description="Specific task message type")
    task_id: str = Field(..., description="ID of the task")
    task_status: str = Field(default="pending", description="Status of the task")
    task_data: Optional[Dict[str, Any]] = Field(None, description="Task-related data")

    @pydantic_validator("task_data")
    def validate_task_data_safety(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate task data safety."""
        if not v:
            return v

        validator = LLMOutputValidator(strict_mode=True)

        def check_value(value: Any, path: str = "") -> Any:
            if isinstance(value, str):
                result = validator.validate_text(value)
                if not result.valid:
                    raise ValueError(f"Unsafe task data at '{path}': {', '.join(result.errors)}")
                return result.sanitized_content or value
            elif isinstance(value, dict):
                return {k: check_value(val, f"{path}.{k}" if path else k) for k, val in value.items()}
            elif isinstance(value, list):
                return [check_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
            return value

        return check_value(v)

    class Config:
        extra = "forbid"


class CodeExecutionRequest(AgentMessageBase):
    """
    Request to execute generated code.
    
    This is a specialized message for the Coder agent that includes
    additional validation for code content.
    """

    message_type: str = Field(default="code_execution_request")
    code: str = Field(..., min_length=1, description="Code to execute")
    language: str = Field(default="python", description="Programming language")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")
    sandbox: bool = Field(default=True, description="Whether to execute in sandbox")

    @pydantic_validator("code")
    def validate_code_safety(cls, v: str) -> str:
        """Validate code for dangerous patterns."""
        validator = LLMOutputValidator(strict_mode=True)
        result = validator.validate_code(v)

        if not result.valid:
            raise ValueError(f"Unsafe code: {', '.join(result.errors)}")

        return v

    class Config:
        extra = "forbid"


# Message type registry for dynamic validation
MESSAGE_TYPES: Dict[str, type] = {
    MessageType.ACTOR_MESSAGE.value: ActorMessage,
    MessageType.STATE_UPDATE.value: StateUpdate,
    MessageType.TOOL_REQUEST.value: ToolRequest,
    MessageType.TOOL_RESPONSE.value: ToolResponse,
    MessageType.COORDINATION_REQUEST.value: CoordinationRequest,
    MessageType.CONSENSUS_PROPOSAL.value: ConsensusProposal,
    MessageType.CONSENSUS_VOTE.value: ConsensusVote,
    MessageType.ERROR.value: ErrorMessage,
    "code_execution_request": CodeExecutionRequest,
}

# Task-related message types
TASK_MESSAGE_TYPES: Dict[str, str] = {
    MessageType.TASK_CREATED.value: "task_created",
    MessageType.TASK_UPDATED.value: "task_updated",
    MessageType.TASK_COMPLETED.value: "task_completed",
    MessageType.TASK_FAILED.value: "task_failed",
}


def validate_message(message_type: str, content: Dict[str, Any]) -> ValidationResult:
    """
    Validate a message based on its type.
    
    Args:
        message_type: Type of the message
        content: Message content
    
    Returns:
        ValidationResult with validation status
    """
    if message_type not in MESSAGE_TYPES:
        # For unknown types, do basic content validation
        validator = LLMOutputValidator(strict_mode=True)
        return validator.validate_structured(content)

    model_class = MESSAGE_TYPES[message_type]

    try:
        # Add message_type to content if not present
        if "message_type" not in content:
            content["message_type"] = message_type

        # Try to create validated model
        model = model_class(**content)

        return ValidationResult(
            valid=True,
            content=model.dict(),
            errors=[],
            warnings=[],
            severity=ValidationSeverity.INFO,
        )
    except ValidationError as e:
        return ValidationResult(
            valid=False,
            content=content,
            errors=[f"{err['loc']}: {err['msg']}" for err in e.errors()],
            warnings=[],
            severity=ValidationSeverity.ERROR,
        )


def create_actor_message(
    content: Dict[str, Any],
    sender_id: str,
    recipient_id: Optional[str] = None,
    priority: MessagePriority = MessagePriority.NORMAL,
    correlation_id: Optional[str] = None,
) -> ActorMessage:
    """
    Create a validated ActorMessage.
    
    Args:
        content: Message content
        sender_id: ID of the sending agent
        recipient_id: ID of the recipient agent
        priority: Message priority
        correlation_id: ID to correlate related messages
    
    Returns:
        Validated ActorMessage
    """
    return ActorMessage(
        content=content,
        sender_id=sender_id,
        recipient_id=recipient_id,
        priority=priority,
        correlation_id=correlation_id,
    )


def create_state_update(
    state_key: str,
    state_value: Any,
    sender_id: str,
    operation: str = "set",
    version: Optional[int] = None,
) -> StateUpdate:
    """
    Create a validated StateUpdate message.
    
    Args:
        state_key: Key identifying the state to update
        state_value: New value for the state
        sender_id: ID of the sending agent
        operation: Operation to perform
        version: Expected version for optimistic locking
    
    Returns:
        Validated StateUpdate
    """
    return StateUpdate(
        state_key=state_key,
        state_value=state_value,
        sender_id=sender_id,
        operation=operation,
        version=version,
    )


def create_tool_request(
    tool_name: str,
    arguments: Dict[str, Any],
    sender_id: str,
    timeout: int = 30,
) -> ToolRequest:
    """
    Create a validated ToolRequest message.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments for the tool
        sender_id: ID of the sending agent
        timeout: Execution timeout in seconds
    
    Returns:
        Validated ToolRequest
    """
    return ToolRequest(
        tool_name=tool_name,
        arguments=arguments,
        sender_id=sender_id,
        timeout=timeout,
    )


def create_tool_response(
    execution_id: str,
    success: bool,
    sender_id: str,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    execution_time_ms: int = 0,
) -> ToolResponse:
    """
    Create a validated ToolResponse message.
    
    Args:
        execution_id: ID of the executed tool request
        success: Whether the tool execution succeeded
        sender_id: ID of the sending agent
        result: Result of the tool execution
        error: Error message if execution failed
        execution_time_ms: Execution time in milliseconds
    
    Returns:
        Validated ToolResponse
    """
    return ToolResponse(
        execution_id=execution_id,
        success=success,
        sender_id=sender_id,
        result=result,
        error=error,
        execution_time_ms=execution_time_ms,
    )
