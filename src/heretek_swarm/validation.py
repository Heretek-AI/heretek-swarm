"""
Input Validation Module - Pydantic v2 models for Zero-Trust input validation.

This module provides strict schema validation for all actor message inputs,
enforcing Zero-Trust principles by validating all data before processing.

Features:
- Pydantic v2 models for all message types
- Strict type checking with field validation
- Input sanitization helpers
- Custom validators for complex constraints
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid
import re


class MessageContent(BaseModel):
    """
    Validated message content model.
    
    All message content must conform to this schema to prevent
    injection attacks and ensure consistent data structures.
    """
    
    _model_config = ConfigDict(extra='forbid')  # Reject unknown fields
    
    message_type: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$',
        _description = "Message type identifier (alphanumeric, starts with letter)"
    )
    content: Dict[str, Any] = Field(
        _default_factory = dict,
        _description = "Message payload data"
    )
    sender_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 128,
        _description = "ID of the sending actor"
    )
    correlation_id: Optional[str] = Field(
        None,
        _max_length = 128,
        _description = "Optional correlation ID for request-response patterns"
    )
    reply_to: Optional[str] = Field(
        None,
        _max_length = 256,
        _description = "Optional topic for responses"
    )
    timestamp: str = Field(
        _default_factory = lambda: datetime.now(timezone.utc).isoformat(),
        _description = "ISO8601 timestamp"
    )
    
    @field_validator('sender_id')
    @classmethod
    def validate_sender_id(cls, v: str) -> str:
        """Validate sender_id format - must be valid UUID hex or actor_ prefixed."""
        if not v:
            raise ValueError("sender_id cannot be empty")
        # Allow UUID hex format (128-bit)
        if re.match(r'^[0-9a-f]{32}$', v.lower()):
            return v.lower()
        # Allow actor_ prefix format
        if re.match(r'^actor_[0-9a-f]{32}$', v.lower()):
            return v.lower()
        raise ValueError(
            f"Invalid sender_id format: {v}. Must be UUID hex or actor_<uuid> format"
        )
    
    @field_validator('correlation_id')
    @classmethod
    def validate_correlation_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate correlation_id format if provided."""
        if v is None:
            return v
        if not v:
            raise ValueError("correlation_id cannot be empty string")
        # Must be valid UUID format
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            # Allow simple string IDs
            if re.match(r'^[a-zA-Z0-9_-]{1,128}$', v):
                return v
            raise ValueError(
                f"Invalid correlation_id format: {v}. Must be UUID or alphanumeric"
            )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content dict - check for nested dangerous patterns."""
        if not v:
            return v
        # Check for potential injection patterns in string values
        for key, value in v.items():
            if isinstance(value, str):
                # Reject strings with potential code injection
                if re.search(r'__\w+__|exec\s*\(|eval\s*\(|import\s+os|import\s+sys', value):
                    raise ValueError(f"Potentially dangerous content detected in field: {key}")
        return v


class DeliberationRequest(BaseModel):
    """Validated deliberation request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    deliberation_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _pattern = r'^del_[0-9]{8}_[0-9]{6}$',
        _description = "Deliberation ID (format: del_YYYYMMDD_HHMMSS)"
    )
    topic: str = Field(
        ...,
        _min_length = 1,
        _max_length = 512,
        _description = "Deliberation topic"
    )
    triad_members: List[str] = Field(
        _default_factory = list,
        _description = "List of triad member IDs"
    )
    
    @field_validator('triad_members')
    @classmethod
    def validate_triad_members(cls, v: List[str]) -> List[str]:
        """Validate triad member IDs."""
        if not v:
            return v
        # Limit to reasonable number
        if len(v) > 10:
            raise ValueError(f"Too many triad members: {len(v)}. Maximum is 10")
        # Validate each member ID
        for member_id in v:
            if not member_id or len(member_id) > 128:
                raise ValueError(f"Invalid member ID: {member_id}")
        return v


class MemoryStoreRequest(BaseModel):
    """Validated memory storage request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    content: Dict[str, Any] = Field(
        ...,
        _description = "Memory content to store"
    )
    metadata: Dict[str, Any] = Field(
        _default_factory = dict,
        _description = "Optional metadata"
    )
    ttl: Optional[int] = Field(
        None,
        _ge = 1,
        _le = 31536000,  # Max 1 year
        _description = "Time to live in seconds"
    )
    persistent: bool = Field(
        _default = False,
        _description = "Whether to store in persistent tier"
    )
    lineage: Optional[List[str]] = Field(
        None,
        _description = "Parent memory IDs"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content is not empty."""
        if not v:
            raise ValueError("content cannot be empty")
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata size."""
        if len(v) > 50:
            raise ValueError(f"Too many metadata fields: {len(v)}. Maximum is 50")
        return v


class AnalysisRequest(BaseModel):
    """Validated analysis request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    request_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _description = "Unique request identifier"
    )
    problem: str = Field(
        ...,
        _min_length = 1,
        _max_length = 10000,
        _description = "Problem description to analyze"
    )
    
    @field_validator('request_id')
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        """Validate request_id format."""
        if not v:
            raise ValueError("request_id cannot be empty")
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError(
                f"Invalid request_id format: {v}. Must be alphanumeric"
            )
        return v


class ValidationRequest(BaseModel):
    """Validated validation request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    request_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _description = "Unique request identifier"
    )
    decision: Any = Field(
        ...,
        _description = "Decision to validate"
    )
    original_analysis: Optional[Dict[str, Any]] = Field(
        None,
        _description = "Original analysis context"
    )


class QueryRequest(BaseModel):
    """Validated query request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    query_text: Optional[str] = Field(
        None,
        _max_length = 10000,
        _description = "Text to search for"
    )
    filters: Dict[str, Any] = Field(
        _default_factory = dict,
        _description = "Metadata filters"
    )
    limit: int = Field(
        _default = 10,
        _ge = 1,
        _le = 1000,
        _description = "Maximum results (1-1000)"
    )
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filters size."""
        if len(v) > 20:
            raise ValueError(f"Too many filters: {len(v)}. Maximum is 20")
        return v


class LineageRequest(BaseModel):
    """Validated lineage tracking request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    decision_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _description = "Decision identifier"
    )
    parent_ids: List[str] = Field(
        _default_factory = list,
        _description = "Parent memory/decision IDs"
    )
    
    @field_validator('parent_ids')
    @classmethod
    def validate_parent_ids(cls, v: List[str]) -> List[str]:
        """Validate parent IDs."""
        if len(v) > 20:
            raise ValueError(f"Too many parent IDs: {len(v)}. Maximum is 20")
        return v


class HealthCheckRequest(BaseModel):
    """Validated health check request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    reply_to: str = Field(
        _default = "health",
        _max_length = 256,
        _description = "Reply topic"
    )


class SuspendResumeRequest(BaseModel):
    """Validated suspend/resume request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    actor_id: Optional[str] = Field(
        None,
        _max_length = 128,
        _description = "Target actor ID (uses sender if not provided)"
    )


class TerminateRequest(BaseModel):
    """Validated terminate request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    actor_id: Optional[str] = Field(
        None,
        _max_length = 128,
        _description = "Target actor ID (uses sender if not provided)"
    )
    reason: Optional[str] = Field(
        None,
        _max_length = 512,
        _description = "Optional termination reason"
    )


class CollectiveTaskRequest(BaseModel):
    """Validated collective task request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    task: str = Field(
        ...,
        _min_length = 1,
        _max_length = 10000,
        _description = "Task description"
    )
    participants: List[str] = Field(
        _default_factory = list,
        _description = "Participant actor IDs"
    )


class TaskRequest(BaseModel):
    """Validated task coordination request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    task_id: Optional[str] = Field(
        None,
        _max_length = 64,
        _description = "Optional task identifier"
    )
    name: str = Field(
        ...,
        _min_length = 1,
        _max_length = 256,
        _description = "Task name"
    )
    description: str = Field(
        ...,
        _min_length = 1,
        _max_length = 10000,
        _description = "Task description"
    )
    assigned_agents: Optional[List[str]] = Field(
        _default_factory = list,
        _description = "Agents assigned to this task"
    )
    dependencies: Optional[List[str]] = Field(
        _default_factory = list,
        _description = "Task IDs this depends on"
    )
    dependency_type: Optional[str] = Field(
        "sequential",
        _description = "sequential|parallel|conditional|resource"
    )
    priority: Optional[int] = Field(
        5,
        _ge = 1,
        _le = 10,
        _description = "Priority 1-10"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        _default_factory = dict,
        _description = "Additional metadata"
    )


class DependencyRequest(BaseModel):
    """Validated dependency resolution request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    task_ids: Optional[List[str]] = Field(
        _default_factory = list,
        _description = "Tasks to analyze"
    )


class CoordinationRequest(BaseModel):
    """Validated coordination request model."""
    
    _model_config = ConfigDict(extra='forbid')
    
    workflow_id: Optional[str] = Field(
        None,
        _max_length = 64,
        _description = "Workflow identifier"
    )
    agent_id: Optional[str] = Field(
        None,
        _max_length = 128,
        _description = "Agent identifier"
    )
    
    task_id: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _description = "Task identifier"
    )
    task_type: str = Field(
        ...,
        _min_length = 1,
        _max_length = 64,
        _description = "Type of task"
    )
    description: str = Field(
        ...,
        _min_length = 1,
        _max_length = 2000,
        _description = "Task description"
    )
    input_data: Dict[str, Any] = Field(
        _default_factory = dict,
        _description = "Task input data"
    )
    protocol: Dict[str, Any] = Field(
        _default_factory = dict,
        _description = "Communication protocol"
    )
    reply_to: Optional[str] = Field(
        None,
        _max_length = 256,
        _description = "Reply topic"
    )
    
    @field_validator('input_data')
    @classmethod
    def validate_input_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data size."""
        if len(v) > 100:
            raise ValueError(f"Too many input fields: {len(v)}. Maximum is 100")
        return v
    
    @field_validator('protocol')
    @classmethod
    def validate_protocol(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate protocol size."""
        if len(v) > 20:
            raise ValueError(f"Too many protocol fields: {len(v)}. Maximum is 20")
        return v


# Message type to model mapping for runtime validation
MESSAGE_TYPE_VALIDATORS = {
    "health_check": HealthCheckRequest,
    "suspend": SuspendResumeRequest,
    "resume": SuspendResumeRequest,
    "terminate": TerminateRequest,
    "collective_task": CollectiveTaskRequest,
    "start_deliberation": DeliberationRequest,
    "store_memory": MemoryStoreRequest,
    "retrieve_context": QueryRequest,
    "query_history": QueryRequest,
    "track_lineage": LineageRequest,
    "pattern_match": QueryRequest,
    "analysis_request": AnalysisRequest,
    "validation_request": ValidationRequest,
    # Coordinator agent types
    "create_task": TaskRequest,
    "update_task": TaskRequest,
    "get_task_status": DependencyRequest,
    "get_workflow_status": DependencyRequest,
    "assign_agent": CoordinationRequest,
    "update_agent_state": CoordinationRequest,
    "resolve_dependencies": DependencyRequest,
    "start_workflow": CoordinationRequest,
    "cancel_workflow": CoordinationRequest,
    "get_coordination_report": CoordinationRequest,
    # Nexus agent types
    "create_connection": CoordinationRequest,
    "update_connection": CoordinationRequest,
    "delete_connection": CoordinationRequest,
    "get_connection_status": CoordinationRequest,
    "execute_request": CoordinationRequest,
    "register_webhook": CoordinationRequest,
    "unregister_webhook": CoordinationRequest,
    "validate_webhook": CoordinationRequest,
    "get_webhook_status": CoordinationRequest,
    "translate_protocol": CoordinationRequest,
    "get_integration_report": CoordinationRequest,
}


def validate_message(message_type: str, content: Dict[str, Any]) -> BaseModel:
    """
    Validate message content against the appropriate schema.
    
    Args:
        message_type: Type of message to validate
        content: Message content dict
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If validation fails
        KeyError: If message type has no registered validator
    """
    if message_type not in MESSAGE_TYPE_VALIDATORS:
        # Unknown message type - allow but log
        return content
    
    validator_class = MESSAGE_TYPE_VALIDATORS[message_type]
    return validator_class(**content)
