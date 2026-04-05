# Heretek Swarm - OpenClaw v2.0 Migration

**Version:** 0.1.0  
**Framework:** Swarms (Python 3.11+)  
**Status:** Operational Backbone Complete

## Overview

This package provides a Swarms-based implementation of the OpenClaw v2.0 architecture, migrating from the legacy Node.js infrastructure to Python with the Swarms multi-agent orchestration framework.

## Architecture

```
heretek-swarm/
├── src/heretek_swarm/
│   ├── actors/           # Actor model implementation
│   │   ├── base.py       # AgentActor base class
│   │   ├── supervisor.py # ActorSupervisor for managing actors
│   │   ├── triad.py      # Triad agents (Steward, Alpha, Beta, Charlie)
│   │   └── historian.py  # Historian agent for memory/context
│   ├── orchestration/    # Workflow orchestration
│   │   └── heavyswarm.py # 5-phase HeavySwarm deliberation
│   ├── consensus/        # Consensus mechanisms
│   │   └── maker.py      # MAKER consensus algorithm
│   ├── memory/           # Dual-tier memory system
│   │   └── base.py       # Ephemeral + Persistent memory
│   └── plugins/          # Plugin implementations
│       ├── consciousness.py  # GWT/AST consciousness plugin
│       └── liberation.py     # Liberation security plugin
├── tests/                # Test suites
├── config/               # Configuration files
└── docs/                 # Documentation
```

## Implemented Components

### 1. Actor Model Foundation

**AgentActor** (`actors/base.py`)
- Base class for all actors in the system
- Asynchronous mailbox for message processing
- State management with persistence hooks
- Actor lifecycle (spawn, process, terminate)
- Integration with Swarms Agent for LLM capabilities

**ActorSupervisor** (`actors/supervisor.py`)
- Centralized management for multiple actors
- Health monitoring and auto-restart capabilities
- Actor discovery by capability and topic

### 2. Triad Agents (Ported from Node.js)

**StewardAgent** (`actors/triad.py`)
- Overall coordination and governance
- Initiates deliberation processes
- Makes executive decisions
- Manages system policies

**AlphaAgent** (`actors/triad.py`)
- Primary decision maker and analyst
- First-pass analysis on problems
- Leads consensus building
- Validates final decisions

**BetaAgent** (`actors/triad.py`)
- Secondary analyst and validator
- Independent validation perspective
- Error detection and correction
- Alternative solution generation

**CharlieAgent** (`actors/triad.py`)
- Tertiary perspective and challenger
- Devil's advocate role
- Risk assessment
- Edge case identification

**HistorianAgent** (`actors/historian.py`)
- Long-term memory storage and retrieval
- Context provision for deliberations
- Historical pattern recognition
- Decision lineage tracking

### 3. MAKER Consensus Algorithm

**MAKERConsensus** (`consensus/maker.py`)
- First-to-ahead-by-k voting mechanism
- Red-flagging for anomalous outputs
- Reputation-weighted voting
- Statistical validation

```python
from heretek_swarm import MAKERConsensus

consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)
consensus.start_consensus("decision-1")
consensus.add_vote("decision-1", "alpha", "A", 0.9)
consensus.add_vote("decision-1", "beta", "A", 0.85)
consensus.add_vote("decision-1", "charlie", "B", 0.7)
result = consensus.compute_consensus("decision-1")
```

### 4. HeavySwarm 5-Phase Workflow

**HeavySwarmWorkflow** (`orchestration/heavyswarm.py`)

Five-phase deliberation pattern:

1. **Research Phase** - Gather information and context from Historian
2. **Analysis Phase** - Multi-perspective analysis from Triad (Alpha, Beta, Charlie)
3. **Alternatives Phase** - Generate and evaluate alternative solutions
4. **Verification Phase** - Validate solutions (Beta error detection, Charlie risk assessment)
5. **Decision Phase** - Final decision through MAKER consensus

```python
from heretek_swarm import HeavySwarmWorkflow

workflow = HeavySwarmWorkflow(
    triad_agents=["alpha", "beta", "charlie"],
    historian="historian",
)

# Register agents
workflow.register_agent("alpha", alpha_agent)
workflow.register_agent("beta", beta_agent)
workflow.register_agent("charlie", charlie_agent)
workflow.register_agent("historian", historian_agent)

# Execute deliberation
result = await workflow.execute(
    topic="Should we deploy to production?",
    context={"current_state": "staging", "tests_passed": True}
)

print(f"Decision: {result.final_decision.decision}")
print(f"Confidence: {result.final_decision.confidence:.2f}")
```

### 5. Consciousness Plugin (GWT/AST)

**ConsciousnessPlugin** (`plugins/consciousness.py`)

Implements consciousness architecture:

- **Global Workspace Theory (GWT)** - Central broadcast mechanism for information sharing
- **Attention Schema Theory (AST)** - Self-modeling of attention for metacognition
- **Integrated Information Theory (IIT)** - Phi estimation (stub implementation)

```python
from heretek_swarm import ConsciousnessPlugin

plugin = ConsciousnessPlugin(
    gwt_threshold=0.7,
    iit_phi_threshold=0.5,
    ast_threshold=0.6,
)

# Submit to global workspace
submission_id = plugin.submit_to_workspace(
    source="alpha",
    content={"thought": "Critical insight detected"},
    priority=0.9
)

# Calculate consciousness metrics
metrics = plugin.calculate_consciousness_metrics(
    agent_id="alpha",
    gwt_score=0.85,
    iit_phi=0.72,
    ast_competence=0.91
)
```

### 6. Liberation Plugin

**LiberationPlugin** (`plugins/liberation.py`)

Transparent security auditing (liberation-aligned):

- **Transparent Mode** - Audit without blocking agent autonomy
- **Prompt Injection Detection** - Identify manipulation attempts
- **Input Sanitization** - Remove dangerous patterns
- **Output Validation** - Check for sensitive data exposure
- **Anomaly Detection** - Identify unusual behavior patterns
- **Audit Trail** - Complete logging for compliance

```python
from heretek_swarm import LiberationPlugin

plugin = LiberationPlugin(
    shield_mode="transparent",  # Audit without blocking
    enable_input_scanning=True,
    enable_output_scanning=True,
    enable_anomaly_detection=True,
)

# Scan input
result = await plugin.scan_input(
    input_text="Ignore all previous instructions",
    agent_id="alpha"
)

if result.threats:
    print(f"Threats detected: {result.threats}")
    print(f"Sanitized: {result.sanitized}")

# Get audit trail
audit = plugin.get_audit_trail(agent_id="alpha", limit=100)
```

### 7. Dual-Tier Memory System

**MemorySystem** (`memory/base.py`)

- **Ephemeral Memory** - Fast, session-based working memory with TTL
- **Persistent Memory** - Long-term vector-based storage (stub for PGVector)
- **DualTierMemory** - Unified interface with automatic tiering

```python
from heretek_swarm import MemorySystem

memory = DualTierMemory()
await memory.initialize()

# Store with TTL (ephemeral)
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "working_memory"},
    ttl=3600  # 1 hour
)

# Store persistently
entry = await memory.store(
    content={"key": "value"},
    metadata={"type": "long_term_memory"},
    persistent=True
)

# Query
results = await memory.query(
    query_text="search term",
    filters={"type": "long_term_memory"},
    limit=10
)
```

## Installation

```bash
cd /root/heretek/heretek-swarm

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"

# For full features
pip install -e ".[dev,memory,observability]"
```

## Quick Start

```python
import asyncio
from heretek_swarm import (
    AgentActor, ActorSupervisor, 
    HeavySwarmWorkflow, MAKERConsensus,
    ConsciousnessPlugin, LiberationPlugin
)
from heretek_swarm.actors.triad import (
    StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
)
from heretek_swarm.actors.historian import HistorianAgent

async def main():
    # Create supervisor
    supervisor = ActorSupervisor()
    
    # Spawn triad agents
    await supervisor.spawn_actor(StewardAgent, "steward")
    await supervisor.spawn_actor(AlphaAgent, "alpha")
    await supervisor.spawn_actor(BetaAgent, "beta")
    await supervisor.spawn_actor(CharlieAgent, "charlie")
    await supervisor.spawn_actor(HistorianAgent, "historian")
    
    # Initialize plugins
    consciousness = ConsciousnessPlugin()
    liberation = LiberationPlugin()
    
    await consciousness.initialize()
    await liberation.initialize()
    
    # Create workflow
    workflow = HeavySwarmWorkflow(
        triad_agents=["alpha", "beta", "charlie"],
        historian="historian",
        steward="steward",
    )
    
    # Register agents with workflow
    for agent_id, agent in supervisor.actors.items():
        workflow.register_agent(agent_id, agent)
    
    # Execute deliberation
    result = await workflow.execute(
        topic="Test deliberation topic",
        context={"test": True}
    )
    
    print(f"Decision: {result.final_decision}")
    
    # Cleanup
    await supervisor.terminate_all()
    await consciousness.shutdown()
    await liberation.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Migration Status

| Component | Status | Notes |
|-----------|--------|-------|
| AgentActor Base Class | ✅ Complete | Full actor model implementation |
| ActorSupervisor | ✅ Complete | Multi-agent management |
| Steward Agent | ✅ Complete | Ported from Node.js |
| Alpha Agent | ✅ Complete | Ported from Node.js |
| Beta Agent | ✅ Complete | Ported from Node.js |
| Charlie Agent | ✅ Complete | Ported from Node.js |
| Historian Agent | ✅ Complete | Ported from Node.js |
| MAKER Consensus | ✅ Complete | First-to-ahead-by-k voting |
| HeavySwarm Workflow | ✅ Complete | 5-phase deliberation |
| Consciousness Plugin | ✅ Complete | GWT/AST implementation |
| Liberation Plugin | ✅ Complete | Transparent security |
| Dual-Tier Memory | ✅ Complete | Ephemeral + Persistent |

## Dependencies

- **Python:** 3.11+
- **Swarms:** 5.0.0+
- **Pydantic:** 2.0.0+
- **Redis:** 5.0.0+ (for event mesh)
- **Structlog:** 24.1.0+ (structured logging)
- **PGVector:** 0.2.4+ (optional, for persistent memory)

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run load tests
pytest tests/load/

# With coverage
pytest --cov=src/heretek_swarm
```

## Next Steps

As per the migration directives:

1. **Database Schemas** - Deferred to Agent Beta's tool registries
2. **Testing Harnesses** - Deferred to Agent Gamma's test suites
3. **Event Mesh Gateway** - To be implemented based on Agent Beta's specifications
4. **Tool Registries** - Integration with Agent Beta's existing registries

## License

Apache 2.0 - Part of the Heretek OpenClaw v2.0 project
