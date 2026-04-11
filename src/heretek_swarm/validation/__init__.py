"""
Validation Module for Heretek Swarm

This module provides comprehensive validation for LLM outputs and agent messages.
It includes:
- LLM output validation with security pattern detection
- Agent message schema validation
- Code sanitization and safety checks
- Tool call validation

Author: Heretek Swarm Collective
Date: 2026-04-07
Version: 1.0.0
"""

from heretek_swarm.validation.agent_messages import (
    ActorMessage,
    AgentMessageBase,
    CodeExecutionRequest,
    ConsensusProposal,
    ConsensusVote,
    CoordinationRequest,
    ErrorMessage,
    MessagePriority,
    MessageType,
    StateUpdate,
    TaskMessage,
    ToolRequest,
    ToolResponse,
    create_actor_message,
    create_state_update,
    create_tool_request,
    create_tool_response,
    validate_message,
)
from heretek_swarm.validation.llm_output import (
    CodeLanguage,
    LLMOutputValidator,
    ValidationResult,
    ValidationSeverity,
    is_code_safe,
    is_text_safe,
    validate_llm_code,
    validate_llm_structured,
    validate_llm_text,
)

__all__ = [
    # LLM Output Validation
    "CodeLanguage",
    "LLMOutputValidator",
    "ValidationSeverity",
    "ValidationResult",
    "validate_llm_code",
    "validate_llm_text",
    "validate_llm_structured",
    "is_code_safe",
    "is_text_safe",
    # Agent Messages
    "AgentMessageBase",
    "ActorMessage",
    "StateUpdate",
    "ToolRequest",
    "ToolResponse",
    "CoordinationRequest",
    "ConsensusProposal",
    "ConsensusVote",
    "ErrorMessage",
    "TaskMessage",
    "CodeExecutionRequest",
    "MessagePriority",
    "MessageType",
    "validate_message",
    "create_actor_message",
    "create_state_update",
    "create_tool_request",
    "create_tool_response",
]
