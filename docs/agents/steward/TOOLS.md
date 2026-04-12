---
name: steward-tools
description: Native capabilities of the Steward Agent
type: agent
---

# Steward Agent Tools

**Tier 1 (Core Triad) | Orchestrator**

## Native Capabilities

### 1. Task Router
Routes tasks to specialized agents based on capability matching and load balancing.

**Interface:**
```python
async def route_task(task: TaskRequest, capabilities: list[str]) -> AgentAssignment
```

**Behavior:**
- Evaluates agent registry for matching capabilities
- Queries agent load via event mesh
- Assigns to optimal agent with fallback routing
- Tracks assignment state until completion

### 2. Deliberation Manager
Manages the Alpha-Beta-Charlie deliberation cycle for consensus decisions.

**Interface:**
```python
async def start_deliberation(session_id: str, problem: str) -> DeliberationSession
async def aggregate_consensus(session_id: str) -> ConsensusResult
```

**Behavior:**
- Creates deliberation session with unique ID
- Routes through triad phases (alpha → beta → charlie)
- Tracks phase completion and findings
- Aggregates into final consensus with confidence score

### 3. Agent State Monitor
Monitors health and status of all registered agents in the swarm.

**Interface:**
```python
async def query_agent_states() -> dict[str, AgentState]
async def get_agent_heartbeat(agent_id: str) -> HeartbeatInfo
```

**Behavior:**
- Subscribes to agent heartbeat events
- Maintains in-memory state cache with TTL
- Reports stale agents for remediation

### 4. Priority Queue Manager
Manages task prioritization and queue ordering.

**Interface:**
```python
async def enqueue_task(task: TaskRequest, priority: int) -> QueuePosition
async def get_next_task() -> TaskRequest | None
```

**Behavior:**
- Maintains priority-sorted task queue
- Handles priority updates and task cancellation
- Blocks on empty queue with timeout

### 5. Consensus Aggregator
Collects and synthesizes perspectives from triad agents.

**Interface:**
```python
async def collect_perspective(agent_id: str, topic: str) -> Perspective
async def synthesize(perspectives: list[Perspective]) -> SynthesisResult
```

**Behavior:**
- Routes synthesis requests to Alpha, Beta, Charlie
- Collects responses within timeout window
- Synthesizes into unified recommendation with dissent tracking

## External Service Tools

### NATS Event Mesh
- **Publish**: Send coordination messages to agents
- **Subscribe**: Receive agent heartbeats and responses
- **Request-Reply**: Synchronous agent queries

### LLM Provider
- **Coordinate**: Generate coordination reasoning
- **Synthesize**: Create consensus summaries

### PostgreSQL (via base class)
- **Persist**: Store deliberation sessions
- **Query**: Retrieve governance history

## Tool Categories

| Category | Tools |
|----------|-------|
| Orchestration | Task Router, Priority Queue Manager |
| Governance | Deliberation Manager, Consensus Aggregator |
| Monitoring | Agent State Monitor |
| Communication | NATS Event Mesh, LLM Provider |