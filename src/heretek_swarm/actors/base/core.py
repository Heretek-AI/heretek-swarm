"""
Core module for AgentActor base class.

This module contains:
- ActorState enum
- ActorMessage dataclass
- ActorStatus dataclass
- AgentActor core initialization and lifecycle methods
"""

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog
from pydantic import ValidationError
from swarms import Agent

import heretek_swarm.actors.stubs as _actor_stubs
from heretek_swarm.actors.stubs import get_db_pool  # noqa: F401 - imported for test patching
from heretek_swarm.actors.validation import (
    validate_message,
)
from heretek_swarm.state.repository import (
    AgentStateRecord,
    StateRepository,
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("AgentActor")


class ActorState(Enum):
    """Actor lifecycle states."""

    SPAWNING = "spawning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class ActorMessage:
    """
    Internal message structure for actor mailbox.

    Attributes:
        sender: ID of the sending actor
        message_type: Type identifier for the message
        content: Message payload
        timestamp: ISO8601 timestamp
        correlation_id: Optional correlation ID for request-response patterns
        reply_to: Optional topic for responses
        metadata: Additional metadata
    """

    sender: str
    message_type: str
    content: dict[str, Any]
    timestamp: str
    correlation_id: str | None = None
    reply_to: str | None = None
    recipient: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActorStatus:
    """
    Actor status information.

    Attributes:
        agent_id: Unique actor identifier
        state: Current lifecycle state
        message_count: Total messages processed
        created_at: Creation timestamp
        topics: Subscribed topics
        capabilities: Actor capabilities
        mailbox_size: Current mailbox queue size
        last_activity: Last activity timestamp
        error_count: Number of errors encountered
    """

    agent_id: str
    state: ActorState
    message_count: int
    created_at: str
    topics: list[str]
    capabilities: list[str]
    mailbox_size: int
    last_activity: str | None = None
    error_count: int = 0


class AgentActor:
    """
    Base class for all actors in the Heretek Swarm system.

    This class implements the actor model pattern with:
    - Message passing via immutable messages
    - State isolation per actor
    - Mailbox-based sequential message processing
    - Integration with Swarms Agent for LLM capabilities

    Example:
        ```python
        class MyCustomAgent(AgentActor):
            async def process_message(self, message: ActorMessage) -> None:
                if message.message_type == "request":
                    response = await self.handle_request(message.content)
                    await self.send(message.reply_to, response)

            async def handle_request(self, content: Dict) -> Dict:
                # Custom logic here
                return {"result": "success"}

        # Usage
        actor = MyCustomAgent(
            agent_id="my-agent-1",
            name="My Custom Agent",
            topics=["requests", "responses"]
        )
        await actor.spawn()
        ```
    """

    # Class-level actor type identifier
    actor_type: str = "AgentActor"

    @classmethod
    def get_actor_type(cls) -> str:
        """
        Get the actor type identifier.

        Returns:
            Actor type string
        """
        return cls.actor_type

    def __init__(
        self,
        agent_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        topics: list[str] | None = None,
        capabilities: list[str] | None = None,
        swarms_agent: Agent | None = None,
        max_mailbox_size: int = 1000,
        heartbeat_interval: float = 10.0,
        actor_type: str | None = None,
        state_repository: StateRepository | None = None,
        load_state_on_init: bool = True,
        persistence_interval: int | None = None,  # P0-1: Continuous persistence
        **kwargs: Any,  # Accept additional kwargs for forward compatibility
    ) -> None:
        """
        Initialize an actor.

        Args:
            agent_id: Unique identifier for the actor (auto-generated if None)
            name: Human-readable name for the actor
            description: Actor description
            topics: Topics to subscribe to
            capabilities: Actor capabilities list
            swarms_agent: Optional Swarms Agent instance for LLM capabilities
            max_mailbox_size: Maximum mailbox queue size
            heartbeat_interval: Interval between heartbeats in seconds
            actor_type: Optional type identifier for factory registration
            state_repository: Optional state persistence repository
            load_state_on_init: Whether to load state from DB on initialization
            persistence_interval: Optional interval (in messages) for auto-persistence.
                                  If None, only persists on terminate (legacy behavior).
                                  Recommended: 10-100 for production use.
        """
        # P1-7: Configuration validation
        if max_mailbox_size <= 0:
            raise ValueError("max_mailbox_size must be positive")
        if heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be positive")

        # P1-10a fix: Use full 128-bit uuid for agent_id instead of truncated 32-bit
        self.agent_id = agent_id or f"actor_{uuid.uuid4().hex}"
        self.name = name or self.__class__.__name__
        self.description = description or f"Actor: {self.name}"
        self.topics = topics or []
        self.capabilities = capabilities or []
        self.swarms_agent = swarms_agent
        self.max_mailbox_size = max_mailbox_size
        self.heartbeat_interval = heartbeat_interval
        self.actor_type = actor_type or self.__class__.__name__

        # State persistence
        self._state_repository: StateRepository | None = state_repository
        self._state_record: AgentStateRecord | None = None
        self._load_state_on_init = load_state_on_init
        self._persistence_interval = persistence_interval  # P0-1: Continuous persistence
        self._messages_since_persist = 0  # P0-1: Track messages for auto-persist

        # Actor state
        self.state: ActorState = ActorState.SPAWNING
        self.mailbox: asyncio.Queue = asyncio.Queue(maxsize=max_mailbox_size)
        self.internal_state: dict[str, Any] = {}
        self.message_count = 0
        self.error_count = 0
        self.created_at = datetime.now(UTC).isoformat()
        self.last_activity: str | None = None

        # Processing tasks
        self._processing_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._running = False

        # LLM and event mesh providers (injectable via stubs for testing)
        self._llm_provider = _actor_stubs.get_llm_provider()
        self._event_mesh = _actor_stubs.get_nats_event_mesh()

        # Message handlers registry
        self._message_handlers: dict[str, Callable] = {}
        self._register_default_handlers()

        logger.info(
            f"[{self.agent_id}] Actor initialized",
            extra={
                "name": self.name,
                "topics": self.topics,
                "capabilities": self.capabilities,
            },
        )

    @property
    def is_alive(self) -> bool:
        """Return True if the actor is in ACTIVE state."""
        return self.state == ActorState.ACTIVE

    async def initialize(self) -> None:
        """Initialize the actor. Override in subclass for custom setup."""

    async def cleanup(self) -> None:
        """Cleanup actor resources. Override in subclass for custom teardown."""
        # Drain the mailbox
        while not self.mailbox.empty():
            try:
                self.mailbox.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Clear internal state
        self.internal_state.clear()

        # Clear message handlers (no re-registration of defaults per test contract)
        self._message_handlers.clear()

        logger.info(f"[{self.agent_id}] Actor cleanup complete")

    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.register_handler("health_check", self._handle_health_check)
        self.register_handler("suspend", self._handle_suspend)
        self.register_handler("resume", self._handle_resume)
        self.register_handler("terminate", self._handle_terminate)
        self.register_handler("collective_task", self._handle_collective_task)

    def _validate_message_content(self, message_type: str, content: dict[str, Any]) -> Any | None:
        """
        Validate message content using Pydantic models.

        Args:
            message_type: Type of message to validate
            content: Message content dict

        Returns:
            Validated model instance or None if validation not available

        Raises:
            ValueError: If validation fails
        """
        try:
            return validate_message(message_type, content)
        except ValidationError as e:
            logger.warning(
                f"[{self.agent_id}] Message validation failed for {message_type}: {e}",
                extra={"validation_errors": e.errors()},
            )
            raise ValueError(f"Invalid message format: {e.errors()}")
        except KeyError:
            # Unknown message type - skip validation
            logger.debug(f"[{self.agent_id}] No validator for message type: {message_type}")
            return None

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a message handler for a specific message type.

        Args:
            message_type: Type of message to handle
            handler: Async handler function
        """
        self._message_handlers[message_type] = handler
        logger.debug(
            f"[{self.agent_id}] Registered handler for {message_type}",
        )

    def unregister_handler(self, message_type: str) -> None:
        """
        Unregister a message handler for a specific message type.

        Args:
            message_type: Type of message to unregister
        """
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]
            logger.debug(
                f"[{self.agent_id}] Unregistered handler for {message_type}",
            )

    async def spawn(self) -> None:
        """
        Spawn the actor and start processing messages.

        This method:
        1. Sets actor state to ACTIVE
        2. Starts mailbox processing loop
        3. Starts heartbeat loop
        4. Calls initialize() hook for subclass setup
        5. Loads state from database if configured
        """
        # P1-6: Idempotency check - prevent multiple spawns
        if self._running:
            logger.warning(f"[{self.agent_id}] Already running, ignoring spawn request")
            return

        try:
            logger.info(
                f"[{self.agent_id}] Agent spawned: {self.name}",
                extra={"state": self.state.value},
            )

            self._running = True
            self.state = ActorState.ACTIVE

            # Load state from database if configured
            if self._load_state_on_init:
                await self.load_state()

            # Start processing tasks
            self._processing_task = asyncio.create_task(self._process_mailbox())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Call initialization hook
            await self.initialize()

            logger.info(
                f"[{self.agent_id}] Actor spawn complete",
                extra={"mailbox_size": self.mailbox.qsize()},
            )
        except Exception as e:
            logger.error(f"[{self.agent_id}] Spawn failed: {e}", exc_info=True)
            self.state = ActorState.ERROR
            self.error_count += 1
            raise

    async def terminate(self) -> None:
        """
        Terminate the actor and cleanup resources.

        This method:
        1. Sets actor state to TERMINATED
        2. Cancels processing tasks
        3. Calls cleanup() hook for subclass teardown
        4. Saves final state
        """
        try:
            logger.info(f"[{self.agent_id}] Agent terminating...")

            self._running = False
            # P1-10c fix: Set state to TERMINATED AFTER cleanup completes, not before
            # First cancel all tasks
            await self._cancel_tasks()

            # Save final state
            await self.save_state()

            # Call cleanup hook
            await self.cleanup()

            # Now set state to TERMINATED after all cleanup is complete
            self.state = ActorState.TERMINATED

            logger.info(f"[{self.agent_id}] Agent terminated")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Terminate failed: {e}", exc_info=True)
            self.state = ActorState.ERROR
            raise

    async def _cancel_tasks(self) -> None:
        """Cancel all running tasks with comprehensive exception handling."""
        tasks_to_cancel = []

        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            tasks_to_cancel.append(self._processing_task)

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            tasks_to_cancel.append(self._heartbeat_task)

        if tasks_to_cancel:
            try:
                # P1-10d fix: Catch all exceptions, not just CancelledError
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            except asyncio.CancelledError:
                # Expected during task cancellation
                pass
            except Exception as e:
                # P1-10d fix: Log any other exceptions during task cancellation
                logger.error(f"[{self.agent_id}] Error during task cancellation: {e}", exc_info=True)


# Trigger mixin bindings when this module is imported
from heretek_swarm.actors.base.message_handling import (
    AgentActorMessageHandling,  # noqa: F401 - triggers mixin injection
)
from heretek_swarm.actors.base.state_management import (
    AgentActorStateManagement,  # noqa: F401 - triggers state management bindings
)
