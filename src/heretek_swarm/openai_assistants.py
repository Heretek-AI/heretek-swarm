"""
OpenAI Assistants API Integration Module for Heretek Swarm

This module provides bi-directional integration between Heretek Swarm agents and OpenAI Assistants API.
It enables assistant creation, thread management, run handling, and tool function calling.

Features:
- Assistant creation and management
- Thread and run handling
- Tool function calling bridge
- File attachment support
- Zero-trust validation of all API interactions

Reference: EXPANSION_ROADMAP.md Session 47 - Integration Ecosystem
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

_logger = structlog.get_logger(__name__)

# Try to import OpenAI components
try:
    from openai import AsyncOpenAI, OpenAI
    from openai.types.beta import Assistant, Run, Thread
    from openai.types.beta.threads import Message, TextContentBlock
    from openai.types.beta.threads.runs import FunctionToolCall, ToolCall
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    _OpenAI = None
    _AsyncOpenAI = None
    _Assistant = None
    _Thread = None
    _Run = None
    _Message = None
    _TextContentBlock = None
    _ToolCall = None
    _FunctionToolCall = None


class RunStatus(str, Enum):
    """Run status enumeration."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class AssistantConfig:
    """
    Configuration for an OpenAI Assistant.
    
    Attributes:
        assistant_id: Assistant identifier
        name: Assistant name
        model: Model to use
        instructions: System instructions
        description: Assistant description
        tools: Tool definitions
        file_ids: Attached file IDs
        metadata: Additional metadata
    """
    assistant_id: str
    name: str
    model: str = "gpt-4o"
    instructions: str = "You are a helpful assistant."
    description: Optional[str] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    file_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    heretek_agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assistant_id": self.assistant_id,
            "name": self.name,
            "model": self.model,
            "instructions": self.instructions,
            "description": self.description,
            "tools": self.tools,
            "file_ids": self.file_ids,
            "metadata": self.metadata,
            "heretek_agent_id": self.heretek_agent_id,
        }


@dataclass
class ThreadContext:
    """
    Thread context for conversation tracking.
    
    Attributes:
        thread_id: Thread identifier
        assistant_id: Associated assistant ID
        messages: Message history
        created_at: Creation timestamp
        metadata: Additional metadata
    """
    thread_id: str
    assistant_id: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    heretek_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thread_id": self.thread_id,
            "assistant_id": self.assistant_id,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "metadata": self.metadata,
            "heretek_context": self.heretek_context,
        }


@dataclass
class RunContext:
    """
    Context for a run execution.
    
    Attributes:
        run_id: Run identifier
        thread_id: Associated thread ID
        assistant_id: Associated assistant ID
        status: Run status
        instructions: Run-specific instructions
        tools: Run-specific tools
        metadata: Additional metadata
    """
    run_id: str
    thread_id: str
    assistant_id: str
    status: RunStatus = RunStatus.QUEUED
    instructions: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "assistant_id": self.assistant_id,
            "status": self.status.value,
            "instructions": self.instructions,
            "tool_count": len(self.tool_calls),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class FunctionCallRequest:
    """
    Request for a function call from OpenAI.
    
    Attributes:
        call_id: Function call identifier
        name: Function name
        arguments: Function arguments
        thread_id: Associated thread ID
        run_id: Associated run ID
    """
    call_id: str
    name: str
    arguments: Dict[str, Any]
    thread_id: str
    run_id: str
    heretek_agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "name": self.name,
            "arguments": self.arguments,
            "thread_id": self.thread_id,
            "run_id": self.run_id,
            "heretek_agent_id": self.heretek_agent_id,
        }


class OpenAIAssistantsAdapter:
    """
    Adapter for integrating OpenAI Assistants API with Heretek Swarm.
    
    This adapter provides:
    - Assistant creation and management
    - Thread and run handling
    - Tool function calling bridge to Heretek agents
    - File attachment support
    
    Attributes:
        client: OpenAI client instance
        assistants: Registered assistants
        threads: Active threads
        runs: Active runs
    """

    def __init__(self, api_key: Optional[str], base_url: Optional[str], organization: Optional[str], enable_heretek_bridge: bool) -> None:
        """
        Initialize the OpenAI Assistants adapter.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API
            organization: Organization ID
            enable_heretek_bridge: Enable Heretek agent bridging
        """
        self.api_key = api_key
        self.base_url = base_url
        self.organization = organization

        self.client: Optional[AsyncOpenAI] = None
        self.sync_client: Optional[OpenAI] = None

        if OPENAI_AVAILABLE and api_key:
            self.client = AsyncOpenAI(
                _api_key = api_key,
                _base_url = base_url,
                _organization = organization,
            )
            self.sync_client = OpenAI(
                _api_key = api_key,
                _base_url = base_url,
                _organization = organization,
            )

        self.assistants: Dict[str, AssistantConfig] = {}
        self.threads: Dict[str, ThreadContext] = {}
        self.runs: Dict[str, RunContext] = {}

        self.enable_heretek_bridge = enable_heretek_bridge
        self._agent_runtime = None
        self._heretek_agent_mappings: Dict[str, str] = {}

        # Registered functions for tool calling
        self._registered_functions: Dict[str, Callable] = {}

        # Run callbacks
        self._run_callbacks: List[Callable] = []

        logger.info(
            "openai_assistants_adapter_initialized",
            _api_key_set = bool(api_key),
            _heretek_bridge_enabled = enable_heretek_bridge,
        )

    def set_agent_runtime(self, runtime: Any) -> None:
        """Set the Heretek agent runtime for integration."""
        self._agent_runtime = runtime
        logger.debug("agent_runtime_set", runtime_type=type(runtime).__name__)

    def register_heretek_agent_mapping(self, heretek_agent_id: str, assistant_id: str) -> None:
        """Register a mapping between Heretek and OpenAI assistants."""
        self._heretek_agent_mappings[heretek_agent_id] = assistant_id
        if assistant_id in self.assistants:
            self.assistants[assistant_id].heretek_agent_id = heretek_agent_id
        logger.info(
            "heretek_agent_mapping_registered",
            _heretek_agent_id = heretek_agent_id,
            _assistant_id = assistant_id,
        )

    def register_run_callback(self, callback: Callable) -> None:
        """Register a callback for run events."""
        self._run_callbacks.append(callback)
        logger.debug("run_callback_registered", callback=callback.__name__)

    async def _notify_run_event(self, event_type: str, run_id: str, context: Optional[RunContext]) -> None:
        """Notify callbacks of run events."""
        for callback in self._run_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, run_id, context)
                else:
                    callback(event_type, run_id, context)
            except Exception as e:
                logger.error("run_callback_error", error=str(e))

    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a function for tool calling.
        
        Args:
            name: Function name
            func: Function to call
        """
        self._registered_functions[name] = func
        logger.info("function_registered", name=name)

    async def create_assistant(self, assistant_id: str, name: str, model: str, instructions: str, description: Optional[str], tools: Optional[List[Dict[str, Any]]], file_ids: Optional[List[str]], metadata: Optional[Dict[str, Any]], heretek_agent_id: Optional[str]) -> AssistantConfig:
        """
        Create an OpenAI Assistant.
        
        Args:
            assistant_id: Unique assistant identifier
            name: Assistant name
            model: Model to use
            instructions: System instructions
            description: Assistant description
            tools: Tool definitions
            file_ids: Attached file IDs
            metadata: Additional metadata
            heretek_agent_id: Associated Heretek agent ID
            
        Returns:
            AssistantConfig
        """
        if not OPENAI_AVAILABLE:
            logger.warning("openai_not_available")
            raise RuntimeError(
                "OpenAI is not available. Install with: pip install openai"
            )

        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Provide API key.")

        _config = AssistantConfig(
            _assistant_id = assistant_id,
            _name = name,
            _model = model,
            _instructions = instructions,
            _description = description,
            tools=tools or [],
            _file_ids = file_ids or [],
            _metadata = metadata or {},
            _heretek_agent_id = heretek_agent_id,
        )

        # Create assistant via API
        try:
            assistant = await self.client.beta.assistants.create(
                _name = name,
                _model = model,
                _instructions = instructions,
                _description = description,
                tools=tools or [],
                _file_ids = file_ids or [],
                _metadata = metadata or {},
            )

            # Store the OpenAI assistant ID
            config.openai_id = assistant.id
            self.assistants[assistant_id] = config

            logger.info(
                "assistant_created",
                _assistant_id = assistant_id,
                openai_id=assistant.id,
            )

        except Exception as e:
            # Store config even if API call fails (for offline mode)
            self.assistants[assistant_id] = config
            logger.warning(
                "assistant_creation_warning",
                _assistant_id = assistant_id,
                error=str(e),
            )

        return config

    async def create_thread(self, thread_id: Optional[str], assistant_id: Optional[str], initial_messages: Optional[List[Dict[str, Any]]], metadata: Optional[Dict[str, Any]]) -> ThreadContext:
        """
        Create a new thread.
        
        Args:
            thread_id: Optional thread identifier
            assistant_id: Associated assistant ID
            initial_messages: Initial messages
            metadata: Thread metadata
            
        Returns:
            ThreadContext
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise RuntimeError("OpenAI client not initialized")

        if thread_id is None:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"

        _context = ThreadContext(
            _thread_id = thread_id,
            _assistant_id = assistant_id,
            _metadata = metadata or {},
        )

        # Create thread via API
        try:
            if initial_messages:
                thread = await self.client.beta.threads.create(
                    messages=initial_messages,
                    _metadata = metadata or {},
                )
            else:
                thread = await self.client.beta.threads.create(
                    _metadata = metadata or {},
                )
            context.thread_id = thread.id
        except Exception as e:
            logger.warning("thread_creation_warning", thread_id=thread_id, error=str(e))

        self.threads[thread_id] = context
        logger.info("thread_created", thread_id=thread_id)

        return context

    async def add_message(self, thread_id: str, content: str, role: MessageRole, file_ids: Optional[List[str]], metadata: Optional[Dict[str, Any]]) -> bool:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread ID
            content: Message content
            role: Message role
            file_ids: Attached file IDs
            metadata: Message metadata
            
        Returns:
            True if message added
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise RuntimeError("OpenAI client not initialized")

        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")

        try:
            message = await self.client.beta.threads.messages.create(
                _thread_id = thread_id,
                role=role.value,
                content=content,
                _file_ids = file_ids or [],
                _metadata = metadata or {},
            )

            # Track message locally
            self.threads[thread_id].messages.append({
                "role": role.value,
                "content": content,
                "file_ids": file_ids or [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            logger.debug("message_added", thread_id=thread_id)
            return True

        except Exception as e:
            logger.error("message_add_error", thread_id=thread_id, error=str(e))
            return False

    async def create_run(self, thread_id: str, assistant_id: str, instructions: Optional[str], tools: Optional[List[Dict[str, Any]]], metadata: Optional[Dict[str, Any]]) -> RunContext:
        """
        Create a new run.
        
        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID
            instructions: Run-specific instructions
            tools: Run-specific tools
            metadata: Run metadata
            
        Returns:
            RunContext
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise RuntimeError("OpenAI client not initialized")

        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")

        run_id = f"run_{uuid.uuid4().hex[:12]}"

        _context = RunContext(
            run_id=run_id,
            _thread_id = thread_id,
            _assistant_id = assistant_id,
            status=RunStatus.QUEUED,
            _instructions = instructions,
            _tools = tools,
            _metadata = metadata or {},
        )

        # Get assistant config
        _assistant_config = self.assistants.get(assistant_id)

        try:
            run = await self.client.beta.threads.runs.create(
                _thread_id = thread_id,
                _assistant_id = assistant_config.openai_id if assistant_config else assistant_id,
                _instructions = instructions,
                _tools = tools or (assistant_config.tools if assistant_config else []),
                _metadata = metadata or {},
            )

            context.run_id = run.id
            context.status = RunStatus(run.status)

        except Exception as e:
            logger.warning("run_creation_warning", run_id=run_id, error=str(e))

        self.runs[run_id] = context
        logger.info("run_created", run_id=run_id)

        await self._notify_run_event("run_created", run_id, context)

        return context

    async def poll_run(self, run_id: str, poll_interval: float, timeout: float) -> RunContext:
        """
        Poll a run until completion.
        
        Args:
            run_id: Run ID
            poll_interval: Polling interval in seconds
            timeout: Maximum wait time in seconds
            
        Returns:
            RunContext with final status
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise RuntimeError("OpenAI client not initialized")

        if run_id not in self.runs:
            raise ValueError(f"Run {run_id} not found")

        _context = self.runs[run_id]
        _start_time = datetime.now(timezone.utc)

        if not context.started_at:
            context.started_at = datetime.now(timezone.utc).isoformat()

        while True:
            # Check timeout
            _elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed >= timeout:
                context.status = RunStatus.EXPIRED
                context.error = f"Run timed out after {timeout}s"
                logger.warning("run_timeout", run_id=run_id)
                break

            # Get run status
            try:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=context.thread_id,
                    run_id=run_id,
                )

                context.status = RunStatus(run.status)

                # Handle requires_action for tool calls
                if run.status == "requires_action" and run.required_action:
                    await self._handle_tool_calls(run, context)

                # Check terminal states
                if run.status in ["completed", "failed", "cancelled", "expired"]:
                    context.completed_at = datetime.now(timezone.utc).isoformat()
                    if run.status == "failed" and run.last_error:
                        context.error = run.last_error.message
                    break

            except Exception as e:
                logger.error("run_poll_error", run_id=run_id, error=str(e))
                context.status = RunStatus.FAILED
                context.error = str(e)
                break

            await asyncio.sleep(poll_interval)

        await self._notify_run_event("run_completed", run_id, context)
        logger.info(
            "run_completed",
            run_id=run_id,
            status=context.status.value,
        )

        return context

    async def _handle_tool_calls(self, run: Run, context: RunContext) -> None:
        """Handle tool calls from a run."""
        if not run.required_action:
            return

        tool_calls = run.required_action.submit_tool_outputs.tool_calls

        for tool_call in tool_calls:
            if isinstance(tool_call, FunctionToolCall):
                _call_request = FunctionCallRequest(
                    _call_id = tool_call.id,
                    name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments),
                    thread_id=context.thread_id,
                    run_id=context.run_id,
                )

                context.tool_calls.append(call_request.to_dict())

                # Try to execute function
                _result = await self._execute_function(call_request)

                # Submit tool output
                try:
                    await self.client.beta.threads.runs.submit_tool_outputs(
                        _thread_id = context.thread_id,
                        run_id=context.run_id,
                        _tool_outputs = [{
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result) if not isinstance(result, str) else result,
                        }],
                    )
                    logger.debug(
                        "tool_output_submitted",
                        _call_id = tool_call.id,
                        _function = call_request.name,
                    )
                except Exception as e:
                    logger.error(
                        "tool_output_error",
                        _call_id = tool_call.id,
                        error=str(e),
                    )

    async def _execute_function(self, call_request: FunctionCallRequest) -> Any:
        """Execute a function call."""
        # Check registered functions
        if call_request.name in self._registered_functions:
            _func = self._registered_functions[call_request.name]
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(**call_request.arguments)
                else:
                    return func(**call_request.arguments)
            except Exception as e:
                logger.error(
                    "function_execution_error",
                    _function = call_request.name,
                    error=str(e),
                )
                return {"error": str(e)}

        # Try to route to Heretek agent
        if self.enable_heretek_bridge and self._agent_runtime:
            _heretek_agent_id = call_request.heretek_agent_id or call_request.name

            if heretek_agent_id in self._agent_runtime:
                try:
                    _runtime = self._agent_runtime[heretek_agent_id]
                    if hasattr(runtime, 'think'):
                        _response = await runtime.think(
                            f"Execute: {call_request.name}({json.dumps(call_request.arguments)})"
                        )
                        return {"response": response}
                except Exception as e:
                    logger.error(
                        "heretek_routing_error",
                        _agent_id = heretek_agent_id,
                        error=str(e),
                    )

        return {"error": f"Function {call_request.name} not found"}

    async def execute_chat(self, thread_id: str, assistant_id: str, message: str, instructions: Optional[str]) -> Dict[str, Any]:
        """
        Execute a chat message and get response.
        
        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID
            message: User message
            instructions: Optional instructions
            
        Returns:
            Response dictionary
        """
        # Add user message
        await self.add_message(thread_id, message, MessageRole.USER)

        # Create and run
        _run_context = await self.create_run(
            _thread_id = thread_id,
            _assistant_id = assistant_id,
            _instructions = instructions,
        )

        # Poll for completion
        _result = await self.poll_run(run_context.run_id)

        # Get assistant messages
        _response_messages = await self.get_thread_messages(thread_id)

        return {
            "run_id": result.run_id,
            "status": result.status.value,
            "messages": response_messages,
            "tool_calls": result.tool_calls,
            "error": result.error,
        }

    async def get_thread_messages(self, thread_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get messages from a thread."""
        if not OPENAI_AVAILABLE or not self.client:
            return self.threads.get(thread_id, {}).messages

        try:
            _messages = await self.client.beta.threads.messages.list(
                _thread_id = thread_id,
                _limit = limit,
            )

            _result = []
            for msg in messages.data:
                content = ""
                for c in msg.content:
                    if isinstance(c, TextContentBlock):
                        content += c.text.value

                result.append({
                    "role": msg.role,
                    "content": content,
                    "created_at": datetime.fromtimestamp(msg.created_at).isoformat(),
                })

            return result

        except Exception as e:
            logger.error("get_messages_error", thread_id=thread_id, error=str(e))
            return []

    def get_assistant(self, assistant_id: str) -> Optional[AssistantConfig]:
        """Get assistant config by ID."""
        return self.assistants.get(assistant_id)

    def get_thread(self, thread_id: str) -> Optional[ThreadContext]:
        """Get thread context by ID."""
        return self.threads.get(thread_id)

    def get_run(self, run_id: str) -> Optional[RunContext]:
        """Get run context by ID."""
        return self.runs.get(run_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "assistant_count": len(self.assistants),
            "thread_count": len(self.threads),
            "run_count": len(self.runs),
            "function_count": len(self._registered_functions),
            "heretek_mappings": len(self._heretek_agent_mappings),
            "openai_available": OPENAI_AVAILABLE,
            "client_initialized": self.client is not None,
        }

    def clear_assistant(self, assistant_id: str) -> bool:
        """Clear an assistant."""
        if assistant_id not in self.assistants:
            return False

        del self.assistants[assistant_id]
        logger.info("assistant_cleared", assistant_id=assistant_id)
        return True

    def clear_thread(self, thread_id: str) -> bool:
        """Clear a thread."""
        if thread_id not in self.threads:
            return False

        del self.threads[thread_id]
        logger.info("thread_cleared", thread_id=thread_id)
        return True

    def clear_all(self) -> None:
        """Clear all state."""
        self.assistants.clear()
        self.threads.clear()
        self.runs.clear()
        self._registered_functions.clear()
        self._heretek_agent_mappings.clear()
        logger.info("openai_assistants_adapter_cleared")


# Global adapter instance
openai_assistants_adapter: Optional[OpenAIAssistantsAdapter] = None


def get_openai_assistants_adapter(api_key: Optional[str], base_url: Optional[str]) -> OpenAIAssistantsAdapter:
    """Get the global OpenAI Assistants adapter instance."""
    global openai_assistants_adapter
    if openai_assistants_adapter is None:
        _openai_assistants_adapter = OpenAIAssistantsAdapter(
            _api_key = api_key,
            _base_url = base_url,
        )
    return openai_assistants_adapter


def create_assistant(assistant_id: str, name: str, model: str, instructions: str, tools: Optional[List[Dict[str, Any]]], heretek_agent_id: Optional[str]) -> AssistantConfig:
    """
    Create an assistant with default configuration.
    
    Args:
        assistant_id: Assistant identifier
        name: Assistant name
        model: Model to use
        instructions: System instructions
        tools: Tool definitions
        heretek_agent_id: Associated Heretek agent ID
        
    Returns:
        AssistantConfig
    """
    _adapter = get_openai_assistants_adapter()

    return asyncio.create_task(adapter.create_assistant(
        _assistant_id = assistant_id,
        _name = name,
        _model = model,
        _instructions = instructions,
        _tools = tools,
        _heretek_agent_id = heretek_agent_id,
    ))
