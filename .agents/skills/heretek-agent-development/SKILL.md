---
name: heretek-agent-development
description: >-
  Agent development for Heretek Swarm's 23-agent system. Use when creating new
  agent actors, implementing agent behaviors, or working with the actor/mixin
  architecture. Covers agent lifecycle, communication patterns, and consensus
  integration.
---

# Heretek Swarm Agent Development

## Agent Architecture

### Base Classes
- **`AgentActor`** - Base class for all agents (`actors/base/core.py`)
- **`SwarmAgent`** - Langroid adapter (`actors/base/langroid_adapter.py`)
- **Mixins** - Cross-cutting concerns in `actors/mixins/`

### Current Agents (23)
```
actors/
├── arbiter/          # Decision arbitration
├── catalyst/         # Change catalyst
├── chronos/          # Time management
├── coder/            # Code generation
├── coordinator/      # Task coordination
├── dreamer/          # Creative ideation
├── echo/             # Reflection/feedback
├── empath/           # Emotional intelligence
├── examiner/         # Quality examination
├── explorer/         # Exploration/discovery
├── habit_forge/      # Pattern formation
├── historian/        # Memory/history
├── metis/            # Strategic thinking
├── nexus/            # Connection hub
├── perceiver/        # Perception/analysis
├── perceiver_plus/   # Enhanced perception
├── prism/            # Perspective synthesis
├── sentinel/         # Security monitoring
├── sentinel_prime/   # Enhanced security
├── alpha/            # Triad member
├── beta/             # Triad member
├── charlie/          # Triad member
└── steward/          # Consensus facilitator
```

## Creating a New Agent

### Step 1: Directory Structure
```bash
mkdir -p backend/heretek_swarm/actors/my_agent
touch backend/heretek_swarm/actors/my_agent/__init__.py
touch backend/heretek_swarm/actors/my_agent/agent.py
```

### Step 2: Implement Agent
```python
# actors/my_agent/agent.py
from heretek_swarm.actors.base.core import AgentActor
from heretek_swarm.actors.mixins.audit import AuditMixin
from heretek_swarm.actors.mixins.health_reporting import HealthReportingMixin

class MyAgent(AgentActor, AuditMixin, HealthReportingMixin):
    """
    Description of what this agent does.
    
    Responsibilities:
    - Responsibility 1
    - Responsibility 2
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.name = "my_agent"
        
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """Process incoming message from other agents."""
        # Implementation
        pass
        
    async def deliberate(self, context: DeliberationContext) -> Decision:
        """Participate in consensus deliberation."""
        # Implementation
        pass
```

### Step 3: Register Agent
```python
# actors/__init__.py
from .my_agent.agent import MyAgent

__all__ = [
    # ... existing agents
    "MyAgent",
]
```

### Step 4: Add Configuration
```yaml
# config/agents.yaml
agents:
  my_agent:
    enabled: true
    tier: 3  # 1=core, 2=support, 3=auxiliary
    capabilities:
      - my_capability
    dependencies:
      - other_agent
```

### Step 5: Write Tests
```python
# tests/test_my_agent.py
import pytest
from heretek_swarm.actors.my_agent.agent import MyAgent

@pytest.fixture
def my_agent():
    config = AgentConfig(name="my_agent")
    return MyAgent(config)

@pytest.mark.asyncio
async def test_process_message(my_agent):
    message = AgentMessage(content="test")
    response = await my_agent.process_message(message)
    assert response.status == "success"
```

## Agent Communication

### Message Types
```python
class AgentMessage:
    content: str
    sender: str
    recipient: str
    message_type: MessageType
    metadata: dict[str, Any]
    timestamp: datetime
```

### Communication Patterns
1. **Direct messaging** - Agent-to-agent
2. **Event mesh** - Publish/subscribe
3. **Queue** - Fallback when direct fails
4. **Consensus** - Triad deliberation

### Sending Messages
```python
# Direct message
await self.send_message(
    recipient="coordinator",
    content="Task completed",
    message_type=MessageType.STATUS
)

# Broadcast
await self.broadcast(
    content="System alert",
    message_type=MessageType.ALERT
)
```

## Consensus System

### Triad Structure
- **Alpha** - Proposes decisions
- **Beta** - Challenges/probes
- **Charlie** - Validates/finalizes
- **Steward** - Facilitates process

### Deliberation Flow
```python
async def deliberate(self, context: DeliberationContext) -> Decision:
    # 1. Analyze proposal
    analysis = await self.analyze(context.proposal)
    
    # 2. Form position
    position = self.form_position(analysis)
    
    # 3. Cast vote
    vote = Vote(
        agent=self.name,
        position=position,
        rationale=self.explain(position)
    )
    
    return vote
```

## Memory Integration

### Accessing Memory
```python
# Read from memory
reader = CogneeMemoryReader()
memories = await reader.search(
    query="relevant context",
    limit=5,
    agent=self.name
)

# Write to memory
writer = CogneeMemoryWriter()
await writer.add(
    content="observation",
    metadata={
        "agent": self.name,
        "importance": 0.8,
        "tags": ["observation", "learning"]
    }
)
```

### Memory Patterns
- **Episodic** - What happened (events)
- **Semantic** - What it means (knowledge)
- **Procedural** - How to do it (skills)

## Health Reporting

### Implement Health Checks
```python
class MyAgent(AgentActor, HealthReportingMixin):
    async def health_check(self) -> HealthStatus:
        return HealthStatus(
            healthy=True,
            metrics={
                "messages_processed": self.message_count,
                "avg_response_time": self.avg_response_time,
                "error_rate": self.error_rate
            },
            last_check=datetime.now()
        )
```

### Monitoring Integration
- Structured logging with `structlog`
- Metrics export to Prometheus
- Health endpoints at `/health`
- Audit trails for all operations

## Testing Agents

### Unit Tests
```python
@pytest.mark.asyncio
async def test_agent_initialization():
    agent = MyAgent(config)
    assert agent.name == "my_agent"
    assert agent.status == "ready"

@pytest.mark.asyncio
async def test_message_processing():
    agent = MyAgent(config)
    message = AgentMessage(content="test")
    response = await agent.process_message(message)
    assert response.status == "success"
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_agent_communication():
    agent_a = AgentA(config_a)
    agent_b = AgentB(config_b)
    
    # Wire up communication
    await agent_a.connect(agent_b)
    
    # Send message
    await agent_a.send_message("agent_b", "hello")
    
    # Verify response
    assert agent_b.received_messages == ["hello"]
```

### Consensus Tests
```python
@pytest.mark.asyncio
async def test_triad_consensus():
    alpha = AlphaAgent(config)
    beta = BetaAgent(config)
    charlie = CharlieAgent(config)
    
    proposal = Proposal(content="test proposal")
    decision = await triad.deliberate(proposal)
    
    assert decision.approved is True
```

## Common Patterns

### Error Handling
```python
async def process_message(self, message: AgentMessage) -> AgentResponse:
    try:
        result = await self._process(message)
        return AgentResponse(status="success", data=result)
    except AgentError as e:
        self.logger.error("processing_failed", error=str(e))
        return AgentResponse(status="error", error=str(e))
```

### Rate Limiting
```python
from heretek_swarm.security.rate_limiter import RateLimiter

class MyAgent(AgentActor):
    def __init__(self, config):
        super().__init__(config)
        self.rate_limiter = RateLimiter(
            max_requests=100,
            window_seconds=60
        )
    
    async def process_message(self, message):
        if not self.rate_limiter.allow(self.name):
            raise RateLimitExceeded()
        # ...
```

### Audit Trail
```python
from heretek_swarm.actors.mixins.audit import AuditMixin

class MyAgent(AgentActor, AuditMixin):
    async def process_message(self, message):
        # Automatically logged
        await self.audit(
            action="message_processed",
            message_id=message.id,
            result="success"
        )
```

## Gotchas

1. **Class naming**: Ruff ignores `N801` in `actors/` - `AgentActor` style allowed
2. **Mixin order**: Put `AgentActor` first, mixins after
3. **Async everywhere**: All I/O must be async
4. **No state mutation**: Agents should be stateless where possible
5. **Message authentication**: All messages must be authenticated
6. **Fire-and-forget tasks**: Always store references to prevent garbage collection

## Best Practices

1. Keep agents focused on single responsibility
2. Use mixins for cross-cutting concerns
3. Implement health checks for monitoring
4. Add audit trails for all operations
5. Write tests for both success and error paths
6. Document agent capabilities and dependencies
7. Follow the Three-tier fallback for communication