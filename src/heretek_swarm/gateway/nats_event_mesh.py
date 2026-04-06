"""
NATSEventMesh - NATS EventMesh Integration for Heretek Swarm

This module provides NATS-based event mesh integration:
- Asynchronous connection management with connection pooling
- Publish/subscribe patterns
- Request-reply pattern with timeout
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
        
        # Subscriptions
        self._subscriptions: Dict[str, Subscription] = {}
        self._subscription_ids: Set[str] = set()
        
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
    def client_count(self) -> int:
        """Get number of active subscriptions."""
        return len([s for s in self._subscriptions.values() if s.active])

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