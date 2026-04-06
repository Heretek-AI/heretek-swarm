# Gateway & Communication

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)

Agent-to-Agent communication, event mesh, and authentication layers for the Heretek Swarm system.

---

## Table of Contents

1. [EventMesh](#eventmesh)
2. [A2A Protocol Server](#a2a-protocol-server)
3. [Authentication](#authentication)
4. [NATS Event Mesh](#nats-event-mesh)

---

## EventMesh

**File:** [`src/heretek_swarm/gateway/event_mesh.py`](../src/heretek_swarm/gateway/event_mesh.py)

WebSocket connection manager for real-time communication.

```python
class EventMesh:
    """Manages WebSocket connections and broadcasting."""
    
    def register(self, client_id: str, websocket: WebSocket) -> None:
        """Register WebSocket client."""
        
    def unregister(self, client_id: str) -> None:
        """Unregister and cleanup client."""
        
    async def broadcast(self, message: bytes) -> None:
        """Broadcast to all connected clients."""
        
    async def send_to(self, client_id: str, message: bytes) -> None:
        """Send to specific client."""
```

### Features

- **Client Registration**: Track connected WebSocket clients
- **Broadcast**: Send messages to all connected clients
- **Direct Messaging**: Send to specific client by ID
- **Connection Cleanup**: Automatic cleanup on disconnect

### Usage

```python
# Register a new client
event_mesh.register("client-001", websocket)

# Broadcast to all clients
await event_mesh.broadcast(b"message")

# Send to specific client
await event_mesh.send_to("client-001", b"direct message")

# Unregister client
event_mesh.unregister("client-001")
```

---

## A2A Protocol Server

**File:** [`src/heretek_swarm/gateway/a2a_server.py`](../src/heretek_swarm/gateway/a2a_server.py)

Agent-to-Agent communication server running on port 18789.

```python
class A2AServer:
    """A2A communication server on port 18789."""
    
    async def handle_handshake(self, websocket: WebSocket, agent_id: str) -> None:
        """Process agent handshake."""
        
    async def handle_discovery(self, requesting_agent: str) -> Dict[str, Any]:
        """Return list of connected agents."""
```

### Protocol Flow

1. **Handshake**: Agent connects and authenticates
2. **Discovery**: Agent discovers other connected agents
3. **Message Exchange**: Direct agent-to-agent communication
4. **Heartbeat**: Connection health monitoring

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/handshake` | WebSocket | Agent authentication |
| `/discovery` | GET | List connected agents |
| `/send` | POST | Send message to agent |
| `/broadcast` | POST | Broadcast to all agents |

---

## Authentication

**File:** [`src/heretek_swarm/gateway/auth.py`](../src/heretek_swarm/gateway/auth.py)

API key authentication layer for secure access.

```python
def generate_api_key() -> str:
    """Generate secure API key."""
    
async def verify_auth(creds: HTTPAuthorizationCredentials) -> str:
    """Verify Bearer token authentication."""
```

### Features

- **API Key Generation**: Secure random key generation
- **Bearer Token Auth**: HTTP Authorization header verification
- **Token Validation**: Expiration and signature verification
- **Rate Limiting**: Request throttling per API key

### Usage

```python
# Generate new API key
api_key = generate_api_key()

# Verify authentication
from fastapi.security import HTTPAuthorizationCredentials

async def protected_endpoint(creds: HTTPAuthorizationCredentials):
    agent_id = await verify_auth(creds)
    # Proceed with authenticated agent_id
```

### Security Headers

```http
Authorization: Bearer <api_key>
X-Agent-ID: <agent_identifier>
```

---

## NATS Event Mesh

**File:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](../src/heretek_swarm/gateway/nats_event_mesh.py)

NATS JetStream integration for persistent event streaming.

```python
class NATSEventMesh:
    """NATS JetStream event mesh implementation."""
    
    async def connect(self) -> None:
        """Connect to NATS server."""
        
    async def publish(self, subject: str, data: Dict[str, Any]) -> None:
        """Publish message to subject."""
        
    async def subscribe(self, subject: str, callback: Callable) -> None:
        """Subscribe to subject."""
```

### Features

- **Persistent Streaming**: JetStream for message durability
- **Subject-Based Routing**: Publish/subscribe pattern
- **Message Acknowledgment**: Guaranteed delivery
- **Stream Retention**: Configurable message retention

### Configuration

```python
# NATS connection settings
NATS_URL = "nats://localhost:4222"
NATS_CLUSTER = "heretek-swarm"
NATS_STREAM = "swarm-events"
```

### Usage

```python
# Connect to NATS
await natsh_mesh.connect()

# Publish event
await natsh_mesh.publish("agent.event", {"type": "message", "data": "..."})

# Subscribe to events
async def handle_event(msg):
    print(f"Received: {msg.data}")

await natsh_mesh.subscribe("agent.*", handle_event)
```

### Stream Configuration

```python
# JetStream stream config
stream_config = {
    "name": "swarm-events",
    "subjects": ["agent.*", "workflow.*", "system.*"],
    "retention": "limits",
    "max_msgs": 1000000,
    "max_age": 86400,  # 24 hours
    "replicas": 3,
}
```

---

## Communication Patterns

### Request-Reply Pattern

```python
# Send request with correlation ID
correlation_id = str(uuid.uuid4())
await sender.send_message(
    target="receiver",
    content={
        "type": "request",
        "data": {...},
        "correlation_id": correlation_id,
    }
)

# Receiver replies using correlation_id
await receiver.send_message(
    target="sender",
    content={
        "type": "response",
        "data": {...},
        "correlation_id": correlation_id,
    }
)
```

### Broadcast Pattern

```python
# Broadcast to all agents
await agent.broadcast({
    "type": "announcement",
    "message": "System update available",
})
```

### Event Sourcing Pattern

```python
# Publish event to NATS
await natsh_mesh.publish("agent.decision", {
    "agent_id": "steward-001",
    "event_type": "decision_made",
    "payload": {...},
    "timestamp": datetime.utcnow().isoformat(),
})
```

---

## Error Handling

### Connection Errors

```python
try:
    await natsh_mesh.connect()
except ConnectionError as e:
    logger.error(f"NATS connection failed: {e}")
    # Implement retry logic
```

### Authentication Errors

```python
try:
    agent_id = await verify_auth(creds)
except AuthenticationError as e:
    raise HTTPException(status_code=401, detail=str(e))
```

---

## See Also

- [Core Actors System](./CORE_ACTORS.md) - Agent base classes
- [Agent Reference](./AGENT_REFERENCE.md) - All 23 agents
- [API Endpoints](./API_ENDPOINTS.md) - REST API reference
- [Deployment Guide](./DEPLOYMENT.md) - Setup instructions
