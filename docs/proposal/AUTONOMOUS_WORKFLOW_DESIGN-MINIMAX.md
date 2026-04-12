# Autonomous Workflow & Agent Communication Design

**Version:** 2.0.0  
**Date:** 2026-04-06  
**Author:** MINIMAX Audit & Design  
**Status:** Design Proposal  

---

## Executive Summary

This document provides a comprehensive design for the Heretek Swarm autonomous workflow, detailing how all 23 agents interconnect through communication channels, MCP tools, and database/RAG components to achieve continuous 24/7 autonomous operation with emergent collective intelligence.

---

## 1. System Overview Architecture

### 1.1 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HERETEK SWARM AUTONOMOUS SYSTEM                     │
└─────────────────────────────────────────────────────────────────────────────┘

  EXTERNAL INPUTS                    AUTONOMOUS CORE                      OUTPUTS
  ─────────────                   ──────────────                      ────────

  ┌──────────┐                  ┌─────────────────────┐              ┌──────────┐
  │  User    │                  │                     │              │  User    │
  │  API     │──────────────────▶│  API Gateway        │─────────────▶│  API    │
  │  Requests│                  │  (FastAPI +        │              │  Re-    │
  └──────────┘                  │   WebSocket)        │              │  sponse  │
                             └──────────┬──────────┘              └──────────┘
                                       │
  ┌──────────┐                  ┌──────────▼──────────┐              ┌──────────┐
  │  Webhook │                  │                 │              │  Webhook│
  │  Events │──────────────────▶│  A2A Protocol   │◀───────────│  Events │
  └──────────┘                  │  Server (18789)  │              └──────────┘
                             └──────────┬──────────┘
                                       │
  ┌──────────┐                  ┌──────────▼──────────┐
  │  NATS    │                  │                     │
  │  Events  │──────────────────▶│  Event Mesh        │
  └──────────┘                  │  (NATS JetStream)  │
                             └──────────┬──────────┘
                                       │
    ════════════════════════════════════╪══════════════════════════════════
                                       │
                                       ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                    ACTOR SUPERVISOR LAYER                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
    │  │  Health   │  │  Auto-     │  │  Scale     │  │  State     │    │
    │  │  Monitor │  │  Restart  │  │  Manager   │  │  Persist  │    │
    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
    └──────────────────────────────────┬────────────────────────────────────┘
                                       │
                                       ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                      23 AGENT COLLECTIVE                                │
    │                                                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                      TIER 1: CORE TRIAD (4)                       │ │
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
    │  │  │ STEWARD  │  │  ALPHA   │  │  BETA    │  │ CHARLIE  │        │ │
    │  │  │ (Gov)   │  │ (Anal)   │  │ (Valid)  │  │ (Chall) │        │ │
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                              │                                         │
    │                              ▼                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                   TIER 2: SUPPORT AGENTS (5)                      │ │
    │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │ │
    │  │  │HISTORIAN│ │ METIS  │ │ EMPATH │ │PERCEIVER│ │  ECHO  │       │ │
    │  │  │ (Memory)│ │(Plan)  │ │ (EQ)   │ │(Sensory)│ │(Comm)  │       │ │
    │  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                              │                                         │
    │                              ��                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                TIER 3: EXPLORATION AGENTS (4)                   │ │
    │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                   │ │
    │  │  │EXPLORER│ │EXAMINER│ │ DREAMER│ │ CODER   │                   │ │
    │  │  │(Find)  │ │ (QA)   │ │(Creative)││ (Build)│                   │ │
    │  │  └────────┘ └────────┘ └────────┘ └────────┘                   │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                              │                                         │
    │                              ▼                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                TIER 4: SAFETY & SECURITY (3)                      │ │
    │  │  ┌────────┐ ┌────────────┐ ┌────────┐                          │ │
    │  │  │SENTINEL│ │SENTINEL    │ │ ARBITER│                          │ │
    │  │  │(Guard) │ │ -PRIME    │ │ (解决) │                          │ │
    │  │  └────────┘ └────────────┘ └────────┘                          │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                              │                                         │
    │                              ▼                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                TIER 5: COORDINATION (4)                        │ │
    │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                   │ │
    │  │  │COORD. │ │ NEXUS  │ │CATALYST│ │ CHRONOS │                   │ │
    │  │  │(Sync) │ │ (API)  │ │(Change)│ │ (Time) │                   │ │
    │  │  └────────┘ └────────┘ └────────┘ └────────┘                   │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                              │                                         │
    │                              ▼                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                TIER 6: ENHANCEMENT (3)                         │ │
    │  │  ┌────────┐ ┌──────────┐ ┌��─────────┐                         │ │
    │  │  │ PRISM   │ │HABIT-FORGE│ │PERCEIVER+│                         │ │
    │  │  │(Multi) │ │ (Pattern)│ │ (Analytics)│                        │ │
    │  │  └────────┘ └──────────┘ └──────────┘                         │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    └───────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                    SUPPORT SYSTEMS                                     │
    │                                                                       │
    │  ┌──────────────────────┐  ┌──────────────────────┐              │
    │  │  MEMORY SYSTEM      │  │  RAG PIPELINE       │              │
    │  │  ┌──────────────┐  │  │  ┌──────────────┐  │              │
    │  │  │  Ephemeral  │  │  │  │  Document   │  │              │
    │  │  │  (Redis)   │  │  │  │  Processor │  │              │
    │  │  └──────────────┘  │  │  └──────────────┘  │              │
    │  │  ┌──────────────┐  │  │  ┌─────────────��┐  │              │
    │  │  │ Persistent │  │  │  │  Embedding │  │              │
    │  │  │(PostgreSQL)│  │  │  │  Service  │  │              │
    │  │  └──────────────┘  │  │  └──────────────┘  │              │
    │  │  ┌──────────────┐  │  │  ┌──────────────┐  │              │
    │  │  │  mem0      │  │  │  │  Vector    │  │              │
    │  │  │  Backend   │  │  │  │  Store    │  │              │
    │  │  └──────────────┘  │  │  └──────────────┘  │              │
    │  └──────────────────────┘  └──────────────────────┘              │
    │                                                                       │
    │  ┌──────────────────────┐  ┌──────────────────────┐              │
    │  │  CONSENSUS ENGINE    │  │  TOOLS REGISTRY     │              │
    │  │  ┌──────────────┐  │  │  ┌──────────────┐  │              │
    │  │  │   MAKER    │  │  │  │  BaseTool  │  │              │
    │  │  │ Algorithm │  │  │  │  Registry │  │              │
    │  │  └──────────────┘  │  │  └──────────────┘  │              │
    │  └──────────────────────┘  └──────────────────────┘              │
    │                                                                       │
    │  ┌──────────────────────┐  ┌──────────────────────┐              │
    │  │  OBSERVABILITY     │  │  WORKFLOW ENGINE    │              │
    │  │  ┌──────────────┐  │  │  ┌──────────────┐  │              │
    │  │  │  Tracing  │  │  │  │  HeavySwarm │  │              │
    │  │  │  Metrics  │  │  │  │  5-Phase  │  │              │
    │  │  │  Logging │  │  │  └──────────────┘  │              │
    │  │  └──────────────┘  │                      │
    │  └──────────────────────┘  └──────────────────────┘              │
    └───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Communication Channels & Groups

### 2.1 Channel Architecture

The system implements three primary communication channel types:

#### 2.1.1 A2A Protocol Channel (Primary)

| Property | Value |
|----------|-------|
| **Protocol** | Agent-to-Agent over WebSocket |
| **Port** | 18789 |
| **Security** | API Key Authentication |
| **Message Format** | JSON (ActorMessage) |
| **Delivery** | Guaranteed with ACK |

```
A2A Message Flow:
┌─────────┐     ┌─────────────┐     ┌─────────┐
│  Agent  │────▶│    A2A     │────▶│  Agent  │
│   A    │     │   Server   │     │   B    │
└─────────┘     └─────────────┘     ���─────────┘
     │                │                    │
     │  1. Handshake │                    │
     │───────────────▶│                    │
     │               │                    │
     │  2. Discovery│                    │
     │◀─────────────│                    │
     │               │                    │
     │  3. Send    │                    │
     │──────────────▶│──────▶actor_b     │
     │               │      mailbox     │
     │  4. ACK    │                    │
     │◀─────────────│◀─────│
```

#### 2.1.2 NATS Event Mesh Channel (Event Streaming)

| Property | Value |
|----------|-------|
| **Protocol** | NATS JetStream |
| **Port** | 4222 |
| **Durability** | Persistent with retention |
| **Subjects** | Hierarchical wildcards |

**Subject Hierarchy:**

```
Subjects:
├── agent.*                    # Agent lifecycle events
│   ├── agent.spawn
│   ├── agent.message
│   ├── agent.terminate
│   └── agent.health
├── workflow.*                 # Workflow events
│   ├── workflow.start
│   ├── workflow.phase
│   ├── workflow.complete
│   └── workflow.error
├── consensus.*               # Consensus events
│   ├── consensus.start
│   ├── consensus.vote
│   └── consensus.complete
├── system.*                 # System events
│   ├── system.alert
│   ├── system.error
│   └── system.metrics
└── state.*                 # State events
    ├── state.snapshot
    └── state.restore
```

#### 2.1.3 WebSocket Broadcast Channel (Real-time)

| Property | Value |
|----------|-------|
| **Protocol** | WebSocket |
| **Use Case** | Dashboard real-time updates |
| **Security** | JWT Token |

### 2.2 Communication Groups

Agents are organized into communication groups based on their collaboration patterns:

#### 2.2.1 Governance Group (Core Decision Making)

```
GovernanceGroup:
├── Members: [Steward, Alpha, Beta, Charlie, Historian]
├── Primary Channel: A2A Protocol
├── Topics: ['decisions', 'deliberations', 'governance']
├── Consensus: MAKER Algorithm
└── Purpose: High-level decision making
```

#### 2.2.2 Execution Group (Task Execution)

```
ExecutionGroup:
├── Members: [Coordinator, Coder, Explorer, Examiner]
├── Primary Channel: A2A Protocol
├── Topics: ['tasks', 'execution', 'results']
└── Purpose: Task planning and execution
```

#### 2.2.3 Safety Group (Security & Validation)

```
SafetyGroup:
├── Members: [Sentinel, SentinelPrime, Arbiter, Beta]
├── Primary Channel: A2A Protocol + NATS
├── Topics: ['security', 'validation', 'alerts']
└── Purpose: Input/output validation, threat response
```

#### 2.2.4 Memory Group (Knowledge & Context)

```
MemoryGroup:
├── Members: [Historian, Metis, Perceiver, PerceiverPlus]
├── Primary Channel: A2A Protocol
├── Topics: ['memory', 'context', 'retrieval']
├── RAG Enabled: true
└── Purpose: Knowledge management and RAG
```

#### 2.2.5 External Integration Group (API & Third-Party)

```
ExternalGroup:
├── Members: [Nexus, Echo, Catalyst]
├── Primary Channel: NATS (for webhooks)
├── Topics: ['external', 'webhooks', 'events']
└── Purpose: External system integration
```

---

## 3. Agent-to-Agent Wiring

### 3.1 Core Triad Communication Patterns

#### 3.1.1 Steward (Orchestrator)

```
Steward接线:
┌────────────────────────────────────────��─��──────────────────┐
│                     STEWARD AGENT                         │
├─────────────────────────────────────────────────────────────┤
│  Inputs:                                                 │
│  ├── user_requests        (A2A - from API Gateway)       │
│  ├── webhook_events      (NATS - external)                │
│  └── system_alerts      (NATS - monitoring)              │
│                                                          │
│  Outputs:                                                │
│  ├── deliberation_start  ──────▶ [α,β,χ,Historian]      │
│  ├── task_assign        ──────▶ [Coordinator, Executor] │
│  └── governance_update  ──────▶ [All Agents]            │
│                                                          │
│  State:                                                  │
│  ├── deliberation_queue  (Ephemeral)                    │
│  ├── active_deliberations (Ephemeral)                    │
│  └── governance_policy   (Persistent)                   │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Alpha (Primary Analyst)

```
Alpha Wiring:
┌─────────────────────────────────────────────────────────────┐
│                      ALPHA AGENT                         │
├─────────────────────────────────────────────────────────────┤
│  Inputs:                                                 │
│  ├── analysis_request   (A2A - from Steward)             │
│  ├── context_data     (A2A - from Historian)            │
│  └── research_data   (A2A - from Explorer)              │
│                                                          │
│  Outputs:                                                │
│  ├── analysis_result ──────▶ [Steward, Beta]            │
│  ├── proposals        ──────▶ [Beta, Charlie]           │
│  └── recommendations  ──────▶ [Metis]                  │
│                                                          │
│  Capabilities:                                          │
│  ├── deep_analysis                                        │
│  ├── proposal_generation                                 │
│  ├── pattern_recognition                                 │
│  └── cause_effect_modeling                               │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.3 Beta (Validator)

```
Beta Wiring:
┌─────────────────────────────────────────────────────────────┐
│                       BETA AGENT                        │
├─────────────────────────────────────────────────────────────┤
│  Inputs:                                                 │
│  ├── validation_request (A2A - from Steward/Alpha)       │
│  ├── proposals       (A2A - from Alpha)                │
│  └── implementations(A2A - from Coder)                │
│                                                          │
│  Outputs:                                                │
│  ├── validation_result ──▶ [Steward, Alpha]           │
│  ├── issues_found      ──▶ [Sentinel]                │
│  └── verified_output  ──▶ [Steward]                  │
│                                                          │
│  Capabilities:                                          │
│  ├── constraint_validation                               │
│  ├── error_detection                                    │
│  ├── edge_case_identification                           │
│  └── quality_assurance                                │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.4 Charlie (Challenger)

```
Charlie Wiring:
┌─────────────────────────────────────────────────────────────┐
│                     CHARLIE AGENT                          │
├─────────────────────────────────────────────────────────────┤
│  Inputs:                                                 │
│  ├── challenge_request (A2A - from Steward)              │
│  ├── proposals       (A2A - from Alpha)                │
│  └── implementations(A2A - from Coder)                │
│                                                          │
│  Outputs:                                                │
│  ├── challenges       ──▶ [Steward, Alpha, Beta]        │
│  ├── risk_assessment ──▶ [SentinelPrime]               │
│  └── edge_cases     ──▶ [Beta]                       │
│                                                          │
│  Capabilities:                                          │
│  ├── adversarial_thinking                                  │
│  ├── risk_assessment                                   │
│  ├── vulnerability_detection                          │
│  └── critical_review                                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Inter-Agent Message Routing

#### 3.2.1 Message Types and Handlers

| Message Type | From | To | Handler |
|-------------|------|-----|--------|
| `deliberation_start` | Steward | α,β,χ,Historian | `_handle_initiate_deliberation` |
| `analysis_request` | Steward | Alpha | `_handle_analyze_proposal` |
| `validation_request` | Steward/Alpha | Beta | `_handle_validate_proposal` |
| `challenge_request` | Steward | Charlie | `_handle_challenge_proposal` |
| `store_memory` | Any | Historian | `_handle_store_memory` |
| `search_memory` | Any | Historian | `_handle_search_memory` |
| `generate_plan` | Steward | Metis | `_handle_generate_plan` |
| `allocate_resources` | Metis | Coordinator | `_handle_allocate_resources` |
| `validate_input` | Any | Sentinel | `_handle_validate_input` |
| `detect_threat` | Sentinel | SentinelPrime | `_handle_detect_threat` |
| `resolve_conflict` | Arbiter | warring agents | `_handle_resolve_conflict` |

#### 3.2.2 Topic Subscriptions

```
Agent Topic Subscriptions:

Steward:   ['requests', 'decisions', 'system.alerts', 'workflow.*']
Alpha:     ['analysis', 'proposals', 'context']
Beta:      ['validation', 'verification', 'issues']
Charlie:   ['challenge', 'risk', 'challenges']
Historian: ['memory', 'context', 'history', 'lineage']
Metis:     ['planning', 'strategy', 'resources']
Empath:    ['sentiment', 'conflict', 'emotional']
Perceiver: ['input', 'sensory', 'features']
Echo:      ['format', 'broadcast', 'external']
Explorer: ['discovery', 'monitoring', 'opportunities']
Examiner: ['testing', 'quality', 'analysis']
Dreamer:  ['creative', 'alternatives', 'ideas']
Coder:    ['code', 'implementation', 'debug']
Sentinel: ['validation', 'safety', 'guardrails']
SentinelPrime: ['threats', 'security', 'incidents']
Arbiter:   ['conflict', 'resolution', 'disputes']
Coordinator: ['coordination', 'tasks', 'sync']
Nexus:     ['external', 'api', 'integration']
Catalyst:  ['change', 'transition', 'migration']
Chronos:   ['scheduling', 'temporal', 'timing']
Prism:     ['perspective', 'viewpoints', 'analysis']
HabitForge:['patterns', 'behavior', 'optimization']
PerceiverPlus: ['analytics', 'advanced', 'insights']
```

---

## 4. MCP Tools Integration

### 4.1 MCP Tools Architecture

The system exposes tools through the Model Context Protocol (MCP) for external AI system integration.

#### 4.1.1 Available MCP Tools

```
MCP Tools Registry:
├── memory
│   ├── memory_store      # Store memory with metadata
│   ├── memory_search     # Semantic search memories
│   └── memory_recall     # Retrieve by ID
├── workflow
│   ├── workflow_execute  # Execute HeavySwarm workflow
│   ├── workflow_status  # Get workflow status
│   └── workflow_cancel  # Cancel running workflow
├── consensus
│   ├── consensus_vote   # Submit vote to MAKER
│   ├── consensus_result # Get consensus result
│   └── consensus_state  # Get consensus state
├── agents
│   ├── agent_spawn      # Spawn new agent
│   ├── agent_terminate # Terminate agent
│   ├── agent_status    # Get agent health
│   └── agent_invoke    # Direct agent invocation
├── rag
│   ├── rag_ingest       # Ingest document
│   ├── rag_query       # Query RAG system
│   └── rag_search      # Semantic search
├── tools
│   ├── tool_execute    # Execute registered tool
│   ├── tool_list      # List available tools
│   └── tool_discover  # Auto-discover tools
└── system
    ├── system_health   # Get system health
    ├── system_metrics # Get metrics
    └── system_config # Get configuration
```

### 4.2 MCP Server Configuration

```python
# MCP Server Configuration
MCPServerConfig(
    name="heretek-swarm-mcp",
    version="1.0.0",
    port=18790,  # MCP server port
    
    # Tools enabled
    tools=[
        "memory.*",
        "workflow.*", 
        "consensus.*",
        "agents.*",
        "rag.*",
    ],
    
    # Authentication
    auth_required=True,
    
    # Rate limiting
    rate_limit=100,  # requests per minute
    
    # Caching
    cache_enabled=True,
    cache_ttl=300,  # seconds
)
```

---

## 5. Database & RAG Components

### 5.1 Database Architecture

```
Database Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐        ┌─────────────────────┐          │
│  │    PostgreSQL      │        │      Redis          │          │
│  │  (Persistent)     │        │   (Ephemeral)       │          │
│  ├─────────────────────┤        ├─────────────────────┤          │
│  │ Tables:           │        │ Keys:              │          │
│  │ - agents          │        │ - agent:*:state    │          │
│  │ - workflows      │        │ - workflow:*:state │          │
│  │ - memories       │        │ - deliberation:*    │          │
│  │ - vectors        │        │ - mailbox:*         │          │
│  │ - decisions      │        │ - metrics:*        │          │
│  │ - audit_log      │        │ - health:*         │          │
│  │ - snapshots     │        │ - cache:*          │          │
│  └─────────────────────┘        └─────────────────────┘          │
│                                                                  │
│  ┌─────────────────────┐        ┌─────────────────────┐          │
│  │   Qdrant           │        │    mem0 Backend     │          │
│  │  (Vector Store)     │        │   (Memory API)      │          │
│  ├─────────────────────┤        ├─────────────────────┤          │
│  │ Collections:      │        │ Entities:          │          │
│  │ - memories        │        │ - agents           │          │
│  │ - documents      │        │ - workflows        │          │
│  │ - decisions     │        │ - memories         │          │
│  │ - audit        │        │ - interactions     │          │
│  └─────────────────────┘        └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Schema Overview

#### 5.2.1 PostgreSQL Schema

```sql
-- Core Tables

-- Agents table
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    capabilities JSONB,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_health_check TIMESTAMP,
    health_score FLOAT
);

-- Workflows table
CREATE TABLE workflows (
    workflow_id UUID PRIMARY KEY,
    workflow_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    current_phase VARCHAR(20),
    context JSONB,
    result JSONB,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Memories table (persistent)
CREATE TABLE memories (
    memory_id UUID PRIMARY KEY,
    content JSONB NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    memory_type VARCHAR(20) NOT NULL,
    lineage JSONB,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP
);

-- Decisions table (MAKER votes)
CREATE TABLE decisions (
    decision_id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows,
    agent_id UUID REFERENCES agents,
    decision VARCHAR(500) NOT NULL,
    confidence FLOAT NOT NULL,
    voting_weight FLOAT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);

-- Audit log table
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY,
    actor_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    payload JSONB,
    created_at TIMESTAMP NOT NULL
);

-- State snapshots
CREATE TABLE snapshots (
    snapshot_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    state_data JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);
```

#### 5.2.2 Redis Key Structure

```
Redis Key Structure:

# Agent state (per-agent)
agent:{agent_id}:state      # Hash    - Current agent state
agent:{agent_id}:mailbox   # List   - Pending messages
agent:{agent_id}:health    # String - Last health check

# Workflow state (per-workflow)
workflow:{workflow_id}:phase      # String - Current phase
workflow:{workflow_id}:context    # Hash   - Workflow context
workflow:{workflow_id}:results    # Hash   - Phase results

# Deliberation state
deliberation:{delib_id}:queue    # List   - Pending items
deliberation:{delib_id}:votes  # Hash   - Collected votes

# Metrics
metrics:{agent_id}:counts     # Hash   - Execution counts
metrics:system:aggregates      # Hash   - System metrics

# Cache
cache:rag:{query_hash}        # String - RAG query cache
cache:tool:{tool_name}        # String - Tool result cache
```

### 5.3 RAG Pipeline

```
RAG Pipeline Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Document   │───▶│   Segment   │───▶│  Embedding   │      │
│  │   Ingestion  │    │   Builder  │    │  Generator  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌──────────────┐                      ┌──────────────┐      │
│  │   Metadata   │                      │   Vector     │      │
│  │   Extractor │                      │   Store      │      │
│  └──────────────┘                      └──────────────┘      │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌──────────────┐                      ┌──────────────┐      │
│  │   Document  │                      │   Qdrant     │      │
│  │   Storage   │                      │   Collection │      │
│  └──────────────┘                      └──────────────┘      │
│                                                                  │
│  Query Flow:                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │    Query    │───▶│   Embedding  │───▶│   Similarity │      │
│  │    Input    │    │   Generate  │    │   Search    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌��─────────────┐                      ┌──────────────┐      │
│  │    rerank   │◀─────────────────────│   Retrieved │      │
│  │   (MMR)    │                       │   Chunks     │      │
│  └──────────────┘                      └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Autonomous Operation Loops

### 6.1 Main Autonomous Loop

The autonomous runtime executes several concurrent loops to maintain 24/7 operation:

```
Autonomous Runtime Loops:
┌─────────────────────────────────────────────────────────────────┐
│                 AUTONOMOUS RUNTIME                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Loop 1: Monitoring Loop (every 30s)                            │
│  ├─ Check agent health status                                  │
│  ├─ Check workflow status                                      │
│  ├─ Check resource utilization                                 │
│  └─ Publish metrics to NATS                                     │
│                                                                  │
│  Loop 2: Auto-Recovery Loop (on failure)                       │
│  ├─ Detect failure via health check                            │
│  ├─ Log failure details                                        │
│  ├─ Attempt auto-restart (max 3 retries)                       │
│  ├─ If persistent: escalate to SentinelPrime                   │
│  └─ Notify governance group                                     │
│                                                                  │
│  Loop 3: Scaling Loop (every 60s)                              │
│  ├─ Check queue depths                                          │
│  ├─ Check resource utilization                                │
│  ├─ Scale up if: queue > threshold OR cpu > 80%               │
│  └─ Scale down if: queue < threshold AND cpu < 30%             │
│                                                                  │
│  Loop 4: State Persistence Loop (every 300s)                    │
│  ├─ Create state snapshot                                       │
│  ├─ Store to PostgreSQL                                         │
│  └─ Store embeddings to Qdrant                                  │
│                                                                  │
│  Loop 5: Metrics Collection Loop (every 60s)                  │
│  ├─ Collect agent execution counts                             │
│  ├─ Collect response time percentiles                          │
│  ├─ Collect consensus statistics                               │
│  └─ Publish to observability system                           │
│                                                                  │
│  Loop 6 (Optional): Consciousness Metrics (every 60s)         │
│  ├─ Calculate workspace coherence                              │
│  ├─ Calculate attention distribution                          │
│  └─ Publish consciousness metrics                             │
└───────────────────────���─���───────────────────────────────────────┘
```

### 6.2 HeavySwarm Workflow Loop

```
HeavySwarm 5-Phase Workflow:
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: RESEARCH                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Steward initiates deliberation                            │ │
│  │   ↓                                                     │ │
│  │ Historian provides context/history                     │ │
│  │   ↓                                                     │ │
│  │ Explorer gathers additional information                 │ │
│  │   ↓                                                     │ │
│  │ Output: Research package with context + history          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  PHASE 2: ANALYSIS                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Alpha analyzes problem (primary perspective)             │ │
│  │   ↓                                                     │ │
│  │ Beta validates (validation perspective)                  │ │
│  │   ↓                                                     │ │
│  │ Charlie challenges (risk perspective)                   │ │
│  │   ↓                                                     │ │
│  │ Output: Multi-perspective analysis                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  PHASE 3: ALTERNATIVES                                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Dreamer generates creative options                       │ │
│  │   ↓                                                     │ │
│  │ Metis evaluates trade-offs                             │ │
│  │   ↓                                                     │ │
│  │ Output: Ranked alternatives with evaluations            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  PHASE 4: VERIFICATION                                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Beta validates each alternative                         │ │
│  │   ↓                                                     │ │
│  │ Charlie assesses risks                                  │ │
│  │   ↓                                                     │ │
│  │ Sentinel performs safety check                         �� │
│  │   ↓                                                     │ │
│  │ Output: Verification results + risk assessment         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  PHASE 5: DECISION                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ MAKER Consensus aggregates votes                         │ │
│  │   ↓                                                     │ │
│  │ Steward makes final decision                            │ │
│  │   ↓                                                     │ │
│  │ Historian documents decision + lineage                 │ │
│  │   ↓                                                     │ │
│  │ Output: Final decision with confidence + red flags     │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Agent Health Monitoring

```
Health Monitoring State Machine:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│    HEALTHY ──▶ DEGRADED ──▶ CRITICAL ──▶ FAILING               │
│       ▲           │           │           │                        │
│       │           ▼           ▼           ▼                        │
│       │      RECOVERING ◀── RECOVERING ◀── RESTARTING            │
│       │           │           │           │                        │
│       └───────────┴───────────┴───────────┘                        │
│                                                                  │
│  State Transitions:                                              │
│  ─────────────────                                              │
│  HEALTHY → DEGRADED:  3 consecutive failed checks              │
│  DEGRADED → CRITICAL: 5 consecutive failed checks              │
│  CRITICAL → FAILING:  Agent unresponsive for 60s               │
│  FAILING → RESTARTING: Auto-restart initiated                    │
│  RESTARTING → HEALTHY: Successful restart, health check passed    │
│  DEGRADED → HEALTHY: 5 consecutive successful checks          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. State Management

### 7.1 State Layers

```
State Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    STATE LAYERS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Ephemeral State (Redis)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ - Agent mailboxes (message queues)                     │   │
│  │ - Current execution context                           │   │
│  │ - Active deliberation state                          │   │
│  │ - Real-time metrics                                  │   │
│  │ - Cache                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  Layer 2: Persistent State (PostgreSQL)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ - Agent configurations                               │   │
│  │ - Workflow definitions                              │   │
│  │ - Decisions and votes                             │   │
│  │ - Long-term memories                              │   │
│  │ - Audit logs                                     │   │
│  │ - State snapshots                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  Layer 3: Vector State (Qdrant)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ - Memory embeddings                                 │   │
│  │ - Document embeddings                               │   │
│  │ - Decision embeddings                             │   │
│  │ - Audit embeddings                                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 State Persistence Strategy

```python
# State Persistence Configuration
StatePersistenceConfig(
    # When to snapshot
    snapshot_interval_seconds=300,        # Every 5 minutes
    
    # What to snapshot
    snapshot_components=[
        "agents",
        "workflows", 
        "memories",
        "decisions"
    ],
    
    # How many snapshots to keep
    max_snapshots=10,
    
    # When to auto-restore
    auto_restore_on_startup=True,
    
    # State to restore from
    restore_from_latest=True
)
```

---

## 8. Observability

### 8.1 Metrics Collection

```
Metrics Categories:
┌─────────────────────────────────────────────────────────────────┐
│                    METRICS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  System Metrics:                                                 │
│  ├─ uptime_seconds                                             │
│  ├─ total_restarts                                           │
│  ├─ total_failures                                           │
│  ├─ memory_usage_bytes                                        │
│  ├─ cpu_percent                                              │
│  └─ active_agents                                           │
│                                                                  │
│  Agent Metrics:                                                │
│  ├─ messages_processed_total                                  │
│  ├─ messages_failed_total                                    │
│  ├─ average_response_time_ms                                 │
│  ├─ health_score                                            │
│  └─ mailbox_size                                            │
│                                                                  │
│  Workflow Metrics:                                            │
│  ├─ workflows_completed_total                                │
│  ├─ workflows_failed_total                                  │
│  ├─ average_duration_ms                                      │
│  └─ phase_durations_ms                                      │
│                                                                  │
│  Consensus Metrics:                                           │
│  ├─ votes_collected_total                                   │
│  ├─ consensus_reached_total                                 │
│  ├─ red_flags_raised_total                                   │
│  └─ average_confidence                                      │
│                                                                  │
│  RAG Metrics:                                                 │
│  ├─ documents_indexed_total                                 │
│  ├─ queries_executed_total                                  │
│  ├─ average_retrieval_time_ms                                │
│  └─ chunks_retrieved_total                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Distributed Tracing

```
Trace Context Propagation:
┌─────────────────────────────────────────────────────────────────┐
│                    TRACE FLOW                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  External Request                                              │
│  │                                                              │
│  │ + trace_id =.generate()                                      │
│  │ + span_id = generate()                                       │
│  │                                                              │
│  ▼                                                              │
│  API Gateway                                                    │
│  │                                                              │
│  │ Request incoming                                             │
│  │   ↓                                                        │
│  │ Validate (Sentinel)                                         │
│  │   ↓                                                        │
│  │ Route to Steward                                             │
│  │   ↓                                                        │
│  │ (all have same trace_id, new span_id per hop)               │
│  │                                                              │
│  ▼                                                              │
│  HeavySwarm Workflow                                           │
│  │                                                              │
│  │ Phase 1: Research                                          │
│  │   ├── Historian (span)                                      │
│  │   └── Explorer (span)                                       │
│  │                                                              │
│  │ Phase 2: Analysis                                           │
│  │   ├── Alpha (span)                                          │
│  │   ├── Beta (span)                                           │
│  │   └── Charlie (span)                                        │
│  │                                                              │
│  │ Phase 5: Decision                                          │
│  │   └── MAKER Consensus (span)                                │
│  │                                                              │
│  ▼                                                              │
│  Response                                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Security & Zero-Trust

### 9.1 Security Layers

```
Security Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: API Gateway Security                                   │
│  ├─ API Key Authentication                                       │
│  ├─ Rate Limiting per key                                       │
│  └─ Request Validation                                         │
│                                                                  │
│  Layer 2: A2A Protocol Security                                 │
│  ├─ Agent Handshake with credentials                           │
│  ├─ Message signing                                            │
│  └─ Channel encryption (TLS)                                   │
│                                                                  │
│  Layer 3: Input Validation (Sentinel)                          │
│  ├─ Pydantic validation for all inputs                        │
│  ├─ Sanitization                                                │
│  └─ Type enforcement                                            │
│                                                                  │
│  Layer 4: Output Validation (Sentinel)                         │
│  ├─ Response filtering                                         │
│  ├─ PII removal                                                 │
│  └─ Content safety check                                        │
│                                                                  │
│  Layer 5: Audit Logging                                         │
│  └─ All actions logged to audit_log table                      │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Guardrails Configuration

```python
# Sentinel Guardrails Configuration
GuardrailsConfig(
    # Input validation
    input_validation={
        "enabled": True,
        "strict_mode": True,
        "max_content_length": 100000,
        "allowed_content_types": ["text", "json"]
    },
    
    # Output filtering
    output_filtering={
        "enabled": True,
        "pii_detection": True,
        "profanity_filter": True,
        "injections_filter": True
    },
    
    # Rate limiting
    rate_limiting={
        "enabled": True,
        "requests_per_minute": 100,
        "burst_size": 10
    },
    
    # Threat detection
    threat_detection={
        "enabled": True,
        "anomaly_detection": True,
        "auto_block": True
    }
)
```

---

## 10. Deployment Configuration

### 10.1 Kubernetes Deployment

```
Kubernetes Resources:
┌─────────────────────────────────────────────────────────────────┐
│                    K8S RESOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Deployments:                                                   │
│  ├─ heretek-swarm-api        (3 replicas)                      │
│  ├─ heretek-swarm-dashboard (2 replicas)                       │
│  └─ heretek-swarm-mcp       (2 replicas)                        │
│                                                                  │
│  StatefulSets:                                                 │
│  ├─ postgres                 (1 replica, 20Gi)                │
│  └─ redis                    (1 replica, 5Gi)                  │
│                                                                  │
│  Services:                                                      │
│  ├─ heretek-swarm-api        (ClusterIP:8000)                  │
│  ├─ heretek-swarm-dashboard (ClusterIP:80)                      │
│  ├─ postgres                (ClusterIP:5432)                 │
│  ├─ redis                   (ClusterIP:6379)                   │
│  └─ qdrant                  (ClusterIP:6333)                  │
│                                                                  │
│  Ingress:                                                       │
│  └─ api.heretek-swarm.com   (HTTPS:443)                         │
│                                                                  │
│  HPA:                                                           │
│  ├─ heretek-swarm-api       (3-10 replicas, 70% CPU)           │
│  └─ heretek-swarm-dashboard(2-5 replicas, 70% CPU)             │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Environment Variables

```yaml
# Required Environment Variables

# Database
DATABASE_URL: postgresql://heretek:password@postgres:5432/heretek_swarm

# Redis
REDIS_URL: redis://redis:6379

# Qdrant (Vector Store)
QDRANT_URL: http://qdrant:6333

# API Keys
OPENAI_API_KEY: sk-...
ANTHROPIC_API_KEY: sk-ant-...

# Auth
JWT_SECRET: heretek-swarm-secret-key
API_KEY: heretek-swarm-api-key

# Feature Flags
CONSCIOUSNESS_ENABLED: true
RAG_ENABLED: true
AUTO_RESTART_ENABLED: true
```

---

## 11. Integration Summary

### 11.1 Quick Reference Wiring Diagram

```
Complete Agent Wiring (Simplified):
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                  │
│  External ──▶ API Gateway ──▶ Steward ──▶ HeavySwarm Workflow   │
│                                                                  │
│  HeavySwarm ──▶ (α, β, χ, Historian) ──▶ MAKER Consensus        │
│                                                                  │
│  Supporting:                                                    │
│  ├── Coordinator ──▶ (Coder, Explorer, Examiner)              │
│  ├── Sentinel ──▶ SentinelPrime ──▶ Arbiter                  │
│  ├── Historian ──▶ Memory (Redis + PostgreSQL + Qdrant)        │
│  ├── Nexus ──▶ External APIs                                   │
│  └── Metis ──▶ Coordinator ──▶ Chronos                       │
│                                                                  │
│  Monitoring:                                                   │
│  ├── ActorSupervisor (health + restart)                       │
│  ├── AutonomousRuntime (loops)                               │
│  └── Observability (tracing + metrics)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Port Reference

| Service | Port | Protocol |
|---------|------|----------|
| API Gateway | 8000 | HTTP |
| A2A Server | 18789 | WebSocket |
| MCP Server | 18790 | HTTP |
| Dashboard | 80 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| Qdrant | 6333 | HTTP |
| NATS | 4222 | TCP |

---

## 12. Implementation Priorities

### Phase 1: Core Foundation
1. Implement Steward, Alpha, Beta, Charlie, Historian (5 agents)
2. Set up A2A Protocol Server
3. Implement MAKER Consensus
4. Configure PostgreSQL + Redis

### Phase 2: Execution Framework
1. Implement Coordinator, Coder (2 agents)
2. Build HeavySwarm Workflow Engine
3. Add health monitoring
4. Set up NATS Event Mesh

### Phase 3: Safety & Integration
1. Implement Sentinel, SentinelPrime, Arbiter (3 agents)
2. Add input/output validation
3. Set up MCP tools
4. Configure RAG pipeline

### Phase 4: Full Deployment
1. Implement remaining 13 agents
2. Add consciousness metrics
3. Performance optimization
4. Full observability

---

**Document Status:** Design Complete  
**Next Step:** Implementation planning  
**Last Updated:** 2026-04-06