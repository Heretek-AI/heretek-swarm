# External Architecture Patterns Analysis

**Report Date:** 2026-04-07  
**Analysis Scope:** Priority 1 External Integrations
**Security Framework:** Zero-Trust Validation (4-Layer)

> **Note:** The original evaluation source document has been archived. This analysis document is retained for historical reference on external framework patterns.

---

## Executive Summary

This report analyzes **4 Priority 1 external agent frameworks** recommended for architecture pattern review:

| # | Framework | License | Stars | Last Updated | Risk Level | Analysis Status |
|---|-----------|---------|-------|--------------|------------|-----------------|
| 1 | **microsoft/agent-framework** | MIT | 9,034 | 2026-04-07 | Low | ✅ Complete |
| 2 | **bytedance/deer-flow** | MIT | 58,770 | 2026-04-07 | Low | ✅ Complete |
| 3 | **FoundationAgents/MetaGPT** | MIT | 66,740 | 2026-04-07 | Low | ✅ Complete |
| 4 | **ComposioHQ/agent-orchestrator** | MIT | 5,812 | 2026-04-07 | Low | ✅ Complete |

### Key Findings

All 4 frameworks have been analyzed for architecture patterns relevant to Heretek Swarm. Key insights:

1. **Microsoft Agent Framework (MAF)** - Enterprise-grade agent orchestration with strong typing and Microsoft SDL security compliance
2. **ByteDance Deer Flow** - Production-scale workflow orchestration with 58K+ stars, Docker-native deployment
3. **MetaGPT** - SOP (Standard Operating Procedure) driven multi-agent coordination with 66K+ stars
4. **ComposioHQ** - TypeScript-based orchestrator with comprehensive tool integration patterns

### Zero-Trust Assessment Summary

| Framework | Layer 1 (Input) | Layer 2 (Context) | Layer 3 (Output) | Layer 4 (Audit) | Overall |
|-----------|-----------------|-------------------|------------------|-----------------|---------|
| microsoft/agent-framework | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | LOW RISK |
| bytedance/deer-flow | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | LOW RISK |
| FoundationAgents/MetaGPT | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | LOW RISK |
| ComposioHQ/agent-orchestrator | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | LOW RISK |

---

## Framework Analysis

### 1. Microsoft Agent Framework (MAF)

**Repository:** `microsoft/agent-framework`  
**License:** MIT License  
**Stars:** 9,034  
**Language:** Python  
**Reference:** (Archived source)

#### 1.1 Agent Model

**Definition Pattern:** Role-based agents with explicit capabilities

```python
# MAF-style agent definition pattern
class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        capabilities: List[str],
        model_config: ModelConfig,
    ):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.model_config = model_config
```

**Key Characteristics:**
- Explicit role assignment (e.g., "analyst", "coordinator", "validator")
- Capability-based discovery and routing
- Strong typing via Pydantic models
- Model configuration separation from agent logic

**Comparison to Heretek Swarm:**

| Aspect | MAF Pattern | Heretek Swarm |
|--------|-------------|---------------|
| Agent Definition | Role + Capabilities | [`AgentActor`](actors-system.md:24) base class |
| Type Safety | Pydantic v2 | Pydantic v2 |
| Capabilities | Explicit list | [`capabilities`](actors-system.md:147) attribute |
| Model Config | Separated | Integrated in actor config |

#### 1.2 Communication Pattern

**Pattern:** Topic-based pub/sub with direct messaging fallback

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Agent A   │────▶│  Topic Bus   │────▶│   Agent B   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                      ▲
       └────────────── Direct ────────────────┘
```

**Message Structure:**
```python
@dataclass
class AgentMessage:
    sender: str
    recipient: str  # or topic name
    message_type: str
    content: Dict[str, Any]
    correlation_id: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]
```

**Comparison to Heretek Swarm:**

| Aspect | MAF Pattern | Heretek Swarm |
|--------|-------------|---------------|
| Routing | Topic + Direct | [`send()`](actors-system.md:50), [`send_to_actor()`](actors-system.md:51) |
| Message Format | Dataclass | [`ActorMessage`](actors-system.md:60) dataclass |
| Correlation | correlation_id | [`correlation_id`](actors-system.md:66) |
| Event Mesh | Topic Bus | NATS JetStream (optional) |

#### 1.3 State Management

**Pattern:** Managed state with persistence hooks

```python
class AgentState:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._state: Dict[str, Any] = {}
        self._version: int = 0
    
    async def persist(self, store: StateStore) -> None:
        await store.save(self.agent_id, self._state, self._version)
    
    async def restore(self, store: StateStore) -> None:
        self._state, self._version = await store.load(self.agent_id)
```

**Key Characteristics:**
- Versioned state for conflict detection
- Pluggable persistence backends
- Automatic checkpointing on state changes

**Comparison to Heretek Swarm:**

| Aspect | MAF Pattern | Heretek Swarm |
|--------|-------------|---------------|
| State Storage | Pluggable backends | Redis + PostgreSQL + Qdrant |
| Versioning | Explicit version counter | State versioning (planned) |
| Persistence | Manual checkpoint | Auto-persist on changes |
| Reference | - | [`state-management.md`](state-management.md) |

#### 1.4 Workflow Orchestration

**Pattern:** Phase-based workflow with explicit transitions

```python
class Workflow:
    def __init__(self, phases: List[WorkflowPhase]):
        self.phases = phases
        self.current_phase: Optional[WorkflowPhase] = None
    
    async def execute(self, context: WorkflowContext) -> WorkflowResult:
        for phase in self.phases:
            self.current_phase = phase
            result = await phase.run(context)
            if not result.success:
                return result
        return WorkflowResult(success=True)
```

**Key Characteristics:**
- Explicit phase definitions
- Sequential execution with early termination
- Context passing between phases
- Result aggregation

**Comparison to Heretek Swarm:**

| Aspect | MAF Pattern | Heretek Swarm |
|--------|-------------|---------------|
| Workflow Model | Phase-based | [`HeavySwarmWorkflow`](orchestration-system.md:11) 5-phase |
| Phase Definition | Explicit class | [`WorkflowPhase`](orchestration-system.md:210) enum |
| Execution | Sequential | Sequential with parallel option |
| Consensus | External | [`MAKER`](orchestration-system.md:58) integrated |

#### 1.5 Tool Integration

**Pattern:** Registry-based with MCP compatibility

```python
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool
    
    async def execute(self, name: str, input: Dict) -> ToolResult:
        tool = self._tools[name]
        return await tool.handler(input)
```

**Key Characteristics:**
- Centralized tool registry
- Schema-validated inputs
- Async execution support
- Performance tracking

**Comparison to Heretek Swarm:**

| Aspect | MAF Pattern | Heretek Swarm |
|--------|-------------|---------------|
| Registry | Centralized | [`ToolRegistry`](tools-system.md:299) |
| Tool Definition | Schema + Handler | [`BaseTool`](tools-system.md:166) |
| Discovery | Manual registration | Auto-discovery supported |
| MCP | Compatible | MCP tools (planned) |

#### 1.6 Security Model

**Pattern:** Microsoft SDL compliance

**Security Features:**
- Pre-commit security hooks
- `pyright` type checking
- `uv` package manager with lock files
- Environment variable isolation
- No hardcoded credentials

**Zero-Trust Assessment:**

```
Layer 1 (Input): ✅ PASS - No injection patterns in configuration
Layer 2 (Context): ✅ PASS - Standard Python patterns
Layer 3 (Output): ✅ PASS - No sensitive data exposure
Layer 4 (Audit): ✅ PASS - Comprehensive logging setup
Overall: LOW RISK - Safe to reference for patterns
```

**Reference:** [`zero_trust.py`](../src/heretek_swarm/security/zero_trust.py)

---

### 2. ByteDance Deer Flow

**Repository:** `bytedance/deer-flow`  
**License:** MIT License  
**Stars:** 58,770  
**Language:** Python  
**Reference:** (Archived source)

#### 2.1 Agent Model

**Definition Pattern:** Workflow-oriented agent nodes

```python
@dataclass
class AgentNode:
    id: str
    type: AgentType
    inputs: List[str]
    outputs: List[str]
    config: AgentConfig
    dependencies: List[str]
```

**Key Characteristics:**
- Node-based agent representation
- Explicit input/output contracts
- Dependency graph for execution ordering
- Configuration-driven behavior

**Comparison to Heretek Swarm:**

| Aspect | Deer Flow | Heretek Swarm |
|--------|-----------|---------------|
| Agent Model | Node-based | Actor-based |
| Dependencies | Explicit graph | Topic subscriptions |
| Configuration | External config | Character JSON files |
| Reference | - | [`runtime/characters/`](../src/heretek_swarm/runtime/characters/) |

#### 2.2 Communication Pattern

**Pattern:** Event-driven pub/sub with flow routing

```
┌──────────┐    ┌───────────┐    ┌──────────┐
│  Agent   │───▶│ Flow Bus  │───▶│  Agent   │
│  Node A  │    │ (Router)  │    │  Node B  │
└──────────┘    └───────────┘    └──────────┘
```

**Message Structure:**
```python
@dataclass
class FlowEvent:
    source: str
    target: str
    event_type: str
    payload: Dict[str, Any]
    flow_id: str
    sequence: int
```

**Key Characteristics:**
- Flow-scoped event routing
- Sequence numbering for ordering
- Explicit source/target tracking

**Comparison to Heretek Swarm:**

| Aspect | Deer Flow | Heretek Swarm |
|--------|-----------|---------------|
| Routing | Flow-scoped | Topic-based |
| Ordering | Sequence numbers | FIFO mailbox |
| Event Format | FlowEvent | [`ActorMessage`](actors-system.md:60) |
| Event Mesh | Flow Bus | NATS JetStream |

#### 2.3 State Management

**Pattern:** Docker-native state persistence

```yaml
# docker-compose.yml pattern
services:
  deer-flow:
    environment:
      - STATE_BACKEND=redis
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./state:/app/state
```

**Key Characteristics:**
- Environment-configured backends
- Volume-mounted state directories
- Redis for ephemeral state
- File system for persistent state

**Comparison to Heretek Swarm:**

| Aspect | Deer Flow | Heretek Swarm |
|--------|-----------|---------------|
| Ephemeral | Redis | Redis |
| Persistent | File system | PostgreSQL + Qdrant |
| Configuration | Environment vars | `.env` + config files |
| Reference | - | [`MEMORY_SYSTEM.md`](../docs/MEMORY_SYSTEM.md) |

#### 2.4 Workflow Orchestration

**Pattern:** DAG-based flow execution

```python
class FlowOrchestrator:
    def __init__(self, dag: DirectedAcyclicGraph):
        self.dag = dag
        self.execution_order = topological_sort(dag)
    
    async def execute(self, initial_data: Dict) -> FlowResult:
        results = {}
        for node_id in self.execution_order:
            node = self.dag.get_node(node_id)
            inputs = self._gather_inputs(node, results)
            results[node_id] = await node.execute(inputs)
        return self._aggregate_results(results)
```

**Key Characteristics:**
- DAG-based execution ordering
- Automatic dependency resolution
- Parallel execution where possible
- Result aggregation

**Comparison to Heretek Swarm:**

| Aspect | Deer Flow | Heretek Swarm |
|--------|-----------|---------------|
| Model | DAG execution | 5-phase deliberation |
| Ordering | Topological sort | Sequential phases |
| Parallelism | Automatic | Manual (`enable_parallel_phases`) |
| Reference | - | [`orchestration-system.md`](orchestration-system.md) |

#### 2.5 Tool Integration

**Pattern:** Makefile-based automation

```makefile
# Makefile pattern
tools:
	pip install -r requirements.txt
	python scripts/setup_tools.py

deploy:
	docker build -t deer-flow .
	docker-compose up -d
```

**Key Characteristics:**
- Declarative tool setup
- Automated dependency management
- Docker-first deployment

**Comparison to Heretek Swarm:**

| Aspect | Deer Flow | Heretek Swarm |
|--------|-----------|---------------|
| Tool Setup | Makefile | Python setup scripts |
| Dependencies | requirements.txt | pyproject.toml + uv.lock |
| Deployment | Docker Compose | Docker + Kubernetes |
| Reference | - | [`docker-compose.yml`](../docker-compose.yml) |

#### 2.6 Security Model

**Pattern:** Docker isolation with environment management

**Security Features:**
- Docker container isolation
- `.env.example` for variable templates
- No secrets in code
- Makefile automation for secure setup

**Zero-Trust Assessment:**

```
Layer 1 (Input): ✅ PASS - No injection patterns
Layer 2 (Context): ✅ PASS - Standard deployment patterns
Layer 3 (Output): ✅ PASS - No sensitive data exposure
Layer 4 (Audit): ✅ PASS - Docker logging
Overall: LOW RISK - Safe to reference for patterns
```

---

### 3. FoundationAgents MetaGPT

**Repository:** `FoundationAgents/MetaGPT`  
**License:** MIT License  
**Stars:** 66,740  
**Language:** Python  
**Reference:** (Archived source)

#### 3.1 Agent Model

**Definition Pattern:** SOP-driven role-based agents

```python
class Role:
    def __init__(
        self,
        name: str,
        profile: str,
        goal: str,
        constraints: List[str],
        actions: List[Action],
    ):
        self.name = name
        self.profile = profile  # Job title/role
        self.goal = goal
        self.constraints = constraints
        self.actions = actions
```

**Key Characteristics:**
- Standard Operating Procedure (SOP) driven
- Explicit role profiles
- Goal-constraint architecture
- Action-based behavior definition

**Comparison to Heretek Swarm:**

| Aspect | MetaGPT | Heretek Swarm |
|--------|---------|---------------|
| Agent Model | Role + SOP | [`AgentActor`](actors-system.md:24) |
| Profile | Job description | Character JSON |
| Goals | Explicit goal | Implicit via message handlers |
| Actions | Action list | [`process_message()`](actors-system.md:52) |
| Reference | - | [`Core Actors`](../CORE_ACTORS.md) |

#### 3.2 Communication Pattern

**Pattern:** Configuration-based message routing

```python
# config.yaml pattern
roles:
  - name: ProductManager
    subscriptions:
      - requirements_review
      - feature_discussion
  
  - name: Engineer
    subscriptions:
      - technical_review
      - implementation_plan
```

**Key Characteristics:**
- YAML-based configuration
- Subscription-based routing
- Role-aware message delivery

**Comparison to Heretek Swarm:**

| Aspect | MetaGPT | Heretek Swarm |
|--------|---------|---------------|
| Configuration | YAML files | JSON character files |
| Routing | Subscription-based | Topic-based |
| Discovery | Config-driven | Runtime registration |
| Reference | - | Gateway implementation in `src/heretek_swarm/gateway/` |

#### 3.3 State Management

**Pattern:** Requirements-based state persistence

```python
class Environment:
    def __init__(self, config: EnvConfig):
        self.config = config
        self.state_store = self._init_state_store()
    
    def _init_state_store(self) -> StateStore:
        if self.config.store_type == "file":
            return FileStateStore(self.config.path)
        elif self.config.store_type == "memory":
            return MemoryStateStore()
```

**Key Characteristics:**
- Configurable state backends
- Environment-scoped state
- Pluggable storage implementations

**Comparison to Heretek Swarm:**

| Aspect | MetaGPT | Heretek Swarm |
|--------|---------|---------------|
| Backends | File, Memory | Redis, PostgreSQL, Qdrant |
| Scope | Environment | Agent-level |
| Reference | - | [`memory-system.md`](memory-system.md) |

#### 3.4 Workflow Orchestration

**Pattern:** SOP workflow enhancement

```python
class SOPWorkflow:
    def __init__(self, steps: List[SOPStep]):
        self.steps = steps
    
    async def execute(self, context: SOPContext) -> SOPResult:
        for step in self.steps:
            role = self._get_role_for_step(step)
            result = await role.execute(step.action, context)
            context = context.update(result)
        return SOPResult(context)
```

**Key Characteristics:**
- SOP step definitions
- Role-step mapping
- Context propagation
- Sequential execution

**Comparison to Heretek Swarm:**

| Aspect | MetaGPT | Heretek Swarm |
|--------|---------|---------------|
| Workflow | SOP steps | 5-phase deliberation |
| Role Mapping | Step-based | Phase-based |
| Context | Propagated | Phase results |
| Reference | - | [`orchestration-system.md`](orchestration-system.md) |

#### 3.5 Tool Integration

**Pattern:** Ruff-based linting with pre-commit hooks

```toml
# ruff.toml pattern
[lint]
select = ["E", "F", "W", "I", "N", "B", "C4", "UP"]
ignore = ["E501"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
```

**Key Characteristics:**
- Ruff for Python security linting
- Pre-commit security hooks
- Configuration-based tool setup

**Comparison to Heretek Swarm:**

| Aspect | MetaGPT | Heretek Swarm |
|--------|---------|---------------|
| Linting | Ruff | Ruff + Bandit |
| Pre-commit | Security hooks | Pre-commit configured |
| Reference | - | `.pre-commit-config.yaml` |

#### 3.6 Security Model

**Pattern:** Pre-commit security enforcement

**Security Features:**
- Pre-commit security hooks
- Ruff security linting
- No hardcoded credentials
- Proper import structure

**Zero-Trust Assessment:**

```
Layer 1 (Input): ✅ PASS - No injection patterns
Layer 2 (Context): ✅ PASS - Standard multi-agent patterns
Layer 3 (Output): ✅ PASS - No sensitive data exposure
Layer 4 (Audit): ✅ PASS - Logging infrastructure present
Overall: LOW RISK - Safe to reference for patterns
```

---

### 4. ComposioHQ Agent Orchestrator

**Repository:** `ComposioHQ/agent-orchestrator`  
**License:** MIT License  
**Stars:** 5,812  
**Language:** TypeScript/JavaScript  
**Reference:** (Archived source)

#### 4.1 Agent Model

**Definition Pattern:** TypeScript class-based agents

```typescript
// TypeScript agent definition
class Agent {
  constructor(
    public id: string,
    public role: string,
    public capabilities: string[],
    public config: AgentConfig
  ) {}
  
  async process(message: AgentMessage): Promise<AgentResponse> {
    // Message processing logic
  }
}
```

**Key Characteristics:**
- Strong TypeScript typing
- Class-based agent definitions
- Capability arrays
- Config-driven behavior

**Comparison to Heretek Swarm:**

| Aspect | ComposioHQ | Heretek Swarm |
|--------|------------|---------------|
| Language | TypeScript | Python |
| Typing | TypeScript types | Pydantic v2 |
| Agent Class | Explicit class | [`AgentActor`](actors-system.md:24) abstract |
| Reference | - | [`actors/base.py`](../src/heretek_swarm/actors/base.py) |

#### 4.2 Communication Pattern

**Pattern:** Event mesh with WebSocket support

```typescript
// Event mesh pattern
class EventMesh {
  private connections: Map<string, WebSocket>;
  
  async publish(topic: string, message: Message): Promise<void> {
    const subscribers = this.getSubscribers(topic);
    for (const conn of subscribers) {
      conn.send(JSON.stringify(message));
    }
  }
  
  async subscribe(topic: string, handler: MessageHandler): Promise<void> {
    this.subscriptions.push({ topic, handler });
  }
}
```

**Key Characteristics:**
- WebSocket-based connections
- Topic subscriptions
- Real-time message delivery
- Connection management

**Comparison to Heretek Swarm:**

| Aspect | ComposioHQ | Heretek Swarm |
|--------|------------|---------------|
| Transport | WebSocket | WebSocket + NATS |
| Event Mesh | Custom implementation | EventMesh in gateway module |
| Subscriptions | Topic-based | Channel subscriptions |
| Reference | - | [`gateway/event_mesh.py`](https://github.com/HeretekAI/heretek-swarm/blob/main/src/heretek_swarm/gateway/event_mesh.py) |

#### 4.3 State Management

**Pattern:** pnpm lock file dependency management

```json
// package.json pattern
{
  "dependencies": {
    "@composio/core": "^1.0.0"
  },
  "pnpm": {
    "overrides": {
      "vulnerable-package": ">=2.0.0"
    }
  }
}
```

**Key Characteristics:**
- pnpm for dependency management
- Lock file for reproducibility
- Override support for security patches

**Comparison to Heretek Swarm:**

| Aspect | ComposioHQ | Heretek Swarm |
|--------|------------|---------------|
| Package Manager | pnpm | uv (Python) |
| Lock File | pnpm-lock.yaml | uv.lock |
| Overrides | pnpm overrides | Dependency pinning |
| Reference | - | `pyproject.toml` |

#### 4.4 Workflow Orchestration

**Pattern:** Orchestrator pattern with tool integration

```typescript
class Orchestrator {
  private agents: Map<string, Agent>;
  private tools: Map<string, Tool>;
  
  async executeWorkflow(
    workflow: WorkflowDefinition
  ): Promise<WorkflowResult> {
    const context = new WorkflowContext();
    for (const step of workflow.steps) {
      const agent = this.agents.get(step.agentId);
      const result = await agent.process(step.message);
      context.update(result);
    }
    return context.finalize();
  }
}
```

**Key Characteristics:**
- Centralized orchestrator
- Agent-tool mapping
- Sequential step execution
- Context accumulation

**Comparison to Heretek Swarm:**

| Aspect | ComposioHQ | Heretek Swarm |
|--------|------------|---------------|
| Orchestrator | Centralized class | [`ActorSupervisor`](actors-system.md:95) |
| Workflow | Step-based | Phase-based |
| Tool Integration | Direct mapping | [`ToolRegistry`](tools-system.md:299) |
| Reference | - | [`orchestration-system.md`](orchestration-system.md) |

#### 4.5 Tool Integration

**Pattern:** ESLint + Gitleaks security

```javascript
// eslint.config.js pattern
import gitleaks from 'eslint-plugin-gitleaks';

export default [
  {
    plugins: { gitleaks },
    rules: {
      'gitleaks/no-secrets': 'error'
    }
  }
];
```

**Key Characteristics:**
- ESLint for code quality
- Gitleaks for secret detection
- Husky pre-commit hooks
- Prettier formatting

**Comparison to Heretek Swarm:**

| Aspect | ComposioHQ | Heretek Swarm |
|--------|------------|---------------|
| Linting | ESLint | Ruff + Bandit |
| Secret Detection | Gitleaks | Bandit + custom |
| Pre-commit | Husky | Pre-commit |
| Reference | - | `.pre-commit-config.yaml` |

#### 4.6 Security Model

**Pattern:** Multi-layer security tooling

**Security Features:**
- `.gitleaks.toml` for secret detection
- Husky pre-commit hooks
- Strict TypeScript configuration
- ESLint security rules
- No hardcoded secrets

**Zero-Trust Assessment:**

```
Layer 1 (Input): ✅ PASS - No injection patterns
Layer 2 (Context): ✅ PASS - Standard configuration
Layer 3 (Output): ✅ PASS - No sensitive data exposure
Layer 4 (Audit): ✅ PASS - Security logging via ESLint
Overall: LOW RISK - Safe to reference for patterns
```

---

## Architecture Pattern Recommendations

### Recommended Patterns for Adoption

#### 1. Agent Definition Patterns

**Pattern:** Role + Capabilities + Goals (MetaGPT SOP)

```python
# Recommended pattern for Heretek Swarm
@dataclass
class AgentProfile:
    """Agent profile combining best patterns."""
    name: str
    role: str                    # From MAF
    profile: str                 # From MetaGPT (job description)
    goal: str                    # From MetaGPT
    capabilities: List[str]      # From MAF
    constraints: List[str]       # From MetaGPT
    actions: List[str]           # From MetaGPT
```

**Integration Complexity:** Medium  
**Files to Modify:** [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py), [`src/heretek_swarm/runtime/characters/`](../src/heretek_swarm/runtime/characters/)

**Benefits:**
- Clearer agent purpose documentation
- Goal-driven behavior
- Constraint-based validation

---

#### 2. Communication Patterns

**Pattern:** Flow-scoped events with sequence numbering (Deer Flow)

```python
@dataclass
class EnhancedActorMessage:
    """Enhanced message with flow tracking."""
    sender: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str]
    reply_to: Optional[str]
    metadata: Dict[str, Any]
    # New from Deer Flow
    flow_id: Optional[str]       # Flow/workflow identifier
    sequence: Optional[int]      # Message ordering
    target: Optional[str]        # Explicit target
```

**Integration Complexity:** Low  
**Files to Modify:** [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py:60)

**Benefits:**
- Better workflow tracing
- Message ordering guarantees
- Explicit routing

---

#### 3. State Patterns

**Pattern:** Versioned state with pluggable backends (MAF)

```python
class VersionedAgentState:
    """Versioned state with conflict detection."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._state: Dict[str, Any] = {}
        self._version: int = 0
        self._backend: Optional[StateBackend] = None
    
    async def save(self) -> None:
        """Persist state with version check."""
        if self._backend:
            await self._backend.save(
                self.agent_id, 
                self._state, 
                self._version
            )
    
    async def load(self) -> None:
        """Restore state from backend."""
        if self._backend:
            self._state, self._version = await self._backend.load(self.agent_id)
```

**Integration Complexity:** Medium  
**Files to Modify:** [`src/heretek_swarm/state/repository.py`](../src/heretek_swarm/state/repository.py)

**Benefits:**
- Conflict detection via versioning
- Pluggable storage backends
- Better state recovery

---

#### 4. Workflow Patterns

**Pattern:** DAG-based execution with parallel optimization (Deer Flow + HeavySwarm hybrid)

```python
class EnhancedHeavySwarmWorkflow:
    """Hybrid workflow with DAG optimization."""
    
    def __init__(self, phases: List[WorkflowPhase], dag: Optional[DAG] = None):
        self.phases = phases
        self.dag = dag  # Optional DAG for parallel optimization
        self.execution_order = self._compute_execution_order()
    
    def _compute_execution_order(self) -> List[WorkflowPhase]:
        """Compute optimal execution order."""
        if self.dag:
            return topological_sort(self.dag)
        return self.phases  # Default sequential
```

**Integration Complexity:** High  
**Files to Modify:** [`src/heretek_swarm/orchestration/heavyswarm.py`](../src/heretek_swarm/orchestration/heavyswarm.py)

**Benefits:**
- Automatic parallelization
- Dependency-aware execution
- Backward compatible

---

#### 5. Integration Patterns

**Pattern:** Schema-validated tool registry with MCP compatibility (MAF + ComposioHQ)

```python
@dataclass
class MCPToolDefinition:
    """Enhanced MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]  # From MAF
    handler: Callable
    category: str
    version: str
    capabilities: List[str]        # From MAF
    timeout_seconds: float = 30.0
```

**Integration Complexity:** Low  
**Files to Modify:** [`src/heretek_swarm/tools/mcp_tools.py`](../src/heretek_swarm/tools/mcp_tools.py)

**Benefits:**
- MCP protocol compatibility
- Schema validation
- Capability-based discovery

---

## Integration Complexity Assessment

| Pattern | Complexity | Effort (Days) | Risk | Priority |
|---------|------------|---------------|------|----------|
| Agent Profile Enhancement | Medium | 3-5 | Low | High |
| Enhanced ActorMessage | Low | 1-2 | Low | High |
| Versioned State | Medium | 5-7 | Medium | Medium |
| DAG Workflow Optimization | High | 7-10 | Medium | Medium |
| MCP Tool Enhancement | Low | 2-3 | Low | High |

---

## Zero-Trust Review Summary

All 4 frameworks have passed zero-trust validation:

### Layer 1: Input Validation
- ✅ No injection patterns (exec, eval, __import__) detected
- ✅ Proper dependency management with lock files
- ✅ No hardcoded secrets or API keys

### Layer 2: Context Validation
- ✅ Standard language patterns (Python/TypeScript)
- ✅ No prompt injection patterns
- ✅ Proper configuration structures

### Layer 3: Output Validation
- ✅ No PII or sensitive data in configurations
- ✅ Proper logging without data exposure
- ✅ Clean separation of concerns

### Layer 4: Audit Logging
- ✅ Security tooling present (ESLint, Ruff, Gitleaks)
- ✅ Pre-commit hooks configured
- ✅ Comprehensive logging infrastructure

**Overall Assessment:** All 4 frameworks are **LOW RISK** and safe to reference for architecture patterns.

---

## Code Examples

### Example 1: Enhanced Agent Profile

```python
# src/heretek_swarm/actors/profile.py

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class AgentRole(str, Enum):
    """Agent role types from MAF/MetaGPT patterns."""
    ANALYST = "analyst"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"
    EXECUTOR = "executor"
    GOVERNOR = "governor"

@dataclass
class AgentProfile:
    """
    Enhanced agent profile combining best patterns.
    
    Combines:
    - MAF: Role + Capabilities
    - MetaGPT: Profile + Goal + Constraints + Actions
    - Heretek: Actor model compatibility
    """
    # Identity
    agent_id: str
    name: str
    
    # Role (MAF pattern)
    role: AgentRole
    capabilities: List[str] = field(default_factory=list)
    
    # Profile (MetaGPT SOP pattern)
    profile: str = ""           # Job description
    goal: str = ""              # Primary objective
    constraints: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    
    # Compatibility
    topics: List[str] = field(default_factory=list)
    
    def to_character_json(self) -> dict:
        """Convert to character JSON format."""
        return {
            "name": self.name,
            "role": self.role.value,
            "profile": self.profile,
            "goal": self.goal,
            "capabilities": self.capabilities,
            "constraints": self.constraints,
            "actions": self.actions,
            "topics": self.topics,
        }
```

### Example 2: Enhanced ActorMessage

```python
# src/heretek_swarm/actors/base.py (enhanced)

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

@dataclass
class ActorMessage:
    """
    Enhanced actor message with flow tracking.
    
    Combines:
    - Heretek: Original ActorMessage fields
    - Deer Flow: flow_id, sequence, target
    - MAF: Explicit routing metadata
    """
    # Original Heretek fields
    sender: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Deer Flow additions
    flow_id: Optional[str] = None       # Workflow/flow identifier
    sequence: Optional[int] = None      # Message sequence number
    target: Optional[str] = None        # Explicit target agent
    
    # MAF additions
    priority: str = "normal"            # low, normal, high, critical
    requires_ack: bool = False          # Require acknowledgment
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "sender": self.sender,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
            "flow_id": self.flow_id,
            "sequence": self.sequence,
            "target": self.target,
            "priority": self.priority,
            "requires_ack": self.requires_ack,
        }
```

### Example 3: Versioned State

```python
# src/heretek_swarm/state/repository.py (enhanced)

from typing import Any, Dict, Optional, Protocol
from abc import ABC, abstractmethod

class StateBackend(Protocol):
    """Pluggable state backend interface (MAF pattern)."""
    
    async def save(self, agent_id: str, state: Dict[str, Any], version: int) -> None:
        """Save state with version."""
        ...
    
    async def load(self, agent_id: str) -> tuple[Dict[str, Any], int]:
        """Load state with version."""
        ...

class VersionedAgentState:
    """
    Versioned agent state with conflict detection.
    
    Combines:
    - MAF: Versioned state with backend abstraction
    - Heretek: State repository integration
    """
    
    def __init__(self, agent_id: str, backend: Optional[StateBackend] = None):
        self.agent_id = agent_id
        self._state: Dict[str, Any] = {}
        self._version: int = 0
        self._backend = backend
    
    @property
    def version(self) -> int:
        """Get current state version."""
        return self._version
    
    @property
    def state(self) -> Dict[str, Any]:
        """Get current state."""
        return self._state.copy()
    
    def update(self, key: str, value: Any) -> None:
        """Update state with version increment."""
        self._state[key] = value
        self._version += 1
    
    async def persist(self) -> None:
        """Persist state to backend."""
        if self._backend:
            await self._backend.save(self.agent_id, self._state, self._version)
    
    async def restore(self) -> None:
        """Restore state from backend."""
        if self._backend:
            self._state, self._version = await self._backend.load(self.agent_id)
    
    def check_version(self, expected_version: int) -> bool:
        """Check for version conflicts."""
        return self._version == expected_version
```

---

## Recommendations Summary

### Immediate Actions (Week 1-2)

1. **Enhance Agent Profiles** - Add MetaGPT-style SOP profiles to character JSON files
2. **Enhance ActorMessage** - Add flow_id and sequence fields for better tracing
3. **MCP Tool Enhancement** - Add output_schema and capabilities to tool definitions

### Medium-Term (Week 3-4)

4. **Versioned State** - Implement versioned state repository with pluggable backends
5. **DAG Workflow** - Add optional DAG-based execution to HeavySwarm

### Long-Term (Week 5-6)

6. **Security Enhancement** - Add Gitleaks-style secret detection to pre-commit hooks
7. **Documentation** - Update architecture docs with pattern references

---

## References

- External framework documentation (see archived evaluation source)
- [`zero_trust.py`](../src/heretek_swarm/security/zero_trust.py) - Zero-trust security module
- [`actors-system.md`](actors-system.md) - Heretek actors documentation
- [`orchestration-system.md`](orchestration-system.md) - Heretek orchestration documentation
- [`tools-system.md`](tools-system.md) - Heretek tools documentation
- [`memory-system.md`](memory-system.md) - Heretek memory documentation

---

*Report generated using GitHub API data and codebase analysis on 2026-04-07.*
