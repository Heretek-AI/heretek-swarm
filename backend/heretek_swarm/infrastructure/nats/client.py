"""NATS Client for Heretek Swarm.

Provides async NATS connection management with OTel distributed tracing.
"""

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog

from heretek_swarm.infrastructure.otel.tracing import (
    SpanStatus,
    get_tracer,
)

if TYPE_CHECKING:
    from heretek_swarm.infrastructure.otel.tracing import TracingConfig

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

    url: str = ""
    name: str = "heretek-swarm"
    max_reconnect_attempts: int = 60
    reconnect_time_wait: float = 2.0
    timeout: float = 30.0
    user_credentials: str | None = None
    nkey_seed: str | None = None
    tracing_config: "TracingConfig | None" = None

    def __post_init__(self) -> None:
        """Resolve NATS URL from env var when not explicitly set."""
        if not self.url:
            nats_url = os.getenv("HERETEK_NATS_URL")
            if not nats_url:
                raise RuntimeError(
                    "HERETEK_NATS_URL is required. Set it to nats://host:port "
                    "or use docker compose."
                )
            self.url = nats_url


@dataclass
class NATSClient:
    """
    Async NATS client wrapper with OTel tracing.

    Provides connection management, topic subscription,
    and distributed tracing for the Heretek Swarm event mesh.
    """

    config: NATSConfig = field(default_factory=NATSConfig)
    _connection: Any = field(default=None, repr=False)
    _state: ConnectionState = field(default=ConnectionState.DISCONNECTED)
    _subscriptions: dict[str, Any] = field(default_factory=dict)
    _tracer: Any = field(default=None)

    def __post_init__(self) -> None:
        """Initialize tracer after dataclass initialization."""
        self._tracer = get_tracer("nats-client")

    async def connect(self) -> bool:
        """
        Establish NATS connection with tracing.

        Returns:
            True if connection successful
        """
        with self._tracer.start_as_current_span(
            "nats.connect",
            kind="client",
            attributes={
                "nats.url": self.config.url,
                "nats.client_name": self.config.name,
            },
        ) as span:
            try:
                self._state = ConnectionState.CONNECTING
                logger.info("nats_connecting", url=self.config.url)

                # Try to import nats library
                try:
                    import nats
                except ImportError:
                    logger.warning(
                        "nats_not_installed",
                        url="https://github.com/nats-io/nats.py",
                    )
                    span.set_status(SpanStatus.ERROR, "nats library not installed")
                    self._state = ConnectionState.FAILED
                    return False

                self._connection = await nats.connect(
                    self.config.url,
                    name=self.config.name,
                    max_reconnect_attempts=self.config.max_reconnect_attempts,
                    reconnect_time_wait=self.config.reconnect_time_wait,
                )

                self._state = ConnectionState.CONNECTED
                span.set_status(SpanStatus.OK)
                logger.info("nats_connected", url=self.config.url)
                return True

            except Exception as e:
                logger.error("nats_connection_failed", error=str(e))
                span.record_exception(e)
                span.set_status(SpanStatus.ERROR, str(e))
                self._state = ConnectionState.FAILED
                return False

    async def disconnect(self) -> None:
        """Close NATS connection with tracing."""
        with self._tracer.start_as_current_span(
            "nats.disconnect",
            kind="client",
            attributes={
                "nats.was_connected": self.is_connected,
                "nats.subscription_count": len(self._subscriptions),
            },
        ) as span:
            try:
                if self._connection:
                    await self._connection.close()
                    logger.info("nats_disconnected")
            except Exception as e:
                logger.warning("nats_disconnect_error", error=str(e))
                span.record_exception(e)
            finally:
                self._connection = None
                self._state = ConnectionState.DISCONNECTED
                span.set_status(SpanStatus.OK)

    async def publish(
        self,
        subject: str,
        payload: bytes | str | dict,
        trace_context: dict[str, str] | None = None,
    ) -> bool:
        """
        Publish message to NATS subject with tracing.

        Args:
            subject: NATS subject/topic
            payload: Message payload
            trace_context: Optional trace context to inject into headers

        Returns:
            True if published successfully
        """
        with self._tracer.start_as_current_span(
            "nats.publish",
            kind="producer",
            attributes={
                "messaging.system": "nats",
                "messaging.destination": subject,
                "messaging.operation": "publish",
            },
        ) as span:
            if self._state != ConnectionState.CONNECTED:
                logger.warning("nats_not_connected", state=self._state.value)
                span.set_status(SpanStatus.ERROR, "not connected")
                return False

            try:
                if isinstance(payload, dict):
                    import json

                    payload = json.dumps(payload).encode()
                elif isinstance(payload, str):
                    payload = payload.encode()

                # Inject trace context into headers if provided
                headers = {}
                if trace_context:
                    headers["tracecontext"] = json.dumps(trace_context)
                elif span.trace_id:
                    headers["tracecontext"] = json.dumps(
                        {
                            "trace_id": span.trace_id,
                            "span_id": span.span_id,
                        }
                    )

                # Publish with optional headers
                if headers:
                    await self._connection.publish(subject, payload, headers=headers)
                else:
                    await self._connection.publish(subject, payload)

                span.set_status(SpanStatus.OK)
                logger.debug("nats_published", subject=subject)
                return True

            except Exception as e:
                logger.error("nats_publish_failed", subject=subject, error=str(e))
                span.record_exception(e)
                span.set_status(SpanStatus.ERROR, str(e))
                return False

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[str, bytes], None],
        queue: str | None = None,
    ) -> str | None:
        """
        Subscribe to NATS subject with tracing.

        Args:
            subject: Subject pattern to subscribe to
            callback: Async callback for messages
            queue: Optional queue group

        Returns:
            Subscription ID or None
        """
        with self._tracer.start_as_current_span(
            "nats.subscribe",
            kind="consumer",
            attributes={
                "messaging.system": "nats",
                "messaging.destination": subject,
                "messaging.operation": "subscribe",
                "messaging.queue": queue or "",
            },
        ) as span:
            if self._state != ConnectionState.CONNECTED:
                logger.warning("nats_not_connected", state=self._state.value)
                span.set_status(SpanStatus.ERROR, "not connected")
                return None

            try:
                sub = await self._connection.subscribe(
                    subject,
                    cb=callback,
                    queue=queue,
                )
                sub_id = f"{subject}:{datetime.now(UTC).timestamp()}"
                self._subscriptions[sub_id] = sub
                span.set_status(SpanStatus.OK)
                logger.info("nats_subscribed", subject=subject, queue=queue)
                return sub_id

            except Exception as e:
                logger.error("nats_subscribe_failed", subject=subject, error=str(e))
                span.record_exception(e)
                span.set_status(SpanStatus.ERROR, str(e))
                return None

    async def unsubscribe(self, sub_id: str) -> bool:
        """
        Unsubscribe from a subject with tracing.

        Args:
            sub_id: Subscription ID to remove

        Returns:
            True if unsubscribed successfully
        """
        with self._tracer.start_as_current_span(
            "nats.unsubscribe",
            kind="consumer",
            attributes={
                "messaging.operation": "unsubscribe",
                "nats.subscription_id": sub_id,
            },
        ) as span:
            if sub_id not in self._subscriptions:
                span.set_status(SpanStatus.ERROR, "subscription not found")
                return False

            try:
                await self._subscriptions[sub_id].unsubscribe()
                del self._subscriptions[sub_id]
                span.set_status(SpanStatus.OK)
                logger.info("nats_unsubscribed", sub_id=sub_id)
                return True

            except Exception as e:
                logger.warning("nats_unsubscribe_error", sub_id=sub_id, error=str(e))
                span.record_exception(e)
                span.set_status(SpanStatus.ERROR, str(e))
                return False

    async def request(
        self,
        subject: str,
        payload: bytes | str | dict,
        timeout_sec: float = 5.0,
    ) -> bytes | None:
        """
        Make a request and wait for a response with tracing.

        Args:
            subject: Subject to send request to
            payload: Request payload
            timeout: Timeout in seconds

        Returns:
            Response payload or None
        """
        import asyncio

        with self._tracer.start_as_current_span(
            "nats.request",
            kind="client",
            attributes={
                "messaging.system": "nats",
                "messaging.destination": subject,
                "messaging.operation": "request",
                "messaging.timeout_ms": int(timeout_sec * 1000),
            },
        ) as span:
            if self._state != ConnectionState.CONNECTED:
                span.set_status(SpanStatus.ERROR, "not connected")
                return None

            try:
                if isinstance(payload, dict):
                    import json

                    payload = json.dumps(payload).encode()
                elif isinstance(payload, str):
                    payload = payload.encode()

                msg = await asyncio.wait_for(
                    self._connection.request(subject, payload),
                    timeout_sec=timeout_sec,
                )
                span.set_status(SpanStatus.OK)
                return msg.data

            except TimeoutError:
                logger.error("nats_request_timeout", subject=subject, timeout_sec=timeout_sec)
                span.set_status(SpanStatus.ERROR, "request timeout")
                return None
            except Exception as e:
                logger.error("nats_request_failed", subject=subject, error=str(e))
                span.record_exception(e)
                span.set_status(SpanStatus.ERROR, str(e))
                return None

    def extract_trace_context(self, msg: Any) -> dict[str, str] | None:
        """
        Extract trace context from a received message.

        Args:
            msg: NATS message with optional headers

        Returns:
            Trace context dict or None
        """
        try:
            if hasattr(msg, "headers") and msg.headers:
                trace_context = msg.headers.get("tracecontext")
                if trace_context:
                    import json

                    return json.loads(trace_context)
        except Exception as e:
            logger.warning("trace_context_extract_failed", error=str(e))
        return None

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._state == ConnectionState.CONNECTED

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def subscription_count(self) -> int:
        """Get number of active subscriptions."""
        return len(self._subscriptions)


# Global client instance
_client: NATSClient | None = None


def get_nats_client(config: NATSConfig | None = None) -> NATSClient:
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


__all__ = [
    "ConnectionState",
    "NATSClient",
    "NATSConfig",
    "get_nats_client",
    "shutdown_nats_client",
]
