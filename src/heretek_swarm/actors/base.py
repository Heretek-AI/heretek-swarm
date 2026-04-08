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
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import ValidationError
from swarms import Agent

from heretek_swarm.actors.validation import (
    validate_message,
    MessageContent,
    HealthCheckRequest,
    SuspendResumeRequest,
    TerminateRequest,
    CollectiveTaskRequest,
)
from heretek_swarm.state.repository import (
    StateRepository,
    AgentStateRecord,
    StateCheckpoint,
)

# Configure structured logging
import structlog
from heretek_swarm.actors.stubs import get_nats_event_mesh, get_llm_provider

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
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        swarms_agent: Optional[Agent] = None,
        max_mailbox_size: int = 1000,
        heartbeat_interval: float = 10.0,
        actor_type: Optional[str] = None,
        state_repository: Optional[StateRepository] = None,
        load_state_on_init: bool = True,
        persistence_interval: Optional[int] = None,  # P0-1: Continuous persistence
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
        self._state_repository: Optional[StateRepository] = state_repository
        self._state_record: Optional[AgentStateRecord] = None
        self._load_state_on_init = load_state_on_init
        self._persistence_interval = persistence_interval  # P0-1: Continuous persistence
        self._messages_since_persist = 0  # P0-1: Track messages for auto-persist

        # Actor state
        self.state: ActorState = ActorState.SPAWNING
        self.mailbox: asyncio.Queue = asyncio.Queue(maxsize=max_mailbox_size)
        self.internal_state: Dict[str, Any] = {}
        self.message_count = 0
        self.error_count = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
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
        self.register_handler("collective_task", self._handle_collective_task)

    def _validate_message_content(self, message_type: str, content: Dict[str, Any]) -> Optional[Any]:
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
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
            reply_to=reply_to,
            metadata=metadata or {},
        )

        # Route through event mesh if available
        event_mesh = self.get_state("_event_mesh")
        if event_mesh is not None:
            try:
                # Send via event mesh
                await event_mesh.send_to_json(
                    topic,
                    {
                        "type": message_type,
                        "from": self.agent_id,
                        "content": content,
                        "correlation_id": correlation_id,
                        "reply_to": reply_to,
                        "metadata": metadata or {},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                logger.info(
                    f"[{self.agent_id}] Message {message_id} sent via event mesh to {topic}",
                    extra={"message_type": message_type},
                )
                return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Event mesh send failed: {e}",
                    extra={"message_id": message_id, "topic": topic},
                )
        
        # Fallback: Direct delivery to actors subscribed to topic
        # Use global actor registry from supervisor
        actor_registry = self._get_actor_registry()
        if actor_registry is not None:
            try:
                # Find actors subscribed to this topic
                delivered = False
                for reg_actor_id, reg_actor in actor_registry.items():
                    if topic in getattr(reg_actor, 'topics', []):
                        await reg_actor.put_message(message)
                        delivered = True
                if delivered:
                    logger.info(
                        f"[{self.agent_id}] Message {message_id} delivered directly to topic subscribers",
                        extra={"message_type": message_type},
                    )
                    return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Direct delivery failed: {e}",
                    extra={"message_id": message_id, "topic": topic},
                )
        
        # Last resort: log the message (should not happen in production)
        logger.warning(
            f"[{self.agent_id}] Message {message_id} queued (no delivery mechanism available)",
            extra={"message_type": message_type, "topic": topic},
        )
        
        # Store in internal queue for later delivery
        self._queue_message(message)
        return message_id
    
    def _queue_message(self, message: ActorMessage) -> None:
        """Queue a message for later delivery when event mesh becomes available."""
        pending_messages = self.get_state("_pending_messages", [])
        pending_messages.append(message)
        self.update_state("_pending_messages", pending_messages)
        logger.debug(
            f"[{self.agent_id}] Message queued for later delivery",
            extra={"message_type": message.message_type},
        )

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
        message_id = str(uuid.uuid4())
        
        # Use global actor registry from supervisor
        actor_registry = self._get_actor_registry()
        if actor_registry is not None and target_actor_id in actor_registry:
            try:
                target_actor = actor_registry[target_actor_id]
                message = ActorMessage(
                    sender=self.agent_id,
                    message_type=message_type,
                    content={
                        "message_type": message_type,
                        "content": content,
                        "sender": self.agent_id,
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    correlation_id=correlation_id,
                )
                await target_actor.put_message(message)
                logger.info(
                    f"[{self.agent_id}] Direct message sent to {target_actor_id}",
                    extra={"message_type": message_type},
                )
                return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Direct actor send failed: {e}",
                    extra={"target": target_actor_id},
                )
        
        # Fallback to topic-based routing
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

    async def send_with_reply(
        self,
        recipient: str,
        message_type: str,
        content: Dict[str, Any],
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Send message and wait for reply with correlation tracking.
        
        Implements the request-reply pattern from Microsoft AutoGen for
        synchronous inter-agent communication.
        
        Args:
            recipient: Target actor ID or topic
            message_type: Message type identifier
            content: Message payload
            timeout: Seconds to wait for reply (default: 30)
            
        Returns:
            Reply content dict, or None if timeout/failure
            
        Raises:
            asyncio.TimeoutError: If no reply received within timeout
        """
        import asyncio
        
        # Generate unique correlation ID for this request
        correlation_id = str(uuid.uuid4())
        reply_channel = f"reply_{self.agent_id}_{correlation_id}"
        
        logger.info(
            f"[{self.agent_id}] Sending request to {recipient} with correlation_id={correlation_id}",
            extra={"message_type": message_type, "timeout": timeout},
        )
        
        # Create a temporary queue for the reply
        reply_queue: asyncio.Queue = asyncio.Queue()
        
        # Register reply handler
        async def handle_reply(message: ActorMessage) -> None:
            """Handle incoming reply message."""
            await reply_queue.put(message)
        
        # Register the reply handler for this specific channel
        self.register_handler(reply_channel, handle_reply)
        
        try:
            # Send request with reply_to channel
            await self.send(
                topic=recipient,
                content=content,
                message_type=message_type,
                correlation_id=correlation_id,
                reply_to=reply_channel,
            )
            
            # Wait for reply with timeout
            try:
                reply_message = await asyncio.wait_for(
                    reply_queue.get(),
                    timeout=timeout,
                )
                
                logger.info(
                    f"[{self.agent_id}] Reply received for correlation_id={correlation_id}",
                    extra={"message_type": reply_message.message_type},
                )
                
                return reply_message.content
                
            except asyncio.TimeoutError:
                logger.warning(
                    f"[{self.agent_id}] Request timeout after {timeout}s for correlation_id={correlation_id}",
                    extra={"recipient": recipient, "message_type": message_type},
                )
                raise
                
        finally:
            # Cleanup: unregister reply handler
            self.unregister_handler(reply_channel)
    
    async def put_message(self, message: ActorMessage) -> None:
        """
        Put a message in the actor's mailbox.

        Args:
            message: Actor message to process
        """
        # P1-10e fix: Add retry logic for message queuing instead of dropping
        max_retries = 3
        retry_delay = 0.1  # 100ms initial delay
        
        for attempt in range(max_retries):
            try:
                await asyncio.wait_for(
                    self.mailbox.put(message),
                    timeout=5.0,
                )
                logger.debug(
                    f"[{self.agent_id}] Message queued",
                    extra={"message_type": message.message_type},
                )
                return  # Success, exit retry loop
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    # P1-10e fix: Retry with exponential backoff
                    logger.warning(
                        f"[{self.agent_id}] Mailbox full, retrying ({attempt + 1}/{max_retries})",
                        extra={"message_type": message.message_type},
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    # P1-10e fix: Only drop after all retries exhausted
                    logger.error(
                        f"[{self.agent_id}] Mailbox full after {max_retries} retries, message dropped",
                        extra={"message_type": message.message_type},
                    )
                    self.error_count += 1

    async def _process_mailbox(self) -> None:
        """Process messages from mailbox in a loop with continuous persistence."""
        logger.info(f"[{self.agent_id}] Starting mailbox processing")

        while self._running:
            try:
                # Get message from mailbox with timeout
                message = await asyncio.wait_for(
                    self.mailbox.get(),
                    timeout=1.0,
                )

                self.message_count += 1
                self._messages_since_persist += 1  # P0-1: Track for auto-persist
                self.last_activity = datetime.now(timezone.utc).isoformat()

                # Process message
                await self.process_message(message)

                # P0-1: Auto-persist if interval configured and threshold reached
                if self._persistence_interval and self._messages_since_persist >= self._persistence_interval:
                    await self.save_state()
                    self._messages_since_persist = 0
                    logger.debug(
                        f"[{self.agent_id}] State persisted after {self._persistence_interval} messages",
                        extra={"total_messages": self.message_count}
                    )

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
        This method is called during actor shutdown to ensure proper resource cleanup.
        """
        try:
            # Clear mailbox to prevent memory leaks
            while not self.mailbox.empty():
                try:
                    self.mailbox.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            # Clear internal state
            self.internal_state.clear()
            
            # Clear message handlers
            self._message_handlers.clear()
            
            logger.debug(f"[{self.agent_id}] Cleanup complete")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Cleanup error: {e}", exc_info=True)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats with state persistence."""
        while self._running:
            try:
                await self.heartbeat()
                # P0-1: Persist state on heartbeat if configured
                if self._persistence_interval is not None:
                    await self.save_state()
                    logger.debug(
                        f"[{self.agent_id}] State persisted on heartbeat",
                        extra={"messages_since_persist": self._messages_since_persist}
                    )
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(5.0)

    async def heartbeat(self) -> None:
        """
        Send a heartbeat signal.

        Override this method in subclasses to implement custom heartbeat logic.
        """
        logger.debug(f"[{self.agent_id}] Heartbeat")

    async def save_state(self) -> None:
        """
        Persist actor state to PostgreSQL via StateRepository.

        Saves actor state with version tracking for optimistic locking.
        Falls back to legacy file system persistence if repository not available.
        """
        import json
        
        state_data = {
            "internal_state": self.internal_state,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "topics": self.topics,
            "capabilities": self.capabilities,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Use state repository if available
        if self._state_repository is not None:
            try:
                # Get current version from stored record
                version = None
                if self._state_record:
                    version = self._state_record.version + 1
                
                self._state_record = await self._state_repository.save_state(
                    agent_id=self.agent_id,
                    state=state_data,
                    agent_type=self.actor_type,
                    version=version,
                )
                logger.info(
                    f"[{self.agent_id}] State persisted via StateRepository",
                    extra={"state": self.state.value, "version": self._state_record.version},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] StateRepository persistence failed: {e}",
                    exc_info=True,
                )
        
        # Legacy fallback: try direct db_pool access
        db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO agent_states (id, agent_id, agent_type, state, version, updated_at, is_active)
                        VALUES (gen_random_uuid(), $1, $2, $3, 1, NOW(), true)
                        ON CONFLICT (agent_id) DO UPDATE
                        SET state = $3, version = agent_states.version + 1, updated_at = NOW()
                        """,
                        self.agent_id,
                        self.actor_type,
                        json.dumps(state_data),
                    )
                logger.info(
                    f"[{self.agent_id}] State persisted to PostgreSQL (legacy)",
                    extra={"state": self.state.value},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] PostgreSQL persistence failed: {e}",
                    exc_info=True,
                )
        
        # Final fallback: persist to file system
        try:
            import os
            state_dir = os.path.join(os.getcwd(), ".actor_states")
            os.makedirs(state_dir, exist_ok=True)
            state_file = os.path.join(state_dir, f"{self.agent_id}.json")
            
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(
                f"[{self.agent_id}] State persisted to file system",
                extra={"path": state_file},
            )
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] File system persistence failed: {e}",
                exc_info=True,
            )

    async def load_state(self) -> None:
        """
        Load actor state from StateRepository.

        Attempts to load from repository first, then falls back to legacy methods.
        """
        import json
        
        # Try StateRepository first
        if self._state_repository is not None:
            try:
                record = await self._state_repository.load_state(self.agent_id)
                if record:
                    self._state_record = record
                    loaded_state = record.state
                    
                    self.internal_state = loaded_state.get("internal_state", {})
                    self.message_count = loaded_state.get("message_count", 0)
                    self.error_count = loaded_state.get("error_count", 0)
                    self.state = ActorState(loaded_state.get("state", "spawning"))
                    self.created_at = loaded_state.get("created_at", self.created_at)
                    self.last_activity = loaded_state.get("last_activity")
                    self.topics = loaded_state.get("topics", self.topics)
                    self.capabilities = loaded_state.get("capabilities", self.capabilities)
                    
                    logger.info(
                        f"[{self.agent_id}] State loaded from StateRepository",
                        extra={"state": self.state.value, "version": record.version},
                    )
                    return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] StateRepository load failed: {e}",
                    exc_info=True,
                )
        
        # Legacy fallback: try direct db_pool access
        db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT state, version FROM agent_states WHERE agent_id = $1 AND is_active = true",
                        self.agent_id,
                    )
                    if row:
                        loaded_state = json.loads(row["state"])
                        self.internal_state = loaded_state.get("internal_state", {})
                        self.message_count = loaded_state.get("message_count", 0)
                        self.error_count = loaded_state.get("error_count", 0)
                        self.state = ActorState(loaded_state.get("state", "spawning"))
                        self.created_at = loaded_state.get("created_at", self.created_at)
                        self.last_activity = loaded_state.get("last_activity")
                        self.topics = loaded_state.get("topics", self.topics)
                        self.capabilities = loaded_state.get("capabilities", self.capabilities)
                        
                        logger.info(
                            f"[{self.agent_id}] State loaded from PostgreSQL (legacy)",
                            extra={"state": self.state.value},
                        )
                        return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] PostgreSQL load failed: {e}",
                    exc_info=True,
                )
        
        # Final fallback: load from file system
        try:
            import os
            state_file = os.path.join(os.getcwd(), ".actor_states", f"{self.agent_id}.json")
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    loaded_state = json.load(f)
                
                self.internal_state = loaded_state.get("internal_state", {})
                self.message_count = loaded_state.get("message_count", 0)
                self.error_count = loaded_state.get("error_count", 0)
                self.state = ActorState(loaded_state.get("state", "spawning"))
                self.created_at = loaded_state.get("created_at", self.created_at)
                self.last_activity = loaded_state.get("last_activity")
                self.topics = loaded_state.get("topics", self.topics)
                self.capabilities = loaded_state.get("capabilities", self.capabilities)
                
                logger.info(
                    f"[{self.agent_id}] State loaded from file system",
                    extra={"path": state_file},
                )
                return
        except Exception as e:
            logger.error(f"[{self.agent_id}] File system load failed: {e}", exc_info=True)
        
        # No state found - actor is starting fresh
        logger.info(f"[{self.agent_id}] No previous state found, starting fresh")

    async def save_checkpoint(
        self,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[StateCheckpoint]:
        """
        Save a versioned state checkpoint.

        Checkpoints are immutable snapshots that can be used for:
        - Rollback after errors
        - State restoration after restart
        - Audit trail

        Args:
            metadata: Optional metadata (reason, trigger, etc.)

        Returns:
            Created checkpoint, or None if repository not available
        """
        if self._state_repository is None:
            logger.warning(f"[{self.agent_id}] Cannot save checkpoint: no state repository")
            return None
        
        state_data = {
            "internal_state": self.internal_state,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "topics": self.topics,
            "capabilities": self.capabilities,
        }
        
        try:
            version = self._state_record.version + 1 if self._state_record else 1
            checkpoint = await self._state_repository.checkpoint(
                agent_id=self.agent_id,
                state=state_data,
                version=version,
                metadata=metadata,
            )
            logger.info(
                f"[{self.agent_id}] Checkpoint saved",
                extra={"version": version, "checkpoint_id": str(checkpoint.checkpoint_id)},
            )
            return checkpoint
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Checkpoint save failed: {e}",
                exc_info=True,
            )
            return None

    async def restore_from_checkpoint(
        self,
        checkpoint_id: uuid.UUID,
    ) -> bool:
        """
        Restore agent state from a checkpoint.

        Args:
            checkpoint_id: UUID of checkpoint to restore from

        Returns:
            True if restored successfully, False otherwise
        """
        if self._state_repository is None:
            logger.warning(f"[{self.agent_id}] Cannot restore checkpoint: no state repository")
            return False
        
        try:
            success = await self._state_repository.restore_from_checkpoint(
                agent_id=self.agent_id,
                checkpoint_id=checkpoint_id,
            )
            
            if success:
                # Reload the state
                await self.load_state()
                logger.info(
                    f"[{self.agent_id}] State restored from checkpoint",
                    extra={"checkpoint_id": str(checkpoint_id)},
                )
            
            return success
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Checkpoint restore failed: {e}",
                exc_info=True,
            )
            return False

    async def get_checkpoints(
        self,
        limit: int = 10,
    ) -> List[StateCheckpoint]:
        """
        Get recent checkpoints for this agent.

        Args:
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints (newest first)
        """
        if self._state_repository is None:
            return []
        
        try:
            return await self._state_repository.get_checkpoints(
                agent_id=self.agent_id,
                limit=limit,
            )
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Failed to get checkpoints: {e}",
                exc_info=True,
            )
            return []

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
        # Use event mesh broadcast if available
        event_mesh = self.get_state("_event_mesh")
        if event_mesh is not None:
            try:
                await event_mesh.broadcast_json({
                    "type": message_type,
                    "from": self.agent_id,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                logger.info(
                    f"[{self.agent_id}] Broadcast sent via event mesh",
                    extra={"message_type": message_type},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Event mesh broadcast failed: {e}",
                    extra={"message_type": message_type},
                )
        
        # Fallback: Broadcast to all actors via registry
        actor_registry = self._get_actor_registry()
        if actor_registry is not None:
            message = ActorMessage(
                sender=self.agent_id,
                message_type=message_type,
                content={
                    "message_type": message_type,
                    "content": content,
                    "sender": self.agent_id,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            sent_count = 0
            for reg_actor_id, reg_actor in actor_registry.items():
                if reg_actor_id != self.agent_id:  # Don't send to self
                    try:
                        await reg_actor.put_message(message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(
                            f"[{self.agent_id}] Broadcast to {reg_actor_id} failed: {e}",
                            extra={"message_type": message_type},
                        )
            logger.info(
                f"[{self.agent_id}] Broadcast sent to {sent_count} actors via registry",
                extra={"message_type": message_type},
            )
            return
        
        # Last resort: topic-based broadcast
        await self.send(
            topic="broadcast",
            content={
                "message_type": message_type,
                "content": content,
                "sender": self.agent_id,
            },
            message_type=message_type,
        )

    # Default message handlers with Zero-Trust validation
    async def _handle_health_check(self, message: ActorMessage) -> None:
        """Handle health check requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("health_check", message.content)
            if validated:
                reply_topic = validated.reply_to
            else:
                reply_topic = message.content.get("reply_to", "health")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Health check validation failed: {e}")
            return
        
        status = self.get_status()

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
        """Handle suspend requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            self._validate_message_content("suspend", message.content)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Suspend validation failed: {e}")
            return
        await self.suspend()

    async def _handle_resume(self, message: ActorMessage) -> None:
        """Handle resume requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            self._validate_message_content("resume", message.content)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Resume validation failed: {e}")
            return
        await self.resume()

    async def _handle_terminate(self, message: ActorMessage) -> None:
        """Handle terminate requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("terminate", message.content)
            if validated and validated.reason:
                logger.info(f"[{self.agent_id}] Termination requested: {validated.reason}")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Terminate validation failed: {e}")
            return
        await self.terminate()

    async def _handle_collective_task(self, message: ActorMessage) -> None:
        """
        Handle collective task contribution requests with validation.
        
        This handler processes collective task requests and returns contributions.
        Subclasses can override this method to provide custom contribution logic.
        
        Args:
            message: ActorMessage with collective task details
        """
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("collective_task", message.content)
            if validated:
                task_id = validated.task_id
                task_type = validated.task_type
                description = validated.description
                input_data = validated.input_data
                protocol = validated.protocol
                reply_to = validated.reply_to
            else:
                # Fallback to unvalidated access
                task_id = message.content.get("task_id")
                task_type = message.content.get("task_type")
                description = message.content.get("description")
                input_data = message.content.get("input_data", {})
                protocol = message.content.get("protocol", {})
                reply_to = message.content.get("reply_to")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Collective task validation failed: {e}")
            return
        
        logger.info(
            f"[{self.agent_id}] Received collective task",
            extra={
                "task_id": task_id,
                "task_type": task_type,
                "description": description,
            }
        )
        
        # Generate contribution (subclasses should override for custom logic)
        contribution = await self._generate_collective_contribution(
            task_id=task_id,
            task_type=task_type,
            description=description,
            input_data=input_data,
            protocol=protocol
        )
        
        # Send response if reply_to is provided
        if reply_to:
            await self.send(
                topic=reply_to,
                content={
                    "message_type": "collective_task_response",
                    "task_id": task_id,
                    "correlation_id": message.correlation_id,
                    **contribution
                },
                correlation_id=message.correlation_id,
            )
    
    async def _generate_collective_contribution(
        self,
        task_id: str,
        task_type: str,
        description: str,
        input_data: Dict[str, Any],
        protocol: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate contribution for a collective task.
        
        Subclasses should override this method to provide custom contribution logic.
        Default implementation uses LLM if available, otherwise returns fallback.
        
        Args:
            task_id: Task identifier
            task_type: Type of task
            description: Task description
            input_data: Task input data
            protocol: Communication protocol
            
        Returns:
            Dict with contribution and confidence
        """
        # Try using LLM if available
        if hasattr(self, 'swarms_agent') and self.swarms_agent is not None:
            try:
                prompt = f"""You are participating in a collective task.

Task Details:
- Task ID: {task_id}
- Task Type: {task_type}
- Description: {description}
- Input Data: {input_data}

Please provide your analysis and recommendation for this collective task."""
                
                response = await self.run_with_llm(prompt, timeout=60)
                return {
                    "contribution": {
                        "analysis": response,
                        "recommendation": "llm_generated",
                        "method": "run_with_llm"
                    },
                    "confidence": 0.75
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] LLM contribution error: {e}")
        
        # Fallback contribution
        return {
            "contribution": {
                "analysis": f"Analysis from {self.name} for task: {description}",
                "recommendation": f"{self.name}_recommendation",
                "method": "fallback"
            },
            "confidence": 0.6
        }

    def _get_actor_registry(self) -> Optional[Dict[str, "AgentActor"]]:
        """
        Get global actor registry from supervisor.
        
        This enables message delivery by accessing the supervisor's actor registry.
        
        Returns:
            Actor registry dict or None if supervisor not available
        """
        try:
            from heretek_swarm.actors.supervisor import get_supervisor
            supervisor = get_supervisor()
            if supervisor and hasattr(supervisor, 'actors'):
                return supervisor.actors
        except (ImportError, Exception):
            pass
        return None

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

    async def run_with_llm(self, prompt: str, timeout: int = 60, **kwargs) -> str:
        """
        Run a prompt through the Swarms agent (if available).

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds (default: 60)
            **kwargs: Additional arguments for agent run

        Returns:
            Agent response

        Raises:
            RuntimeError: If no Swarms agent configured
            asyncio.TimeoutError: If LLM call times out
        """
        if self.swarms_agent is None:
            raise RuntimeError("No Swarms agent configured")

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.swarms_agent.run,
                    prompt,
                    **kwargs,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"[{self.agent_id}] LLM call timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM call failed: {e}", exc_info=True)
            raise
