# Core Actors System

**Version:** 2.0.0  
**Session:** 21 (2026-04-06)

The Actor Model implementation forms the foundation of the Heretek Swarm architecture, providing async message passing, state management, and lifecycle coordination for all 23 agents.

---

## Table of Contents

1. [AgentActor Base Class](#agentactor-base-class)
2. [ActorMessage](#actormessage)
3. [ActorFactory](#actorfactory)
4. [ActorSupervisor](#actorsupervisor)
5. [Validation Models](#validation-models)

---

## AgentActor Base Class

**File:** [`backend/heretek_swarm/actors/base.py`](../backend/heretek_swarm/actors/base.py)

The foundation for all agent implementations, providing:
- Async message handling
- State management
- Health monitoring
- Zero-Trust input validation

```python
class AgentActor:
    """Base class for all agents in the Heretek Swarm system."""
    
    async def initialize(self) -> None:
        """Initialize agent resources."""
        
    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message with validation."""
        
    async def terminate(self) -> None:
        """Cleanup and shutdown agent."""
        
    async def send_message(self, target: str, content: Dict[str, Any]) -> None:
        """Send message to another actor."""
        
    async def broadcast(self, content: Dict[str, Any]) -> None:
        """Broadcast message to all actors."""
```

### Key Features

- **Async Lifecycle**: All agents implement async initialize/terminate methods
- **Message Processing**: Centralized process_message with validation
- **Inter-Agent Communication**: send_message and broadcast for A2A communication
- **Health Monitoring**: Built-in health state tracking

---

## ActorMessage

**File:** [`backend/heretek_swarm/actors/base.py`](../backend/heretek_swarm/actors/base.py)

Message structure for inter-agent communication.

```python
@dataclass
class ActorMessage:
    """Message structure for inter-agent communication."""
    sender_id: str
    target_id: str
    message_type: str
    content: Dict[str, Any]
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: str = ""
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| sender_id | str | ID of the sending agent |
| target_id | str | ID of the target agent |
| message_type | str | Type of message (e.g., "request", "response") |
| content | Dict[str, Any] | Message payload |
| correlation_id | Optional[str] | ID for correlating request/response |
| reply_to | Optional[str] | ID to reply to |
| timestamp | str | ISO 8601 timestamp |

---

## ActorFactory

**File:** [`backend/heretek_swarm/actors/factory.py`](../backend/heretek_swarm/actors/factory.py)

Creates and configures agent instances with proper initialization.

```python
class ActorFactory:
    """Factory for creating agent instances."""
    
    @staticmethod
    def create_agent(agent_type: str, agent_id: str, config: Dict[str, Any]) -> AgentActor:
        """Create agent instance by type."""
        
    @staticmethod
    def get_all_agent_classes() -> Dict[str, Type[AgentActor]]:
        """Return mapping of all available agent classes."""
```

### Usage

```python
# Create a specific agent
agent = ActorFactory.create_agent("steward", "steward-001", config)

# Get all available agent types
agents = ActorFactory.get_all_agent_classes()
```

---

## ActorSupervisor

**File:** [`backend/heretek_swarm/actors/supervisor.py`](../backend/heretek_swarm/actors/supervisor.py)

Manages agent lifecycle and coordination.

```python
class ActorSupervisor:
    """Supervisor for managing agent lifecycle."""
    
    async def spawn_actor(self, agent_class: Type[AgentActor], agent_id: str) -> str:
        """Spawn new actor instance."""
        
    async def terminate_actor(self, agent_id: str) -> bool:
        """Terminate specific actor."""
        
    async def get_actor_status(self, agent_id: str) -> Dict[str, Any]:
        """Get actor health and status."""
        
    async def terminate_all(self) -> None:
        """Terminate all actors and cleanup."""
```

### Lifecycle Management

1. **Spawn**: Creates and initializes new agent instances
2. **Monitor**: Tracks health status of all agents
3. **Terminate**: Gracefully shuts down individual or all agents

---

## Validation Models

**File:** [`backend/heretek_swarm/actors/validation.py`](../backend/heretek_swarm/actors/validation.py)

Pydantic v2 validation models for Zero-Trust input validation.

### MessageContent

```python
class MessageContent(BaseModel):
    """Validated message content model."""
    message_type: str = Field(...)
    content: Dict[str, Any] = Field(...)
    sender_id: str = Field(...)
    correlation_id: Optional[str] = Field(...)
    reply_to: Optional[str] = Field(...)
    timestamp: str = Field(...)
```

### Validators

- **sender_id**: Validates agent ID format
- **correlation_id**: Validates UUID format if provided
- **content**: Ensures non-empty dictionary
- **filters**: Validates query filter structure
- **parent_ids**: Validates lineage parent IDs

### Request Models

| Model | Purpose |
|-------|---------|
| `DeliberationRequest` | Triad deliberation requests |
| `MemoryStoreRequest` | Memory storage operations |
| `AnalysisRequest` | Analysis task requests |
| `ValidationRequest` | Validation task requests |
| `QueryRequest` | Memory query requests |
| `LineageRequest` | Decision lineage tracking |
| `HealthCheckRequest` | Agent health checks |
| `SuspendResumeRequest` | Agent suspend/resume |
| `TerminateRequest` | Agent termination |
| `CollectiveTaskRequest` | Multi-agent tasks |
| `TaskRequest` | Task coordination |
| `DependencyRequest` | Dependency resolution |
| `CoordinationRequest` | Workflow coordination |

---

## See Also

- [Agent Reference](./AGENT_REFERENCE.md) - All 23 agent implementations
- Gateway implementation in `backend/heretek_swarm/gateway/` - A2A protocol and event mesh
- [Memory System](./MEMORY_SYSTEM.md) - Memory storage and retrieval
