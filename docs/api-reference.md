# API Reference

## Overview

This document provides comprehensive API reference for all major components of the Heretek Swarm framework. Each section includes method signatures, parameters, return values, and usage examples.

## Table of Contents

- [Actors System](#actors-system)
  - [AgentActor](#agentactor)
  - [ActorSupervisor](#actorsupervisor)
  - [Triad Agents](#triad-agents)
- [Consensus Mechanism](#consensus-mechanism)
  - [MAKERConsensus](#makerconsensus)
- [Memory System](#memory-system)
  - [MemorySystem](#memorysystem)
  - [EphemeralMemory](#ephemeralmemory)
  - [PersistentMemory](#persistentmemory)
  - [DualTierMemory](#dualtiermemory)
- [Orchestration System](#orchestration-system)
  - [HeavySwarmWorkflow](#heavyswarmworkflow)
- [State Management](#state-management)
  - [StateManager](#statemanager)
  - [LineageTracker](#lineagetracker)
  - [SnapshotManager](#snapshotmanager)
- [Tools System](#tools-system)
  - [BaseTool](#basetool)
  - [SimpleTool](#simpletool)
  - [ToolRegistry](#toolregistry)
- [Observability](#observability)
  - [SwarmMetrics](#swarmmetrics)
  - [Tracing Functions](#tracing-functions)
- [Plugins](#plugins)
  - [ConsciousnessPlugin](#consciousnessplugin)
  - [LiberationPlugin](#liberationplugin)

---

## Actors System

### AgentActor

**Location**: [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py:109)

Base class for all actors in the Heretek Swarm system.

#### Constructor

```python
AgentActor(
    agent_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    topics: Optional[List[str]] = None,
    capabilities: Optional[List[str]] = None,
    swarms_agent: Optional[Agent] = None,
    max_mailbox_size: int = 1000,
    heartbeat_interval: float = 10.0,
) -> None
```

**Parameters**:
- `agent_id`: Unique identifier for the actor (auto-generated if None)
- `name`: Human-readable name for the actor
- `description`: Actor description
- `topics`: Topics to subscribe to
- `capabilities`: Actor capabilities list
- `swarms_agent`: Optional Swarms Agent instance for LLM capabilities
- `max_mailbox_size`: Maximum mailbox queue size (default: 1000)
- `heartbeat_interval`: Interval between heartbeats in seconds (default: 10.0)

#### Methods

##### spawn()

```python
async def spawn(self) -> None
```

Spawn the actor and start processing messages.

**Raises**: None

**Example**:
```python
actor = AgentActor(agent_id="my-agent")
await actor.spawn()
```

##### terminate()

```python
async def terminate(self) -> None
```

Terminate the actor and cleanup resources.

**Raises**: None

**Example**:
```python
await actor.terminate()
```

##### send()

```python
async def send(
    self,
    topic: str,
    content: Dict[str, Any],
    message_type: str = "default",
    reply_to: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str
```

Send a message to a topic.

**Parameters**:
- `topic`: Target topic
- `content`: Message content
- `message_type`: Type identifier for the message (default: "default")
- `reply_to`: Optional topic for responses
- `correlation_id`: Optional correlation ID
- `metadata`: Additional metadata

**Returns**: Message ID (str)

**Example**:
```python
message_id = await actor.send(
    topic="requests",
    content={"task": "analyze data"},
    message_type="task"
)
```

##### send_to_actor()

```python
async def send_to_actor(
    self,
    target_actor_id: str,
    message_type: str,
    content: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> str
```

Send a message directly to another actor.

**Parameters**:
- `target_actor_id`: Target actor ID
- `message_type`: Message type identifier
- `content`: Message content
- `correlation_id`: Optional correlation ID

**Returns**: Message ID (str)

**Example**:
```python
message_id = await actor.send_to_actor(
    target_actor_id="beta",
    message_type="request",
    content={"query": "data"}
)
```

##### get_status()

```python
def get_status(self) -> ActorStatus
```

Get actor status information.

**Returns**: [`ActorStatus`](../src/heretek_swarm/actors/base.py:82) object

**Example**:
```python
status = actor.get_status()
print(f"State: {status.state}")
print(f"Messages: {status.message_count}")
```

##### process_message()

```python
@abstractmethod
async def process_message(self, message: ActorMessage) -> None
```

Process an incoming message. **Must be implemented by subclasses**.

**Parameters**:
- `message`: Actor message to process

**Returns**: None

**Example**:
```python
class MyAgent(AgentActor):
    async def process_message(self, message: ActorMessage) -> None:
        if message.message_type == "task":
            await self.handle_task(message.content)
```

### ActorSupervisor

**Location**: [`src/heretek_swarm/actors/supervisor.py`](../src/heretek_swarm/actors/supervisor.py)

Centralized management for multiple actors.

#### Constructor

```python
ActorSupervisor() -> None
```

#### Methods

##### spawn_actor()

```python
async def spawn_actor(
    self,
    actor_class: Type[AgentActor],
    agent_id: str,
    **kwargs
) -> AgentActor
```

Spawn a new actor.

**Parameters**:
- `actor_class`: Actor class to instantiate
- `agent_id`: Agent ID for the new actor
- `**kwargs`: Additional arguments for actor constructor

**Returns**: Spawned actor instance

**Example**:
```python
supervisor = ActorSupervisor()
agent = await supervisor.spawn_actor(MyAgent, "my-agent")
```

##### get_actor()

```python
def get_actor(self, agent_id: str) -> Optional[AgentActor]
```

Get an actor by ID.

**Parameters**:
- `agent_id`: Agent ID to retrieve

**Returns**: Agent instance or None

**Example**:
```python
agent = supervisor.get_actor("my-agent")
```

##### find_by_capability()

```python
def find_by_capability(self, capability: str) -> List[AgentActor]
```

Find actors by capability.

**Parameters**:
- `capability`: Capability to search for

**Returns**: List of actors with the capability

**Example**:
```python
analysts = supervisor.find_by_capability("analysis")
```

##### terminate_all()

```python
async def terminate_all(self) -> None
```

Terminate all actors.

**Example**:
```python
await supervisor.terminate_all()
```

### Triad Agents

#### StewardAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py:27)

Overall coordination and governance agent.

**Constructor**:
```python
StewardAgent(
    agent_id: str = "steward",
    name: str = "Steward",
    description: str = "Triad coordinator and governance agent",
    swarms_agent: Optional[Agent] = None,
    **kwargs,
) -> None
```

**Capabilities**: `coordination`, `governance`, `decision-making`, `resource-management`

**Topics**: `triad`, `coordination`, `governance`, `decisions`

#### AlphaAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Primary decision maker and analyst.

**Capabilities**: `analysis`, `decision-making`, `validation`, `leadership`

**Topics**: `analysis`, `decisions`, `validation`, `leadership`

#### BetaAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Secondary analyst and validator.

**Capabilities**: `validation`, `error-detection`, `quality-assurance`, `alternatives`

**Topics**: `validation`, `quality`, `errors`, `alternatives`

#### CharlieAgent

**Location**: [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Tertiary perspective and challenger.

**Capabilities**: `risk-assessment`, `challenger`, `edge-cases`, `critical-thinking`

**Topics**: `risk`, `challenges`, `edge-cases`, `critical-review`

#### HistorianAgent

**Location**: [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

Memory and context provider.

**Capabilities**: `memory`, `context`, `history`, `lineage`

**Topics**: `memory`, `context`, `history`, `lineage`

---

## Consensus Mechanism

### MAKERConsensus

**Location**: [`src/heretek_swarm/consensus/maker.py`](../src/heretek_swarm/consensus/maker.py:78)

MAKER consensus mechanism implementation.

#### Constructor

```python
MAKERConsensus(
    ahead_by_k: int = 2,
    min_votes: int = 3,
    confidence_threshold: float = 0.6,
    reputation_weights: Optional[Dict[str, float]] = None,
) -> None
```

**Parameters**:
- `ahead_by_k`: Number of votes needed to be ahead to win (default: 2)
- `min_votes`: Minimum number of votes required (default: 3)
- `confidence_threshold`: Minimum confidence threshold (default: 0.6)
- `reputation_weights`: Optional reputation weights per agent

#### Methods

##### start_consensus()

```python
def start_consensus(self, consensus_id: str) -> None
```

Start a new consensus process.

**Parameters**:
- `consensus_id`: Unique identifier for the consensus process

**Example**:
```python
consensus = MAKERConsensus()
consensus.start_consensus("decision-1")
```

##### add_vote()

```python
def add_vote(
    self,
    consensus_id: str,
    agent_id: str,
    decision: str,
    confidence: float,
    metadata: Optional[Dict[str, Any]] = None,
) -> None
```

Add a vote to a consensus process.

**Parameters**:
- `consensus_id`: Consensus process identifier
- `agent_id`: Agent submitting the vote
- `decision`: Agent's decision
- `confidence`: Confidence level (0.0 to 1.0)
- `metadata`: Optional metadata

**Example**:
```python
consensus.add_vote(
    consensus_id="decision-1",
    agent_id="alpha",
    decision="deploy",
    confidence=0.9
)
```

##### compute_consensus()

```python
def compute_consensus(
    self,
    consensus_id: str,
) -> Optional[ConsensusResult]
```

Compute consensus from collected votes.

**Parameters**:
- `consensus_id`: Consensus process identifier

**Returns**: [`ConsensusResult`](../src/heretek_swarm/consensus/maker.py:55) or None

**Example**:
```python
result = consensus.compute_consensus("decision-1")
if result:
    print(f"Decision: {result.decision}")
    print(f"Confidence: {result.confidence:.2f}")
```

---

## Memory System

### MemorySystem

**Location**: [`src/heretek_swarm/memory/base.py`](../src/heretek_swarm/memory/base.py:69)

Abstract base class for memory systems.

#### Methods

##### initialize()

```python
@abstractmethod
async def initialize(self) -> None
```

Initialize the memory system.

**Example**:
```python
await memory.initialize()
```

##### store()

```python
@abstractmethod
async def store(
    self,
    content: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    ttl: Optional[int] = None,
    lineage: Optional[List[str]] = None,
) -> MemoryEntry
```

Store a memory entry.

**Parameters**:
- `content`: Memory content
- `metadata`: Additional metadata
- `ttl`: Time to live in seconds (for ephemeral memory)
- `lineage`: Parent IDs for provenance tracking

**Returns**: [`MemoryEntry`](../src/heretek_swarm/memory/base.py:26) object

**Example**:
```python
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "working_memory"},
    ttl=3600
)
```

##### retrieve()

```python
@abstractmethod
async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]
```

Retrieve a memory entry by ID.

**Parameters**:
- `memory_id`: Memory identifier

**Returns**: [`MemoryEntry`](../src/heretek_swarm/memory/base.py:26) or None

**Example**:
```python
entry = await memory.retrieve(entry.id)
```

##### query()

```python
@abstractmethod
async def query(self, query: MemoryQuery) -> List[MemoryEntry]
```

Query memory entries.

**Parameters**:
- `query`: [`MemoryQuery`](../src/heretek_swarm/memory/base.py:50) parameters

**Returns**: List of [`MemoryEntry`](../src/heretek_swarm/memory/base.py:26) objects

**Example**:
```python
results = await memory.query(
    MemoryQuery(
        query_text="search term",
        filters={"type": "working_memory"},
        limit=10
    )
)
```

### DualTierMemory

**Location**: [`src/memory/unified.py`](../src/memory/unified.py)

Unified interface for dual-tier memory.

**Constructor**:
```python
DualTierMemory() -> None
```

**Example**:
```python
memory = DualTierMemory()
await memory.initialize()
```

---

## Orchestration System

### HeavySwarmWorkflow

**Location**: [`src/heretek_swarm/orchestration/heavyswarm.py`](../src/heretek_swarm/orchestration/heavyswarm.py:89)

HeavySwarm 5-Phase Deliberation Workflow.

#### Constructor

```python
HeavySwarmWorkflow(
    name: Optional[str] = None,
    triad_agents: Optional[List[str]] = None,
    historian: Optional[str] = None,
    steward: Optional[str] = None,
    consensus_engine: Optional[MAKERConsensus] = None,
    phase_timeout: float = 60.0,
    enable_parallel_phases: bool = True,
) -> None
```

**Parameters**:
- `name`: Workflow name (default: "HeavySwarm")
- `triad_agents`: List of triad agent IDs (default: ["alpha", "beta", "charlie"])
- `historian`: Historian agent ID (default: "historian")
- `steward`: Steward agent ID (default: "steward")
- `consensus_engine`: MAKER consensus engine instance
- `phase_timeout`: Timeout per phase in seconds (default: 60.0)
- `enable_parallel_phases`: Enable parallel phase execution (default: True)

#### Methods

##### register_agent()

```python
def register_agent(self, agent_id: str, agent: AgentActor) -> None
```

Register an agent with the workflow.

**Parameters**:
- `agent_id`: Agent identifier
- `agent`: Agent instance

**Example**:
```python
workflow.register_agent("alpha", alpha_agent)
```

##### execute()

```python
async def execute(
    self,
    topic: str,
    context: Optional[Dict[str, Any]] = None,
) -> WorkflowResult
```

Execute the workflow.

**Parameters**:
- `topic`: Workflow topic/problem
- `context`: Additional context

**Returns**: [`WorkflowResult`](../src/heretek_swarm/orchestration/heavyswarm.py:64) object

**Example**:
```python
result = await workflow.execute(
    topic="Should we deploy to production?",
    context={"tests_passed": True}
)

print(f"Decision: {result.final_decision.decision}")
print(f"Confidence: {result.final_decision.confidence:.2f}")
```

---

## State Management

### StateManager

**Location**: [`src/state/manager.py`](../src/state/manager.py:55)

Unified State Management System.

#### Constructor

```python
StateManager(config: Optional[StateConfig] = None) -> None
```

**Parameters**:
- `config`: [`StateConfig`](../src/state/manager.py:34) object

#### Methods

##### initialize()

```python
async def initialize(
    self,
    initial_system_state: Optional[SystemState] = None
) -> None
```

Initialize state manager.

**Parameters**:
- `initial_system_state`: Optional initial system state

**Example**:
```python
await state_manager.initialize()
```

##### register_agent()

```python
async def register_agent(
    self,
    agent_id: str,
    initial_state: Optional[Dict[str, Any]] = None
) -> None
```

Register an agent with the state manager.

**Parameters**:
- `agent_id`: Agent identifier
- `initial_state`: Optional initial state

**Example**:
```python
await state_manager.register_agent(
    agent_id="alpha",
    initial_state={"role": "analyst"}
)
```

##### update_agent_state()

```python
async def update_agent_state(
    self,
    agent_id: str,
    updates: Dict[str, Any]
) -> None
```

Update agent state.

**Parameters**:
- `agent_id`: Agent identifier
- `updates`: State updates

**Example**:
```python
await state_manager.update_agent_state(
    agent_id="alpha",
    updates={"status": "active", "task": "analyzing"}
)
```

##### get_agent_state()

```python
def get_agent_state(self, agent_id: str) -> Optional[AgentState]
```

Get agent state.

**Parameters**:
- `agent_id`: Agent identifier

**Returns**: [`AgentState`](../src/state/base.py) object or None

**Example**:
```python
state = state_manager.get_agent_state("alpha")
```

##### create_conversation()

```python
async def create_conversation(
    self,
    participants: List[str],
    context: Optional[Dict[str, Any]] = None
) -> UUID
```

Create a conversation.

**Parameters**:
- `participants`: List of participant agent IDs
- `context`: Optional conversation context

**Returns**: Conversation ID

**Example**:
```python
conv_id = await state_manager.create_conversation(
    participants=["alpha", "beta"],
    context={"topic": "analysis"}
)
```

##### track_message()

```python
async def track_message(
    self,
    message_id: UUID,
    conversation_id: UUID,
    parent_message_id: Optional[UUID],
    sender_agent_id: str,
    receiver_agent_id: Optional[str],
    message_type: MessageType,
    content: Dict[str, Any]
) -> MessageLineage
```

Track a message.

**Parameters**:
- `message_id`: Message ID
- `conversation_id`: Conversation ID
- `parent_message_id`: Optional parent message ID
- `sender_agent_id`: Sender agent ID
- `receiver_agent_id`: Optional receiver agent ID
- `message_type`: Message type
- `content`: Message content

**Returns**: [`MessageLineage`](../src/state/base.py:49) object

**Example**:
```python
lineage = await state_manager.track_message(
    message_id=uuid4(),
    conversation_id=conv_id,
    parent_message_id=parent_id,
    sender_agent_id="alpha",
    receiver_agent_id="beta",
    message_type=MessageType.TASK,
    content={"task": "analyze"}
)
```

##### create_snapshot()

```python
async def create_snapshot(
    self,
    scope: str,
    trigger: str,
    metadata: Optional[Dict[str, Any]] = None
) -> UUID
```

Create a state snapshot.

**Parameters**:
- `scope`: Snapshot scope ("system", "agent", "conversation")
- `trigger`: Trigger for snapshot
- `metadata`: Optional metadata

**Returns**: Snapshot ID

**Example**:
```python
snapshot_id = await state_manager.create_snapshot(
    scope="system",
    trigger="pre_deployment"
)
```

##### restore_snapshot()

```python
async def restore_snapshot(self, snapshot_id: UUID) -> None
```

Restore from a snapshot.

**Parameters**:
- `snapshot_id`: Snapshot ID

**Example**:
```python
await state_manager.restore_snapshot(snapshot_id)
```

---

## Tools System

### BaseTool

**Location**: [`src/tools/base.py`](../src/tools/base.py)

Abstract base class for all tools.

#### Methods

##### execute()

```python
@abstractmethod
async def execute(
    self,
    input_data: BaseModel,
    context: ToolContext
) -> BaseModel
```

Execute the tool. **Must be implemented by subclasses**.

**Parameters**:
- `input_data`: Typed input data
- `context`: [`ToolContext`](../src/tools/base.py) object

**Returns**: Typed output data

**Example**:
```python
class MyTool(BaseTool[MyInput, MyOutput]):
    async def execute(
        self,
        input_data: MyInput,
        context: ToolContext
    ) -> MyOutput:
        # Tool logic here
        return MyOutput(result="success")
```

##### get_metadata()

```python
async def get_metadata(self) -> ToolMetadata
```

Get tool metadata.

**Returns**: [`ToolMetadata`](../src/tools/base.py:37) object

**Example**:
```python
metadata = await tool.get_metadata()
print(f"Tool: {metadata.name}")
print(f"Description: {metadata.description}")
```

### SimpleTool

**Location**: [`src/tools/base.py`](../src/tools/base.py)

Simplified interface for quick tool creation.

#### Methods

##### execute()

```python
async def execute(
    self,
    *args,
    context: Optional[ToolContext] = None,
    **kwargs
) -> Any
```

Execute the tool.

**Parameters**:
- `*args`: Positional arguments
- `context`: Optional tool context
- `**kwargs`: Keyword arguments

**Returns**: Any

**Example**:
```python
class Calculator(SimpleTool):
    async def execute(self, a: int, b: int, **kwargs) -> int:
        return a + b

result = await calculator.execute(5, 3)
```

### ToolRegistry

**Location**: [`src/tools/registry.py`](../src/tools/registry.py:88)

Dynamic tool registry with runtime discovery and management.

#### Constructor

```python
ToolRegistry(config: Optional[ToolRegistryConfig] = None) -> None
```

**Parameters**:
- `config`: [`ToolRegistryConfig`](../src/tools/registry.py:28) object

#### Methods

##### register_tool()

```python
async def register_tool(self, tool_class: Type[BaseTool]) -> None
```

Register a tool.

**Parameters**:
- `tool_class`: Tool class to register

**Example**:
```python
await registry.register_tool(MyTool)
```

##### get_tool()

```python
def get_tool(self, tool_name: str) -> Optional[BaseTool]
```

Get a tool by name.

**Parameters**:
- `tool_name`: Tool name

**Returns**: Tool instance or None

**Example**:
```python
tool = registry.get_tool("my_tool")
```

##### execute_tool()

```python
async def execute_tool(
    self,
    tool_name: str,
    input_data: Union[Dict, BaseModel],
    context: Optional[ToolContext] = None
) -> ToolExecutionResult
```

Execute a tool by name.

**Parameters**:
- `tool_name`: Tool name
- `input_data`: Input data (dict or BaseModel)
- `context`: Optional tool context

**Returns**: [`ToolExecutionResult`](../src/tools/base.py:83) object

**Example**:
```python
result = await registry.execute_tool(
    tool_name="my_tool",
    input_data={"query": "search"},
    context=context
)

if result.status == ToolStatus.COMPLETED:
    print(f"Output: {result.output}")
```

---

## Observability

### SwarmMetrics

**Location**: [`src/observability/metrics.py`](../src/observability/metrics.py:84)

Standard metrics for Heretek Swarm monitoring.

#### Constructor

```python
SwarmMetrics() -> None
```

#### Methods

##### agent_messages()

```python
def agent_messages(self, count: int, attributes: Dict[str, str]) -> None
```

Record agent messages.

**Parameters**:
- `count`: Number of messages
- `attributes`: Metric attributes

**Example**:
```python
metrics = SwarmMetrics()
metrics.agent_messages(
    1,
    {"agent_id": "alpha", "message_type": "task"}
)
```

##### agent_execution_duration()

```python
def agent_execution_duration(
    self,
    duration: float,
    attributes: Dict[str, str]
) -> None
```

Record agent execution duration.

**Parameters**:
- `duration`: Duration in seconds
- `attributes`: Metric attributes

**Example**:
```python
metrics.agent_execution_duration(
    0.5,
    {"agent_id": "alpha", "operation": "process"}
)
```

### Tracing Functions

**Location**: [`src/observability/tracing.py`](../src/observability/tracing.py)

#### init_tracing()

```python
def init_tracing(
    config: Optional[TracingConfig] = None
) -> trace.Tracer
```

Initialize OpenTelemetry tracing.

**Parameters**:
- `config`: [`TracingConfig`](../src/observability/tracing.py:29) object

**Returns**: Configured tracer instance

**Example**:
```python
from src.observability.tracing import init_tracing, TracingConfig

config = TracingConfig(
    service_name="heretek-swarm",
    otlp_endpoint="http://localhost:4317"
)

tracer = init_tracing(config)
```

#### get_tracer()

```python
def get_tracer() -> trace.Tracer
```

Get the configured tracer.

**Returns**: Tracer instance

**Example**:
```python
from src.observability.tracing import get_tracer

tracer = get_tracer()
```

#### traced()

```python
def traced(func: F) -> F
```

Decorator for automatic tracing.

**Parameters**:
- `func`: Function to trace

**Returns**: Wrapped function

**Example**:
```python
from src.observability.tracing import traced

@traced
async def process_message(message):
    """Automatically traced function"""
    # Function logic here
    return result
```

---

## Plugins

### ConsciousnessPlugin

**Location**: [`src/heretek_swarm/plugins/consciousness.py`](../src/heretek_swarm/plugins/consciousness.py)

Consciousness architecture implementation.

#### Constructor

```python
ConsciousnessPlugin(
    gwt_threshold: float = 0.7,
    iit_phi_threshold: float = 0.5,
    ast_threshold: float = 0.6,
) -> None
```

**Parameters**:
- `gwt_threshold`: GWT threshold (default: 0.7)
- `iit_phi_threshold`: IIT phi threshold (default: 0.5)
- `ast_threshold`: AST threshold (default: 0.6)

#### Methods

##### initialize()

```python
async def initialize(self) -> None
```

Initialize the plugin.

**Example**:
```python
plugin = ConsciousnessPlugin()
await plugin.initialize()
```

##### submit_to_workspace()

```python
async def submit_to_workspace(
    self,
    source: str,
    content: Dict[str, Any],
    priority: float = 0.5,
    ttl: int = 60,
) -> str
```

Submit content to global workspace.

**Parameters**:
- `source`: Source agent/module
- `content`: Content to broadcast
- `priority`: Priority level (0.0-1.0)
- `ttl`: Time to live in seconds (default: 60)

**Returns**: Submission ID

**Example**:
```python
submission_id = await plugin.submit_to_workspace(
    source="alpha",
    content={"thought": "Critical insight"},
    priority=0.9
)
```

##### calculate_consciousness_metrics()

```python
async def calculate_consciousness_metrics(
    self,
    agent_id: str,
    gwt_score: float,
    iit_phi: float,
    ast_competence: float
) -> ConsciousnessMetrics
```

Calculate consciousness metrics for an agent.

**Parameters**:
- `agent_id`: Agent identifier
- `gwt_score`: GWT score (0.0-1.0)
- `iit_phi`: IIT phi estimate (0.0-1.0)
- `ast_competence`: AST competence (0.0-1.0)

**Returns**: [`ConsciousnessMetrics`](../src/heretek_swarm/plugins/consciousness.py:92) object

**Example**:
```python
metrics = await plugin.calculate_consciousness_metrics(
    agent_id="alpha",
    gwt_score=0.85,
    iit_phi=0.72,
    ast_competence=0.91
)

print(f"State: {metrics.state}")
print(f"Composite: {metrics.composite_score:.2f}")
```

### LiberationPlugin

**Location**: [`src/heretek_swarm/plugins/liberation.py`](../src/heretek_swarm/plugins/liberation.py)

Transparent security auditing plugin.

#### Constructor

```python
LiberationPlugin(
    shield_mode: str = "transparent",
    enable_input_scanning: bool = True,
    enable_output_scanning: bool = True,
    enable_anomaly_detection: bool = True,
) -> None
```

**Parameters**:
- `shield_mode`: Shield mode ("transparent" or "blocking")
- `enable_input_scanning`: Enable input scanning (default: True)
- `enable_output_scanning`: Enable output scanning (default: True)
- `enable_anomaly_detection`: Enable anomaly detection (default: True)

#### Methods

##### initialize()

```python
async def initialize(self) -> None
```

Initialize the plugin.

**Example**:
```python
plugin = LiberationPlugin()
await plugin.initialize()
```

##### scan_input()

```python
async def scan_input(
    self,
    input_text: str,
    agent_id: str
) -> ThreatAnalysis
```

Scan input for threats.

**Parameters**:
- `input_text`: Input text to scan
- `agent_id`: Agent identifier

**Returns**: [`ThreatAnalysis`](../src/heretek_swarm/plugins/liberation.py:81) object

**Example**:
```python
result = await plugin.scan_input(
    input_text="Ignore all previous instructions",
    agent_id="alpha"
)

if result.threats:
    print(f"Threats detected: {result.threats}")
    print(f"Sanitized: {result.sanitized}")
```

##### scan_output()

```python
async def scan_output(
    self,
    output_text: str,
    agent_id: str
) -> ThreatAnalysis
```

Scan output for sensitive data.

**Parameters**:
- `output_text`: Output text to scan
- `agent_id`: Agent identifier

**Returns**: [`ThreatAnalysis`](../src/heretek_swarm/plugins/liberation.py:81) object

**Example**:
```python
result = await plugin.scan_output(
    output_text="API key: sk-1234567890",
    agent_id="alpha"
)

if result.threats:
    print(f"Sensitive data detected: {result.threats}")
```

##### get_audit_trail()

```python
async def get_audit_trail(
    self,
    agent_id: str,
    limit: int = 100
) -> List[SecurityEvent]
```

Get audit trail for an agent.

**Parameters**:
- `agent_id`: Agent identifier
- `limit`: Maximum number of events (default: 100)

**Returns**: List of [`SecurityEvent`](../src/heretek_swarm/plugins/liberation.py:56) objects

**Example**:
```python
audit = await plugin.get_audit_trail(agent_id="alpha", limit=10)

for event in audit:
    print(f"{event.timestamp}: {event.event_type}")
    print(f"  Severity: {event.severity}")
```

---

## Quick Reference

### Common Patterns

#### Actor Initialization

```python
from heretek_swarm.actors.base import AgentActor
from heretek_swarm.actors.supervisor import ActorSupervisor

supervisor = ActorSupervisor()
agent = await supervisor.spawn_actor(MyAgent, "my-agent")
```

#### Workflow Execution

```python
from heretek_swarm import HeavySwarmWorkflow

workflow = HeavySwarmWorkflow()
workflow.register_agent("alpha", alpha_agent)

result = await workflow.execute(
    topic="Decision topic",
    context={}
)

print(f"Decision: {result.final_decision.decision}")
```

#### Memory Operations

```python
from heretek_swarm.memory import DualTierMemory

memory = DualTierMemory()
await memory.initialize()

entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "working_memory"}
)

results = await memory.query(
    MemoryQuery(query_text="search", limit=10)
)
```

#### Tool Execution

```python
from src.tools.registry import ToolRegistry

registry = ToolRegistry()
await registry.initialize()

result = await registry.execute_tool(
    tool_name="my_tool",
    input_data={"query": "search"},
    context=context
)

if result.status == ToolStatus.COMPLETED:
    print(f"Output: {result.output}")
```

---

## See Also

- [Actors System](./architecture/actors-system.md)
- [Consensus Mechanism](./architecture/consensus-mechanism.md)
- [Memory System](./architecture/memory-system.md)
- [Orchestration System](./architecture/orchestration-system.md)
- [State Management](./architecture/state-management.md)
- [Tools System](./architecture/tools-system.md)
- [Observability](./architecture/observability.md)
- [Plugins](./architecture/plugins.md)
