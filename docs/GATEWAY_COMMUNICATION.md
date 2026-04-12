# Gateway & Communication

**Version:** 2.0.0  
**Date:** 2026-04-10  
**Status:** Active

---

## Overview

This document describes the Heretek Swarm's gateway architecture and communication protocols, including the A2A (Agent-to-Agent) protocol and Event Mesh for inter-agent messaging.

---

## Components

### A2A Protocol Server

**Location:** [`src/heretek_swarm/gateway/a2a_server.py`](../src/heretek_swarm/gateway/a2a_server.py)

The A2AServer implements the Agent-to-Agent protocol for direct agent communication.

**Features:**
- WebSocket-based real-time messaging
- Authentication token management
- Agent discovery and registration
- Message broadcast and unicast
- Proposal/vote handling for consensus

### Event Mesh

**Location:** [`src/heretek_swarm/gateway/event_mesh.py`](../src/heretek_swarm/gateway/event_mesh.py)

The EventMesh provides pub/sub messaging across the swarm.

### NATS JetStream Integration

**Location:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](../src/heretek_swarm/gateway/nats_event_mesh.py)

NATS-enabled event mesh with JetStream persistence.

### Message Replay

**Location:** [`src/heretek_swarm/gateway/message_replay.py`](../src/heretek_swarm/gateway/message_replay.py)

Time-travel message replay capabilities for debugging and analysis.

---

## Message Types

| Type | Description | Direction |
|------|------------|----------|
| handshake | Initial connection handshake | Agent → Server |
| discovery | Agent capability advertisement | Bidirectional |
| message | Direct agent-to-agent message | Bidirectional |
| broadcast | Broadcast to all agents | Agent → All |
| proposal | Consensus proposal | Agent → Server |
| vote | Consensus vote | Agent → Server |

---

## Authentication

The gateway uses token-based authentication:
- Token generation via `AuthTokenManager.generate_token()`
- Token validation via `AuthTokenManager.validate_token()`
- Token revocation via `AuthTokenManager.revoke_token()`

**Environment Variables:**
- `A2A_SECRET_KEY`: Secret key for token signing

---

## API Reference

### A2AServer

```python
from heretek_swarm.gateway import A2AServer, MessageType, AgentInfo

server = A2AServer()
await server.start()
```

### EventMesh

```python
from heretek_swarm.gateway import EventMesh

mesh = EventMesh()
await mesh.publish("topic", {"data": "message"})
```

---

**Status:** IMPLEMENTED - Complete gateway and communication stack verified.