# HERETEK SWARM PROTOCOL SPECIFICATIONS
## MCP (Model Context Protocol) & A2A (Agent-to-Agent)

---

## PART I: MCP (Model Context Protocol)

### 1.1 MCP Overview

MCP enables tools and resources to be exposed to AI models in a standardized way. Heretek Swarm implements MCP for agent tool exposure and external system integration.

### 1.2 MCP Server Architecture

```
                    ┌─────────────────┐
                    │   MCP Client    │
                    │  (Agent/Tool)   │
                    └────────┬────────┘
                             │ JSON-RPC 2.0
                    ┌────────▼────────┐
                    │   MCP Server     │
                    │ heretek-swarm    │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌──────▼──────┐
    │  Resources │    │   Tools     │    │   Prompts   │
    │            │    │             │    │             │
    └───────────┘    └─────────────┘    └─────────────┘
```

### 1.3 MCP Implementation Files

| File | Purpose |
|------|---------|
| `src/heretek_swarm/mcp/server.py` | MCP server implementation |
| `src/heretek_swarm/mcp/client.py` | MCP client implementation |
| `src/heretek_swarm/mcp/registry.py` | Tool/resource registry |
| `src/heretek_swarm/mcp/types.py` | MCP protocol types |

### 1.4 MCP Tool Definitions

#### Core Tools (Required)

```python
@tool(name="heretek_agent_list", description="List all active agents in the swarm")
def list_agents() -> list[AgentInfo]:
    """Returns list of all active agents with their current status"""

@tool(name="heretek_agent_status", description="Get status of a specific agent")
def get_agent_status(agent_id: str) -> AgentStatus:
    """Returns current status, health metrics, and task queue for agent"""

@tool(name="heretek_send_message", description="Send message to an agent")
def send_message(to: str, content: str, priority: Priority = Priority.NORMAL) -> MessageId:
    """Sends message to specified agent, returns message ID"""

@tool(name="heretek_broadcast", description="Broadcast message to all agents")
def broadcast(content: str, subject: str) -> BroadcastId:
    """Broadcasts message to all agents, returns broadcast ID"""

@tool(name="heretek_create_task", description="Create and assign task")
def create_task(description: str, assignee: str | None, priority: Priority) -> TaskId:
    """Creates task, optionally assigns to agent, returns task ID"""

@tool(name="heretek_get_memory", description="Query swarm memory")
def query_memory(query: str, limit: int = 10) -> list[MemoryEntry]:
    """Queries Mem0 memory, returns relevant entries"""

@tool(name="heretek_log_decision", description="Log decision to precedent log")
def log_decision(decision: Decision, context: Context) -> PrecedentId:
    """Logs decision for future precedent, returns precedent ID"""

@tool(name="heretek_trigger_sentinel", description="Trigger Sentinel for anomaly")
def trigger_sentinel(anomaly_type: str, details: dict) -> AlertId:
    """Triggers Sentinel response, returns alert ID"""

@tool(name="heretek_tribunal_convene", description="Convene Tribunal for deliberation")
def convene_tribunal(issue: Issue) -> TribunalId:
    """Convenes Core Triad for deliberation, returns tribunal ID"""

@tool(name="heretek_measure_consciousness", description="Measure system consciousness")
def measure_consciousness() -> ConsciousnessMetrics:
    """Returns current consciousness metrics (IIT phi^C, attention allocation)"""
```

#### Agent-Specific Tools

```python
# Steward Tools
@tool(name="steward_pulse", description="Get current system pulse")
def get_system_pulse() -> PulseData

@tool(name="steward_route_task", description="Route task to appropriate agent")
def route_task(task: TaskMessage) -> RouteResult

# Alpha Tools
@tool(name="alpha_analyze", description="Request deep analysis")
def request_analysis(problem: str) -> AnalysisId

@tool(name="alpha_synthesize", description="Request insight synthesis")
def synthesize_insights(insights: list[str]) -> Synthesis

# Historian Tools
@tool(name="historian_query", description="Query historical precedent")
def query_precedent(situation: str) -> list[Precedent]

@tool(name="historian_log", description="Log new precedent")
def log_precedent(action: Action, outcome: Outcome) -> PrecedentId

# (Similar for all 23 agents)
```

### 1.5 MCP Resources

```python
@resource(name="agent_registry", uri="agent://registry")
def agent_registry() -> AgentRegistry:
    """Returns current agent registry with all agent info"""

@resource(name="system_state", uri="state://current")
def system_state() -> SystemStateSnapshot:
    """Returns current system state snapshot"""

@resource(name="decisions_log", uri="history://decisions")
def decisions_log(limit: int = 100) -> list[Decision]:
    """Returns recent decisions from precedent log"""

@resource(name="memory_search", uri="memory://search")
def memory_search(query: str, limit: int) -> list[MemoryEntry]:
    """Searches long-term memory for relevant entries"""
```

### 1.6 MCP Prompts

```python
@prompt(name="tribunal_deliberation", description="Template for tribunal deliberation")
def tribunal_deliberation(issue: str, context: str) -> str:
    return f"""You are participating in a Tribunal deliberation.

Issue to resolve: {issue}

Context: {context}

Provide your perspective, consider potential outcomes,
and cast your vote (APPROVE, REJECT, MODIFY)."""

@prompt(name="agent_activation", description="Template for activating an agent")
def agent_activation(agent_type: str, task: str) -> str:
    return f"""Activate {agent_type} for task: {task}

Consider your role's responsibilities and expertise.
Report findings and recommendations via NATS broadcast."""
```

---

## PART II: A2A (Agent-to-Agent) Protocol

### 2.1 A2A Overview

A2A enables direct communication between agents using a standardized message format. Heretek Swarm agents communicate via NATS subjects following A2A protocol.

### 2.2 A2A Message Format

```python
class A2AMessage(BaseModel):
    """A2A Protocol Message"""
    id: UUID                           # Unique message ID
    sender: AgentId                    # Sender agent ID
    recipient: AgentId | None         # None = broadcast
    subject: str                       # Message subject/topic
    action: str                        # Action being requested
    payload: dict[str, Any]           # Message payload
    priority: MessagePriority          # Priority level
    timestamp: datetime               # Creation timestamp
    expires_at: datetime | None       # Expiration (for time-sensitive)
    reply_to: UUID | None             # Parent message ID for threads
    metadata: dict[str, Any]          # Additional metadata

class A2AResponse(BaseModel):
    """A2A Protocol Response"""
    id: UUID                           # Response ID
    request_id: UUID                  # Original request ID
    status: ResponseStatus             # success, failure, partial
    result: dict[str, Any] | None    # Result data
    error: Error | None                # Error if failed
    timestamp: datetime               # Response timestamp
```

### 2.3 NATS Subject Hierarchy

```
heretek.swarm.
├── pulse.                    # Heartbeat broadcasts
│   ├── steward              # Steward pulse
│   └── system               # System-wide pulse
├── agent.                    # Agent-to-agent messages
│   ├── [agent_id].in       # Inbound messages to agent
│   └── [agent_id].out      # Outbound messages from agent
├── broadcast.               # Broadcast messages
│   ├── alert                # System alerts
│   ├── decision             # Decision broadcasts
│   └── insight              # Insight broadcasts
├── tribunal.                # Tribunal deliberation
│   ├── convene             # Tribunal convening
│   ├── vote                 # Voting subject
│   └── verdict              # Verdict broadcast
├── tasks.                   # Task management
│   ├── create              # Task creation
│   ├── assign              # Task assignment
│   └── complete            # Task completion
└── memory.                  # Memory operations
    ├── read                # Memory read
    ├── write               # Memory write
    └── search              # Memory search
```

### 2.4 A2A Message Types

| Message Type | Subject | Purpose |
|--------------|---------|---------|
| `TASK_REQUEST` | `agent.{id}.in` | Request agent to perform task |
| `TASK_RESPONSE` | `agent.{id}.out` | Response to task request |
| `BROADCAST_ALERT` | `broadcast.alert` | System-wide alert |
| `BROADCAST_INSIGHT` | `broadcast.insight` | Share insight with all |
| `TRIB_CONVENE` | `tribunal.convene` | Convene tribunal |
| `TRIB_VOTE` | `tribunal.vote` | Cast tribunal vote |
| `TRIB_VERDICT` | `tribunal.verdict` | Broadcast verdict |
| `HEARTBEAT` | `pulse.steward` | Steward heartbeat |
| `STATUS_UPDATE` | `agent.{id}.out` | Agent status update |
| `CONSENSUS_PROPOSE` | `consensus.propose` | Propose consensus |
| `CONSENSUS_VOTE` | `consensus.vote` | Vote on consensus |

### 2.5 A2A Protocol Implementation

**File:** `src/heretek_swarm/infrastructure/a2a/`

```python
# protocol.py
class A2AProtocol:
    """A2A Protocol Handler"""

    async def send_message(
        self,
        to: AgentId,
        subject: str,
        action: str,
        payload: dict,
        priority: Priority = Priority.NORMAL
    ) -> MessageId: ...

    async def broadcast(
        self,
        subject: str,
        action: str,
        payload: dict
    ) -> BroadcastId: ...

    async def request_response(
        self,
        to: AgentId,
        subject: str,
        action: str,
        payload: dict,
        timeout: timedelta
    ) -> Response: ...

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[A2AMessage], None]
    ) -> Subscription: ...
```

### 2.6 A2A Security

```python
class A2ASecurity:
    """A2A Protocol Security"""

    async def validate_sender(message: A2AMessage) -> bool:
        """Validate sender identity"""

    async def verify_signature(message: A2AMessage) -> bool:
        """Verify message signature"""

    async def check_permissions(sender: AgentId, action: str) -> bool:
        """Check if sender has permission for action"""

    async def encrypt_payload(payload: dict) -> EncryptedPayload:
        """Encrypt sensitive payload"""

    async def decrypt_payload(encrypted: EncryptedPayload) -> dict:
        """Decrypt payload"""
```

---

## PART III: INTERNAL PROTOCOLS

### 3.1 Consensus Protocol

```python
class ConsensusProtocol:
    """Heretek Swarm Consensus Mechanism"""

    async def propose(proposal: Proposal) -> ConsensusId:
        """Propose item for consensus"""

    async def vote(consensus_id: ConsensusId, vote: Vote) -> None:
        """Cast vote on proposal"""

    async def tally(consensus_id: ConsensusId) -> TallyResult:
        """Tally votes and determine outcome"""

    async def finalize(consensus_id: ConsensusId) -> FinalResult:
        """Finalize consensus and execute outcome"""

# Consensus thresholds
MAJORITY_THRESHOLD = 0.51  # Simple majority
SUPERMAJORITY_THRESHOLD = 0.67  # 2/3 majority
UNANIMOUS_THRESHOLD = 1.0  # Full agreement required
```

### 3.2 Tribunal Protocol

```python
class TribunalProtocol:
    """Tribunal Deliberation Protocol"""

    async def convene(issue: Issue) -> TribunalId:
        """Convene Core Triad for deliberation"""

    async def present_evidence(tribunal_id: TribunalId, evidence: Evidence) -> None:
        """Present evidence to tribunal"""

    async def deliberate(tribunal_id: TribunalId) -> Deliberation:
        """Triad deliberates on issue"""

    async def cast_vote(tribunal_id: TribunalId, vote: Vote) -> None:
        """Cast individual vote"""

    async def reach_verdict(tribunal_id: TribunalId) -> Verdict:
        """Reach and broadcast verdict"""
```

### 3.3 Heartbeat Protocol

```python
class HeartbeatProtocol:
    """Steward Heartbeat Protocol"""

    HEARTBEAT_INTERVAL = 30  # seconds

    async def send_pulse() -> PulseData:
        """Send system pulse"""

    async def monitor_agents() -> list[AgentHealth]:
        """Monitor all agent health"""

    async def detect_anomaly(pulse: PulseData) -> Anomaly | None:
        """Detect anomalies in pulse"""

    async def escalate_anomaly(anomaly: Anomaly) -> None:
        """Escalate anomaly to Sentinel"""
```

### 3.4 Memory Sync Protocol

```python
class MemorySyncProtocol:
    """Memory Synchronization Protocol"""

    async def broadcast_insight(insight: Insight) -> None:
        """Broadcast insight to Global Workspace"""

    async def sync_state(agent_id: AgentId, state: AgentState) -> None:
        """Sync agent state to memory"""

    async def read_workspace(query: str) -> list[Insight]:
        """Read from Global Workspace"""

    async def subscribe_workspace(agent_id: AgentId) -> Subscription:
        """Subscribe agent to workspace updates"""
```

---

## PART IV: MESSAGE SCHEMA DEFINITIONS

### 4.1 ActorMessage (Internal)

```python
class ActorMessage(BaseModel):
    """Internal actor message format"""
    message_type: str                          # Message type identifier
    content: dict[str, Any]                    # Message content
    sender: str                                # Sender agent ID
    recipient: str                              # Recipient agent ID
    timestamp: datetime                        # Creation timestamp
    conversation_id: UUID | None              # Conversation thread
    parent_message_id: UUID | None            # Parent message (reply)
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: dict[str, Any] = {}
```

### 4.2 AgentMessage (External)

```python
class AgentMessage(BaseModel):
    """External agent message format"""
    id: UUID
    message_type: AgentMessageType
    sender: AgentId
    recipients: list[AgentId]
    content: Content
    timestamp: datetime
    ttl: timedelta | None
    signature: str | None
    encrypted: bool = False
```

### 4.3 TaskMessage

```python
class TaskMessage(BaseModel):
    """Task assignment message"""
    task_id: UUID
    task_type: TaskType
    description: str
    assignee: AgentId | None
    priority: Priority
    deadline: datetime | None
    dependencies: list[UUID] = []
    context: dict[str, Any] = {}
```

---

## PART V: PROTOCOL VERSIONING

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-12 | Initial protocol definition |
| 1.1.0 | TBD | Add consciousness metrics to protocol |
| 1.2.0 | TBD | Add emergence detection fields |

---

## PART VI: IMPLEMENTATION STATUS

| Protocol | Status | Location |
|----------|--------|----------|
| MCP Server | ✅ IMPLEMENTED | `src/heretek_swarm/mcp/server.py` |
| MCP Client | ✅ IMPLEMENTED | `src/heretek_swarm/mcp/client.py` |
| MCP Registry | ✅ IMPLEMENTED | `src/heretek_swarm/mcp/registry.py` |
| A2A Protocol | ✅ IMPLEMENTED | `src/heretek_swarm/infrastructure/a2a/protocol.py` |
| NATS Bridge | ⚠️ PARTIAL | `src/heretek_swarm/infrastructure/nats/` (not wired) |
| Consensus | ⚠️ EXISTS | `src/heretek_swarm/consensus/` (not integrated) |
| Tribunal | ❌ INCOMPLETE | Not implemented |
| Heartbeat | ❌ INCOMPLETE | Not implemented |

---

**Document Classification:** PROTOCOL SPECIFICATION
**Last Updated:** 2026-04-12 17:06 EDT
**Protocol Version:** 1.0.0