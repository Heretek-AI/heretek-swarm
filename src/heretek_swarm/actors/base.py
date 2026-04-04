"""
AgentActor - Base class for all actors in the Heretek Swarm system.

This module provides the foundational actor implementation with:
- Asynchronous mailbox for message processing
- State management with persistence
- Actor lifecycle (spawn, process, terminate)
- Message routing and handling
- Integration with Swarms framework
"""

import asyncio
import logging
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from swarms import Agent

# Configure structured logging
import structlog

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
    content: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    topics: List[str]
    capabilities: List[str]
    mailbox_size: int
    last_activity: Optional[str] = None
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

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        swarms_agent: Optional[Agent] = None,
        max_mailbox_size: int = 1000,
        heartbeat_interval: float = 10.0,
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
        """
        self.agent_id = agent_id or f"actor_{uuid.uuid4().hex[:8]}"
        self.name = name or self.__class__.__name__
        self.description = description or f"Actor: {self.name}"
        self.topics = topics or []
        self.capabilities = capabilities or []
        self.swarms_agent = swarms_agent
        self.max_mailbox_size = max_mailbox_size
        self.heartbeat_interval = heartbeat_interval

        # Actor state
        self.state: ActorState = ActorState.SPAWNING
        self.mailbox: asyncio.Queue = asyncio.Queue(maxsize=max_mailbox_size)
        self.internal_state: Dict[str, Any] = {}
        self.message_count = 0
        self.error_count = 0
        self.created_at = datetime.utcnow().isoformat()
        self.last_activity: Optional[str] = None

        # Processing tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

        # Message handlers registry
        self._message_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

        logger.info(
            f"[{self.agent_id}] Actor initialized",
            extra={
                "name": self.name,
                "topics": self.topics,
                "capabilities": self.capabilities,
            },
        )

    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.register_handler("health_check", self._handle_health_check)
        self.register_handler("suspend", self._handle_suspend)
        self.register_handler("resume", self._handle_resume)
        self.register_handler("terminate", self._handle_terminate)

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

    async def spawn(self) -> None:
        """
        Spawn the actor and start processing messages.

        This method:
        1. Sets actor state to ACTIVE
        2. Starts mailbox processing loop
        3. Starts heartbeat loop
        4. Calls initialize() hook for subclass setup
        """
        logger.info(
            f"[{self.agent_id}] Agent spawned: {self.name}",
            extra={"state": self.state.value},
        )

        self._running = True
        self.state = ActorState.ACTIVE

        # Start processing tasks
        self._processing_task = asyncio.create_task(self._process_mailbox())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Call initialization hook
        await self.initialize()

        logger.info(
            f"[{self.agent_id}] Actor spawn complete",
            extra={"mailbox_size": self.mailbox.qsize()},
        )

    async def terminate(self) -> None:
        """
        Terminate the actor and cleanup resources.

        This method:
        1. Sets actor state to TERMINATED
        2. Cancels processing tasks
        3. Calls cleanup() hook for subclass teardown
        4. Saves final state
        """
        logger.info(f"[{self.agent_id}] Agent terminating...")

        self._running = False
        self.state = ActorState.TERMINATED

        # Cancel tasks
        await self._cancel_tasks()

        # Save final state
        await self.save_state()

        # Call cleanup hook
        await self.cleanup()

        logger.info(f"[{self.agent_id}] Agent terminated")

    async def _cancel_tasks(self) -> None:
        """Cancel all running tasks."""
        tasks_to_cancel = []

        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            tasks_to_cancel.append(self._processing_task)

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            tasks_to_cancel.append(self._heartbeat_task)

        if tasks_to_cancel:
            try:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    async def send(
        self,
        topic: str,
        content: Dict[str, Any],
        message_type: str = "default",
        reply_to: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send a message to a topic.

        Args:
            topic: Target topic
            content: Message content
            message_type: Type identifier for the message
            reply_to: Optional topic for responses
            correlation_id: Optional correlation ID
            metadata: Additional metadata

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        message = ActorMessage(
            sender=self.agent_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id,
            reply_to=reply_to,
            metadata=metadata or {},
        )

        # In a full implementation, this would route through event mesh
        # For now, log the message send
        logger.debug(
            f"[{self.agent_id}] Sent message {message_id} to {topic}",
            extra={"message_type": message_type},
        )

        return message_id

    async def send_to_actor(
        self,
        target_actor_id: str,
        message_type: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Send a message directly to another actor.

        Args:
            target_actor_id: Target actor ID
            message_type: Message type identifier
            content: Message content
            correlation_id: Optional correlation ID

        Returns:
            Message ID
        """
        return await self.send(
            topic=f"actor:{target_actor_id}",
            content={
                "message_type": message_type,
                "content": content,
                "sender": self.agent_id,
            },
            message_type=message_type,
            correlation_id=correlation_id,
        )

    async def put_message(self, message: ActorMessage) -> None:
        """
        Put a message in the actor's mailbox.

        Args:
            message: Actor message to process
        """
        try:
            await asyncio.wait_for(
                self.mailbox.put(message),
                timeout=5.0,
            )
            logger.debug(
                f"[{self.agent_id}] Message queued",
                extra={"message_type": message.message_type},
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"[{self.agent_id}] Mailbox full, message dropped",
                extra={"message_type": message.message_type},
            )
            self.error_count += 1

    async def _process_mailbox(self) -> None:
        """Process messages from mailbox in a loop."""
        logger.info(f"[{self.agent_id}] Starting mailbox processing")

        while self._running:
            try:
                # Get message from mailbox with timeout
                message = await asyncio.wait_for(
                    self.mailbox.get(),
                    timeout=1.0,
                )

                self.message_count += 1
                self.last_activity = datetime.utcnow().isoformat()

                # Process message
                await self.process_message(message)

                # Mark as done
                self.mailbox.task_done()

            except asyncio.TimeoutError:
                # No messages, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(
                    f"[{self.agent_id}] Error processing message: {e}",
                    exc_info=True,
                )

    @abstractmethod
    async def process_message(self, message: ActorMessage) -> None:
        """
        Process an incoming message.

        This method MUST be implemented by subclasses to handle
        domain-specific message processing.

        Args:
            message: Actor message to process
        """
        pass

    async def initialize(self) -> None:
        """
        Initialize the actor after spawning.

        Override this method in subclasses for custom initialization logic.
        """
        pass

    async def cleanup(self) -> None:
        """
        Cleanup resources when actor terminates.

        Override this method in subclasses for custom cleanup logic.
        """
        pass

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running:
            try:
                await self.heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat error: {e}")
                await asyncio.sleep(5.0)

    async def heartbeat(self) -> None:
        """
        Send a heartbeat signal.

        Override this method in subclasses to implement custom heartbeat logic.
        """
        logger.debug(f"[{self.agent_id}] Heartbeat")

    async def save_state(self) -> None:
        """
        Persist actor state.

        Override this method in subclasses to implement custom state persistence.
        """
        state = {
            "internal_state": self.internal_state,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "state": self.state.value,
            "saved_at": datetime.utcnow().isoformat(),
        }
        logger.debug(f"[{self.agent_id}] State persisted")

    async def load_state(self) -> None:
        """
        Load actor state from persistence.

        Override this method in subclasses to implement custom state loading.
        """
        logger.info(f"[{self.agent_id}] State loaded")

    def get_status(self) -> ActorStatus:
        """
        Get actor status information.

        Returns:
            Current actor status
        """
        return ActorStatus(
            agent_id=self.agent_id,
            state=self.state,
            message_count=self.message_count,
            created_at=self.created_at,
            topics=self.topics,
            capabilities=self.capabilities,
            mailbox_size=self.mailbox.qsize(),
            last_activity=self.last_activity,
            error_count=self.error_count,
        )

    async def suspend(self) -> None:
        """Suspend the actor temporarily."""
        if self.state == ActorState.ACTIVE:
            self.state = ActorState.SUSPENDED
            logger.info(f"[{self.agent_id}] Agent suspended")

    async def resume(self) -> None:
        """Resume a suspended actor."""
        if self.state == ActorState.SUSPENDED:
            self.state = ActorState.ACTIVE
            logger.info(f"[{self.agent_id}] Agent resumed")

    async def broadcast(
        self,
        content: Dict[str, Any],
        message_type: str = "broadcast",
    ) -> None:
        """
        Broadcast a message to all actors.

        Args:
            content: Message content
            message_type: Message type identifier
        """
        await self.send(
            topic="broadcast",
            content={
                "message_type": message_type,
                "content": content,
                "sender": self.agent_id,
            },
            message_type=message_type,
        )

    # Default message handlers
    async def _handle_health_check(self, message: ActorMessage) -> None:
        """Handle health check requests."""
        status = self.get_status()
        reply_topic = message.content.get("reply_to", "health")

        await self.send(
            topic=reply_topic,
            content={
                "message_type": "health_response",
                "status": {
                    "agent_id": status.agent_id,
                    "state": status.state.value,
                    "message_count": status.message_count,
                    "error_count": status.error_count,
                },
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_suspend(self, message: ActorMessage) -> None:
        """Handle suspend requests."""
        await self.suspend()

    async def _handle_resume(self, message: ActorMessage) -> None:
        """Handle resume requests."""
        await self.resume()

    async def _handle_terminate(self, message: ActorMessage) -> None:
        """Handle terminate requests."""
        await self.terminate()

    def update_state(self, key: str, value: Any) -> None:
        """
        Update internal state.

        Args:
            key: State key
            value: State value
        """
        self.internal_state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get internal state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return self.internal_state.get(key, default)

    async def run_with_llm(self, prompt: str, **kwargs) -> str:
        """
        Run a prompt through the Swarms agent (if available).

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments for agent run

        Returns:
            Agent response
        """
        if self.swarms_agent is None:
            raise RuntimeError("No Swarms agent configured")

        return await asyncio.to_thread(
            self.swarms_agent.run,
            prompt,
            **kwargs,
        )
