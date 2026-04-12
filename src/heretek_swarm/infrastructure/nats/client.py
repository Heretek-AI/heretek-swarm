"""
NATS Client for Heretek Swarm.

Provides async NATS connection management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger("nats.client")


class ConnectionState(Enum):
    """NATS connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class NATSConfig:
    """Configuration for NATS connection."""
    url: str = "nats://localhost:4222"
    name: str = "heretek-swarm"
    max_reconnect_attempts: int = 60
    reconnect_time_step: float = 2.0
    timeout: float = 30.0
    user_credentials: str | None = None
    nkey_seed: str | None = None


@dataclass
class NATSClient:
    """
    Async NATS client wrapper.

    Provides connection management and topic subscription
    for the Heretek Swarm event mesh.
    """
    config: NATSConfig = field(default_factory=NATSConfig)
    _connection: Any = field(default=None, repr=False)
    _state: ConnectionState = field(default=ConnectionState.DISCONNECTED)
    _subscriptions: dict[str, Any] = field(default_factory=dict)

    async def connect(self) -> bool:
        """
        Establish NATS connection.

        Returns:
            True if connection successful
        """
        try:
            self._state = ConnectionState.CONNECTING
            logger.info("nats_connecting", url=self.config.url)

            # Try to import nats library
            try:
                import nats
            except ImportError:
                logger.warning("nats_not_installed", url="https://github.com/nats-io/nats.py")
                self._state = ConnectionState.FAILED
                return False

            self._connection = await nats.connect(
                self.config.url,
                name=self.config.name,
                max_reconnect_attempts=self.config.max_reconnect_attempts,
                reconnect_time_step=self.config.reconnect_time_step,
            )

            self._state = ConnectionState.CONNECTED
            logger.info("nats_connected", url=self.config.url)
            return True

        except Exception as e:
            logger.error("nats_connection_failed", error=str(e))
            self._state = ConnectionState.FAILED
            return False

    async def disconnect(self) -> None:
        """Close NATS connection."""
        if self._connection:
            try:
                await self._connection.close()
                logger.info("nats_disconnected")
            except Exception as e:
                logger.warning("nats_disconnect_error", error=str(e))
            finally:
                self._connection = None
                self._state = ConnectionState.DISCONNECTED

    async def publish(self, subject: str, payload: bytes | str | dict) -> bool:
        """
        Publish message to NATS subject.

        Args:
            subject: NATS subject/topic
            payload: Message payload

        Returns:
            True if published successfully
        """
        if self._state != ConnectionState.CONNECTED:
            logger.warning("nats_not_connected", state=self._state.value)
            return False

        try:
            if isinstance(payload, dict):
                import json
                payload = json.dumps(payload).encode()
            elif isinstance(payload, str):
                payload = payload.encode()

            await self._connection.publish(subject, payload)
            logger.debug("nats_published", subject=subject)
            return True

        except Exception as e:
            logger.error("nats_publish_failed", subject=subject, error=str(e))
            return False

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[str, bytes], None],
        queue: str | None = None,
    ) -> str | None:
        """
        Subscribe to NATS subject.

        Args:
            subject: Subject pattern to subscribe to
            callback: Async callback for messages
            queue: Optional queue group

        Returns:
            Subscription ID or None
        """
        if self._state != ConnectionState.CONNECTED:
            logger.warning("nats_not_connected", state=self._state.value)
            return None

        try:
            sub = await self._connection.subscribe(
                subject,
                cb=callback,
                queue=queue,
            )
            sub_id = f"{subject}:{datetime.utcnow().timestamp()}"
            self._subscriptions[sub_id] = sub
            logger.info("nats_subscribed", subject=subject, queue=queue)
            return sub_id

        except Exception as e:
            logger.error("nats_subscribe_failed", subject=subject, error=str(e))
            return None

    async def unsubscribe(self, sub_id: str) -> bool:
        """Unsubscribe from a subject."""
        if sub_id in self._subscriptions:
            try:
                await self._subscriptions[sub_id].unsubscribe()
                del self._subscriptions[sub_id]
                return True
            except Exception as e:
                logger.warning("nats_unsubscribe_error", sub_id=sub_id, error=str(e))
        return False

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._state == ConnectionState.CONNECTED

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state


# Global client instance
_client: NATSClient | None = None


async def get_nats_client(config: NATSConfig | None = None) -> NATSClient:
    """Get or create global NATS client."""
    global _client
    if _client is None:
        _client = NATSClient(config=config or NATSConfig())
    return _client


async def shutdown_nats_client() -> None:
    """Shutdown global NATS client."""
    global _client
    if _client:
        await _client.disconnect()
        _client = None
