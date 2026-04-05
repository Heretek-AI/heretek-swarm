# Heretek Swarm Documentation Index

Welcome to the comprehensive documentation for Heretek Swarm - a Python-based multi-agent orchestration framework implementing OpenClaw v2.0 architecture.

## Quick Start

```bash
cd /root/heretek/heretek-swarm

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"

# For full features
pip install -e ".[dev,memory,observability]"
```

## Documentation Structure

### Architecture Documentation

Comprehensive documentation for each major system component:

- **[Actors System](architecture/actors-system.md)** - Actor model implementation, lifecycle management, and Triad agents
- **[Consensus Mechanism](architecture/consensus-mechanism.md)** - MAKER consensus algorithm for decision aggregation
- **[Memory System](architecture/memory-system.md)** - Dual-tier memory architecture with ephemeral and persistent layers
- **[Orchestration System](architecture/orchestration-system.md)** - HeavySwarm 5-phase deliberation workflow
- **[State Management](architecture/state-management.md)** - Unified state management with lineage tracking and snapshots
- **[Tools System](architecture/tools-system.md)** - Tool architecture for extending agent capabilities
- **[Observability](architecture/observability.md)** - Metrics, tracing, and structured logging
- **[Plugins](architecture/plugins.md)** - Consciousness and Liberation plugins

### API Reference

Complete API reference for all components:

- **[API Reference](api-reference.md)** - Comprehensive API documentation with method signatures and examples

### Additional Documentation

- **[Legacy Skills Audit](LEGACY_SKILLS_AUDIT.md)** - Audit report of legacy shell-based skills
- **[Main README](../README.md)** - Project overview and quick start guide

## System Overview

### Core Components

The Heretek Swarm framework consists of several interconnected systems:

1. **Actors System** - Message-driven agent orchestration with actor model pattern
2. **Triad Agents** - Specialized agents (Steward, Alpha, Beta, Charlie, Historian) for deliberation
3. **MAKER Consensus** - First-to-ahead-by-k voting mechanism for decision aggregation
4. **HeavySwarm Workflow** - 5-phase deliberation pattern for complex analysis
5. **Dual-Tier Memory** - Ephemeral and persistent memory with semantic search
6. **State Management** - Unified state with lineage tracking and snapshots
7. **Tools System** - Dynamic tool registry for extending agent capabilities
8. **Observability** - Metrics, tracing, and structured logging
9. **Plugins** - Consciousness (GWT/AST) and Liberation (security) plugins

## Key Features

### Actor Model
- Message passing via immutable messages
- State isolation per actor
- Mailbox-based sequential message processing
- Integration with Swarms Agent for LLM capabilities
- Health monitoring and heartbeat mechanism

### Triad Agents
- **Steward**: Overall coordination and governance
- **Alpha**: Primary decision maker and analyst
- **Beta**: Secondary analyst and validator
- **Charlie**: Tertiary perspective and challenger
- **Historian**: Memory and context provider

### MAKER Consensus
- First-to-ahead-by-k voting mechanism
- Red-flagging for anomalous outputs
- Reputation-weighted voting
- Statistical validation

### HeavySwarm Workflow
- **Phase 1 - Research**: Gather information and context
- **Phase 2 - Analysis**: Multi-perspective analysis from Triad
- **Phase 3 - Alternatives**: Generate and evaluate alternative solutions
- **Phase 4 - Verification**: Validate and verify solutions
- **Phase 5 - Decision**: Final decision through MAKER consensus

### Dual-Tier Memory
- **Ephemeral Layer**: Fast, session-based working memory with TTL
- **Persistent Layer**: Long-term vector-based storage with semantic search
- **Automatic Tiering**: Intelligent routing to appropriate tier
- **Lineage Tracking**: Complete provenance for all memories

### State Management
- **Unified State**: Single source of truth for agent and conversation state
- **Lineage Tracking**: Complete message provenance
- **Snapshots**: Capture and restore system states
- **Rollback**: Revert to previous states if needed
- **Automatic Recovery**: Self-healing from failures

### Tools System
- **Type-Safe**: Pydantic-based input/output validation
- **Dynamic Registry**: Runtime tool discovery and loading
- **Performance Monitoring**: Built-in metrics and tracing
- **Hot Reloading**: Update tools without restart

### Observability
- **Metrics**: Prometheus-compatible metrics collection
- **Tracing**: OpenTelemetry-based distributed tracing
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Dashboards**: Real-time monitoring and alerting

### Plugins

#### Consciousness Plugin
- **Global Workspace Theory (GWT)**: Central broadcast mechanism
- **Attention Schema Theory (AST)**: Self-modeling of attention
- **Integrated Information Theory (IIT)**: Phi estimation
- **Consciousness Metrics**: Measure and track consciousness levels

#### Liberation Plugin
- **Transparent Mode**: Audit without blocking agent autonomy
- **Prompt Injection Detection**: Identify manipulation attempts
- **Input Sanitization**: Remove dangerous patterns
- **Output Validation**: Check for sensitive data exposure
- **Anomaly Detection**: Identify unusual behavior patterns
- **Audit Trail**: Complete logging for compliance

## Migration Status

All major components have been successfully migrated from the legacy Node.js infrastructure to Python with the Swarms framework:

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
| State Management | ✅ Complete | Lineage + Snapshots |
| Tools System | ✅ Complete | Dynamic registry |
| Observability | ✅ Complete | Metrics + Tracing |

## Dependencies

- **Python**: 3.11+
- **Swarms**: 5.0.0+
- **Pydantic**: 2.0.0+
- **Redis**: 5.0.0+ (for event mesh)
- **Structlog**: 24.1.0+ (structured logging)
- **PGVector**: 0.2.4+ (optional, for persistent memory)
- **OpenTelemetry**: 1.0.0+ (for observability)

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

## License

Apache 2.0 - Part of the Heretek OpenClaw v2.0 project

---

**Version**: 0.1.0  
**Framework**: Swarms (Python 3.11+)  
**Status**: Operational Backbone Complete
