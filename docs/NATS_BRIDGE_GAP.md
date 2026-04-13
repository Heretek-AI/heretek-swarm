# NATS Bridge Gap Analysis

**Status:** Gap Identified
**Date:** 2026-04-13
**Priority:** High

---

## Executive Summary

The Heretek Swarm has NATS infrastructure code present in `src/heretek_swarm/infrastructure/nats/` but it is **not wired to the actor system**. Actors receive `None` from stub functions and have no actual NATS connectivity.

---

## What's Implemented

### NATS Infrastructure (`src/heretek_swarm/infrastructure/nats/`)

| File | Purpose |
|------|---------|
| `client.py` | `NATSClient` - core NATS connection manager |
| `publisher.py` | `NATSPublisher` - structured event publishing |
| `subscriber.py` | `NATSSubscriber` - event subscription |
| `broadcast.py` | `PatternBroadcast` - pattern broadcasting for collective learning |
| `discovery.py` | Agent discovery with heartbeats and presence |
| `consensus.py` | Consensus mechanisms via NATS |
| `memory_sync.py` | Memory synchronization across agents |

### Topics Configured

- `agents.*.messages` - Agent-to-agent messaging
- `agents.*.events` - Agent lifecycle events
- `consensus.*` - Consensus deliberations
- `consciousness.*` - Consciousness metrics
- `swarm.*` - Swarm-wide events
- `patterns.*` - Pattern broadcasting

### A2A Gateway (`src/heretek_swarm/gateway/`)

- **EventMesh** - WebSocket-based connection manager (NOT NATS)
- **A2AProtocol** - Agent-to-Agent protocol over WebSocket port 18789
- **nats_event_mesh.py** - Placeholder with no actual NATS integration

---

## The Gap

### 1. Actor Stubs Return None

`src/heretek_swarm/actors/stubs.py`:

```python
def get_nats_event_mesh() -> None:
    """Get the NATS event mesh instance. Returns None (stub function for testing)."""
    return
```

**Reality:** Actors calling `get_nats_event_mesh()` get `None`, not a NATS client.

### 2. NATS Infrastructure Not Injected into Actors

The actor base classes in `actors/base/` do not import or use `NATSClient`. Message handling is internal only.

### 3. EventMesh is WebSocket, Not NATS

The `gateway/event_mesh.py` is a WebSocket manager - it manages browser/app connections, not NATS pub/sub. This is a separate system.

### 4. No Bridge Between NATS and Actors

There is no component that:
- Subscribes to NATS topics
- Converts NATS messages to actor messages
- Publishes actor events to NATS

---

## Required Dependencies

### Python Packages (need to be installed)

```
nats-py>=2.3.0          # Official NATS Python client (MISSING - only nats-server is in deps)
pydantic>=2.0           # For message validation
```

**Current state:** `pyproject.toml` has `nats-server>=3.0.0` (NATS binary) but NOT `nats-py` (Python client library).

### Infrastructure

```
NATS Server (typically localhost:4222)
├── Enable JetStream for persistence (optional)
└── Configure subjects as listed above
```

---

## How to Wire It Up

### Step 1: Install Dependencies

```bash
pip install nats-py>=2.3.0
```

### Step 2: Create the Bridge Module

Create `src/heretek_swarm/infrastructure/nats_bridge.py`:

```python
"""
NATS-to-Actor Bridge

Subscribes to NATS topics and converts messages to actor internal format.
Publishes actor events to NATS topics.
"""

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class NATSBridge:
    """
    Bridge between NATS event mesh and actor message handling.

    Responsibilities:
    - Subscribe to NATS subjects (agents.*, consensus.*, swarm.*)
    - Convert incoming NATS messages to actor messages
    - Route messages to appropriate actor message handlers
    - Publish actor events to NATS for inter-agent communication
    """

    def __init__(self, nats_client, message_handler):
        self._client = nats_client
        self._handler = message_handler
        self._subscriptions = []

    async def start(self) -> None:
        """Start the bridge - subscribe to NATS topics."""
        if not self._client or not self._client.is_connected:
            logger.error("nats_bridge_no_client")
            return

        # Subscribe to agent message topics
        await self._subscribe("agents.*.messages", self._handle_agent_message)
        await self._subscribe("agents.*.events", self._handle_agent_event)
        await self._subscribe("consensus.*", self._handle_consensus)
        await self._subscribe("swarm.*", self._handle_swarm_event)

        logger.info("nats_bridge_started")

    async def _subscribe(self, subject: str, handler: Any) -> None:
        """Subscribe to a NATS subject."""
        async def wrapped_handler(msg):
            await handler(subject, msg.data.decode())

        sub = await self._client.subscribe(subject, handler=wrapped_handler)
        self._subscriptions.append(sub)

    async def _handle_agent_message(self, subject: str, data: str) -> None:
        """Handle incoming agent-to-agent message."""
        # Parse and route to actor message handler
        pass

    async def publish_event(self, event: dict) -> None:
        """Publish actor event to NATS."""
        pass
```

### Step 3: Initialize NATS in Actor Base

In `actors/base/core.py`:

```python
from heretek_swarm.infrastructure.nats import get_nats_client, NATSPublisher

class AgentActor:
    def __init__(self, ...):
        self._nats_publisher = NATSPublisher()

    async def initialize_nats(self) -> None:
        """Initialize NATS connection for this actor."""
        await self._nats_publisher.initialize(source=self.agent_id)
```

### Step 4: Wire in Runtime

In `runtime/main_loop.py`:

```python
from heretek_swarm.infrastructure.nats import get_nats_client
from heretek_swarm.infrastructure.nats_bridge import NATSBridge

async def initialize_swarm():
    nats_client = await get_nats_client()
    await nats_client.connect()

    bridge = NATSBridge(nats_client, actor_message_handler)
    await bridge.start()
```

---

## Configuration

### Environment Variables

```bash
# NATS Connection
NATS_URL=nats://localhost:4222
NATS_USER=admin
NATS_PASS=password
NATS_TOKEN=

# JetStream (optional)
NATS_STREAM_ENABLED=true
NATS_STREAM_NAME=heretek-swarm
```

### Docker Compose (add to existing)

```yaml
services:
  nats:
    image: nats:latest
    ports:
      - "4222:4222"
      - "8222:8222"  # monitoring
    command: ["-js"]  # enable JetStream
```

---

## Alternative: Use A2A Over NATS

If the goal is inter-container agent communication, consider:

1. **A2A over NATS** - Run A2A protocol messages over NATS pub/sub instead of WebSocket
2. **EventMesh over NATS** - Replace WebSocket EventMesh with NATS-based pub/sub

This would unify the communication layer rather than maintaining two separate systems.

---

## Verification Checklist

- [ ] `nats-py` installed in dependencies
- [ ] `NATSClient` connects successfully
- [ ] Actors can publish events via `NATSPublisher`
- [ ] Actors receive messages from NATS subscriptions
- [ ] `get_nats_event_mesh()` returns real instance (not `None`)
- [ ] Docker compose includes NATS service
- [ ] Inter-container communication works via NATS