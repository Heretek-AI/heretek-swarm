"""
NATSEventMesh - NATS EventMesh Integration for Heretek Swarm

This module provides NATS-based event mesh integration with JetStream support:
- Asynchronous connection management with connection pooling
- Publish/subscribe patterns
- Request-reply pattern with timeout
- JetStream stream creation and management
- Durable consumer subscriptions
- Message replay for event sourcing
- Integration with existing EventMesh
- Graceful fallback to in-memory mesh if NATS unavailable

Reference: MiniMax Audit Lines 11-30 (EventMesh bug fix)
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

# Try to import NATS, but make it optional
try:
    import nats
    from nats.errors import NatsError
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NatsError = Exception


class ConnectionState(Enum):
    """NATS connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class Subscription:
    """NATS subscription wrapper."""
    subject: str
    callback: Callable[["NATSEventMesh", str, Dict[str, Any]], None]
    sid: str
    active: bool = True


@dataclass
class NATSMessage:
    """NATS message wrapper."""
    subject: str
    data: Dict[str, Any]
    reply: Optional[str] = None
    sid: Optional[str] = None
    timestamp: str = field(default_factory=datetime.now(timezone.utc).isoformat)


class NATSEventMesh:
    """
    NATS EventMesh integration for Heretek Swarm.
    
    Provides distributed messaging via NATS with:
    - Connection management and auto-reconnection
    - Publish/subscribe patterns
    - Request-reply pattern
    - Fallback to in-memory mesh if NATS unavailable
    
    Example:
        ```python
        # Initialize with NATS
        mesh = NATSEventMesh(
            servers=["nats://localhost:4222"],
            fallback=True
        )
        await mesh.connect()
        
        # Subscribe to subject
        async def handle_message(mesh, subject, data):
            print(f"Received: {data}")
        
        await mesh.subscribe("events.>", handle_message)
        
        # Publish message
        await mesh.publish("events.test", {"message": "hello"})
        
        # Request-reply
        response = await mesh.request(
            "events.query",
            {"query": "test"},
            timeout=5.0
        )
        ```
    """
    
    def __init__(
        self,
        servers: Optional[List[str]] = None,
        name: Optional[str] = None,
        fallback: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_timewait: float = 1.0,
        ping_interval: int = 30,
        max_outstanding: int = 1000,
    ) -> None:
        """
        Initialize NATS EventMesh.
        
        Args:
            servers: List of NATS server URLs
            name: Client name
            fallback: Enable fallback to in-memory mesh
            max_reconnect_attempts: Max reconnection attempts
            reconnect_timewait: Time to wait between reconnect attempts
            ping_interval: Ping interval in seconds
            max_outstanding: Max pending messages
        """
        self.servers = servers or ["nats://localhost:4222"]
        self.client_name = name or "heretek-swarm"
        self.fallback = fallback
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_timewait = reconnect_timewait
        self.ping_interval = ping_interval
        self.max_outstanding = max_outstanding
        
        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._nc = None  # NATS connection
        self._js = None  # JetStream context
        self._js_context: Optional[Any] = None  # JetStream context manager
        
        # JetStream streams
        self._streams: Dict[str, Dict[str, Any]] = {}
        
        # Subscriptions
        self._subscriptions: Dict[str, Subscription] = {}
        self._subscription_ids: Set[str] = set()
        
        # Durable consumers
        self._consumers: Dict[str, Any] = {}
        
        # In-memory fallback
        self._fallback_mesh: Optional["_InMemoryFallback"] = None
        self._use_fallback = False
        
        # Connection lock
        self._lock = asyncio.Lock()
        
        logger.info(
            "NATSEventMesh initialized",
            extra={
                "servers": self.servers,
                "fallback": self.fallback,
                "nats_available": NATS_AVAILABLE,
            },
        )

    @property
    def is_connected(self) -> bool:
        """Check if connected to NATS."""
        return self._state == ConnectionState.CONNECTED and self._nc is not None

    @property
    def jetstream_enabled(self) -> bool:
        """Check if JetStream is available."""
        return self._js is not None and NATS_AVAILABLE

    @property
    def client_count(self) -> int:
        """Get number of active subscriptions."""
        return len([s for s in self._subscriptions.values() if s.active])

    @property
    def stream_count(self) -> int:
        """Get number of created streams."""
        return len(self._streams)

    async def connect(self) -> bool:
        """
        Connect to NATS servers.
        
        Returns:
            True if connected successfully
        """
        if not NATS_AVAILABLE:
            logger.warning("NATS not available, using fallback")
            return await self._enable_fallback()

        async with self._lock:
            self._state = ConnectionState.CONNECTING
            
            try:
                # Connect to first available server
                self._nc = await self._connect_to_server()
                
                if self._nc is not None:
                    self._state = ConnectionState.CONNECTED
                    logger.info("Connected to NATS")
                    
                    # Initialize JetStream context
                    try:
                        self._js = self._nc.jetstream()
                        logger.info("JetStream context initialized")
                    except Exception as e:
                        logger.warning(f"JetStream not available: {e}")
                        self._js = None
                    
                    return True
                    
            except Exception as e:
                logger.error("Failed to connect to NATS", error=str(e))
            
            # Fallback to in-memory mesh
            if self.fallback:
                return await self._enable_fallback()
            
            self._state = ConnectionState.DISCONNECTED
            return False

    async def _connect_to_server(self) -> Optional[Any]:
        """Connect to a NATS server with retry."""
        last_error = None
        
        for server in self.servers:
            for attempt in range(self.max_reconnect_attempts):
                try:
                    logger.debug(f"Connecting to {server} (attempt {attempt + 1})")
                    
                    nc = await nats.connect(
                        server,
                        name=self.client_name,
                        reconnect_timewait=self.reconnect_timewait,
                        ping_interval=self.ping_interval,
                        max_outstanding=self.max_outstanding,
                    )
                    
                    logger.info(f"Connected to {server}")
                    return nc
                    
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Failed to connect to {server}",
                        error=str(e),
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(self.reconnect_timewait)
        
        raise last_error or Exception("No servers available")

    async def _enable_fallback(self) -> bool:
        """Enable in-memory fallback mesh."""
        if self.fallback:
            self._fallback_mesh = _InMemoryFallback()
            self._use_fallback = True
            self._state = ConnectionState.CONNECTED
            logger.info("Using in-memory fallback mesh")
            return True
        return False

    async def disconnect(self) -> None:
        """Disconnect from NATS and cleanup."""
        async with self._lock:
            self._state = ConnectionState.CLOSING
            
            # Unsubscribe all
            for sub in self._subscriptions.values():
                if sub.active:
                    sub.active = False
            
            # Close NATS connection
            if self._nc is not None:
                try:
                    await self._nc.close()
                except Exception as e:
                    logger.error("Error closing NATS connection", error=str(e))
                finally:
                    self._nc = None
            
            self._state = ConnectionState.DISCONNECTED
            self._subscriptions.clear()
            
            logger.info("Disconnected from NATS")

    async def create_stream(
        self,
        name: str,
        subjects: List[str],
        storage: str = "file",
        retention: str = "limits",
        max_msgs: int = 100000,
        max_age: int = 86400,  # 24 hours in seconds
    ) -> bool:
        """
        Create a JetStream for message persistence.
        
        Args:
            name: Stream name
            subjects: List of subjects to capture
            storage: Storage type ("file" or "memory")
            retention: Retention policy ("limits", "interest", or "workqueue")
            max_msgs: Maximum messages to retain
            max_age: Maximum age of messages in seconds
            
        Returns:
            True if stream created successfully
        """
        if not self.jetstream_enabled:
            logger.warning("JetStream not available")
            return False
        
        try:
            import nats.js.api as js_api
            
            storage_type = js_api.StorageType.FILE if storage == "file" else js_api.StorageType.MEMORY
            retention_policy = getattr(js_api.RetentionPolicy, retention.upper(), js_api.RetentionPolicy.LIMITS)
            
            config = js_api.StreamConfig(
                name=name,
                subjects=subjects,
                storage=storage_type,
                retention=retention_policy,
                max_msgs=max_msgs,
                max_age=max_age * 1_000_000_000,  # Convert to nanoseconds
            )
            
            stream_info = await self._js.add_stream(config=config)
            
            self._streams[name] = {
                "name": name,
                "subjects": subjects,
                "storage": storage,
                "retention": retention,
                "max_msgs": max_msgs,
                "max_age": max_age,
                "created": datetime.now(timezone.utc).isoformat(),
            }
            
            logger.info(f"JetStream '{name}' created", subjects=subjects)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create stream '{name}': {e}")
            return False

    async def delete_stream(self, name: str) -> bool:
        """
        Delete a JetStream.
        
        Args:
            name: Stream name
            
        Returns:
            True if deleted successfully
        """
        if not self.jetstream_enabled:
            return False
        
        try:
            await self._js.delete_stream(name)
            self._streams.pop(name, None)
            logger.info(f"JetStream '{name}' deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete stream '{name}': {e}")
            return False

    async def publish_to_stream(
        self,
        stream_name: str,
        subject: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish message to a JetStream.
        
        Args:
            stream_name: Name of the stream
            subject: Message subject
            data: Message data
            
        Returns:
            True if published successfully
        """
        if not self.jetstream_enabled:
            return False
        
        if stream_name not in self._streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return False
        
        try:
            ack = await self._js.publish(subject, json.dumps(data).encode('utf-8'))
            logger.debug(f"Published to stream '{stream_name}'", seq=ack.seq)
            return True
        except Exception as e:
            logger.error(f"Failed to publish to stream: {e}")
            return False

    async def subscribe_durable(
        self,
        stream_name: str,
        durable_name: str,
        callback: Callable[[str, Dict[str, Any]], None],
        deliver_policy: str = "all",
        ack_policy: bool = True,
    ) -> Optional[str]:
        """
        Subscribe with durable consumer for at-least-once delivery.
        
        Args:
            stream_name: Name of the stream to consume from
            durable_name: Durable consumer name (persists across reconnects)
            callback: Async callback function (subject, data)
            deliver_policy: Delivery policy ("all", "last", "new", or "by_start_sequence")
            ack_policy: Enable acknowledgment (at-least-once delivery)
            
        Returns:
            Consumer ID or None if failed
        """
        if not self.jetstream_enabled:
            return None
        
        if stream_name not in self._streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return None
        
        try:
            import nats.js.api as js_api
            
            deliver = getattr(js_api.DeliverPolicy, deliver_policy.upper(), js_api.DeliverPolicy.ALL)
            ack = js_api.AckPolicy.EXPLICIT if ack_policy else js_api.AckPolicy.NONE
            
            # Create or bind to durable consumer
            consumer_info = await self._js.pull_subscribe(
                stream=stream_name,
                durable=durable_name,
                deliver_policy=deliver,
                ack_policy=ack,
            )
            
            consumer_id = f"consumer_{stream_name}_{durable_name}"
            self._consumers[consumer_id] = consumer_info
            
            # Start message processing loop
            asyncio.create_task(self._process_durable_messages(
                consumer_info,
                stream_name,
                durable_name,
                callback
            ))
            
            logger.info(f"Durable consumer '{durable_name}' created on stream '{stream_name}'")
            return consumer_id
            
        except Exception as e:
            logger.error(f"Failed to create durable consumer: {e}")
            return None

    async def _process_durable_messages(
        self,
        consumer: Any,
        stream_name: str,
        durable_name: str,
        callback: Callable[[str, Dict[str, Any]], None],
    ) -> None:
        """
        Process messages from a durable consumer.
        
        Args:
            consumer: JetStream consumer
            stream_name: Stream name
            durable_name: Durable consumer name
            callback: Message callback
        """
        while True:
            try:
                msgs = await consumer.fetch(batch=10, timeout=5.0)
                for msg in msgs:
                    try:
                        data = json.loads(msg.data.decode('utf-8'))
                        await callback(msg.subject, data)
                        await msg.ack()
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await msg.nak()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Durable consumer error: {e}")
                await asyncio.sleep(1.0)

    async def replay_stream(
        self,
        stream_name: str,
        start_sequence: Optional[int] = None,
        start_time: Optional[datetime] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Replay messages from a JetStream.
        
        Args:
            stream_name: Name of the stream to replay
            start_sequence: Start from specific sequence number
            start_time: Start from specific timestamp
            callback: Optional callback for each message
            
        Returns:
            List of replayed messages
        """
        if not self.jetstream_enabled:
            return []
        
        if stream_name not in self._streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return []
        
        messages = []
        
        try:
            import nats.js.api as js_api
            
            # Determine deliver policy
            if start_sequence is not None:
                deliver_policy = js_api.DeliverPolicy.BY_START_SEQUENCE
            elif start_time is not None:
                deliver_policy = js_api.DeliverPolicy.BY_START_TIME
            else:
                deliver_policy = js_api.DeliverPolicy.ALL
            
            consumer_info = await self._js.pull_subscribe(
                stream=stream_name,
                durable=f"replay_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                deliver_policy=deliver_policy,
                opt_start_seq=start_sequence,
                opt_start_time=start_time,
            )
            
            # Fetch all messages
            while True:
                try:
                    msgs = await consumer_info.fetch(batch=100, timeout=2.0)
                    for msg in msgs:
                        data = json.loads(msg.data.decode('utf-8'))
                        messages.append({
                            "subject": msg.subject,
                            "data": data,
                            "sequence": msg.metadata.sequence.stream if msg.metadata else None,
                            "timestamp": msg.metadata.timestamp if msg.metadata else None,
                        })
                        if callback:
                            await callback(msg.subject, data)
                        await msg.ack()
                except asyncio.TimeoutError:
                    break
            
            logger.info(f"Replayed {len(messages)} messages from stream '{stream_name}'")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to replay stream: {e}")
            return []

    async def reconstruct_state(
        self,
        entity_id: str,
        stream_name: str,
        event_applier: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Reconstruct entity state from event stream.
        
        Event sourcing pattern: replay all events for an entity and apply
        them to reconstruct current state.
        
        Args:
            entity_id: Entity identifier to reconstruct
            stream_name: Name of the event stream
            event_applier: Function to apply event to state (state, event) -> new_state
            initial_state: Initial state to start from
            
        Returns:
            Reconstructed state dictionary
        """
        state = initial_state or {}
        
        def filter_callback(subject: str, data: Dict[str, Any]):
            nonlocal state
            if data.get("entity_id") == entity_id:
                state = event_applier(state, data)
        
        await self.replay_stream(
            stream_name=stream_name,
            callback=filter_callback,
        )
        
        logger.info(f"Reconstructed state for entity '{entity_id}' from {len(state)} fields")
        return state

    async def publish(self, subject: str, data: Dict[str, Any], reply: Optional[str] = None) -> bool:
        """
        Publish message to subject.
        
        Args:
            subject: NATS subject (supports wildcards)
            data: Message data (will be JSON encoded)
            reply: Optional reply subject
            
        Returns:
            True if published successfully
        """
        if self._use_fallback and self._fallback_mesh is not None:
            return await self._fallback_mesh.publish(subject, data)
        
        if not self.is_connected:
            logger.warning("Not connected, cannot publish")
            return False
        
        try:
            message = json.dumps(data).encode('utf-8')
            await self._nc.publish(subject, message, reply=reply)
            await self._nc.flush()
            logger.debug("Published message", subject=subject)
            return True
        except Exception as e:
            logger.error("Failed to publish", subject=subject, error=str(e))
            return False

    async def subscribe(
        self,
        subject: str,
        callback: Callable[["NATSEventMesh", str, Dict[str, Any]], None],
    ) -> Optional[str]:
        """
        Subscribe to subject.
        
        Args:
            subject: NATS subject (supports wildcards)
            callback: Async callback function (mesh, subject, data)
            
        Returns:
            Subscription ID or None if failed
        """
        if self._use_fallback and self._fallback_mesh is not None:
            return await self._fallback_mesh.subscribe(subject, callback)
        
        if not self.is_connected:
            logger.warning("Not connected, cannot subscribe")
            return None
        
        try:
            # Create subscription
            sid = f"sub_{len(self._subscriptions)}"
            
            async def wrapper(msg):
                try:
                    data = json.loads(msg.data.decode('utf-8')) if msg.data else {}
                    await callback(self, msg.subject, data)
                except Exception as e:
                    logger.error("Subscription callback error", subject=subject, error=str(e))
            
            sub = await self._nc.subscribe(subject, cb=wrapper)
            sub.sid = sid
            
            self._subscriptions[sid] = Subscription(
                subject=subject,
                callback=callback,
                sid=sid,
                active=True,
            )
            
            logger.info("Subscribed to subject", subject=subject, sid=sid)
            return sid
            
        except Exception as e:
            logger.error("Failed to subscribe", subject=subject, error=str(e))
            return None

    async def unsubscribe(self, sid: str) -> bool:
        """
        Unsubscribe by subscription ID.
        
        Args:
            sid: Subscription ID
            
        Returns:
            True if unsubscribed successfully
        """
        if self._use_fallback and self._fallback_mesh is not None:
            return await self._fallback_mesh.unsubscribe(sid)
        
        if sid not in self._subscriptions:
            logger.warning("Subscription not found", sid=sid)
            return False
        
        try:
            sub = self._subscriptions[sid]
            sub.active = False
            del self._subscriptions[sid]
            logger.info("Unsubscribed", sid=sid)
            return True
        except Exception as e:
            logger.error("Failed to unsubscribe", sid=sid, error=str(e))
            return False

    async def request(
        self,
        subject: str,
        data: Dict[str, Any],
        timeout: float = 5.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Request-reply pattern.
        
        Args:
            subject: Request subject
            data: Request data
            timeout: Request timeout in seconds
            
        Returns:
            Response data or None if timeout/error
        """
        if self._use_fallback and self._fallback_mesh is not None:
            return await self._fallback_mesh.request(subject, data, timeout)
        
        if not self.is_connected:
            logger.warning("Not connected, cannot request")
            return None
        
        try:
            message = json.dumps(data).encode('utf-8')
            msg = await self._nc.request(subject, message, timeout=timeout)
            
            if msg and msg.data:
                response = json.loads(msg.data.decode('utf-8'))
                logger.debug("Request response", subject=subject)
                return response
            
            return None
        except asyncio.TimeoutError:
            logger.warning("Request timeout", subject=subject, timeout=timeout)
            return None
        except Exception as e:
            logger.error("Request failed", subject=subject, error=str(e))
            return None

    def get_subscription_ids(self) -> Set[str]:
        """Get set of all active subscription IDs."""
        return {sid for sid, sub in self._subscriptions.items() if sub.active}

    async def close_all(self) -> None:
        """Close all connections and cleanup."""
        await self.disconnect()


class _InMemoryFallback:
    """In-memory fallback for when NATS is unavailable."""
    
    def __init__(self) -> None:
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._sub_counter = 0
        self._pending: Dict[str, asyncio.Future] = {}

    async def publish(self, subject: str, data: Dict[str, Any]) -> bool:
        """Publish to in-memory subscribers."""
        for sub in self._subscriptions.get(subject, []):
            try:
                await sub(subject, data)
            except Exception:
                pass
        return True

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[str, Dict[str, Any]], None],
    ) -> str:
        """Subscribe in-memory."""
        sid = f"mem_{self._sub_counter}"
        self._sub_counter += 1
        
        if subject not in self._subscriptions:
            self._subscriptions[subject] = []
        self._subscriptions[subject].append(callback)
        
        return sid

    async def unsubscribe(self, sid: str) -> bool:
        """Unsubscribe in-memory."""
        return True

    async def request(
        self,
        subject: str,
        data: Dict[str, Any],
        timeout: float,
    ) -> Optional[Dict[str, Any]]:
        """Request in-memory (no response by default)."""
        await self.publish(subject, data)
        return None


class NATSEventMeshMixin:
    """
    Mixin to add NATS EventMesh capabilities to existing EventMesh.
    
    Example:
        ```python
        class NATSEnabledEventMesh(NATSEventMeshMixin, EventMesh):
            pass
        
        mesh = NATSEnabledEventMesh()
        await mesh.setup_nats(servers=["nats://localhost:4222"])
        ```
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize mixin."""
        self._nats_mesh: Optional[NATSEventMesh] = None
        self._nats_enabled = False
        self._nats_config = kwargs.copy()
    
    async def setup_nats(
        self,
        servers: Optional[List[str]] = None,
        fallback: bool = True,
    ) -> bool:
        """
        Setup NATS EventMesh integration.
        
        Args:
            servers: List of NATS server URLs
            fallback: Enable fallback to in-memory
            
        Returns:
            True if NATS connection established
        """
        config = self._nats_config.copy()
        if servers:
            config["servers"] = servers
        config["fallback"] = fallback
        
        self._nats_mesh = NATSEventMesh(**config)
        self._nats_enabled = await self._nats_mesh.connect()
        
        return self._nats_enabled

    @property
    def nats_mesh(self) -> Optional[NATSEventMesh]:
        """Get NATS mesh instance."""
        return self._nats_mesh

    @property
    def nats_enabled(self) -> bool:
        """Check if NATS is enabled."""
        return self._nats_enabled


# =============================================================================
# JetStreamManager Integration
# =============================================================================

class NATSEventMeshWithJetStream(NATSEventMesh):
    """
    Enhanced NATSEventMesh with JetStreamManager integration.
    
    Combines the messaging capabilities of NATSEventMesh with the
    stream management features of JetStreamManager for comprehensive
    event mesh functionality.
    
    Example:
        ```python
        mesh = NATSEventMeshWithJetStream(
            servers=["nats://localhost:4222"],
            fallback=True
        )
        await mesh.connect()
        
        # Initialize default streams
        await mesh.initialize_jetstream()
        
        # Publish to stream
        await mesh.publish_to_stream(
            stream_name="AGENT_EVENTS",
            subject="agent.test.state",
            data={"state": "running"}
        )
        ```
    """
    
    def __init__(
        self,
        servers: Optional[List[str]] = None,
        name: Optional[str] = None,
        fallback: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_timewait: float = 1.0,
        ping_interval: int = 30,
        max_outstanding: int = 1000,
        zero_trust_enabled: bool = True,
    ) -> None:
        """
        Initialize enhanced NATSEventMesh with JetStream.
        
        Args:
            servers: List of NATS server URLs
            name: Client name
            fallback: Enable fallback to in-memory mesh
            max_reconnect_attempts: Max reconnection attempts
            reconnect_timewait: Time to wait between reconnect attempts
            ping_interval: Ping interval in seconds
            max_outstanding: Max pending messages
            zero_trust_enabled: Enable zero-trust security
        """
        super().__init__(
            servers=servers,
            name=name,
            fallback=fallback,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_timewait=reconnect_timewait,
            ping_interval=ping_interval,
            max_outstanding=max_outstanding,
        )
        
        # JetStream manager reference
        self._js_manager = None
        self._zero_trust_enabled = zero_trust_enabled
        
        logger.info("NATSEventMeshWithJetStream initialized")
    
    @property
    def jetstream_manager(self) -> Optional[Any]:
        """Get JetStream manager instance."""
        return self._js_manager
    
    @property
    def jetstream_ready(self) -> bool:
        """Check if JetStream is ready."""
        return self._js_manager is not None and self._js_manager.is_connected
    
    async def initialize_jetstream(
        self,
        create_default_streams: bool = True,
    ) -> bool:
        """
        Initialize JetStream manager and create streams.
        
        Args:
            create_default_streams: Create default stream configurations
            
        Returns:
            True if initialized successfully
        """
        if not self.is_connected:
            logger.warning("Not connected, cannot initialize JetStream")
            return False
        
        try:
            # Import JetStreamManager
            from heretek_swarm.gateway.jetstream_manager import (
                JetStreamManager,
                JetStreamConfig,
            )
            
            # Create manager
            self._js_manager = JetStreamManager(
                servers=self.servers,
                name=self.client_name,
                zero_trust_enabled=self._zero_trust_enabled,
                fallback_enabled=self.fallback,
            )
            
            # Connect
            connected = await self._js_manager.connect()
            if not connected:
                logger.warning("JetStreamManager connection failed")
                return False
            
            # Create default streams if requested
            if create_default_streams:
                results = await self._js_manager.initialize_default_streams()
                logger.info("Default streams initialized", results=results)
            
            logger.info("JetStream initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize JetStream: {e}")
            return False
    
    async def publish_event(
        self,
        stream_name: str,
        event_type: str,
        entity_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish a domain event to a stream.
        
        Args:
            stream_name: Target stream name
            event_type: Type of event (e.g., "agent.state.changed")
            entity_id: Entity identifier
            payload: Event payload
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            True if published successfully
        """
        if not self.jetstream_ready:
            # Fallback to regular publish
            subject = f"{stream_name}.{event_type}.{entity_id}"
            return await self.publish(subject, payload)
        
        # Build event envelope
        event = {
            "event_id": f"{event_type}-{entity_id}-{datetime.now(timezone.utc).timestamp()}",
            "event_type": event_type,
            "entity_id": entity_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        
        # Determine subject based on stream type
        if stream_name == "AGENT_EVENTS":
            subject = f"agent.{entity_id}.events"
        elif stream_name == "WORKFLOW_EVENTS":
            subject = f"workflow.{entity_id}.events"
        elif stream_name == "CONSCIOUSNESS_METRICS":
            subject = f"consciousness.{entity_id}.metrics"
        elif stream_name == "SYSTEM_HEALTH":
            subject = f"health.{entity_id}.metrics"
        else:
            subject = f"{stream_name}.{event_type}"
        
        return await self._js_manager.publish(
            stream_name=stream_name,
            subject=subject,
            data=event,
            correlation_id=correlation_id,
        )
    
    async def subscribe_to_events(
        self,
        stream_name: str,
        event_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        durable_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Subscribe to events from a stream.
        
        Args:
            stream_name: Source stream name
            event_type: Optional event type filter
            entity_id: Optional entity ID filter
            callback: Message callback function
            durable_name: Optional durable consumer name
            
        Returns:
            Consumer/subscription ID or None if failed
        """
        if not self.jetstream_ready:
            # Fallback to regular subscribe
            if event_type and entity_id:
                subject = f"{stream_name}.{event_type}.{entity_id}"
            elif event_type:
                subject = f"{stream_name}.{event_type}.>"
            else:
                subject = f"{stream_name}.>"
            return await self.subscribe(subject, callback)
        
        # Build subject filter
        if event_type and entity_id:
            subject_filter = f"agent.{entity_id}.events"
        elif event_type:
            subject_filter = f"agent.*.events"
        else:
            subject_filter = ">"
        
        # Create consumer config
        from heretek_swarm.gateway.jetstream_manager import (
            ConsumerConfig,
            DeliverPolicy,
            AckPolicy,
        )
        
        consumer_config = ConsumerConfig(
            durable_name=durable_name or f"consumer_{stream_name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            stream_name=stream_name,
            deliver_policy=DeliverPolicy.NEW,
            ack_policy=AckPolicy.EXPLICIT,
            filter_subject=subject_filter,
        )
        
        return await self._js_manager.create_consumer(consumer_config, callback)
    
    async def replay_events(
        self,
        stream_name: str,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None,
        event_type: Optional[str] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Replay events from a stream.
        
        Args:
            stream_name: Source stream name
            start_sequence: Start sequence number
            end_sequence: End sequence number
            event_type: Optional event type filter
            callback: Optional callback for each message
            
        Returns:
            List of replayed events
        """
        if not self.jetstream_ready:
            logger.warning("JetStream not ready, cannot replay events")
            return []
        
        # Build subject filter
        subject_filter = None
        if event_type:
            subject_filter = f"*.{event_type}.*"
        
        return await self._js_manager.replay_messages(
            stream_name=stream_name,
            start_sequence=start_sequence,
            end_sequence=end_sequence,
            subject_filter=subject_filter,
            callback=callback,
        )
    
    async def get_stream_stats(self, stream_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a stream.
        
        Args:
            stream_name: Stream name
            
        Returns:
            Stream statistics or None if not found
        """
        if not self.jetstream_ready:
            return None
        
        info = await self._js_manager.get_stream_info(stream_name)
        if not info:
            return None
        
        return info.to_dict()
    
    async def shutdown(self) -> None:
        """Shutdown JetStream and NATS connections."""
        if self._js_manager:
            await self._js_manager.disconnect()
            self._js_manager = None
        
        await self.disconnect()
        logger.info("NATSEventMeshWithJetStream shutdown complete")