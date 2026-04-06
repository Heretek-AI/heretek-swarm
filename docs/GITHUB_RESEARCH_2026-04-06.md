# GitHub Research Report - 2026-04-06

## Heretek Swarm - AI Framework Research

**Research Period:** 2026-04-06  
**License Focus:** MIT/Apache-2.0  
**Research Targets:** 12 repositories across 5 categories

---

## Executive Summary

This research report analyzes state-of-the-art implementations across multi-agent systems, visual workflow builders, AI observability platforms, and event mesh technologies. The analysis focuses on patterns and architectures that can enhance Heretek Swarm's existing actor model, workflow engine, and observability systems.

### Key Findings

| Category | Top Pattern | Integration Priority |
|----------|-------------|---------------------|
| Multi-Agent Systems | AutoGen conversable agents with request-reply | P0 |
| Workflow Orchestration | LangGraph typed state machines | P0 |
| Visual Builders | React Flow custom node handles | P1 |
| Observability | Langfuse trace hierarchy visualization | P1 |
| Event Mesh | NATS JetStream persistence | P2 |

---

## 1. Multi-Agent Systems Analysis

### 1.1 Microsoft AutoGen Patterns

**Repository:** [`microsoft/autogen`](https://github.com/microsoft/autogen)  
**License:** MIT

#### Key Architecture Patterns

**1. ConversableAgent Base Class**
- All agents inherit from `ConversableAgent` with unified message interface
- Supports synchronous and asynchronous message handling
- Built-in conversation history management with configurable max turns

**2. Request-Reply Pattern**
```python
# AutoGen-style request with correlation
async def send_with_reply(
    recipient: "ConversableAgent",
    message: str,
    request_id: str = None,
    timeout: int = 30
) -> Reply:
    correlation_id = request_id or str(uuid.uuid4())
    reply_channel = f"reply_{correlation_id}"
    
    # Subscribe to reply channel
    subscription = await self.subscribe(reply_channel)
    
    # Send message with reply_to metadata
    await self.send(recipient, {
        "content": message,
        "correlation_id": correlation_id,
        "reply_to": reply_channel
    })
    
    # Wait for reply with timeout
    reply = await subscription.receive(timeout=timeout)
    return reply
```

**3. Group Chat Manager**
- Central coordinator for multi-agent conversations
- Maintains speaker selection logic (round-robin, LLM-based, priority)
- Tracks conversation history across all participants

**Comparison with Current Implementation:**

| Feature | AutoGen | Heretek Swarm | Gap |
|---------|---------|---------------|-----|
| Base Agent Class | `ConversableAgent` | `AgentActor` | ✅ Covered |
| Message Correlation | Built-in request-reply | Manual implementation | ⚠️ Needs enhancement |
| Conversation History | Automatic with max turns | Manual via historian | ⚠️ Could be simplified |
| Group Chat | `GroupChatManager` | `ActorSupervisor` | ✅ Similar pattern |
| Tool Integration | `@tool` decorator | Plugin system | ✅ Compatible |

**Stealable Code Patterns:**
1. Request-reply with correlation IDs ([`send_with_reply()`](src/heretek_swarm/actors/base.py:312) enhancement)
2. Conversation history auto-trimming
3. LLM-based speaker selection for group chats

---

### 1.2 LangGraph Patterns

**Repository:** [`langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph)  
**License:** MIT

#### Key Architecture Patterns

**1. StateGraph with Typed State**
```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_step: str
    results: dict
    metadata: dict

# Define graph
graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("analysis", analysis_node)
graph.add_edge("research", "analysis")
graph.add_conditional_edges(
    "analysis",
    should_continue,
    {
        "continue": "research",
        "end": END
    }
)
```

**2. Conditional Edges**
- Dynamic routing based on state evaluation
- Supports loops and branching
- Type-safe state transitions

**3. Checkpointing**
- Persistent state snapshots at each node
- Enables workflow resumption after failures
- Supports time-travel debugging

**Comparison with Current Implementation:**

| Feature | LangGraph | Heretek Swarm | Gap |
|---------|-----------|---------------|-----|
| Typed State | `TypedDict` with annotations | Generic `WorkflowContext` | ⚠️ Needs typed state |
| Conditional Edges | `add_conditional_edges` | Basic condition evaluation | ⚠️ Limited |
| Checkpointing | Built-in persistence | Manual state snapshots | ⚠️ Could be automated |
| Graph Visualization | Built-in Mermaid export | None | ❌ Missing |

**Stealable Code Patterns:**
1. Typed workflow state with annotations ([`WorkflowContext`](src/heretek_swarm/workflow/engine.py:104) enhancement)
2. Conditional edge evaluation ([`_evaluate_condition()`](src/heretek_swarm/workflow/engine.py:419) enhancement)
3. Workflow checkpoint serialization

---

### 1.3 CrewAI Patterns

**Repository:** [`joaomdmoura/crewai`](https://github.com/joaomdmoura/crewai)  
**License:** MIT

#### Key Architecture Patterns

**1. Role-Based Agents**
```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role='Senior Research Analyst',
    goal='Discover insights from data',
    backstory='Expert in market research with 10 years experience',
    verbose=True,
    allow_delegation=False
)

task = Task(
    description='Analyze market trends',
    expected_output='Report with 5 key insights',
    agent=researcher
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    verbose=2,
    process=Process.sequential  # or Process.hierarchical
)
```

**2. Task Delegation**
- Hierarchical delegation through manager agents
- Task assignment based on role compatibility
- Automatic handoff between agents

**3. Process Types**
- `sequential`: Linear task execution
- `hierarchical`: Manager delegates to subordinates

**Comparison with Current Implementation:**

| Feature | CrewAI | Heretek Swarm | Gap |
|---------|--------|---------------|-----|
| Role-Based Agents | Explicit role/goal/backstory | Character JSON files | ✅ Similar approach |
| Task Delegation | Manager-based | `AgentHandoff` strategies | ✅ Compatible |
| Process Types | Sequential/Hierarchical | `HeavySwarmWorkflow` phases | ✅ More advanced |
| Output Validation | `expected_output` field | Manual validation | ⚠️ Could be enhanced |

**Stealable Code Patterns:**
1. Role-based agent configuration ([`characters/*.json`](src/heretek_swarm/runtime/characters/))
2. Task output validation schema
3. Hierarchical crew structure

---

## 2. Visual Workflow Builder Patterns

### 2.1 React Flow / XYFlow

**Repository:** [`xyflow/xyflow`](https://github.com/xyflow/xyflow)  
**License:** MIT

#### Key Architecture Patterns

**1. Custom Node Types with Handles**
```tsx
interface CustomNodeProps {
  data: {
    label: string;
    type: NodeType;
    config: NodeConfig;
  };
}

export function CustomNode({ data }: CustomNodeProps) {
  return (
    <div className="custom-node">
      <Handle type="target" position={Position.Top} id="input" />
      
      <div className="node-content">
        <NodeHeader type={data.type} label={data.label} />
        <NodeConfigForm config={data.config} />
      </div>
      
      <Handle type="source" position={Position.Bottom} id="output" />
    </div>
  );
}
```

**2. Multiple Handles per Node**
- Support for multiple input/output connections
- Type-safe handle connections
- Custom handle styling

**3. Node Palette with Drag-and-Drop**
```tsx
const nodePalette = [
  { type: 'agent', category: 'AI', icon: <AgentIcon /> },
  { type: 'condition', category: 'Logic', icon: <ConditionIcon /> },
  { type: 'tool', category: 'Action', icon: <ToolIcon /> },
];

function PaletteItem({ type, icon }: PaletteItemProps) {
  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('application/reactflow', type);
    event.dataTransfer.effectAllowed = 'move';
  };
  
  return (
    <div draggable onDragStart={onDragStart}>{icon}</div>
  );
}
```

**Comparison with Current Implementation:**

| Feature | React Flow | Heretek Swarm | Gap |
|---------|------------|---------------|-----|
| Custom Nodes | Full customization | Basic node types | ⚠️ Limited types |
| Multiple Handles | Supported | Single handle | ❌ Missing |
| Drag-and-Drop | Built-in | Basic implementation | ⚠️ Could be enhanced |
| Minimap | Built-in component | Implemented | ✅ Covered |
| Node Palette | Customizable | Basic palette | ⚠️ Limited categories |

**Stealable Code Patterns:**
1. Custom handles for multiple connections ([`EnhancedCanvas.tsx`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx:149) enhancement)
2. Node palette with category filtering
3. Minimap with custom node colors

---

### 2.2 Node-RED Patterns

**Repository:** [`node-red/node-red`](https://github.com/node-red/node-red)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Node Registry**
```javascript
RED.nodes.registerType('function', FunctionNode, {
  credentials: { key: { type: "text" } },
  inputs: 1,
  outputs: 1,
  icon: "function.svg",
  label: function() { return this.name || "function"; }
});
```

**2. Flow Editor**
- Visual node configuration dialogs
- Property editors with validation
- Real-time flow validation

**3. Runtime Execution**
- Message passing between nodes
- Catch and status nodes for error handling
- Subflow support for reusable components

**Stealable Patterns:**
1. Node type registry with metadata
2. Property editor dialogs
3. Subflow/component abstraction

---

### 2.3 n8n Patterns

**Repository:** [`n8n-io/n8n`](https://github.com/n8n-io/n8n)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Execution Visualization**
- Real-time execution highlighting
- Data preview at each node
- Execution history with replay

**2. Node Configuration**
- Form-based configuration UI
- Expression editor for dynamic values
- Credential management

**Stealable Patterns:**
1. Execution highlighting (active node visualization)
2. Data preview panels
3. Expression editor for dynamic configuration

---

## 3. Observability Patterns

### 3.1 Langfuse

**Repository:** [`langfuse-lang/langfuse`](https://github.com/langfuse-lang/langfuse)  
**License:** MIT

#### Key Architecture Patterns

**1. Trace Hierarchy**
```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create trace
trace = langfuse.trace(
    name="agent-execution",
    user_id="user-123",
    session_id="session-456",
    metadata={"agent_type": "steward"}
)

# Create spans
generation = trace.generation(
    name="llm-call",
    model="gpt-4",
    input=prompt,
    output=response
)

score = trace.score(
    name="quality",
    value=0.95,
    comment="High quality response"
)
```

**2. Score Tracking**
- Quality scores for LLM generations
- Latency metrics
- Token usage tracking

**3. Session Management**
- Group traces by session
- User-level analytics
- Conversation threading

**Comparison with Current Implementation:**

| Feature | Langfuse | Heretek Swarm | Gap |
|---------|----------|---------------|-----|
| Trace Hierarchy | Trace → Span → Generation | Flat spans | ⚠️ Needs hierarchy |
| Scoring | Built-in score API | Manual metrics | ⚠️ Could be enhanced |
| Session Tracking | Automatic | Manual | ⚠️ Could be simplified |
| LLM Metrics | Token/cost tracking | Basic latency | ⚠️ Missing cost tracking |

**Stealable Code Patterns:**
1. Trace hierarchy builder ([`TracingConfig`](src/observability/tracing.py:28) enhancement)
2. Score tracking for agent quality
3. Session-based trace grouping

---

### 3.2 Arize Phoenix

**Repository:** [`Arize-ai/phoenix`](https://github.com/Arize-ai/phoenix)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Distributed Tracing**
- OpenTelemetry native support
- Span attribute filtering
- Latency heatmaps

**2. LLM-Specific Metrics**
- Token usage breakdown
- Embedding visualization
- Retrieval quality analysis

**Stealable Patterns:**
1. OpenTelemetry integration (already implemented)
2. Embedding quality visualization
3. Retrieval effectiveness metrics

---

### 3.3 MLflow

**Repository:** [`mlflow/mlflow`](https://github.com/mlflow/mlflow)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Experiment Tracking**
```python
import mlflow

mlflow.set_experiment("agent-evaluation")

with mlflow.start_run():
    mlflow.log_param("agent_type", "steward")
    mlflow.log_param("model", "gpt-4")
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("latency_ms", 234)
    mlflow.log_artifact("results.json")
```

**2. Model Registry**
- Versioned model tracking
- Stage transitions (Staging → Production)
- Model comparison

**Stealable Patterns:**
1. Experiment tracking for agent runs
2. Metric comparison across runs
3. Artifact storage for results

---

## 4. Event Mesh Patterns

### 4.1 NATS JetStream

**Repository:** [`nats-io/nats-server`](https://github.com/nats-io/nats-server)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Stream Persistence**
```python
from nats.aio.client import Client

nc = Client()
await nc.connect("nats://localhost:4222")

# Create JetStream context
js = nc.jetstream()

# Create persistent stream
await js.add_stream(
    name="AGENT_MESSAGES",
    subjects=["agents.*"],
    storage="file",  # or "memory"
    retention="limits",
    max_msgs=100000
)

# Publish with acknowledgment
await js.publish("agents.steward", b"message", stream="AGENT_MESSAGES")

# Subscribe with durable consumer
sub = await js.subscribe(
    "agents.*",
    durable="processor",
    deliver_policy="all"
)
```

**2. Consumer Groups**
- Load-balanced message consumption
- At-least-once delivery guarantee
- Acknowledgment-based processing

**3. Stream Mirroring**
- Cross-region replication
- Disaster recovery
- Multi-cluster sync

**Comparison with Current Implementation:**

| Feature | NATS JetStream | Heretek Swarm | Gap |
|---------|----------------|---------------|-----|
| Persistence | File/memory storage | In-memory fallback | ⚠️ Limited persistence |
| Consumer Groups | Durable consumers | Basic pub/sub | ⚠️ Missing |
| Acknowledgments | Explicit ack/nak | Fire-and-forget | ⚠️ Missing |
| Replay | Seek to sequence/time | No replay | ❌ Missing |

**Stealable Code Patterns:**
1. JetStream stream creation ([`NATSEventMesh`](src/heretek_swarm/gateway/nats_event_mesh.py:63) enhancement)
2. Durable consumer subscription
3. Message acknowledgment handling

---

### 4.2 Apache Kafka

**Repository:** [`apache/kafka`](https://github.com/apache/kafka)  
**License:** Apache-2.0

#### Key Architecture Patterns

**1. Topic Partitioning**
- Parallel message processing
- Ordered messages within partitions
- Consumer group rebalancing

**2. Stream Processing**
- KSQL for stream queries
- Kafka Streams for processing
- Event sourcing patterns

**Stealable Patterns:**
1. Topic-based message routing
2. Consumer group coordination
3. Event sourcing for state reconstruction

---

## 5. Cross-Reference with Current Codebase

### 5.1 Actor System Comparison

**Current Implementation:** [`src/heretek_swarm/actors/base.py`](src/heretek_swarm/actors/base.py:109)

```python
class AgentActor:
    """Actor model implementation with mailbox pattern."""
    
    async def send(self, recipient: str, message: ActorMessage) -> bool:
        """Send message to another actor."""
        pass
    
    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message (abstract)."""
        pass
```

**Enhancement Opportunities:**

1. **Request-Reply Pattern** (from AutoGen)
   - Add correlation ID to [`ActorMessage`](src/heretek_swarm/actors/base.py:57)
   - Implement `send_with_reply()` method
   - Add reply timeout handling

2. **Conversation History** (from AutoGen)
   - Auto-trim history based on max turns
   - Store in [`HistorianAgent`](src/heretek_swarm/actors/historian.py)
   - Add conversation summary generation

3. **Typed State** (from LangGraph)
   - Add type annotations to actor state
   - Validate state transitions
   - Add state checkpointing

---

### 5.2 Workflow Engine Comparison

**Current Implementation:** [`src/heretek_swarm/workflow/engine.py`](src/heretek_swarm/workflow/engine.py:174)

```python
class WorkflowEngine:
    """Workflow execution with topological sort."""
    
    async def execute_workflow(self, workflow: Workflow) -> WorkflowResult:
        """Execute workflow in dependency order."""
        sorted_nodes = self._topological_sort(graph)
        # Execute nodes in order
```

**Enhancement Opportunities:**

1. **Typed Workflow State** (from LangGraph)
   - Replace generic `WorkflowContext` with typed state
   - Add state annotations for each node type
   - Validate state transitions

2. **Conditional Edges** (from LangGraph)
   - Enhance [`_evaluate_condition()`](src/heretek_swarm/workflow/engine.py:419) with type safety
   - Support complex routing logic
   - Add cycle detection

3. **Checkpointing** (from LangGraph)
   - Serialize state after each node
   - Enable workflow resumption
   - Add time-travel debugging

---

### 5.3 Observability Comparison

**Current Implementation:** [`src/observability/tracing.py`](src/observability/tracing.py:144)

```python
def traced(name: str = None, attributes: Dict = None):
    """Decorator for adding tracing to functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name):
                return func(*args, **kwargs)
```

**Enhancement Opportunities:**

1. **Trace Hierarchy** (from Langfuse)
   - Add parent-child span relationships
   - Track workflow execution as trace tree
   - Add session grouping

2. **LLM Metrics** (from Langfuse)
   - Track token usage per agent
   - Calculate cost per execution
   - Add quality scoring

3. **Workflow Tracing** (from n8n)
   - Highlight active workflow nodes
   - Show data flow between nodes
   - Add execution replay

---

### 5.4 Event Mesh Comparison

**Current Implementation:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py:63)

```python
class NATSEventMesh:
    """NATS integration with in-memory fallback."""
    
    async def publish(self, subject: str, data: Dict) -> bool:
        """Publish message to NATS."""
        pass
    
    async def subscribe(self, subject: str, callback: Callable) -> str:
        """Subscribe to subject."""
        pass
```

**Enhancement Opportunities:**

1. **JetStream Integration** (from NATS)
   - Add stream creation methods
   - Implement durable consumers
   - Add message acknowledgment

2. **Event Sourcing** (from Kafka)
   - Persist all messages to stream
   - Enable message replay
   - Support state reconstruction

---

## 6. Recommended Integrations

### Priority Matrix

| Integration | Priority | Effort | Impact | Files to Modify |
|-------------|----------|--------|--------|-----------------|
| Request-Reply Pattern | P0 | Low | High | [`base.py`](src/heretek_swarm/actors/base.py) |
| Typed Workflow State | P0 | Medium | High | [`engine.py`](src/heretek_swarm/workflow/engine.py) |
| Trace Hierarchy | P1 | Medium | High | [`tracing.py`](src/observability/tracing.py) |
| JetStream Consumers | P2 | High | Medium | [`nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py) |
| Custom Handles (UI) | P1 | Low | Medium | [`EnhancedCanvas.tsx`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx) |
| Node Configuration Forms | P1 | Medium | Medium | [`WorkflowBuilder.tsx`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx) |

---

## 7. Code Adaptation Plan

### Phase 1: Core Communication (Week 1-2)

**Files to Modify:**
- [`src/heretek_swarm/actors/base.py`](src/heretek_swarm/actors/base.py)
- [`src/heretek_swarm/actors/handoff.py`](src/heretek_swarm/actors/handoff.py)

**Changes:**
1. Add correlation ID to [`ActorMessage`](src/heretek_swarm/actors/base.py:57)
2. Implement `send_with_reply()` method
3. Add conversation history auto-management
4. Enhance [`AgentHandoff`](src/heretek_swarm/actors/handoff.py:37) with typed context

**Example Implementation:**
```python
# src/heretek_swarm/actors/base.py

@dataclass
class ActorMessage:
    message_type: str
    content: Any
    sender_id: str
    correlation_id: Optional[str] = None  # NEW
    reply_to: Optional[str] = None  # NEW
    timestamp: float = field(default_factory=time.time)

class AgentActor:
    async def send_with_reply(
        self,
        recipient: str,
        message: Any,
        timeout: int = 30
    ) -> Optional[Any]:
        """Send message and wait for reply with correlation."""
        correlation_id = str(uuid.uuid4())
        reply_channel = f"reply_{self.actor_id}_{correlation_id}"
        
        # Create reply subscription
        subscription = await self.event_mesh.subscribe(reply_channel)
        
        try:
            # Send message with reply_to
            await self.send(recipient, ActorMessage(
                message_type="request",
                content=message,
                sender_id=self.actor_id,
                correlation_id=correlation_id,
                reply_to=reply_channel
            ))
            
            # Wait for reply
            reply = await subscription.receive(timeout=timeout)
            return reply.content
            
        finally:
            await self.event_mesh.unsubscribe(reply_channel)
```

---

### Phase 2: Observability Enhancement (Week 2-3)

**Files to Modify:**
- [`src/observability/tracing.py`](src/observability/tracing.py)
- [`src/observability/metrics.py`](src/observability/metrics.py)

**Changes:**
1. Add trace hierarchy builder
2. Implement workflow trace tracking
3. Add LLM token/cost metrics
4. Add session-based grouping

**Example Implementation:**
```python
# src/observability/tracing.py

class WorkflowTracer:
    """Trace hierarchy builder for workflow execution."""
    
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        self._active_traces: Dict[str, Span] = {}
    
    def start_workflow_trace(
        self,
        workflow_id: str,
        user_id: str = None,
        session_id: str = None
    ) -> Span:
        """Start root trace for workflow."""
        trace = self.tracer.start_as_current_span(
            name=f"workflow:{workflow_id}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "workflow.id": workflow_id,
                "user.id": user_id,
                "session.id": session_id,
                "trace.type": "workflow"
            }
        )
        self._active_traces[workflow_id] = trace
        return trace
    
    def start_node_span(
        self,
        workflow_id: str,
        node_id: str,
        node_type: str
    ) -> Span:
        """Start span for node execution."""
        parent = self._active_traces.get(workflow_id)
        span = self.tracer.start_as_current_span(
            name=f"node:{node_id}",
            context=trace.set_span_in_context(parent),
            attributes={
                "node.id": node_id,
                "node.type": node_type,
                "workflow.id": workflow_id
            }
        )
        return span
```

---

### Phase 3: Workflow Engine Enhancement (Week 3-4)

**Files to Modify:**
- [`src/heretek_swarm/workflow/engine.py`](src/heretek_swarm/workflow/engine.py)

**Changes:**
1. Add typed workflow state
2. Implement conditional edges
3. Add checkpointing
4. Add cycle detection

**Example Implementation:**
```python
# src/heretek_swarm/workflow/engine.py

from typing import TypedDict, Annotated, Generic, TypeVar

# Typed state pattern from LangGraph
class WorkflowState(TypedDict, total=False):
    """Typed workflow state with annotations."""
    messages: Annotated[list, "append"]
    results: Annotated[dict, "merge"]
    current_phase: str
    metadata: dict

T = TypeVar('T', bound=WorkflowState)

class WorkflowEngine(Generic[T]):
    """Generic workflow engine with typed state."""
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_state: T
    ) -> T:
        """Execute workflow with typed state."""
        context = WorkflowContext(
            workflow_id=workflow.id,
            state=initial_state,
            checkpoints=[]  # For resumption
        )
        
        # Execute with checkpointing
        for node_id in self._topological_sort(graph):
            # Save checkpoint
            await self._save_checkpoint(context, node_id)
            
            # Execute node
            result = await self._execute_node(node_id, context)
            
            # Update typed state
            context.state = self._merge_state(context.state, result)
        
        return context.state
```

---

### Phase 4: UI Enhancements (Week 4-5)

**Files to Modify:**
- [`dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx)
- [`dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx)

**Changes:**
1. Add custom handles for multiple connections
2. Implement form-based node configuration
3. Add execution highlighting
4. Add data preview panels

**Example Implementation:**
```tsx
// dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx

interface AgentNodeData {
  label: string;
  type: 'agent' | 'workflow' | 'tool';
  inputs: string[];  // Multiple input handles
  outputs: string[]; // Multiple output handles
  config: AgentConfig;
}

export function AgentNode({ data, selected }: NodeProps<AgentNodeData>) {
  return (
    <div className={`agent-node ${selected ? 'selected' : ''}`}>
      {/* Multiple input handles */}
      {data.inputs.map((input, idx) => (
        <Handle
          key={input}
          type="target"
          position={Position.Top}
          id={`input-${idx}`}
          style={{ left: `${(idx + 1) * 25}%` }}
        />
      ))}
      
      <NodeHeader type={data.type} label={data.label} />
      <NodeConfigForm config={data.config} />
      
      {/* Multiple output handles */}
      {data.outputs.map((output, idx) => (
        <Handle
          key={output}
          type="source"
          position={Position.Bottom}
          id={`output-${idx}`}
          style={{ left: `${(idx + 1) * 25}%` }}
        />
      ))}
    </div>
  );
}
```

---

### Phase 5: Event Mesh Enhancement (Week 5-6)

**Files to Modify:**
- [`src/heretek_swarm/gateway/nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py)

**Changes:**
1. Add JetStream stream management
2. Implement durable consumers
3. Add message acknowledgment
4. Add replay capability

**Example Implementation:**
```python
# src/heretek_swarm/gateway/nats_event_mesh.py

class JetStreamEventMesh(NATSEventMesh):
    """NATS EventMesh with JetStream persistence."""
    
    async def create_stream(
        self,
        name: str,
        subjects: List[str],
        storage: str = "file",
        retention: str = "limits"
    ) -> bool:
        """Create JetStream for message persistence."""
        try:
            js = self._client.jetstream()
            await js.add_stream(
                name=name,
                subjects=subjects,
                storage=storage,
                retention=retention,
                max_msgs=100000
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to create stream: {e}")
            return False
    
    async def subscribe_durable(
        self,
        subject: str,
        durable_name: str,
        callback: Callable
    ) -> str:
        """Subscribe with durable consumer for at-least-once delivery."""
        try:
            js = self._client.jetstream()
            sub = await js.subscribe(
                subject,
                durable=durable_name,
                deliver_policy="all"  # Receive all messages
            )
            
            # Create task to process messages with ack
            async def process_with_ack():
                async for msg in sub.messages:
                    try:
                        await callback(msg.data)
                        await msg.ack()  # Acknowledge on success
                    except Exception as e:
                        await msg.nak()  # Negative ack on failure
                        self.logger.error(f"Message processing failed: {e}")
            
            asyncio.create_task(process_with_ack())
            return sub._id
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
            return None
    
    async def replay_stream(
        self,
        stream_name: str,
        start_sequence: int = None,
        start_time: datetime = None
    ) -> AsyncIterator[Dict]:
        """Replay messages from stream."""
        js = self._client.jetstream()
        
        # Create ephemeral consumer for replay
        consumer = await js.pull_subscribe(
            stream=stream_name,
            durable=f"replay_{uuid.uuid4()}",
            deliver_policy="by_start_sequence" if start_sequence else "by_start_time",
            opt_start_seq=start_sequence,
            opt_start_time=start_time
        )
        
        async for batch in consumer.fetch(batch=100):
            for msg in batch:
                yield json.loads(msg.data.decode())
                await msg.ack()
```

---

## 8. License Compliance

### License Analysis

All researched repositories use permissive licenses compatible with Heretek Swarm:

| Repository | License | Attribution Required | Commercial Use |
|------------|---------|---------------------|----------------|
| microsoft/autogen | MIT | Yes (license file) | ✅ Allowed |
| langchain-ai/langgraph | MIT | Yes (license file) | ✅ Allowed |
| joaomdmoura/crewai | MIT | Yes (license file) | ✅ Allowed |
| xyflow/xyflow | MIT | Yes (license file) | ✅ Allowed |
| node-red/node-red | Apache-2.0 | Yes (license + notice) | ✅ Allowed |
| n8n-io/n8n | Apache-2.0 | Yes (license + notice) | ✅ Allowed |
| langfuse-lang/langfuse | MIT | Yes (license file) | ✅ Allowed |
| Arize-ai/phoenix | Apache-2.0 | Yes (license + notice) | ✅ Allowed |
| mlflow/mlflow | Apache-2.0 | Yes (license + notice) | ✅ Allowed |
| nats-io/nats-server | Apache-2.0 | Yes (license + notice) | ✅ Allowed |
| apache/kafka | Apache-2.0 | Yes (license + notice) | ✅ Allowed |

### Attribution Requirements

**MIT License:**
- Include original copyright notice
- Include license text in documentation
- No requirement to disclose changes

**Apache-2.0 License:**
- Include original copyright notice
- Include license text in documentation
- Include NOTICE file if present
- State significant changes made to files

### Recommended Actions

1. Create `docs/THIRD_PARTY_LICENSES.md` with all attributions
2. Add license headers to modified files (Apache-2.0 requirement)
3. Document any borrowed patterns in code comments
4. Maintain list of adapted code patterns

---

## 9. Implementation Roadmap

### Week 1-2: Core Communication
- [ ] Add correlation ID to [`ActorMessage`](src/heretek_swarm/actors/base.py:57)
- [ ] Implement `send_with_reply()` in [`AgentActor`](src/heretek_swarm/actors/base.py:109)
- [ ] Add conversation history management
- [ ] Write unit tests for request-reply

### Week 2-3: Observability
- [ ] Create `WorkflowTracer` class in [`tracing.py`](src/observability/tracing.py)
- [ ] Add LLM token/cost metrics to [`SwarmMetrics`](src/observability/metrics.py:84)
- [ ] Implement session-based trace grouping
- [ ] Add trace visualization to dashboard

### Week 3-4: Workflow Engine
- [ ] Add typed state to [`WorkflowContext`](src/heretek_swarm/workflow/engine.py:104)
- [ ] Enhance [`_evaluate_condition()`](src/heretek_swarm/workflow/engine.py:419)
- [ ] Implement checkpointing
- [ ] Add cycle detection

### Week 4-5: UI Enhancements
- [ ] Add custom handles to [`AgentNode`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx)
- [ ] Implement form-based config in [`WorkflowBuilder`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx)
- [ ] Add execution highlighting
- [ ] Add data preview panels

### Week 5-6: Event Mesh
- [ ] Create `JetStreamEventMesh` subclass
- [ ] Implement durable consumers
- [ ] Add message acknowledgment
- [ ] Implement replay capability

---

## 10. Conclusion

This research identified 20+ actionable patterns across 12 repositories that can enhance Heretek Swarm's capabilities. The highest priority enhancements are:

1. **Request-Reply Pattern** (AutoGen) - Critical for agent coordination
2. **Typed Workflow State** (LangGraph) - Essential for type safety
3. **Trace Hierarchy** (Langfuse) - Key for debugging complex workflows
4. **Custom Handles** (React Flow) - Improves workflow builder UX
5. **JetStream Persistence** (NATS) - Enables event sourcing

All patterns are from MIT/Apache-2.0 licensed projects, ensuring compatibility with Heretek Swarm's licensing. The estimated implementation timeline is 6 weeks with incremental delivery.

---

**Research Completed:** 2026-04-06  
**Next Review:** 2026-04-13  
**Status:** Ready for implementation
