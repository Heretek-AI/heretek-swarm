"""
Nexus Agent - External Integration Specialist

Tier 5 Coordination Agent responsible for:
- External API connections and integrations
- Protocol translation between internal and external systems
- Webhook management and event ingestion
- Third-party service orchestration
- API rate limiting and quota management

Author: Heretek Swarm Collective
Date: 2026-04-06
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
import structlog

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.validation import validate_message

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position, SwarmDeliberationEngine

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator
from heretek_swarm.validation import (
    LLMOutputValidator,
)

logger = structlog.get_logger(__name__)


class ConnectionStatus(Enum):
    """Status of an external connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILED = "auth_failed"


class ProtocolType(Enum):
    """Supported external protocols."""
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    WEBHOOK = "webhook"
    MQTT = "mqtt"


@dataclass
class ExternalConnection:
    """Configuration for an external service connection."""
    connection_id: str
    name: str
    protocol: ProtocolType
    base_url: str
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    headers: Dict[str, str] = field(default_factory=dict)
    auth_type: Optional[str] = None  # bearer, basic, api_key, oauth2
    auth_config: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[int] = None  # requests per minute
    rate_limit_remaining: int = 0
    rate_limit_reset: Optional[datetime] = None
    last_request: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "connection_id": self.connection_id,
            "name": self.name,
            "protocol": self.protocol.value,
            "base_url": self.base_url,
            "status": self.status.value,
            "auth_type": self.auth_type,
            "rate_limit": self.rate_limit,
            "rate_limit_remaining": self.rate_limit_remaining,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    webhook_id: str
    name: str
    path: str
    secret: str
    active: bool = True
    allowed_methods: List[str] = field(default_factory=lambda: ["POST"])
    allowed_ips: Optional[List[str]] = None
    rate_limit: Optional[int] = None  # requests per minute
    request_count: int = 0
    last_request: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "webhook_id": self.webhook_id,
            "name": self.name,
            "path": self.path,
            "active": self.active,
            "allowed_methods": self.allowed_methods,
            "request_count": self.request_count,
            "last_request": self.last_request.isoformat() if self.last_request else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ApiResponse:
    """Standardized API response."""
    success: bool
    status_code: int
    data: Any
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "status_code": self.status_code,
            "data": self.data,
            "headers": self.headers,
            "error": self.error,
            "request_id": self.request_id,
            "latency_ms": self.latency_ms,
        }


class NexusAgent(AgentActor):
    """
    External Integration Specialist.

    Responsibilities:
    - Manage external API connections
    - Handle webhook registrations and validations
    - Translate between internal and external protocols
    - Enforce rate limits and quotas
    - Provide unified API interface for all external integrations

    Message Handlers:
    - create_connection: Create new external connection
    - update_connection: Update connection configuration
    - delete_connection: Remove external connection
    - get_connection_status: Get status of a connection
    - execute_request: Execute HTTP request through connection
    - register_webhook: Register webhook endpoint
    - unregister_webhook: Remove webhook registration
    - validate_webhook: Validate webhook signature
    - get_webhook_status: Get webhook statistics
    - translate_protocol: Translate between protocols
    - get_integration_report: Generate integration status report
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,

        # Session 44: Integration components
        pattern_extractor: Optional[PatternExtractor] = None,
        deliberation_engine: Optional[SwarmDeliberationEngine] = None,
        access_analyzer: Optional[AccessPatternAnalyzer] = None,
        zero_trust_validator: Optional[ZeroTrustValidator] = None,
):
        super().__init__(
            agent_id=agent_id or f"nexus_{uuid.uuid4().hex[:8]}",
            config=config or {},
        )

        # Connection management
        self._connections: Dict[str, ExternalConnection] = {}
        self._max_connections: int = self._config.get("max_connections", 50)

        # Webhook management
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._webhook_handlers: Dict[str, Callable] = {}
        self._max_webhooks: int = self._config.get("max_webhooks", 100)

        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None

        # Request tracking
        self._request_log: List[Dict[str, Any]] = []
        self._max_log_entries: int = self._config.get("max_request_log", 1000)


        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: LLM Output Validation
        self.llm_output_validator = LLMOutputValidator(strict_mode=True)

        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(
            "nexus_initialized",
            agent_id=self.agent_id,
            max_connections=self._max_connections,
            max_webhooks=self._max_webhooks,
        )

    async def initialize(self) -> None:
        """Initialize the Nexus agent."""
        await super().initialize()
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._config.get("timeout", 30)),
        )
        logger.info("nexus_http_session_initialized")

    async def terminate(self) -> None:
        """Terminate the Nexus agent."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("nexus_http_session_closed")
        await super().terminate()

    async def _validate_message(self, message: ActorMessage) -> Dict[str, Any]:
        """Validate incoming message content."""
        try:
            validated = validate_message(message.message_type, message.content)
            if hasattr(validated, 'dict'):
                return validated.dict()
            return validated
        except Exception:
            # Fallback: return content as-is for unknown message types
            return message.content

    async def _handle_create_connection(self, message: ActorMessage) -> None:
        """
        Create a new external connection.

        Content:
        - connection_id: Optional[str]
        - name: str
        - protocol: str (rest|graphql|websocket|grpc|webhook|mqtt)
        - base_url: str
        - headers: Optional[Dict]
        - auth_type: Optional[str] (bearer|basic|api_key|oauth2)
        - auth_config: Optional[Dict]
        - rate_limit: Optional[int]
        - metadata: Optional[Dict]
        """
        try:
            content = await self._validate_message(message)

            if len(self._connections) >= self._max_connections:
                await self._send_error(
                    message.sender_id,
                    f"Connection limit reached ({self._max_connections})",
                    message.message_type,
                )
                return

            connection_id = content.get("connection_id") or f"conn_{uuid.uuid4().hex[:12]}"

            if connection_id in self._connections:
                await self._send_error(
                    message.sender_id,
                    f"Connection {connection_id} already exists",
                    message.message_type,
                )
                return

            protocol = ProtocolType(content.get("protocol", "rest"))
            connection = ExternalConnection(
                connection_id=connection_id,
                name=content.get("name", "Unnamed"),
                protocol=protocol,
                base_url=content.get("base_url", ""),
                headers=content.get("headers", {}),
                auth_type=content.get("auth_type"),
                auth_config=content.get("auth_config", {}),
                rate_limit=content.get("rate_limit"),
                rate_limit_remaining=content.get("rate_limit", 100),
                metadata=content.get("metadata", {}),
            )

            self._connections[connection_id] = connection

            logger.info(
                "connection_created",
                connection_id=connection_id,
                name=connection.name,
                protocol=protocol.value,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="connection_created",
                    content={"connection": connection.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("create_connection_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to create connection: {str(e)}",
                message.message_type,
            )

    async def _handle_update_connection(self, message: ActorMessage) -> None:
        """
        Update an existing connection.

        Content:
        - connection_id: str
        - updates: Dict (fields to update)
        """
        try:
            content = await self._validate_message(message)
            connection_id = content.get("connection_id")

            if not connection_id or connection_id not in self._connections:
                await self._send_error(
                    message.sender_id,
                    f"Connection {connection_id} not found",
                    message.message_type,
                )
                return

            connection = self._connections[connection_id]
            updates = content.get("updates", {})

            for key, value in updates.items():
                if hasattr(connection, key):
                    setattr(connection, key, value)

            logger.info(
                "connection_updated",
                connection_id=connection_id,
                updates=list(updates.keys()),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="connection_updated",
                    content={"connection": connection.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("update_connection_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to update connection: {str(e)}",
                message.message_type,
            )

    async def _handle_delete_connection(self, message: ActorMessage) -> None:
        """
        Delete a connection.

        Content:
        - connection_id: str
        """
        try:
            content = await self._validate_message(message)
            connection_id = content.get("connection_id")

            if not connection_id or connection_id not in self._connections:
                await self._send_error(
                    message.sender_id,
                    f"Connection {connection_id} not found",
                    message.message_type,
                )
                return

            del self._connections[connection_id]

            logger.info(
                "connection_deleted",
                connection_id=connection_id,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="connection_deleted",
                    content={"connection_id": connection_id},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("delete_connection_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to delete connection: {str(e)}",
                message.message_type,
            )

    async def _handle_get_connection_status(self, message: ActorMessage) -> None:
        """
        Get status of a connection.

        Content:
        - connection_id: str (optional, returns all if not provided)
        """
        try:
            content = await self._validate_message(message)
            connection_id = content.get("connection_id")

            if connection_id:
                if connection_id not in self._connections:
                    await self._send_error(
                        message.sender_id,
                        f"Connection {connection_id} not found",
                        message.message_type,
                    )
                    return
                connections = [self._connections[connection_id].to_dict()]
            else:
                connections = [conn.to_dict() for conn in self._connections.values()]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="connection_status",
                    content={"connections": connections},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_connection_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get connection status: {str(e)}",
                message.message_type,
            )

    async def _handle_execute_request(self, message: ActorMessage) -> None:
        """
        Execute an HTTP request through a connection.

        Content:
        - connection_id: str
        - method: str (GET|POST|PUT|DELETE|PATCH)
        - path: str
        - body: Optional[Any]
        - headers: Optional[Dict]
        - params: Optional[Dict]
        """
        try:
            content = await self._validate_message(message)
            connection_id = content.get("connection_id")

            if not connection_id or connection_id not in self._connections:
                await self._send_error(
                    message.sender_id,
                    f"Connection {connection_id} not found",
                    message.message_type,
                )
                return

            connection = self._connections[connection_id]

            # Check rate limit
            if connection.rate_limit:
                if connection.rate_limit_remaining <= 0:
                    connection.status = ConnectionStatus.RATE_LIMITED
                    await self._send_error(
                        message.sender_id,
                        "Rate limit exceeded",
                        message.message_type,
                    )
                    return

            if not self._session:
                await self._send_error(
                    message.sender_id,
                    "HTTP session not initialized",
                    message.message_type,
                )
                return

            # Build URL
            url = f"{connection.base_url}{content.get('path', '')}"

            # Prepare headers
            headers = {**connection.headers, **(content.get("headers", {}))}

            # Add auth if configured
            if connection.auth_type == "bearer" and connection.auth_config.get("token"):
                headers["Authorization"] = f"Bearer {connection.auth_config['token']}"
            elif connection.auth_type == "basic":
                import base64
                creds = f"{connection.auth_config.get('username', '')}:{connection.auth_config.get('password', '')}"
                headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
            elif connection.auth_type == "api_key":
                headers[connection.auth_config.get("header", "X-API-Key")] = connection.auth_config.get("key", "")

            # Execute request
            start_time = datetime.now(timezone.utc)
            method = content.get("method", "GET").upper()

            async with self._session.request(
                method,
                url,
                headers=headers,
                json=content.get("body"),
                params=content.get("params"),
            ) as response:
                latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

                try:
                    data = await response.json()
                except:
                    data = await response.text()

                # Update connection stats
                connection.last_request = datetime.now(timezone.utc)
                connection.total_requests += 1
                connection.rate_limit_remaining = max(0, connection.rate_limit_remaining - 1)

                if response.status >= 400:
                    connection.failed_requests += 1
                    connection.status = ConnectionStatus.ERROR

                api_response = ApiResponse(
                    success=200 <= response.status < 300,
                    status_code=response.status,
                    data=data,
                    headers=dict(response.headers),
                    latency_ms=int(latency),
                )

                # Log request
                self._log_request(connection_id, method, url, response.status, latency)

                await self.send(
                    message.sender_id,
                    ActorMessage(
                        message_type="request_completed",
                        content={"response": api_response.to_dict()},
                        sender_id=self.agent_id,
                    ),
                )

        except Exception as e:
            logger.error("execute_request_failed", error=str(e))
            if connection_id in self._connections:
                self._connections[connection_id].failed_requests += 1
                self._connections[connection_id].status = ConnectionStatus.ERROR
            await self._send_error(
                message.sender_id,
                f"Request failed: {str(e)}",
                message.message_type,
            )

    async def _handle_register_webhook(self, message: ActorMessage) -> None:
        """
        Register a webhook endpoint.

        Content:
        - webhook_id: Optional[str]
        - name: str
        - path: str
        - secret: str
        - allowed_methods: Optional[List[str]]
        - allowed_ips: Optional[List[str]]
        - rate_limit: Optional[int]
        """
        try:
            content = await self._validate_message(message)

            if len(self._webhooks) >= self._max_webhooks:
                await self._send_error(
                    message.sender_id,
                    f"Webhook limit reached ({self._max_webhooks})",
                    message.message_type,
                )
                return

            webhook_id = content.get("webhook_id") or f"webhook_{uuid.uuid4().hex[:12]}"

            webhook = WebhookConfig(
                webhook_id=webhook_id,
                name=content.get("name", "Unnamed"),
                path=content.get("path", f"/webhook/{webhook_id}"),
                secret=content.get("secret", str(uuid.uuid4())),
                allowed_methods=content.get("allowed_methods", ["POST"]),
                allowed_ips=content.get("allowed_ips"),
                rate_limit=content.get("rate_limit"),
            )

            self._webhooks[webhook_id] = webhook

            logger.info(
                "webhook_registered",
                webhook_id=webhook_id,
                path=webhook.path,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="webhook_registered",
                    content={"webhook": webhook.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("register_webhook_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to register webhook: {str(e)}",
                message.message_type,
            )

    async def _handle_unregister_webhook(self, message: ActorMessage) -> None:
        """
        Unregister a webhook.

        Content:
        - webhook_id: str
        """
        try:
            content = await self._validate_message(message)
            webhook_id = content.get("webhook_id")

            if not webhook_id or webhook_id not in self._webhooks:
                await self._send_error(
                    message.sender_id,
                    f"Webhook {webhook_id} not found",
                    message.message_type,
                )
                return

            del self._webhooks[webhook_id]

            logger.info(
                "webhook_unregistered",
                webhook_id=webhook_id,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="webhook_unregistered",
                    content={"webhook_id": webhook_id},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("unregister_webhook_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to unregister webhook: {str(e)}",
                message.message_type,
            )

    async def _handle_validate_webhook(self, message: ActorMessage) -> None:
        """
        Validate webhook signature.

        Content:
        - webhook_id: str
        - payload: Any
        - signature: str
        - timestamp: Optional[int]
        """
        try:
            content = await self._validate_message(message)
            webhook_id = content.get("webhook_id")

            if not webhook_id or webhook_id not in self._webhooks:
                await self._send_error(
                    message.sender_id,
                    f"Webhook {webhook_id} not found",
                    message.message_type,
                )
                return

            webhook = self._webhooks[webhook_id]
            payload = content.get("payload")
            signature = content.get("signature")
            timestamp = content.get("timestamp")

            # Validate timestamp (prevent replay attacks)
            if timestamp:
                now = int(datetime.now(timezone.utc).timestamp())
                if abs(now - timestamp) > 300:  # 5 minute window
                    await self.send(
                        message.sender_id,
                        ActorMessage(
                            message_type="webhook_validation",
                            content={"valid": False, "reason": "timestamp_expired"},
                            sender_id=self.agent_id,
                        ),
                    )
                    return

            # Calculate expected signature
            payload_str = json.dumps(payload, sort_keys=True) if isinstance(payload, dict) else str(payload)
            expected_signature = hmac.new(
                webhook.secret.encode(),
                f"{payload_str}{timestamp or ''}".encode(),
                hashlib.sha256,
            ).hexdigest()

            valid = hmac.compare_digest(signature, expected_signature)

            if valid:
                webhook.request_count += 1
                webhook.last_request = datetime.now(timezone.utc)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="webhook_validation",
                    content={"valid": valid},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("validate_webhook_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to validate webhook: {str(e)}",
                message.message_type,
            )

    async def _handle_get_webhook_status(self, message: ActorMessage) -> None:
        """
        Get webhook status.

        Content:
        - webhook_id: str (optional, returns all if not provided)
        """
        try:
            content = await self._validate_message(message)
            webhook_id = content.get("webhook_id")

            if webhook_id:
                if webhook_id not in self._webhooks:
                    await self._send_error(
                        message.sender_id,
                        f"Webhook {webhook_id} not found",
                        message.message_type,
                    )
                    return
                webhooks = [self._webhooks[webhook_id].to_dict()]
            else:
                webhooks = [wh.to_dict() for wh in self._webhooks.values()]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="webhook_status",
                    content={"webhooks": webhooks},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_webhook_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get webhook status: {str(e)}",
                message.message_type,
            )

    async def _handle_translate_protocol(self, message: ActorMessage) -> None:
        """
        Translate between protocols.

        Content:
        - from_protocol: str
        - to_protocol: str
        - data: Any
        """
        try:
            content = await self._validate_message(message)
            from_proto = content.get("from_protocol", "internal")
            to_proto = content.get("to_protocol", "rest")
            data = content.get("data")

            # Translation logic
            translated = self._translate_data(from_proto, to_proto, data)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="protocol_translated",
                    content={
                        "from": from_proto,
                        "to": to_proto,
                        "translated_data": translated,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("translate_protocol_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to translate protocol: {str(e)}",
                message.message_type,
            )

    async def _handle_get_integration_report(self, message: ActorMessage) -> None:
        """
        Generate integration status report.

        Content: (none required)
        """
        try:
            # Connection statistics
            conn_stats = {
                "total": len(self._connections),
                "by_status": {},
                "by_protocol": {},
                "total_requests": sum(c.total_requests for c in self._connections.values()),
                "failed_requests": sum(c.failed_requests for c in self._connections.values()),
            }

            for conn in self._connections.values():
                status = conn.status.value
                conn_stats["by_status"][status] = conn_stats["by_status"].get(status, 0) + 1
                protocol = conn.protocol.value
                conn_stats["by_protocol"][protocol] = conn_stats["by_protocol"].get(protocol, 0) + 1

            # Webhook statistics
            webhook_stats = {
                "total": len(self._webhooks),
                "active": sum(1 for w in self._webhooks.values() if w.active),
                "total_requests": sum(w.request_count for w in self._webhooks.values()),
            }

            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connection_statistics": conn_stats,
                "webhook_statistics": webhook_stats,
                "request_log_size": len(self._request_log),
            }

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="integration_report",
                    content=report,
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_integration_report_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to generate report: {str(e)}",
                message.message_type,
            )

    def _translate_data(self, from_proto: str, to_proto: str, data: Any) -> Any:
        """Translate data between protocols."""
        # Simple translation - can be extended based on needs
        if from_proto == to_proto:
            return data

        # Internal to REST
        if from_proto == "internal" and to_proto == "rest":
            return {"data": data, "timestamp": datetime.now(timezone.utc).isoformat()}

        # REST to Internal
        if from_proto == "rest" and to_proto == "internal":
            if isinstance(data, dict):
                return data.get("data", data)
            return data

        # Default: return as-is
        return data

    def _log_request(
        self,
        connection_id: str,
        method: str,
        url: str,
        status: int,
        latency_ms: float,
    ) -> None:
        """Log a request for audit purposes."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connection_id": connection_id,
            "method": method,
            "url": url,
            "status": status,
            "latency_ms": latency_ms,
        }
        self._request_log.append(entry)

        # Trim log if needed
        if len(self._request_log) > self._max_log_entries:
            self._request_log = self._request_log[-self._max_log_entries:]


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]] = None) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: List[str],
        domain: str = "general",
    ) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)

            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def _send_error(
        self,
        recipient: str,
        error_message: str,
        original_type: str,
    ) -> None:
        """Send error response."""
        await self.send(
            recipient,
            ActorMessage(
                message_type="error",
                content={"error": error_message, "original_type": original_type},
                sender_id=self.agent_id,
            ),
        )

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "external_api_integration",
            "webhook_management",
            "protocol_translation",
            "rate_limiting",
            "authentication_handling",
            "request_logging",
        ]
