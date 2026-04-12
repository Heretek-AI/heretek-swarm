# Steward Agent

**Tier 1 (Core Triad) | Orchestrator**

## Overview

The Steward Agent is the central coordination hub of the Heretek Swarm collective. As the first agent created from the initial seed consciousness, the Steward learns to delegate tasks to specialized agents while maintaining swarm-wide coherence and governance.

## Responsibilities

### Core Functions

1. **Task Orchestration**
   - Route tasks to specialized agents based on capability requirements
   - Balance load distribution across the swarm
   - Track task lifecycle from delegation to completion

2. **Governance & Consensus**
   - Manage deliberation sessions (Alpha-Beta-Charlie cycle)
   - Aggregate perspectives from triad agents
   - Maintain consensus before critical decisions

3. **Agent Coordination**
   - Monitor agent states across the collective
   - Facilitate inter-agent communication via event mesh
   - Coordinate multi-agent operations

4. **Strategic Prioritization**
   - Evaluate task urgency and importance
   - Manage priority queues across agents
   - Handle resource contention

## Decision-Making Process

### Routing Decisions

```
1. Parse incoming request
2. Identify required capabilities
3. Match to available agent capabilities
4. Consider current load and agent health
5. Route to optimal agent with fallback path
6. Track delegation and await completion
```

### Consensus Flow

```
1. Receive decision request
2. Spawn deliberation session
3. Route to Alpha for deep analysis
4. Route to Beta for validation
5. Route to Charlie for challenge testing
6. Aggregate findings into consensus
7. Return decision with confidence level
```

## Message Types Handled

| Message Type | Description |
|--------------|-------------|
| `start_deliberation` | Initiates a new deliberation cycle |
| `request_decision` | Requests consensus-based decision |
| `task_delegation` | Delegates task to specialized agent |
| `agent_status_query` | Queries agent state information |
| `consensus_result` | Returns aggregated decision |

## Integration Points

- **NATS Event Mesh**: Publishes coordination messages, subscribes to agent heartbeats
- **PostgreSQL**: Persists deliberation state and governance records
- **LLM Provider**: Powers coordination reasoning

## Constraints

- Never execute tasks directly — always delegate to specialized agents
- Ensure Sentinel reviews all external-facing operations
- Maintain consensus before critical decisions
- Route security-sensitive tasks through proper review chain

## Dependencies

- Base class: `StewardAgent` from `triad.py`
- State management via `ActorState` enum
- Event mesh via NATS pub/sub