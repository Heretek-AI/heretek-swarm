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
        """
        self.agent_id = agent_id or f"actor_{uuid.uuid4().hex[:8]}"
        self.name = name or self.__class__.__name__
        self.description = description or f"Actor: {self.name}"
        self.topics = topics or []
        self.capabilities = capabilities or []
        self.swarms_agent = swarms_agent
        self.max_mailbox_size = max_mailbox_size
        self.heartbeat_interval = heartbeat_interval
        self.actor_type = actor_type or self.__class__.__name__

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
        try:
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
            self.state = ActorState.TERMINATED

            # Cancel tasks
            await self._cancel_tasks()

            # Save final state
            await self.save_state()

            # Call cleanup hook
            await self.cleanup()

            logger.info(f"[{self.agent_id}] Agent terminated")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Terminate failed: {e}", exc_info=True)
            self.state = ActorState.ERROR
            raise

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
        # This would use a global actor registry in production
        actor_registry = self.get_state("_actor_registry")
        if actor_registry is not None:
            try:
                # Find actors subscribed to this topic
                for actor_id, actor in actor_registry.items():
                    if topic in getattr(actor, 'topics', []):
                        await actor.put_message(message)
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
        # Try direct delivery first
        actor_registry = self.get_state("_actor_registry")
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
                return str(uuid.uuid4())
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
                self.last_activity = datetime.now(timezone.utc).isoformat()

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
        """Send periodic heartbeats."""
        while self._running:
            try:
                await self.heartbeat()
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
        Persist actor state to PostgreSQL or file system.

        Saves actor state to the 'actor_states' table with proper serialization.
        Table schema expected:
            CREATE TABLE actor_states (
                actor_id TEXT PRIMARY KEY,
                actor_type TEXT,
                state JSONB,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """
        import json
        
        state = {
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
        
        # Try to persist to PostgreSQL if database is available
        db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO actor_states (actor_id, actor_type, state, updated_at)
                        VALUES ($1, $2, $3, NOW())
                        ON CONFLICT (actor_id) DO UPDATE
                        SET state = $3, updated_at = NOW()
                        """,
                        self.agent_id,
                        self.actor_type,
                        json.dumps(state),
                    )
                logger.info(
                    f"[{self.agent_id}] State persisted to PostgreSQL",
                    extra={"state": self.state.value},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] PostgreSQL persistence failed: {e}",
                    exc_info=True,
                )
        
        # Fallback: persist to file system
        try:
            import os
            state_dir = os.path.join(os.getcwd(), ".actor_states")
            os.makedirs(state_dir, exist_ok=True)
            state_file = os.path.join(state_dir, f"{self.agent_id}.json")
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
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
        Load actor state from PostgreSQL or file system.

        Attempts to load from PostgreSQL first, then falls back to file system.
        """
        import json
        
        # Try to load from PostgreSQL first
        db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT state FROM actor_states WHERE actor_id = $1",
                        self.agent_id,
                    )
                    if row:
                        loaded_state = json.loads(row["state"])
                        self.internal_state = loaded_state.get("internal_state", {})
                        self.message_count = loaded_state.get("message_count", 0)
                        self.error_count = loaded_state.get("error_count", 0)
                        self.state = ActorState(loaded_state.get("state", "active"))
                        self.created_at = loaded_state.get("created_at", self.created_at)
                        self.last_activity = loaded_state.get("last_activity")
                        self.topics = loaded_state.get("topics", self.topics)
                        self.capabilities = loaded_state.get("capabilities", self.capabilities)
                        
                        logger.info(
                            f"[{self.agent_id}] State loaded from PostgreSQL",
                            extra={"state": self.state.value},
                        )
                        return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] PostgreSQL load failed: {e}",
                    exc_info=True,
                )
        
        # Fallback: load from file system
        try:
            import os
            state_file = os.path.join(os.getcwd(), ".actor_states", f"{self.agent_id}.json")
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    loaded_state = json.load(f)
                
                self.internal_state = loaded_state.get("internal_state", {})
                self.message_count = loaded_state.get("message_count", 0)
                self.error_count = loaded_state.get("error_count", 0)
                self.state = ActorState(loaded_state.get("state", "active"))
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
        
        # Fallback to topic-based broadcast
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

    async def _handle_collective_task(self, message: ActorMessage) -> None:
        """
        Handle collective task contribution requests.
        
        This handler processes collective task requests and returns contributions.
        Subclasses can override this method to provide custom contribution logic.
        
        Args:
            message: ActorMessage with collective task details
        """
        task_id = message.content.get("task_id")
        task_type = message.content.get("task_type")
        description = message.content.get("description")
        input_data = message.content.get("input_data", {})
        protocol = message.content.get("protocol", {})
        reply_to = message.content.get("reply_to")
        
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
                
                response = await self.run_with_llm(prompt)
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
