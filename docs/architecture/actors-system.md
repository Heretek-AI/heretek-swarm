# Actors System Documentation

## Overview

The Actors System is the foundational component of the Heretek Swarm framework, implementing the actor model pattern for concurrent, message-driven agent orchestration. Each actor operates independently with its own state, communicating exclusively through immutable messages.

## Core Architecture

### Actor Model Pattern

The actor model provides:
- **Message Passing**: Actors communicate via immutable messages
- **State Isolation**: Each actor maintains isolated internal state
- **Mailbox Processing**: Sequential processing of messages from a queue
- **Concurrency**: Multiple actors can run concurrently without shared state
- **Resilience**: Actor failures are isolated and can be supervised

### Key Components

#### 1. AgentActor (Base Class)

**Location**: [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py)

The [`AgentActor`](../src/heretek_swarm/actors/base.py:109) class is the abstract base for all actors in the system.

**Features**:
- Asynchronous mailbox for message processing
- State management with persistence hooks
- Actor lifecycle management (spawn, process, terminate)
- Message routing and handling
- Integration with Swarms Agent for LLM capabilities
- Structured logging with structlog
- Health monitoring and heartbeat mechanism

**Lifecycle States**:

```python
class ActorState(Enum):
    SPAWNING = "spawning"    # Actor is initializing
    ACTIVE = "active"        # Actor is processing messages
    SUSPENDED = "suspended"  # Actor is temporarily paused
    TERMINATED = "terminated" # Actor has shut down
    ERROR = "error"          # Actor encountered an error
```

**Core Methods**:

- [`spawn()`](../src/heretek_swarm/actors/base.py:221): Initialize and start the actor
- [`terminate()`](../src/heretek_swarm/actors/base.py:251): Gracefully shutdown the actor
- [`send()`](../src/heretek_swarm/actors/base.py:295): Send a message to a topic
- [`send_to_actor()`](../src/heretek_swarm/actors/base.py:339): Send a message directly to another actor
- [`process_message()`](../src/heretek_swarm/actors/base.py:426): Abstract method for handling messages (must be implemented)
- [`initialize()`](../src/heretek_swarm/actors/base.py:438): Hook for custom initialization
- [`cleanup()`](../src/heretek_swarm/actors/base.py:446): Hook for custom cleanup
- [`get_status()`](../src/heretek_swarm/actors/base.py:497): Get current actor status

**Message Structure**:

```python
@dataclass
class ActorMessage:
    sender: str                    # ID of the sending actor
    message_type: str              # Type identifier for the message
    content: Dict[str, Any]        # Message payload
    timestamp: str                 # ISO8601 timestamp
    correlation_id: Optional[str]  # For request-response patterns
    reply_to: Optional[str]        # Topic for responses
    metadata: Dict[str, Any]       # Additional metadata
```

**Example Usage**:

```python
from heretek_swarm.actors.base import AgentActor

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

#### 2. ActorSupervisor

**Location**: [`src/heretek_swarm/actors/supervisor.py`](../src/heretek_swarm/actors/supervisor.py)

The [`ActorSupervisor`](../src/heretek_swarm/actors/supervisor.py) manages multiple actors with health monitoring and auto-restart capabilities.

**Features**:
- Centralized actor management
- Health monitoring with periodic checks
- Auto-restart on failure
- Actor discovery by capability and topic
- Actor lifecycle coordination

**Example Usage**:

```python
from heretek_swarm.actors.supervisor import ActorSupervisor

supervisor = ActorSupervisor()

# Spawn actors
await supervisor.spawn_actor(AlphaAgent, "alpha")
await supervisor.spawn_actor(BetaAgent, "beta")
await supervisor.spawn_actor(CharlieAgent, "charlie")

# Get actor by ID
alpha = supervisor.get_actor("alpha")

# Find actors by capability
analysts = supervisor.find_by_capability("analysis")

# Terminate all actors
await supervisor.terminate_all()
```

## Triad Agents

The Triad is a specialized set of four agents that work together for deliberation and decision-making:

### 1. StewardAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py:27)

**Role**: Overall coordination and governance

**Responsibilities**:
- Initiating deliberation processes
- Coordinating between Triad members
- Making final executive decisions
- Managing system governance and policy
- Overseeing resource allocation

**Capabilities**: `coordination`, `governance`, `decision-making`, `resource-management`

**Topics**: `triad`, `coordination`, `governance`, `decisions`

**Message Handlers**:
- `start_deliberation`: Begin a new deliberation process
- `request_decision`: Handle decision requests
- `report_status`: Process status reports
- `policy_update`: Update governance policies

### 2. AlphaAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

**Role**: Primary decision maker and analyst

**Responsibilities**:
- First-pass analysis on problems
- Leading consensus building
- Validating final decisions
- Providing primary analytical perspective

**Capabilities**: `analysis`, `decision-making`, `validation`, `leadership`

**Topics**: `analysis`, `decisions`, `validation`, `leadership`

### 3. BetaAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

**Role**: Secondary analyst and validator

**Responsibilities**:
- Independent validation perspective
- Error detection and correction
- Alternative solution generation
- Quality assurance on decisions

**Capabilities**: `validation`, `error-detection`, `quality-assurance`, `alternatives`

**Topics**: `validation`, `quality`, `errors`, `alternatives`

### 4. CharlieAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

**Role**: Tertiary perspective and challenger

**Responsibilities**:
- Devil's advocate role
- Risk assessment
- Edge case identification
- Challenging assumptions

**Capabilities**: `risk-assessment`, `challenger`, `edge-cases`, `critical-thinking`

**Topics**: `risk`, `challenges`, `edge-cases`, `critical-review`

### 5. HistorianAgent

**Location**: [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

**Role**: Memory and context provider

**Responsibilities**:
- Long-term memory storage and retrieval
- Context provision for deliberations
- Historical pattern recognition
- Decision lineage tracking

**Capabilities**: `memory`, `context`, `history`, `lineage`

**Topics**: `memory`, `context`, `history`, `lineage`

## Message Flow

### Actor Communication Pattern

```
┌─────────────┐
│   Actor A   │
│             │
│  ┌───────┐  │
│  │Mailbox│  │
│  └───────┘  │
└──────┬──────┘
       │
       │ send()
       │
       ▼
┌─────────────┐
│ Event Mesh  │ (Topic Routing)
└──────┬──────┘
       │
       │ route()
       │
       ▼
┌─────────────┐
│   Actor B   │
│             │
│  ┌───────┐  │
│  │Mailbox│  │
│  └───────┘  │
└─────────────┘
```

### Message Processing Loop

1. Message arrives in actor's mailbox
2. Actor retrieves message (FIFO order)
3. Actor processes message via [`process_message()`](../src/heretek_swarm/actors/base.py:426)
4. Handler is invoked based on message type
5. Optional response is sent back
6. Message is marked as done
7. Loop continues for next message

## Actor Supervision Strategy

### Supervision Tree

```
ActorSupervisor
├── StewardAgent
├── AlphaAgent
├── BetaAgent
├── CharlieAgent
└── HistorianAgent
```

### Failure Handling

- **One-for-One**: Only the failed actor is restarted
- **One-for-All**: All actors in the group are restarted
- **Escalation**: Failures are escalated to the supervisor

## Best Practices

### 1. Actor Design

- Keep actors focused on a single responsibility
- Minimize shared state between actors
- Use immutable messages
- Implement proper error handling
- Use structured logging

### 2. Message Design

- Use descriptive message types
- Include correlation IDs for request-response patterns
- Keep messages small and focused
- Use metadata for additional context

### 3. Resource Management

- Set appropriate mailbox sizes
- Configure heartbeat intervals
- Implement proper cleanup in [`cleanup()`](../src/heretek_swarm/actors/base.py:446)
- Use timeouts for blocking operations

### 4. Testing

- Test actors in isolation
- Test message flows
- Test error scenarios
- Test supervision strategies

## Performance Considerations

### Mailbox Size

- Default: 1000 messages
- Adjust based on message processing time
- Monitor mailbox size in production
- Consider backpressure for slow consumers

### Message Processing

- Keep message handlers fast
- Offload long-running work to background tasks
- Use async/await properly
- Avoid blocking operations

### Memory Usage

- Monitor actor state size
- Implement state persistence for large state
- Use memory-efficient data structures
- Clean up unused resources

## Troubleshooting

### Common Issues

1. **Mailbox Full**: Messages being dropped
   - Increase [`max_mailbox_size`](../src/heretek_swarm/actors/base.py:149)
   - Optimize message processing
   - Implement backpressure

2. **Actor Not Responding**: No messages processed
   - Check actor state with [`get_status()`](../src/heretek_swarm/actors/base.py:497)
   - Review message handler logic
   - Check for blocking operations

3. **High Memory Usage**: Actor state growing
   - Implement state persistence
   - Clean up unused data
   - Monitor state size

4. **Message Loss**: Messages not arriving
   - Check topic subscriptions
   - Verify message routing
   - Review event mesh configuration

## API Reference

### AgentActor

See [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py) for complete API documentation.

### ActorSupervisor

See [`src/heretek_swarm/actors/supervisor.py`](../src/heretek_swarm/actors/supervisor.py) for complete API documentation.

### Triad Agents

See [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py) for complete API documentation.

## See Also

- [Consensus Mechanism](./consensus-mechanism.md)
- [HeavySwarm Workflow](./orchestration-system.md)
- [Memory System](./memory-system.md)
- [State Management](./state-management.md)
