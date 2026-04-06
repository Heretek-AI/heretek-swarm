# Heretek Swarm API Reference

## Complete Codebase Documentation

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)  
**Health Score:** 100/100  
**Agents:** 23/23 Implemented

---

## Table of Contents

1. [Core Actors System](#core-actors-system)
2. [Agent Reference](#agent-reference)
3. [Gateway & Communication](#gateway--communication)
4. [Memory System](#memory-system)
5. [Consciousness Plugins](#consciousness-plugins)
6. [API Endpoints](#api-endpoints)
7. [Deployment Guide](#deployment-guide)

---

## Core Actors System

### AgentActor Base Class

**File:** [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py)

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

### ActorMessage

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

### ActorFactory

**File:** [`src/heretek_swarm/actors/factory.py`](../src/heretek_swarm/actors/factory.py)

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

### ActorSupervisor

**File:** [`src/heretek_swarm/actors/supervisor.py`](../src/heretek_swarm/actors/supervisor.py)

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

---

## Agent Reference

### Tier 1: Core Triad

#### StewardAgent
**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Governance and orchestration agent that coordinates deliberations.

```python
class StewardAgent(AgentActor):
    """Orchestrates deliberation process between Alpha, Beta, Charlie."""
    
    async def _handle_initiate_deliberation(self, message: ActorMessage) -> None:
        """Start deliberation process."""
        
    async def _handle_collect_decision(self, message: ActorMessage) -> None:
        """Collect final decision from triad."""
```

#### AlphaAgent
**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Deep analysis and proposal generation.

```python
class AlphaAgent(AgentActor):
    """Generates detailed analysis and initial proposals."""
    
    async def _handle_analyze_proposal(self, message: ActorMessage) -> None:
        """Analyze proposal and generate recommendations."""
```

#### BetaAgent
**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Validation and verification of proposals.

```python
class BetaAgent(AgentActor):
    """Validates proposals against constraints and requirements."""
    
    async def _handle_validate_proposal(self, message: ActorMessage) -> None:
        """Validate proposal and identify issues."""
```

#### CharlieAgent
**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Challenge agent that stress-tests proposals.

```python
class CharlieAgent(AgentActor):
    """Challenges proposals to identify weaknesses."""
    
    async def _handle_challenge_proposal(self, message: ActorMessage) -> None:
        """Challenge proposal with counter-arguments."""
```

### Tier 2: Support Agents

#### HistorianAgent
**File:** [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

Memory and knowledge management with dual-tier storage.

```python
class HistorianAgent(AgentActor):
    """Manages episodic and semantic memory storage."""
    
    async def _handle_store_memory(self, message: ActorMessage) -> None:
        """Store memory with caching."""
        
    async def _handle_search_memory(self, message: ActorMessage) -> None:
        """Search memory with filters."""
        
    async def _handle_get_lineage(self, message: ActorMessage) -> None:
        """Get decision lineage."""
```

#### MetisAgent
**File:** [`src/heretek_swarm/actors/metis.py`](../src/heretek_swarm/actors/metis.py)

Strategic planning and resource allocation.

```python
class MetisAgent(AgentActor):
    """Generates strategic plans and allocates resources."""
    
    async def _handle_generate_plan(self, message: ActorMessage) -> None:
        """Generate strategic plan with phases."""
        
    async def _handle_allocate_resources(self, message: ActorMessage) -> None:
        """Allocate resources based on priorities."""
```

#### EmpathAgent
**File:** [`src/heretek_swarm/actors/empath.py`](../src/heretek_swarm/actors/empath.py)

Emotional intelligence and conflict mediation.

```python
class EmpathAgent(AgentActor):
    """Monitors emotional state and mediates conflicts."""
    
    async def _handle_analyze_sentiment(self, message: ActorMessage) -> None:
        """Analyze sentiment of content."""
        
    async def _handle_mediate_conflict(self, message: ActorMessage) -> None:
        """Mediate conflict between agents."""
```

#### PerceiverAgent
**File:** [`src/heretek_swarm/actors/perceiver.py`](../src/heretek_swarm/actors/perceiver.py)

Multi-modal sensory input processing.

```python
class PerceiverAgent(AgentActor):
    """Processes multi-modal sensory input."""
    
    async def _handle_process_input(self, message: ActorMessage) -> None:
        """Process multi-modal input (text, image, audio)."""
        
    async def _handle_extract_features(self, message: ActorMessage) -> None:
        """Extract features from input."""
```

#### EchoAgent
**File:** [`src/heretek_swarm/actors/echo.py`](../src/heretek_swarm/actors/echo.py)

Communication and protocol translation.

```python
class EchoAgent(AgentActor):
    """Handles multi-channel communication and protocol translation."""
    
    async def _handle_format_message(self, message: ActorMessage) -> None:
        """Format message for specific channel."""
        
    async def _handle_broadcast(self, message: ActorMessage) -> None:
        """Broadcast to multiple channels."""
```

### Tier 3: Exploration Agents

#### ExplorerAgent
**File:** [`src/heretek_swarm/actors/explorer.py`](../src/heretek_swarm/actors/explorer.py)

Intelligence gathering and opportunity discovery.

```python
class ExplorerAgent(AgentActor):
    """Monitors sources for opportunities and anomalies."""
    
    async def _handle_start_monitoring(self, message: ActorMessage) -> None:
        """Begin monitoring a source."""
        
    async def _handle_generate_report(self, message: ActorMessage) -> None:
        """Generate intelligence report."""
```

#### ExaminerAgent
**File:** [`src/heretek_swarm/actors/examiner.py`](../src/heretek_swarm/actors/examiner.py)

Quality assurance and testing.

```python
class ExaminerAgent(AgentActor):
    """Performs QA testing and code analysis."""
    
    async def _handle_generate_test_plan(self, message: ActorMessage) -> None:
        """Generate test plan for component."""
        
    async def _handle_analyze_quality(self, message: ActorMessage) -> None:
        """Analyze code quality metrics."""
```

#### DreamerAgent
**File:** [`src/heretek_swarm/actors/dreamer.py`](../src/heretek_swarm/actors/dreamer.py)

Creative solution generation.

```python
class DreamerAgent(AgentActor):
    """Generates creative solutions and novel ideas."""
    
    async def _handle_generate_ideas(self, message: ActorMessage) -> None:
        """Generate creative ideas using techniques."""
        
    async def _handle_explore_alternatives(self, message: ActorMessage) -> None:
        """Explore alternative solutions."""
```

#### CoderAgent
**File:** [`src/heretek_swarm/actors/coder.py`](../src/heretek_swarm/actors/coder.py)

Code generation and implementation.

```python
class CoderAgent(AgentActor):
    """Generates code and performs code review."""
    
    async def _handle_generate_code(self, message: ActorMessage) -> None:
        """Generate code in specified language."""
        
    async def _handle_review_code(self, message: ActorMessage) -> None:
        """Review code for issues."""
        
    async def _handle_debug_code(self, message: ActorMessage) -> None:
        """Debug and fix code issues."""
```

### Tier 4: Safety & Security

#### SentinelAgent
**File:** [`src/heretek_swarm/actors/sentinel.py`](../src/heretek_swarm/actors/sentinel.py)

Safety guardian for input/output validation.

```python
class SentinelAgent(AgentActor):
    """Validates inputs and outputs for safety."""
    
    async def _handle_validate_input(self, message: ActorMessage) -> None:
        """Validate input for safety concerns."""
        
    async def _handle_safety_check(self, message: ActorMessage) -> None:
        """Perform comprehensive safety check."""
```

#### SentinelPrimeAgent
**File:** [`src/heretek_swarm/actors/sentinel_prime.py`](../src/heretek_swarm/actors/sentinel_prime.py)

Security commander for threat response.

```python
class SentinelPrimeAgent(AgentActor):
    """Commands security response to threats."""
    
    async def _handle_detect_threat(self, message: ActorMessage) -> None:
        """Detect and classify security threats."""
        
    async def _handle_respond_threat(self, message: ActorMessage) -> None:
        """Execute threat response protocol."""
```

#### ArbiterAgent
**File:** [`src/heretek_swarm/actors/arbiter.py`](../src/heretek_swarm/actors/arbiter.py)

Conflict resolution between agents.

```python
class ArbiterAgent(AgentActor):
    """Resolves conflicts between agents."""
    
    async def _handle_resolve_conflict(self, message: ActorMessage) -> None:
        """Mediate and resolve agent conflict."""
        
    async def _handle_arbitrate_decision(self, message: ActorMessage) -> None:
        """Arbitrate disputed decisions."""
```

### Tier 5: Coordination Agents

#### CoordinatorAgent
**File:** [`src/heretek_swarm/actors/coordinator.py`](../src/heretek_swarm/actors/coordinator.py)

Multi-agent task synchronization.

```python
class CoordinatorAgent(AgentActor):
    """Coordinates multi-agent workflows."""
    
    async def _handle_start_workflow(self, message: ActorMessage) -> None:
        """Start coordinated workflow."""
        
    async def _handle_resolve_dependencies(self, message: ActorMessage) -> None:
        """Resolve task dependencies."""
```

#### NexusAgent
**File:** [`src/heretek_swarm/actors/nexus.py`](../src/heretek_swarm/actors/nexus.py)

External API integration.

```python
class NexusAgent(AgentActor):
    """Integrates with external APIs and services."""
    
    async def _handle_call_api(self, message: ActorMessage) -> None:
        """Call external API with authentication."""
        
    async def _handle_manage_webhook(self, message: ActorMessage) -> None:
        """Manage webhook subscriptions."""
```

#### CatalystAgent
**File:** [`src/heretek_swarm/actors/catalyst.py`](../src/heretek_swarm/actors/catalyst.py)

Change management.

```python
class CatalystAgent(AgentActor):
    """Manages change requests and rollbacks."""
    
    async def _handle_propose_change(self, message: ActorMessage) -> None:
        """Propose change with impact analysis."""
        
    async def _handle_execute_rollback(self, message: ActorMessage) -> None:
        """Execute rollback procedure."""
```

#### ChronosAgent
**File:** [`src/heretek_swarm/actors/chronos.py`](../src/heretek_swarm/actors/chronos.py)

Time-based scheduling.

```python
class ChronosAgent(AgentActor):
    """Manages time-based scheduling and deadlines."""
    
    async def _handle_schedule_task(self, message: ActorMessage) -> None:
        """Schedule task with recurrence."""
        
    async def _handle_set_deadline(self, message: ActorMessage) -> None:
        """Set deadline with warnings."""
```

### Tier 6: Enhancement Agents

#### PrismAgent
**File:** [`src/heretek_swarm/actors/prism.py`](../src/heretek_swarm/actors/prism.py)

Multi-perspective analysis.

```python
class PrismAgent(AgentActor):
    """Analyzes issues from multiple perspectives."""
    
    async def _handle_generate_perspectives(self, message: ActorMessage) -> None:
        """Generate multiple perspectives on issue."""
        
    async def _handle_detect_biases(self, message: ActorMessage) -> None:
        """Detect cognitive biases in content."""
```

#### HabitForgeAgent
**File:** [`src/heretek_swarm/actors/habit_forge.py`](../src/heretek_swarm/actors/habit_forge.py)

Behavior optimization.

```python
class HabitForgeAgent(AgentActor):
    """Designs and tracks habit formation."""
    
    async def _handle_create_habit(self, message: ActorMessage) -> None:
        """Create habit with trigger-routine-reward loop."""
        
    async def _handle_analyze_patterns(self, message: ActorMessage) -> None:
        """Analyze behavioral patterns."""
```

#### PerceiverPlusAgent
**File:** [`src/heretek_swarm/actors/perceiver_plus.py`](../src/heretek_swarm/actors/perceiver_plus.py)

Advanced analytics.

```python
class PerceiverPlusAgent(AgentActor):
    """Performs advanced statistical analytics."""
    
    async def _handle_analyze_data(self, message: ActorMessage) -> None:
        """Perform comprehensive data analysis."""
        
    async def _handle_forecast_values(self, message: ActorMessage) -> None:
        """Forecast future values."""
```

---

## Gateway & Communication

### EventMesh

**File:** [`src/heretek_swarm/gateway/event_mesh.py`](../src/heretek_swarm/gateway/event_mesh.py)

WebSocket connection manager for real-time communication.

```python
class EventMesh:
    """Manages WebSocket connections and broadcasting."""
    
    def register(self, client_id: str, websocket: WebSocket) -> None:
        """Register WebSocket client."""
        
    def unregister(self, client_id: str) -> None:
        """Unregister and cleanup client."""
        
    async def broadcast(self, message: bytes) -> None:
        """Broadcast to all connected clients."""
        
    async def send_to(self, client_id: str, message: bytes) -> None:
        """Send to specific client."""
```

### A2A Protocol Server

**File:** [`src/heretek_swarm/gateway/a2a_server.py`](../src/heretek_swarm/gateway/a2a_server.py)

Agent-to-Agent communication server.

```python
class A2AServer:
    """A2A communication server on port 18789."""
    
    async def handle_handshake(self, websocket: WebSocket, agent_id: str) -> None:
        """Process agent handshake."""
        
    async def handle_discovery(self, requesting_agent: str) -> Dict[str, Any]:
        """Return list of connected agents."""
```

### Authentication

**File:** [`src/heretek_swarm/gateway/auth.py`](../src/heretek_swarm/gateway/auth.py)

API key authentication layer.

```python
def generate_api_key() -> str:
    """Generate secure API key."""
    
async def verify_auth(creds: HTTPAuthorizationCredentials) -> str:
    """Verify Bearer token authentication."""
```

### NATS Event Mesh

**File:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](../src/heretek_swarm/gateway/nats_event_mesh.py)

NATS JetStream integration for persistent event streaming.

```python
class NATSEventMesh:
    """NATS JetStream event mesh implementation."""
    
    async def connect(self) -> None:
        """Connect to NATS server."""
        
    async def publish(self, subject: str, data: Dict[str, Any]) -> None:
        """Publish message to subject."""
        
    async def subscribe(self, subject: str, callback: Callable) -> None:
        """Subscribe to subject."""
```

---

## Memory System

### Mem0Backend

**File:** [`src/memory/mem0_backend.py`](../src/memory/mem0_backend.py)

Vector memory backend using mem0.

```python
class Mem0Backend:
    """Vector memory backend with mem0 integration."""
    
    async def initialize(self) -> None:
        """Initialize connections to Qdrant and OpenAI."""
        
    async def store(self, entry: MemoryEntry) -> str:
        """Store memory entry."""
        
    async def search(self, query: MemoryQuery) -> MemoryResult:
        """Search memories by query."""
        
    async def shutdown(self) -> None:
        """Cleanup connections."""
```

### Memory Base

**File:** [`src/memory/base.py`](../src/memory/base.py)

Core memory models and interfaces.

```python
class MemoryEntry(BaseModel):
    """Memory entry model."""
    id: UUID
    agent_id: str
    content: str
    memory_type: MemoryType
    tier: MemoryTier
    metadata: Dict[str, Any]
    
class MemoryQuery(BaseModel):
    """Memory search query."""
    query_text: Optional[str]
    agent_ids: List[str]
    memory_types: List[MemoryType]
    limit: int
```

---

## Consciousness Plugins

### ConsciousnessPlugin

**File:** [`src/heretek_swarm/plugins/consciousness.py`](../src/heretek_swarm/plugins/consciousness.py)

GWT/AST implementation.

```python
class ConsciousnessPlugin:
    """Implements GWT and AST consciousness theories."""
    
    def submit_to_workspace(self, source: str, content: Dict, priority: float) -> str:
        """Submit content to global workspace."""
        
    def update_agent_attention(self, agent_id: str, focus: str, intensity: float) -> Dict:
        """Update agent attention state."""
        
    def calculate_consciousness_metrics(self, agent_id: str) -> ConsciousnessMetrics:
        """Calculate consciousness metrics."""
```

### Enhanced Consciousness Plugin

**File:** [`src/heretek_swarm/plugins/consciousness_enhanced.py`](../src/heretek_swarm/plugins/consciousness_enhanced.py)

IIT and FEP implementation.

```python
class EnhancedConsciousnessPlugin:
    """Enhanced plugin with IIT and FEP."""
    
    class IITCalculator:
        """Calculate Integrated Information (Phi)."""
        def calculate_phi(self, agent_ids: List[str]) -> IITConnectivity:
            """Calculate Phi for agent group."""
    
    class FEPTracker:
        """Track Free Energy Principle metrics."""
        def update_prediction(self, prediction: float, observation: float) -> FEPMetrics:
            """Update prediction and calculate free energy."""
```

---

## API Endpoints

### Main API

**File:** [`src/heretek_swarm/api/main.py`](../src/heretek_swarm/api/main.py)

FastAPI application with all endpoints.

```python
app = FastAPI(title="Heretek Swarm API", version="1.11.0")

# Include routers
app.include_router(workflows.router, prefix="/api/workflows")
app.include_router(consciousness.router, prefix="/api/consciousness")
app.include_router(observability.router, prefix="/api/observability")
app.include_router(plugins.router, prefix="/api/plugins")
app.include_router(evaluation.router, prefix="/api/evaluation")
```

### Workflow Endpoints

**File:** [`src/heretek_swarm/api/workflows.py`](../src/heretek_swarm/api/workflows.py)

```python
@router.post("/execute")
async def execute_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Execute workflow with specified agents."""
    
@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> WorkflowStatus:
    """Get workflow execution status."""
```

### Consciousness Endpoints

**File:** [`src/heretek_swarm/api/consciousness.py`](../src/heretek_swarm/api/consciousness.py)

```python
@router.get("/metrics")
async def get_consciousness_metrics() -> ConsciousnessMetricsResponse:
    """Get global consciousness metrics."""
    
@router.get("/agent/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str) -> AgentMetricsResponse:
    """Get metrics for specific agent."""
    
@router.post("/workspace/submit")
async def submit_to_workspace(request: WorkspaceSubmitRequest) -> str:
    """Submit content to global workspace."""
```

### Observability Endpoints

**File:** [`src/heretek_swarm/api/observability.py`](../src/heretek_swarm/api/observability.py)

```python
@router.get("/traces")
async def get_traces() -> List[Trace]:
    """Get execution traces."""
    
@router.get("/metrics/latency")
async def get_latency_metrics() -> LatencyMetrics:
    """Get latency statistics."""
```

---

## Deployment Guide

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Qdrant 1.7+

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
# Required variables:
# - OPENAI_API_KEY
# - DATABASE_URL
# - REDIS_URL
# - QDRANT_HOST
```

### Docker Deployment

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configurations
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/qdrant-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/dashboard-deployment.yaml

# Apply ingress
kubectl apply -f k8s/ingress.yaml
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run database migrations
python scripts/run_migrations.py

# Start API server
uvicorn heretek_swarm.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=src/heretek_swarm
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Consciousness metrics
curl http://localhost:8000/api/consciousness/metrics

# Agent status
curl http://localhost:8000/api/agents/status
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=src/heretek_swarm --cov-report=html
```

### Test Categories

- `tests/actors/` - Agent unit tests
- `tests/integration/` - Integration tests
- `tests/memory/` - Memory backend tests
- `tests/plugins/` - Plugin tests
- `tests/security/` - Security tests
- `tests/load/` - Load tests

---

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
