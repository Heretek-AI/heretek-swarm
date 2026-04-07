"""
Base Tool Architecture for Heretek Swarm

Provides the foundation for Python-native Swarms tools with:
- Type-safe inputs/outputs via Pydantic
- Automatic validation
- Structured error handling
- Performance monitoring
- Observability hooks
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field, ValidationError

logger = structlog.get_logger()

# Type variables for generic tool inputs/outputs
TInput = TypeVar('TInput', bound=BaseModel)
TOutput = TypeVar('TOutput', bound=BaseModel)


class ToolStatus(str, Enum):
    """Tool execution status"""
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class ToolMetadata(BaseModel):
    """Metadata for tool registration and discovery"""
    
    # Identity
    tool_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, description="Unique tool name")
    version: str = Field(default="1.0.0", description="Tool version")
    
    # Description
    description: str = Field(..., min_length=1, description="Tool description")
    category: str = Field(default="general", description="Tool category")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    
    # Authorship
    author: Optional[str] = Field(None, description="Tool author")
    source: Optional[str] = Field(None, description="Source repository")
    
    # Capabilities
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for inputs")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for outputs")
    
    # Requirements
    requires_memory: bool = Field(default=False, description="Requires memory access")
    requires_state: bool = Field(default=False, description="Requires state management")
    external_dependencies: List[str] = Field(default_factory=list)
    
    # Performance
    timeout_seconds: float = Field(default=30.0, ge=1.0)
    max_concurrent: int = Field(default=10, ge=1)
    
    # Status
    status: ToolStatus = Field(default=ToolStatus.READY)
    enabled: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = Field(None)
    
    # Metrics
    total_executions: int = Field(default=0, ge=0)
    successful_executions: int = Field(default=0, ge=0)
    failed_executions: int = Field(default=0, ge=0)
    avg_execution_time_ms: float = Field(default=0.0, ge=0)


class ToolExecutionResult(BaseModel, Generic[TOutput]):
    """Result from tool execution"""
    
    # Execution info
    execution_id: UUID = Field(default_factory=uuid4)
    tool_id: UUID = Field(...)
    tool_name: str = Field(...)
    
    # Status
    status: ToolStatus = Field(...)
    error: Optional[str] = Field(None)
    error_details: Optional[Dict[str, Any]] = Field(None)
    
    # Output - use Any to allow primitive types, TOutput is for type hints only
    output: Optional[Any] = Field(None)
    raw_output: Optional[Any] = Field(None)
    
    # Performance
    execution_time_ms: float = Field(..., ge=0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context
    input_data: Optional[Dict[str, Any]] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ToolContext(BaseModel):
    """Context passed to tool during execution"""
    
    # Agent context
    agent_id: str = Field(..., description="Executing agent ID")
    session_id: Optional[UUID] = Field(None, description="Session ID")
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID")
    
    # Memory access
    memory_enabled: bool = Field(default=False)
    state_enabled: bool = Field(default=False)
    
    # Execution context
    request_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Security
    permissions: List[str] = Field(default_factory=list)


class BaseTool(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for all Heretek Swarm tools.
    
    Provides:
    - Type-safe input/output validation
    - Execution monitoring
    - Error handling
    - Performance tracking
    - Observability hooks
    
    Usage:
        class MyTool(BaseTool[MyInput, MyOutput]):
            def __init__(self):
                super().__init__(
                    name="my_tool",
                    description="Does something useful",
                    category="utility"
                )
            
            async def execute(self, input_data: MyInput, context: ToolContext) -> MyOutput:
                # Implementation
                return MyOutput(result="success")
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
        timeout_seconds: float = 30.0,
        requires_memory: bool = False,
        requires_state: bool = False
    ):
        self.metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            version=version,
            timeout_seconds=timeout_seconds,
            requires_memory=requires_memory,
            requires_state=requires_state
        )
        
        # Execution tracking
        self._execution_count = 0
        self._total_time_ms = 0.0
        self._errors = 0
        
        logger.debug(
            "tool_initialized",
            tool_name=name,
            category=category
        )
    
    @abstractmethod
    async def execute(
        self,
        input_data: TInput,
        context: ToolContext
    ) -> TOutput:
        """
        Execute the tool with validated input.
        
        Args:
            input_data: Validated input data
            context: Execution context
        
        Returns:
            Tool output
        
        Raises:
            ToolExecutionError: If execution fails
        """
        pass
    
    async def run(
        self,
        input_data: Dict[str, Any],
        context: Optional[ToolContext] = None
    ) -> ToolExecutionResult:
        """
        Run the tool with input validation and monitoring.
        
        Args:
            input_data: Raw input data
            context: Optional execution context
        
        Returns:
            Execution result with status and output
        """
        start_time = datetime.now(timezone.utc)
        execution_id = uuid4()
        
        # Create default context if not provided
        if context is None:
            context = ToolContext(agent_id="system")
        
        # Validate input
        try:
            validated_input = await self._validate_input(input_data)
        except ValidationError as e:
            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.metadata.tool_id,
                tool_name=self.metadata.name,
                status=ToolStatus.FAILED,
                error=f"Input validation failed: {str(e)}",
                execution_time_ms=0,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                input_data=input_data
            )
        
        # Check if tool is enabled
        if not self.metadata.enabled:
            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.metadata.tool_id,
                tool_name=self.metadata.name,
                status=ToolStatus.DISABLED,
                error="Tool is disabled",
                execution_time_ms=0,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                input_data=input_data
            )
        
        # Execute with timeout
        try:
            import asyncio
            
            # Create execution coroutine
            async def execute_with_timeout():
                return await self.execute(validated_input, context)
            
            # Execute with timeout
            output = await asyncio.wait_for(
                execute_with_timeout(),
                timeout=self.metadata.timeout_seconds
            )
            
            # Calculate execution time
            execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Update metrics
            self._execution_count += 1
            self._total_time_ms += execution_time_ms
            self.metadata.total_executions += 1
            self.metadata.successful_executions += 1
            self.metadata.avg_execution_time_ms = (
                self._total_time_ms / self._execution_count
            )
            self.metadata.last_used_at = datetime.now(timezone.utc)
            
            # Log success
            logger.info(
                "tool_execution_success",
                tool_name=self.metadata.name,
                execution_id=str(execution_id),
                execution_time_ms=execution_time_ms
            )
            
            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.metadata.tool_id,
                tool_name=self.metadata.name,
                status=ToolStatus.COMPLETED,
                output=output,
                execution_time_ms=execution_time_ms,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                input_data=input_data
            )
        
        except asyncio.TimeoutError:
            self._errors += 1
            self.metadata.failed_executions += 1
            
            logger.warning(
                "tool_execution_timeout",
                tool_name=self.metadata.name,
                timeout=self.metadata.timeout_seconds
            )
            
            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.metadata.tool_id,
                tool_name=self.metadata.name,
                status=ToolStatus.FAILED,
                error=f"Execution timeout after {self.metadata.timeout_seconds}s",
                execution_time_ms=self.metadata.timeout_seconds * 1000,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                input_data=input_data
            )
        
        except Exception as e:
            self._errors += 1
            self.metadata.failed_executions += 1
            
            logger.error(
                "tool_execution_error",
                tool_name=self.metadata.name,
                execution_id=str(execution_id),
                error=str(e)
            )
            
            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.metadata.tool_id,
                tool_name=self.metadata.name,
                status=ToolStatus.FAILED,
                error=str(e),
                error_details={"type": type(e).__name__},
                execution_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                input_data=input_data
            )
    
    async def _validate_input(self, input_data: Dict[str, Any]) -> TInput:
        """
        Validate input data against expected schema.
        
        Override this method for custom validation logic.
        
        Note: We use type hints and __orig_bases__ instead of __orig_class__
        because __orig_class__ is not available at runtime in Python 3.13+
        """
        # Try to get input type from generic type parameters
        # Fall back to a safe default if we can't determine the type
        input_type: Optional[type] = None
        
        # Try __orig_bases__ for generic type info
        if hasattr(self, '__orig_bases__') and self.__orig_bases__:
            for base in self.__orig_bases__:
                if hasattr(base, '__args__') and base.__args__:
                    potential_type = base.__args__[0]
                    # Ensure it's actually a type before using
                    if isinstance(potential_type, type):
                        input_type = potential_type
                        break
        
        # If we couldn't determine the type, return input as-is
        if input_type is None:
            return input_data  # type: ignore
        
        # Only try issubclass if we have a valid type
        try:
            if issubclass(input_type, BaseModel):
                return input_type(**input_data)
        except (TypeError, AttributeError):
            # If issubclass fails, return as dict
            pass
        
        # If not a Pydantic model, return as dict
        return input_data  # type: ignore
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata"""
        return self.metadata
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "tool_id": str(self.metadata.tool_id),
            "name": self.metadata.name,
            "total_executions": self._execution_count,
            "successful_executions": self.metadata.successful_executions,
            "failed_executions": self.metadata.failed_executions,
            "avg_execution_time_ms": self.metadata.avg_execution_time_ms,
            "success_rate": (
                self.metadata.successful_executions / self._execution_count
                if self._execution_count > 0 else 0
            ),
            "enabled": self.metadata.enabled,
            "status": self.metadata.status.value
        }
    
    def enable(self) -> None:
        """Enable the tool"""
        self.metadata.enabled = True
        self.metadata.status = ToolStatus.READY
        logger.info("tool_enabled", tool_name=self.metadata.name)
    
    def disable(self) -> None:
        """Disable the tool"""
        self.metadata.enabled = False
        self.metadata.status = ToolStatus.DISABLED
        logger.info("tool_disabled", tool_name=self.metadata.name)


class ToolExecutionError(Exception):
    """Custom exception for tool execution errors"""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        execution_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.tool_name = tool_name
        self.execution_id = execution_id
        self.details = details or {}


class SimpleTool(BaseTool[Dict[str, Any], Dict[str, Any]]):
    """
    Simplified tool for quick prototyping.
    
    Use when you don't need strict input/output typing.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func,
        category: str = "general",
        tags: Optional[List[str]] = None,
        timeout_seconds: float = 30.0
    ):
        super().__init__(
            name=name,
            description=description,
            category=category,
            tags=tags,
            timeout_seconds=timeout_seconds
        )
        self._func = func
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Execute the wrapped function"""
        import asyncio
        
        # Check if function is async
        if asyncio.iscoroutinefunction(self._func):
            return await self._func(**input_data)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._func(**input_data)
            )
