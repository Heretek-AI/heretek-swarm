# Implementation Plan: INTG-01 — Coordinator Task Synchronization

## Task Overview

**Owner**: Coordinator
**Depends**: Phase 1 (NATS event mesh, health reporting)
**Verification**: Coordinator manages task dependency graph; synchronization operational; coordination ratio ≤ 0.35 of total capacity.

## Edge Cases

- Task dependency cycle — detection and resolution; Steward notified
- Agent dependency deadlock — configurable timeout; escalation to Arbiter

---

## 1. Analysis of Existing Code

### 1.1 Coordinator Agent (`src/heretek_swarm/actors/coordinator.py`)

**Current Capabilities**:
- `CoordinatedTask` and `AgentState` dataclasses
- `TaskStatus` enum (PENDING, READY, IN_PROGRESS, BLOCKED, COMPLETED, FAILED, CANCELLED)
- `DependencyType` enum (SEQUENTIAL, PARALLEL, CONDITIONAL, RESOURCE)
- Basic task management handlers: `create_task`, `update_task`, `get_task_status`
- Workflow management: `start_workflow`, `cancel_workflow`
- Agent tracking: `assign_agent`, `update_agent_state`
- Dependency graph: `_dependency_graph` (task_id → dependent task_ids), `_reverse_deps` (task_id → dependency task_ids)
- Topological sort: `_topological_sort()`
- Parallel group identification: `_identify_parallel_groups()`
- Critical path finding: `_find_critical_path()`
- Basic unblocking: `_unblock_dependents()`

**Missing for INTG-01**:
- No cycle detection in dependency graph
- No deadlock detection for agent dependencies
- No coordination ratio tracking
- No escalation mechanisms (Steward for cycles, Arbiter for deadlocks)
- No dedicated task graph module
- No dedicated synchronization module

---

## 2. Implementation Architecture

### 2.1 Files to Create

```
src/heretek_swarm/coordination/
├── __init__.py                    # Package init
├── task_graph.py                  # NEW - Task dependency graph module
├── sync.py                        # NEW - Synchronization mechanisms
```

### 2.2 Files to Modify

```
src/heretek_swarm/actors/coordinator.py  # ENHANCE - Integrate new modules
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/coordination/task_graph.py` (NEW)

**Purpose**: Dedicated task dependency graph with cycle detection and graph algorithms.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid

class GraphNodeType(Enum):
    """Types of nodes in the task graph."""
    TASK = "task"
    MILESTONE = "milestone"
    BARRIER = "barrier"

class EdgeType(Enum):
    """Types of edges in the task graph."""
    DEPENDENCY = "dependency"
    BLOCKS = "blocks"
    WAITS_FOR = "waits_for"
    PART_OF = "part_of"

@dataclass
class GraphNode:
    """A node in the task dependency graph."""
    node_id: str
    node_type: GraphNodeType = GraphNodeType.TASK
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Graph metrics (updated by algorithms)
    in_degree: int = 0
    out_degree: int = 0
    depth: int = 0  # Longest path from root
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "depth": self.depth,
        }

@dataclass
class GraphEdge:
    """An edge in the task dependency graph."""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.DEPENDENCY
    weight: float = 1.0  # For critical path calculation
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
        }
```

#### Core Class: `TaskGraph`

```python
class TaskGraph:
    """
    Task dependency graph with cycle detection and graph algorithms.
    
    Responsibilities:
    1. Maintain task dependency graph structure
    2. Detect cycles using Tarjan's algorithm
    3. Calculate graph metrics (depth, complexity, critical path)
    4. Provide topological ordering
    5. Serialize/deserialize for persistence
    
    Key Methods:
    - add_node(), remove_node(), add_edge(), remove_edge()
    - detect_cycles() - returns cycle information
    - get_topological_order() - Kahn's algorithm
    - calculate_critical_path() - longest path
    - get_graph_metrics() - statistics
    """

    def __init__(self, max_nodes: int = 10000):
        # Graph structure
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        
        # Adjacency lists for O(1) neighbor lookup
        self._adjacency: dict[str, set[str]] = {}  # node -> neighbors (outgoing)
        self._reverse_adjacency: dict[str, set[str]] = {}  # node -> predecessors (incoming)
        
        # Metrics
        self._max_nodes = max_nodes
        self._cycle_cache: list[list[str]] | None = None
        self._topo_order_cache: list[str] | None = None
        
        # Configuration
        self._cycle_resolution_strategy: str = "notify"  # "notify", "remove", "break"
        
    # === Node Management ===
    
    def add_node(self, node_id: str, node_type: GraphNodeType = GraphNodeType.TASK,
                 metadata: dict[str, Any] | None = None) -> GraphNode:
        """Add a node to the graph."""
        
    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all connected edges."""
        
    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        
    def node_exists(self, node_id: str) -> bool:
        """Check if node exists."""
        
    # === Edge Management ===
    
    def add_edge(self, source_id: str, target_id: str,
                 edge_type: EdgeType = EdgeType.DEPENDENCY,
                 weight: float = 1.0) -> GraphEdge | None:
        """Add an edge (dependency) between nodes."""
        # Returns None if would create cycle
        # Updates in_degree/out_degree for both nodes
        
    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge."""
        
    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges outgoing from a node."""
        
    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges incoming to a node."""
        
    # === Cycle Detection (Tarjan's Algorithm) ===
    
    def detect_cycles(self) -> dict[str, Any]:
        """
        Detect cycles using Tarjan's strongly connected components algorithm.
        
        Returns:
            {
                "has_cycles": bool,
                "cycles": list[list[str]]  # List of cycle node IDs,
                "cycle_count": int,
            }
        """
        # Tarjan's algorithm implementation
        # Returns cycle information if found
        
    def get_cycle_detection_timestamp(self) -> datetime:
        """Return timestamp of last cycle detection."""
        
    # === Cycle Resolution ===
    
    def resolve_cycle(self, cycle: list[str], strategy: str | None = None) -> dict[str, Any]:
        """
        Resolve a detected cycle.
        
        Strategies:
        - "notify": Notify Steward, leave graph unchanged
        - "remove": Remove the edge that creates the cycle (oldest dependency)
        - "break": Break the cycle by removing a node (last resort)
        
        Returns:
            {
                "resolved": bool,
                "action": str,
                "details": str,
            }
        """
        
    # === Topological Sort (Kahn's Algorithm) ===
    
    def get_topological_order(self) -> list[str]:
        """
        Get topological ordering using Kahn's algorithm.
        
        Returns:
            List of node IDs in topological order
            
        Raises:
            ValueError if graph contains cycles
        """
        # Uses Kahn's algorithm with priority queue for deterministic ordering
        # Respects node priorities when available
        
    # === Critical Path Calculation ===
    
    def calculate_critical_path(self) -> dict[str, Any]:
        """
        Calculate the critical path (longest dependency chain).
        
        Returns:
            {
                "critical_path": list[str],  # Node IDs
                "path_length": float,
                "estimated_duration": float,
            }
        """
        # Uses longest path algorithm
        # Weights edges for duration estimation
        
    # === Graph Metrics ===
    
    def get_graph_metrics(self) -> dict[str, Any]:
        """
        Calculate graph statistics.
        
        Returns:
            {
                "node_count": int,
                "edge_count": int,
                "max_depth": int,
                "avg_depth": float,
                "complexity_score": float,  # Higher = more complex graph
                "parallelism_factor": float,  # 0-1, higher = more parallelizable
            }
        """
        
    def calculate_load(self) -> float:
        """Calculate coordination load as ratio of graph operations."""
        
    # === Serialization ===
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary."""
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskGraph":
        """Deserialize graph from dictionary."""
```

#### Cycle Detection Implementation Details

```python
# Tarjan's Algorithm for strongly connected components
def _tarjan_scc(self) -> list[list[str]]:
    """
    Tarjan's strongly connected components algorithm.
    
    Time: O(V + E)
    Space: O(V)
    
    Returns:
        List of strongly connected components (cycles)
    """
    # DFS-based implementation
    # Uses stack for node tracking
    # Low-link values for SCC identification
```

#### Example Usage

```python
# Create task graph
graph = TaskGraph()

# Add tasks as nodes
graph.add_node("task-1", metadata={"priority": 1})
graph.add_node("task-2", metadata={"priority": 2})
graph.add_node("task-3", metadata={"priority": 1})
graph.add_node("task-4", metadata={"priority": 3})

# Add dependencies (edges)
graph.add_edge("task-1", "task-2")  # task-2 depends on task-1
graph.add_edge("task-2", "task-3")  # task-3 depends on task-2
graph.add_edge("task-3", "task-4")  # task-4 depends on task-3

# Detect cycles
cycle_result = graph.detect_cycles()
if cycle_result["has_cycles"]:
    print(f"Found {cycle_result['cycle_count']} cycles")

# Get execution order
execution_order = graph.get_topological_order()

# Calculate critical path
critical = graph.calculate_critical_path()
print(f"Critical path: {critical['critical_path']}")
```

---

### 3.2 `src/heretek_swarm/coordination/sync.py` (NEW)

**Purpose**: Synchronization mechanisms with deadlock detection, timeout management, and coordination ratio tracking.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

class DeadlockState(Enum):
    """States of a potential deadlock."""
    NONE = "none"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    RESOLVING = "resolving"
    RESOLVED = "resolved"

class EscalationLevel(Enum):
    """Escalation levels for coordination issues."""
    NONE = "none"
    COORDINATOR = "coordinator"
    STEWARD = "steward"
    ARBITER = "arbiter"
    HUMAN = "human"

@dataclass
class AgentDependency:
    """A dependency between agents on shared resources/tasks."""
    dependency_id: str
    waiting_agent_id: str
    holding_agent_id: str
    resource_id: str
    wait_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    state: DeadlockState = DeadlockState.NONE
    cycle_detected: bool = False
    
    @property
    def wait_duration(self) -> timedelta:
        """Calculate how long agent has been waiting."""
        return datetime.now(UTC) - self.wait_start
        
    @property
    def is_expired(self) -> bool:
        """Check if timeout has been exceeded."""
        return self.wait_duration > self.timeout

@dataclass
class CoordinationMetrics:
    """Metrics for coordination overhead tracking."""
    total_capacity: float = 1.0  # Normalized (0-1)
    coordination_used: float = 0.0
    coordination_ratio: float = 0.0  # coordination_used / total_capacity
    active_sync_operations: int = 0
    pending_dependencies: int = 0
    deadlocks_detected: int = 0
    cycles_detected: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_capacity": self.total_capacity,
            "coordination_used": self.coordination_used,
            "coordination_ratio": self.coordination_ratio,
            "active_sync_operations": self.active_sync_operations,
            "pending_dependencies": self.pending_dependencies,
            "deadlocks_detected": self.deadlocks_detected,
            "cycles_detected": self.cycles_detected,
            "last_updated": self.last_updated.isoformat(),
        }
```

#### Core Class: `TaskSynchronizer`

```python
class TaskSynchronizer:
    """
    Task synchronization with deadlock detection and resolution.
    
    Responsibilities:
    1. Track agent dependencies and wait-for relationships
    2. Detect deadlocks using wait-for graph
    3. Manage configurable timeouts
    4. Escalate to Arbiter when needed
    5. Track coordination ratio (must stay <= 0.35)
    6. Emit health reports for monitoring
    
    Key Metrics:
    - Coordination ratio <= 0.35
    - Deadlock detection timeout: configurable (default 30s)
    - Escalation to Arbiter after deadlock confirmation
    """

    def __init__(
        self,
        deadlock_timeout: timedelta = timedelta(seconds=30),
        max_retries: int = 3,
        coordination_budget: float = 0.35,  # Max coordination ratio
    ):
        # Dependency tracking
        self._dependencies: dict[str, AgentDependency] = {}
        self._agent_locks: dict[str, set[str]] = {}  # agent_id -> resource_ids held
        
        # Wait-for graph for deadlock detection
        self._wait_for_graph: dict[str, set[str]] = {}  # agent -> agents it waits for
        
        # Configuration
        self._deadlock_timeout = deadlock_timeout
        self._max_retries = max_retries
        self._coordination_budget = coordination_budget
        
        # Metrics
        self._metrics = CoordinationMetrics()
        
        # Escalation handlers
        self._steward_client: Any = None  # For cycle notification
        self._arbiter_client: Any = None  # For deadlock escalation
        
        # Callbacks
        self._on_cycle_detected: callable | None = None
        self._on_deadlock_detected: callable | None = None
        
    # === Dependency Management ===
    
    async def register_dependency(
        self,
        waiting_agent: str,
        holding_agent: str,
        resource_id: str,
    ) -> str:
        """
        Register an agent dependency (wait-for relationship).
        
        Returns:
            dependency_id for tracking
        """
        
    async def release_dependency(self, dependency_id: str) -> bool:
        """
        Release a dependency when resource becomes available.
        
        Returns:
            True if released, False if not found
        """
        
    async def get_blocking_agents(self, agent_id: str) -> list[str]:
        """
        Get agents that are blocking a given agent.
        
        Returns:
            List of agent IDs this agent is waiting on
        """
        
    # === Deadlock Detection (Wait-For Graph) ===
    
    async def detect_deadlock(self, agent_id: str | None = None) -> dict[str, Any]:
        """
        Detect deadlocks using wait-for graph cycle detection.
        
        Algorithm:
        1. Build wait-for graph from dependencies
        2. Detect cycles using DFS
        3. Return cycle information if found
        
        Returns:
            {
                "has_deadlock": bool,
                "deadlock_chain": list[str] | None,  # Cycle of agent IDs
                "suspected_agents": list[str],
                "detection_time": datetime,
            }
        """
        # Uses DFS-based cycle detection on wait-for graph
        # Returns first detected deadlock chain
        
    async def check_deadlock_timeout(self) -> list[AgentDependency]:
        """
        Check for dependencies that have exceeded timeout.
        
        Returns:
            List of expired dependencies
        """
        
    # === Deadlock Resolution ===
    
    async def resolve_deadlock(
        self,
        deadlock_chain: list[str],
        strategy: str = "escalate",
    ) -> dict[str, Any]:
        """
        Resolve a detected deadlock.
        
        Strategies:
        - "timeout": Force release after timeout (default)
        - "negotiate": Request agents release voluntarily
        - "escalate": Escalate to Arbiter for binding decision
        
        Returns:
            {
                "resolved": bool,
                "action": str,
                "agents_notified": list[str],
                "escalation_level": EscalationLevel,
            }
        """
        
    async def escalate_to_arbiter(
        self,
        deadlock_chain: list[str],
        context: dict[str, Any],
    ) -> str:
        """
        Escalate deadlock to Arbiter for resolution.
        
        Returns:
            escalation_id for tracking
        """
        
    # === Cycle Detection (for task dependencies) ===
    
    async def notify_cycle_detected(
        self,
        cycle: list[str],
        graph_snapshot: dict[str, Any],
    ) -> None:
        """
        Notify Steward of detected task dependency cycle.
        
        This is called when the TaskGraph detects a cycle.
        Steward should be informed for governance awareness.
        """
        
    # === Coordination Ratio Tracking ===
    
    async def record_coordination_usage(self, operation_type: str, cost: float) -> None:
        """
        Record coordination overhead.
        
        Coordination ratio = coordination_used / total_capacity
        Must stay <= 0.35
        """
        
    async def get_coordination_ratio(self) -> float:
        """
        Get current coordination ratio.
        
        Returns:
            Coordination ratio (0.0 to 1.0)
            Must be <= 0.35 for healthy operation
        """
        
    async def pause_coordination_if_needed(self) -> bool:
        """
        Pause lower-priority coordination if ratio exceeds budget.
        
        Returns:
            True if coordination was paused
        """
        
    def get_metrics(self) -> CoordinationMetrics:
        """Get current coordination metrics."""
        
    # === Health Integration ===
    
    async def emit_health_report(self) -> dict[str, Any]:
        """
        Emit synchronization health report.
        
        Returns:
            Health status for HealthReportingMixin
        """
```

#### Wait-For Graph Deadlock Detection

```python
# Algorithm for wait-for graph cycle detection
def _detect_wait_for_cycle(self) -> list[str] | None:
    """
    Detect cycles in the wait-for graph.
    
    Uses DFS with coloring:
    - WHITE: unvisited
    - GRAY: in progress (on current path)
    - BLACK: completed (fully processed)
    
    A cycle exists if we encounter a GRAY node during DFS.
    
    Time: O(V + E) where V = agents, E = wait-for relationships
    """
    # Track visited and in-progress nodes
    # Use recursion or stack for DFS
    # Return cycle path if found
```

#### Coordination Ratio Calculation

```python
def _calculate_coordination_ratio(self) -> float:
    """
    Calculate coordination overhead ratio.
    
    Formula:
    coordination_ratio = (
        sync_time_spent + 
        deadlock_detection_time + 
        message_overhead
    ) / total_processing_time
    
    Must stay <= 0.35 (35% of capacity)
    
    Components tracked:
    - Active sync operations (weighted by duration)
    - Pending dependencies (lightweight tracking)
    - Deadlock detection cycles (expensive)
    - Cycle resolution overhead
    """
    # Sum weighted time components
    # Divide by total time window
    # Return as 0-1 ratio
```

#### Example Usage

```python
# Initialize synchronizer
sync = TaskSynchronizer(
    deadlock_timeout=timedelta(seconds=30),
    coordination_budget=0.35,
)

# Register dependency (agent-2 waits for agent-1 on resource-X)
dep_id = await sync.register_dependency(
    waiting_agent="agent-2",
    holding_agent="agent-1",
    resource_id="resource-X",
)

# Check for deadlocks
result = await sync.detect_deadlock("agent-2")
if result["has_deadlock"]:
    # Handle deadlock
    resolution = await sync.resolve_deadlock(
        result["deadlock_chain"],
        strategy="escalate"
    )

# Monitor coordination ratio
ratio = await sync.get_coordination_ratio()
print(f"Coordination ratio: {ratio:.2%}")  # e.g., "32.5%"
```

---

### 3.3 Coordinator Enhancements (`src/heretek_swarm/actors/coordinator.py`)

#### New Imports

```python
from heretek_swarm.coordination.task_graph import TaskGraph, GraphNode, GraphEdge, GraphNodeType, EdgeType
from heretek_swarm.coordination.sync import TaskSynchronizer, AgentDependency, CoordinationMetrics, DeadlockState, EscalationLevel
```

#### New Attributes

```python
# Task graph module
self._task_graph: TaskGraph | None = None

# Synchronization module
self._synchronizer: TaskSynchronizer | None = None

# Configuration
self._cycle_notification_enabled: bool = True
self._deadlock_escalation_enabled: bool = True

# Metrics tracking
self._coordination_ratio_history: list[float] = []
self._max_coordination_ratio: float = 0.35
```

#### New Message Handlers

```python
# In _register_handlers()
"graph_detect_cycles": self._handle_graph_detect_cycles,
"graph_get_metrics": self._handle_graph_get_metrics,
"graph_get_topological_order": self._handle_graph_get_topological_order,
"sync_register_dependency": self._handle_sync_register_dependency,
"sync_release_dependency": self._handle_sync_release_dependency,
"sync_detect_deadlock": self._handle_sync_detect_deadlock,
"get_coordination_ratio": self._handle_get_coordination_ratio,
"get_sync_health": self._handle_get_sync_health,
```

#### New Methods

```python
async def _handle_graph_detect_cycles(self, message: ActorMessage) -> None:
    """
    Detect cycles in task dependency graph.
    
    Content: {}  # Optional {"task_ids": [...]}
    
    Returns: {
        "has_cycles": bool,
        "cycle_count": int,
        "cycles": list[list[str]],
    }
    """

async def _handle_graph_get_metrics(self, message: ActorMessage) -> None:
    """
    Get task graph metrics.
    
    Returns: {
        "node_count": int,
        "edge_count": int,
        "max_depth": int,
        "complexity_score": float,
        "parallelism_factor": float,
    }
    """

async def _handle_sync_register_dependency(self, message: ActorMessage) -> None:
    """
    Register an agent dependency for tracking.
    
    Content: {
        "waiting_agent": str,
        "holding_agent": str,
        "resource_id": str,
    }
    """

async def _handle_sync_detect_deadlock(self, message: ActorMessage) -> None:
    """
    Detect deadlocks in agent dependencies.
    
    Content: {"agent_id": str | None}  # None = check all
    
    Returns: {
        "has_deadlock": bool,
        "deadlock_chain": list[str] | None,
        "detection_time": str,
    }
    """

async def _handle_get_coordination_ratio(self, message: ActorMessage) -> None:
    """
    Get current coordination ratio.
    
    Returns: {
        "coordination_ratio": float,
        "total_capacity": float,
        "coordination_used": float,
        "is_healthy": bool,
    }
    """
```

#### Cycle Detection Integration

```python
async def _notify_steward_of_cycle(self, cycle: list[str]) -> None:
    """
    Notify Steward when task dependency cycle is detected.
    
    Message format:
    - message_type: "cycle_detected"
    - content: {
        "cycle_node_ids": list[str],
        "graph_snapshot": {...},
        "resolution_suggested": str,
        "requires_intervention": bool,
    }
    """
    # Send to Steward via NATS
    await self.send(
        "steward",
        ActorMessage(
            message_type="cycle_detected",
            content={
                "cycle_node_ids": cycle,
                "coordinator_id": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "resolution_strategy": "awaiting_steward_guidance",
            },
            sender_id=self.agent_id,
        ),
    )
```

#### Deadlock Resolution Integration

```python
async def _escalate_deadlock_to_arbiter(self, deadlock_chain: list[str]) -> None:
    """
    Escalate deadlock to Arbiter when resolution fails.
    
    Message format:
    - message_type: "deadlock_escalation"
    - content: {
        "deadlock_chain": list[str],
        "agents_involved": list[str],
        "context": {...},
        "requested_resolution": str,
    }
    """
    # Send to Arbiter via NATS
    await self.send(
        "arbiter",
        ActorMessage(
            message_type="deadlock_escalation",
            content={
                "deadlock_chain": deadlock_chain,
                "coordinator_id": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "context": {"attempts_resolved": 0},
            },
            sender_id=self.agent_id,
        ),
    )
```

#### Coordination Ratio Tracking

```python
async def _update_coordination_ratio(self) -> float:
    """
    Update and return current coordination ratio.
    
    Calculates ratio based on:
    - Sync operation time / total time
    - Graph algorithm overhead
    - Message processing for coordination
    
    Returns:
        Current coordination ratio (0.0 to 1.0)
    """
    # Sample current metrics from synchronizer
    metrics = self._synchronizer.get_metrics()
    
    # Calculate weighted ratio
    sync_cost = metrics.active_sync_operations * 0.01
    deadlock_cost = metrics.deadlocks_detected * 0.05
    cycle_cost = metrics.cycles_detected * 0.03
    
    ratio = min(1.0, sync_cost + deadlock_cost + cycle_cost)
    
    # Track history for trend analysis
    self._coordination_ratio_history.append(ratio)
    if len(self._coordination_ratio_history) > 100:
        self._coordination_ratio_history.pop(0)
    
    return ratio

def _is_coordination_healthy(self, ratio: float) -> bool:
    """Check if coordination ratio is within healthy bounds."""
    return ratio <= self._max_coordination_ratio
```

---

## 4. Integration Points

### 4.1 With NATS Event Mesh (Phase 1)

- Use NATS for inter-agent coordination messages
- Subscribe to task completion events for unblocking
- Publish coordination ratio metrics for monitoring

### 4.2 With Steward Agent

- Notify Steward when cycles detected
- Request guidance on cycle resolution strategy
- Report coordination health metrics

### 4.3 With Arbiter Agent

- Escalate deadlocks after configurable timeout
- Provide deadlock chain and context for resolution
- Accept binding decisions on resource allocation

### 4.4 With HealthReportingMixin

- Emit health reports with:
  - Task graph metrics
  - Coordination ratio
  - Active deadlocks
  - Cycle detection status

---

## 5. Edge Case Handling

### 5.1 Task Dependency Cycle

**Detection**:
- TaskGraph.detect_cycles() uses Tarjan's SCC algorithm
- Called during edge addition to catch cycles early
- Also called on demand via `graph_detect_cycles` message

**Detection Flow**:
```
Edge Added
    ↓
Check would create cycle?
    ↓ (yes)
Call detect_cycles()
    ↓
Found cycle: [A, B, C, A]
    ↓
Log CRITICAL event
    ↓
Notify Steward (if enabled)
    ↓
Return cycle to caller
    ↓
Resolution strategy applied
```

**Resolution Strategies**:
1. **notify** (default): Notify Steward, leave graph unchanged, require manual intervention
2. **remove**: Automatically remove the oldest edge that creates the cycle
3. **break**: Break the cycle by removing a node (last resort, task cancelled)

**Steward Notification Format**:
```python
{
    "message_type": "cycle_detected",
    "content": {
        "cycle_node_ids": ["task-1", "task-2", "task-3"],
        "cycle_edge_ids": ["edge-5", "edge-8"],
        "coordinator_id": "coordinator_abc123",
        "timestamp": "2026-04-14T10:30:00Z",
        "graph_snapshot": {
            "nodes": [...],
            "edges": [...],
        },
        "resolution_options": ["notify", "remove", "break"],
    }
}
```

### 5.2 Agent Dependency Deadlock

**Detection**:
- TaskSynchronizer builds wait-for graph from dependencies
- DFS-based cycle detection on wait-for graph
- Timeout-based detection: if agent waiting > configured timeout

**Detection Flow**:
```
Dependency Registered
    ↓
Build/Update Wait-For Graph
    ↓
Check for cycles (deadlock detection)
    ↓ (cycle found)
DeadlockState = SUSPECTED
    ↓
Check timeout exceeded?
    ↓ (yes)
DeadlockState = CONFIRMED
    ↓
Attempt resolution
    ↓ (failed after max_retries)
Escalate to Arbiter
```

**Wait-For Graph Example**:
```
Agent A holds Resource 1
Agent B waits for Resource 1
Agent B holds Resource 2  
Agent C waits for Resource 2

Wait-For Graph:
A → (nothing, holds resource)
B → A (waits for resource held by A)
C → B (waits for resource held by B)

Cycle: A ← B ← C ← A? No wait...

If A waits for resource held by B, and B waits for resource held by A:
A → B → A (DEADLOCK)
```

**Resolution Flow**:
```
Deadlock Detected: [A, B, A]
    ↓
Attempt 1: Request voluntary release
    ↓
Attempt 2: Force timeout release
    ↓
Attempt 3: Escalate to Arbiter
    ↓
Arbiter makes binding decision
    ↓
Decision applied, dependencies updated
    ↓
DeadlockState = RESOLVED
```

**Arbiter Escalation Format**:
```python
{
    "message_type": "deadlock_escalation",
    "content": {
        "deadlock_chain": ["agent-A", "agent-B", "agent-C"],
        "resources_involved": ["resource-1", "resource-2"],
        "waiting_agents": {
            "agent-B": {"waiting_for": "resource-1", "held_by": "agent-A"},
            "agent-C": {"waiting_for": "resource-2", "held_by": "agent-B"},
        },
        "context": {
            "coordinator_id": "coordinator_abc123",
            "timestamp": "2026-04-14T10:30:00Z",
            "attempts_resolved": 3,
        },
        "requested_resolution": "binding_decision",
    }
}
```

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Task dependency graph | TaskGraph nodes/edges created | Tasks stored with edges |
| Cycle detection | Tarjan's algorithm on graph | Cycles detected and reported |
| Cycle resolution | Resolved cycles / total cycles | 100% detected cycles resolved |
| Steward notification | Cycle events sent to Steward | All cycles notified |
| Agent dependency tracking | Dependencies registered | Dependencies tracked in wait-for graph |
| Deadlock detection | Wait-for graph cycle detection | Deadlocks detected |
| Deadlock timeout | Configurable, default 30s | Expired dependencies flagged |
| Deadlock resolution | Resolved / total deadlocks | All confirmed deadlocks resolved |
| Arbiter escalation | Deadlocks escalated after timeout | Escalation occurs |
| Coordination ratio | coordination_used / total_capacity | ≤ 0.35 (35%) |
| Graph metrics | Node count, depth, complexity | Metrics reported |

---

## 7. Implementation Order

### Phase 1: Task Graph Module (Day 1-2)

1. Create `src/heretek_swarm/coordination/__init__.py`
   - Package initialization
   - Exports for public API

2. Create `src/heretek_swarm/coordination/task_graph.py`
   - `GraphNode`, `GraphEdge`, `GraphNodeType`, `EdgeType` dataclasses
   - `TaskGraph` class with node/edge management
   - `_tarjan_scc()` for cycle detection
   - `get_topological_order()` using Kahn's algorithm
   - `calculate_critical_path()` for longest path
   - `get_graph_metrics()` for statistics

### Phase 2: Synchronization Module (Day 3-4)

3. Create `src/heretek_swarm/coordination/sync.py`
   - `AgentDependency`, `CoordinationMetrics` dataclasses
   - `TaskSynchronizer` class with dependency tracking
   - `_detect_wait_for_cycle()` for deadlock detection
   - `resolve_deadlock()` with strategies
   - `escalate_to_arbiter()` for escalation
   - `record_coordination_usage()` and `get_coordination_ratio()`

### Phase 3: Coordinator Integration (Day 5-6)

4. Enhance `src/heretek_swarm/actors/coordinator.py`
   - Add imports for task_graph and sync
   - Add `_task_graph` and `_synchronizer` attributes
   - Add new message handlers
   - Integrate cycle detection with task creation
   - Integrate deadlock detection with dependency tracking
   - Add coordination ratio monitoring

### Phase 4: Testing & Verification (Day 7)

5. Create tests:
   - `tests/coordination/test_task_graph.py` (~150 lines)
   - `tests/coordination/test_sync.py` (~150 lines)
   - `tests/coordination/test_coordinator_intg.py` (~100 lines)

6. Verify:
   - Cycle detection works
   - Deadlock detection works
   - Coordination ratio ≤ 0.35
   - Steward/Arbiter integration functional

---

## 8. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/coordination/__init__.py` | CREATE | ~30 |
| `src/heretek_swarm/coordination/task_graph.py` | CREATE | ~450 |
| `src/heretek_swarm/coordination/sync.py` | CREATE | ~400 |
| `src/heretek_swarm/actors/coordinator.py` | ENHANCE | ~250 |
| `tests/coordination/test_task_graph.py` | CREATE | ~150 |
| `tests/coordination/test_sync.py` | CREATE | ~150 |
| `tests/coordination/test_coordinator_intg.py` | CREATE | ~100 |

**Total New Code**: ~1,130 lines
**Total Test Code**: ~400 lines

---

## 9. Dependencies

```
Phase 1 (NATS Event Mesh) ─────────────────────────┐
                                                     │
Phase 1 (HealthReportingMixin) ─────────────────────┼──► INTG-01
                                                     │
Phase 1 (ValidationMixin) ──────────────────────────┘
```

**Phase 1 dependencies**:
- NATS for inter-agent communication
- HealthReportingMixin for health reports
- ValidationMixin for message validation

**Task dependencies**:
- Task 11 (INTG-01) is prerequisite for Tasks 12, 13, 14
- INTG-02 (Nexus External API) depends on INTG-01
- INTG-03 (Catalyst Paradigm Shifts) depends on INTG-01
- INTG-04 (Chronos Time Perception) depends on INTG-01

---

## 10. Open Questions (for resolution during implementation)

1. **Cycle resolution default**: Should default be "notify" or "remove"? Notify gives Steward more control but requires manual intervention.

2. **Deadlock timeout value**: 30 seconds default — appropriate for the swarm's operational tempo?

3. **Coordination ratio threshold**: 0.35 — should this be configurable per workflow type?

4. **Escalation to Arbiter**: What context should be included? Agent priorities? Task importance?

5. **Graph persistence**: Should TaskGraph be persisted to PostgreSQL for recovery?

6. **Integration with existing _dependency_graph**: The current implementation has `_dependency_graph`. Should we migrate to TaskGraph or maintain both with sync?

---

## 11. Monitoring and Alerting

### Health Metrics to Track

```python
{
    "coordination_ratio": 0.32,  # Must stay <= 0.35
    "active_sync_operations": 5,
    "pending_dependencies": 12,
    "deadlocks_detected": 0,
    "cycles_detected": 0,
    "graph_node_count": 45,
    "graph_edge_count": 67,
    "graph_max_depth": 8,
    "critical_path_length": 12,
}
```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| coordination_ratio | > 0.30 | > 0.35 |
| deadlocks_detected | > 0 in 5min | > 0 ongoing |
| cycles_detected | > 0 | > 0 unresolved |
| pending_dependencies | > 50 | > 100 |

---

## 12. Future Enhancements (Out of Scope for INTG-01)

- Dynamic task graph rebalancing
- Predictive deadlock detection (ML-based)
- Cross-cluster coordination
- Priority inheritance for deadlock resolution
- Distributed task graph with sharding