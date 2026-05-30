# Heretek Swarm - Autonomous Workflow Guide

**Version:** 2.0.0
**Date:** 2026-04-06
**Status:** Implementation Complete

---

## Executive Summary

This document provides comprehensive guidance for operating the Heretek Swarm 23-agent AI cluster in autonomous 24/7 mode. The autonomous workflow implementation wires all agents into a cohesive system with:

- **6-Tier Agent Architecture** - 23 agents across governance, support, exploration, safety, coordination, and enhancement tiers
- **Communication Channels** - NATS-based event mesh with formal channel subscriptions
- **MCP Tools Integration** - 12+ standardized tools for memory, communication, consensus, RAG, and external integration
- **MAKER Consensus** - First-to-ahead-by-k voting with red-flagging for collective decisions
- **Health Monitoring** - Continuous health checks with auto-recovery
- **Consciousness Metrics** - IIT Phi, Attention Schema, and Global Workspace Theory implementations

---

## 1. Quick Start

### 1.1 Prerequisites

```bash
# Required services
docker-compose up -d postgres redis qdrant nats

# Install dependencies
pip install -e .
```

### 1.2 Starting Autonomous Mode

```bash
# Start the autonomous swarm
python -m heretek_swarm.runtime.main_loop

# Or with custom config
python -c "
from heretek_swarm.runtime.main_loop import AutonomousSwarm
import asyncio

config = {
    'nats_servers': ['nats://localhost:4222'],
    'persistent': {'connection_string': 'postgresql://user:pass@localhost/heretek_swarm'},
}
swarm = AutonomousSwarm(config)
asyncio.run(swarm.initialize())
asyncio.run(swarm.run())
"
```

### 1.3 Docker Deployment

```bash
# Build autonomous container
docker build -f docker/Dockerfile.autonomous -t heretek-swarm:autonomous .

# Run with docker-compose
docker-compose -f docker-compose.yml -f docker-compose.autonomous.yml up -d
```

---

## 2. Architecture Overview

### 2.1 Agent Tiers

| Tier | Name | Agents | Role |
|------|------|--------|------|
| Tier 1 | Core Triad | Steward, Alpha, Beta, Charlie | Governance & Decision Making |
| Tier 2 | Support | Historian, Metis, Empath, Perceiver, Echo | Memory, Strategy, Communication |
| Tier 3 | Exploration | Explorer, Examiner, Dreamer, Coder | Research, QA, Creativity, Implementation |
| Tier 4 | Safety | Sentinel, Sentinel-Prime, Arbiter | Security & Conflict Resolution |
| Tier 5 | Coordination | Coordinator, Nexus, Catalyst, Chronos | Multi-Agent Coordination |
| Tier 6 | Enhancement | Prism, Habit-Forge, Perceiver+ | Optimization & Advanced Analytics |

### 2.2 Autonomous Loop Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTONOMOUS RUNTIME LOOP                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 0: INGRESS                                                            │
│  Chronos (Scheduled) → Nexus (External) → Echo (Channels) → Perceiver (Sensory)│
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: TRIAGE (Steward)                                                   │
│  Classifies and routes all incoming tasks to appropriate channels           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  TRIAD PATH       │    │  EXPLORATION PATH │    │  SAFETY PATH      │
│  Alpha→Beta→Charlie│   │  Explorer→Examiner│    │  Sentinel→Prime   │
│  + Historian      │    │  + Dreamer/Coder  │    │  + Arbiter        │
└───────────────────┘    └───────────────────┘    └───────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: COORDINATION                                                       │
│  Coordinator → Metis → Catalyst → Empath                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: CONSENSUS (MAKER)                                                  │
│  Collect votes → Apply reputation → Check red-flags → Compute winner        │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: ENHANCEMENT                                                        │
│  Prism (Multi-View) → Habit-Forge (Optimize) → Historian (Persist)          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: OUTPUT                                                             │
│  Echo (Broadcast) → Nexus (External) → Consciousness (Metrics)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Communication Channels

### 3.1 Channel Architecture

Channels are organized by type and purpose. Each channel has a NATS subject mapping.

#### Internal Channels

| Channel | Subject | Subscribers | Message Types |
|---------|---------|-------------|---------------|
| Triad | `swarm.internal.triad` | steward, alpha, beta, charlie | proposal, analysis, validation, challenge, decision |
| Coordination | `swarm.internal.coordination` | coordinator, catalyst, chronos, metis | task_start, task_complete, dependency_ready, blocker |
| Safety | `swarm.internal.safety` | sentinel, sentinel-prime, arbiter, steward | threat_detected, quarantine, all_clear, incident_report |
| Memory | `swarm.internal.memory` | historian, prism, habit-forge | store_request, retrieve_request, learn_pattern, forget |
| Exploration | `swarm.internal.exploration` | explorer, examiner, dreamer, coder | research_task, analysis_result, creative_request, code_review |
| Perception | `swarm.internal.perception` | perceiver, perceiver-plus, empath, echo | input_received, sentiment_analysis, translation_request |

#### System Channels

| Channel | Subject | Subscribers | Message Types |
|---------|---------|-------------|---------------|
| Health | `swarm.system.health` | * (all) | heartbeat, health_status, error_report, restart_request |
| Consciousness | `swarm.system.consciousness` | * (all) | phi_update, attention_state, workspace_broadcast |
| Consensus | `swarm.system.consensus` | steward, alpha, beta, charlie | vote_cast, consensus_reached, red_flag |
| Workflow | `swarm.workflow.events` | * (all) | workflow_start, workflow_phase, workflow_complete |

#### External Channels

| Channel | Subject | Subscribers | Message Types |
|---------|---------|-------------|---------------|
| Discord | `swarm.external.discord` | nexus, echo | discord_message, discord_command, discord_response |
| Slack | `swarm.external.slack` | nexus, echo | slack_message, slack_command, slack_response |
| Telegram | `swarm.external.telegram` | nexus, echo | telegram_message, telegram_command |
| API | `swarm.external.api` | nexus | api_request, api_response, webhook_event |

### 3.2 Message Format

All channel messages follow the `ChannelMessage` structure:

```python
@dataclass
class ChannelMessage:
    subject: str                    # NATS subject
    correlation_id: str             # Unique message ID
    reply_to: Optional[str]         # Response subject
    sender_agent: str               # Sending agent ID
    target_agents: List[str]        # Target agents
    message_type: str               # Type identifier
    content: Dict[str, Any]         # Payload
    metadata: Dict[str, Any]        # Context
    timestamp: str                  # ISO8601
    priority: str                   # low, normal, high, critical
    requires_ack: bool              # Require acknowledgment
    workflow_id: Optional[str]      # Associated workflow
    task_id: Optional[str]          # Associated task
```

---

## 4. MCP Tools

### 4.1 Available Tools

The MCP (Model Context Protocol) tools registry provides 12+ standardized tools:

#### Memory Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `memory_store` | Store information in collective memory | `{content: str, metadata: object, importance: number}` |
| `memory_retrieve` | Retrieve memories by semantic query | `{query: str, limit: int, tier: string}` |

#### Communication Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `agent_message` | Send message to another agent | `{target_agent: str, message_type: str, content: object}` |
| `agent_handoff` | Transfer task context to another agent | `{to_agent: str, context: object, reason: str}` |

#### Consensus Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `consensus_propose` | Submit proposal for collective decision | `{proposal: str, context: object, urgency: string}` |
| `consensus_vote` | Cast vote on active proposal | `{proposal_id: str, vote: str, confidence: number}` |

#### Knowledge Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `rag_query` | Query RAG knowledge base | `{query: str, mode: string, top_k: int}` |
| `rag_ingest` | Ingest document into RAG | `{content: str, source: str, metadata: object}` |

#### Integration Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `external_api_call` | Make authenticated API call | `{connection_id: str, endpoint: str, method: str, payload: object}` |
| `notification_send` | Send notification to channels | `{channel: str, message: str, priority: string}` |

#### Workflow Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `workflow_start` | Start workflow execution | `{workflow_type: str, params: object, topic: str}` |
| `workflow_status` | Get workflow status | `{workflow_id: str}` |

#### System Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `system_health` | Get system health status | `{}` |

### 4.2 Tool Usage Example

```python
from heretek_swarm.tools.mcp_tools import CoreMCPTools

# Initialize tools
mcp_tools = CoreMCPTools(
    memory_system=memory,
    rag_pipeline=rag,
    consensus_engine=consensus,
    event_mesh=event_mesh,
)

# Invoke a tool
result = await mcp_tools.get_registry().invoke(
    name="memory_store",
    arguments={
        "content": "Important information",
        "metadata": {"source": "agent-alpha"},
        "importance": 0.8,
    },
    context={"agent_id": "alpha"},
)

print(result)  # {"success": True, "result": {...}}
```

---

## 4B. Unified Knowledge Access (NEW)

### 4B.1 Overview

The Unified Knowledge Access layer provides combined querying of memory and RAG systems with intelligent reranking using MMR (Maximal Marginal Relevance).

### 4B.2 Usage

```python
from heretek_swarm.knowledge.unified_access import UnifiedKnowledgeAccess, KnowledgeQueryBuilder

# Initialize
knowledge = UnifiedKnowledgeAccess(
    memory_system=memory,
    rag_pipeline=rag,
)

# Simple query
result = await knowledge.query(
    query="What was the decision about X?",
    sources=["memory", "rag"],
    limit=10,
    rerank=True,
    diversity_lambda=0.5,
)

# Fluent builder pattern
result = await (KnowledgeQueryBuilder(knowledge)
    .query("Decision history")
    .from_sources("memory", "rag")
    .with_limit(10)
    .with_diversity(0.7)
    .filtered_by(agent_id="alpha")
    .execute())
```

### 4B.3 MMR Reranking

The MMR (Maximal Marginal Relevance) algorithm balances relevance and diversity:

| diversity_lambda | Behavior |
|-----------------|----------|
| 0.0 | Pure relevance (highest scoring items first) |
| 0.5 | Balanced relevance and diversity |
| 1.0 | Pure diversity (most different items first) |

### 4B.4 Agent Integration

**Historian Agent:**
- `unified_query()` method for knowledge queries
- `_handle_unified_query` handler for message-based queries
- Integrated with memory and RAG systems

**Perceiver+ Agent:**
- `knowledge_enhanced_query()` for analytics context
- `knowledge_enhanced_analysis` handler for combined data+knowledge analysis

---

## 5. Background Loops

The autonomous runtime runs 5 concurrent background loops:

| Loop | Interval | Purpose |
|------|----------|---------|
| Health Monitor | 30s | Check agent health, auto-restart failed agents |
| Consciousness | 5s | Update Phi metrics, global workspace broadcast |
| Task Processing | 1s | Poll for new tasks, route to appropriate agents |
| Memory Maintenance | 300s | Tier optimization, cleanup expired entries |
| Scaling | 60s | Auto-scale agents based on load |

---

## 6. Health Monitoring

### 6.1 Agent Health States

```
HEALTHY ──▶ DEGRADED ──▶ CRITICAL ──▶ FAILING
   ▲           │           │           │
   │           ▼           ▼           ▼
   │      RECOVERING ◀── RECOVERING ◀── RESTARTING
   │           │           │           │
   └───────────┴───────────┴───────────┘

State Transitions:
- HEALTHY → DEGRADED:  3 consecutive failed checks
- DEGRADED → CRITICAL: 5 consecutive failed checks
- CRITICAL → FAILING:  Agent unresponsive for 60s
- FAILING → RESTARTING: Auto-restart initiated
- RESTARTING → HEALTHY: Successful restart, health check passed
```

### 6.2 Health Metrics

```json
{
  "timestamp": "2026-04-06T17:00:00Z",
  "active_actors": 23,
  "mailbox_sizes": {
    "steward": 5,
    "alpha": 3,
    "beta": 2,
    "...": "..."
  },
  "system_status": "healthy"
}
```

---

## 7. Configuration

### 7.1 Full Configuration Example

```python
config = {
    # NATS Event Mesh
    "nats_servers": ["nats://localhost:4222"],
    
    # Timing
    "health_check_interval": 30,
    "loop_interval": 1,
    "consciousness_interval": 5,
    "memory_maintenance_interval": 300,
    "scaling_interval": 60,
    
    # Memory
    "ephemeral": {"ttl_seconds": 3600},
    "persistent": {
        "connection_string": "postgresql://user:pass@localhost/heretek_swarm",
    },
    
    # RAG
    "rag": {
        "embedding_provider": "openai",
        "collection_name": "heretek_documents",
    },
    
    # Consensus
    "consensus": {
        "ahead_by_k": 2,
        "min_votes": 3,
        "red_flag_threshold": 0.3,
    },
}
```

### 7.2 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://heretek:password@localhost/heretek_swarm

# Redis
REDIS_URL=redis://localhost:6379

# Qdrant
QDRANT_URL=http://localhost:6333

# NATS
NATS_SERVERS=nats://localhost:4222

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Feature Flags
CONSCIOUSNESS_ENABLED=true
RAG_ENABLED=true
AUTO_RESTART_ENABLED=true
```

---

## 8. Task Routing

The Steward agent uses keyword-based routing rules:

```python
TASK_ROUTING_RULES = {
    "deliberation": {
        "keywords": ["decide", "evaluate", "assess", "recommend", "approve"],
        "channel": "swarm.internal.triad",
        "agents": ["alpha", "beta", "charlie", "historian"],
        "consensus_required": True,
    },
    "research": {
        "keywords": ["research", "investigate", "gather", "discover", "find"],
        "channel": "swarm.internal.exploration",
        "agents": ["explorer", "examiner", "historian"],
        "consensus_required": False,
    },
    "implementation": {
        "keywords": ["build", "create", "implement", "code", "develop"],
        "channel": "swarm.internal.exploration",
        "agents": ["dreamer", "coder", "examiner"],
        "consensus_required": False,
    },
    "security": {
        "keywords": ["threat", "vulnerability", "attack", "breach", "unsafe"],
        "channel": "swarm.internal.safety",
        "agents": ["sentinel", "sentinel-prime", "arbiter"],
        "consensus_required": True,
        "priority": "critical",
    },
    "query": {
        "keywords": ["what", "when", "where", "who", "find information"],
        "channel": "swarm.internal.memory",
        "agents": ["historian", "perceiver-plus"],
        "consensus_required": False,
    },
    "external": {
        "keywords": ["api", "webhook", "external", "integration"],
        "channel": "swarm.external.api",
        "agents": ["nexus", "echo"],
        "consensus_required": False,
    },
}
```

---

## 9. Observability

### 9.1 Metrics Categories

| Category | Metrics |
|----------|---------|
| System | uptime_seconds, total_restarts, total_failures, memory_usage_bytes, cpu_percent, active_agents |
| Agent | messages_processed_total, messages_failed_total, average_response_time_ms, health_score, mailbox_size |
| Workflow | workflows_completed_total, workflows_failed_total, average_duration_ms, phase_durations_ms |
| Consensus | votes_collected_total, consensus_reached_total, red_flags_raised_total, average_confidence |
| RAG | documents_indexed_total, queries_executed_total, average_retrieval_time_ms, chunks_retrieved_total |

### 9.2 Distributed Tracing

All requests include trace context propagation:

```
External Request → API Gateway → Steward → HeavySwarm Workflow
                         │
                         ▼
              Trace Context:
              - trace_id: generated per request
              - span_id: new per hop
              - All agents share trace_id
```

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent not spawning | Import error or missing dependency | Check agent file exists and imports correctly |
| Channel subscription failed | NATS not connected | Verify NATS server is running |
| Memory store failing | Database connection issue | Check PostgreSQL connection string |
| Consensus timeout | Insufficient voters | Verify Triad agents are healthy |
| High mailbox queue | Agent processing slow | Check agent logs for errors |

### 10.2 Debug Commands

```bash
# Check agent health
curl http://localhost:8000/api/health

# List active agents
curl http://localhost:8000/api/agents

# Get channel stats
python -c "
from heretek_swarm.channels.registry import ChannelRegistry
registry = ChannelRegistry()
print(registry.get_all_stats())
"

# Get MCP tools
python -c "
from heretek_swarm.tools.mcp_tools import CoreMCPTools
tools = CoreMCPTools()
print(tools.get_registry().list_tools())
"
```

---

## 11. References

### 11.1 Related Documentation

- [`API_ENDPOINTS.md`](docs/API_ENDPOINTS.md) - API reference
- [`DEPLOYMENT.md`](docs/DEPLOYMENT.md) - Deployment guide

> **Note:** Legacy proposal documents from `docs/proposal/` directory were removed during consolidation.
> Consciousness metrics are documented in [`docs/architecture/emergent-intelligence.md`](docs/architecture/emergent-intelligence.md).
> Future development planning has been migrated to the GSD milestone system.

---

**Document Version:** 2.0.0  
**Last Updated:** 2026-04-06  
**Status:** Implementation Complete
