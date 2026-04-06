# Heretek Swarm Autonomous Workflow Design

**Version:** 1.0.0  
**Date:** 2026-04-06  
**Author:** Multi (AI Assistant)  
**Tracking ID:** QWEN  
**Audit Scope:** Full System Architecture Review

---

## Executive Summary

This document presents a comprehensive architecture audit and autonomous workflow design for the Heretek Swarm 23-agent AI cluster. After analyzing the existing implementation, I provide specific recommendations for wiring agents into a cohesive 24/7 autonomous loop, including communication channel architecture, MCP tools integration patterns, and database/RAG component connections.

### Key Findings

| Aspect | Status | Confidence |
|--------|--------|------------|
| Agent Implementation | ✅ Complete (23/23) | High |
| Message Passing | ✅ Actor Model | High |
| Consensus Mechanism | ✅ MAKER Algorithm | High |
| Memory System | ✅ Dual-Tier | High |
| RAG Pipeline | ✅ Complete | High |
| Event Mesh | ⚠️ Partial (NATS optional) | Medium |
| MCP Integration | ❌ Not Implemented | N/A |
| Autonomous Loop | ⚠️ Runtime exists, not wired | Medium |
| Tool Registry | ✅ Complete | High |

---

## 1. Current State Audit

### 1.1 Agent Inventory

All 23 agents are implemented across 6 tiers:

#### Tier 1: Core Triad (Governance) ✅
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Steward | `actors/triad.py` | ✅ Complete | Coordination, governance, decision-making |
| Alpha | `actors/triad.py` | ✅ Complete | Analysis, decision-making, validation |
| Beta | `actors/triad.py` | ✅ Complete | Validation, error-detection, QA |
| Charlie | `actors/triad.py` | ✅ Complete | Risk-assessment, challenger, edge-cases |

#### Tier 2: Support Agents (Knowledge & Memory) ⚠️
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Historian | `actors/historian.py` | ✅ Complete | Memory, context, history, lineage |
| Metis | `actors/metis.py` | ⚠️ Character only | Strategic planning, resource allocation |
| Empath | `actors/empath.py` | ⚠️ Character only | Sentiment, mediation, emotional state |
| Perceiver | `actors/perceiver.py` | ⚠️ Character only | Multi-modal input, feature extraction |
| Echo | `actors/echo.py` | ⚠️ Character only | Communication, protocol translation |

#### Tier 3: Exploration Agents (Discovery & Creation) ⚠️
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Explorer | `actors/explorer.py` | ⚠️ Character only | Intelligence gathering, anomaly detection |
| Examiner | `actors/examiner.py` | ⚠️ Character only | QA testing, code analysis |
| Dreamer | `actors/dreamer.py` | ⚠️ Character only | Creative solutions, divergent thinking |
| Coder | `actors/coder.py` | ⚠️ Character only | Code generation, review, debugging |

#### Tier 4: Safety & Security (Protection) ⚠️
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Sentinel | `actors/sentinel.py` | ⚠️ Character only | Input/output safety validation |
| Sentinel-Prime | `actors/sentinel_prime.py` | ⚠️ Character only | Threat detection, security response |
| Arbiter | `actors/arbiter.py` | ⚠️ Character only | Conflict resolution, arbitration |

#### Tier 5: Coordination Agents (Integration) ⚠️
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Coordinator | `actors/coordinator.py` | ⚠️ Character only | Multi-agent workflow coordination |
| Nexus | `actors/nexus.py` | ⚠️ Character only | External API integration |
| Catalyst | `actors/catalyst.py` | ⚠️ Character only | Change management, rollback |
| Chronos | `actors/chronos.py` | ⚠️ Character only | Scheduling, deadlines, timeline |

#### Tier 6: Enhancement Agents (Optimization) ⚠️
| Agent | File | Status | Capabilities |
|-------|------|--------|--------------|
| Prism | `actors/prism.py` | ⚠️ Character only | Multi-perspective, bias detection |
| Habit-Forge | `actors/habit_forge.py` | ⚠️ Character only | Behavior optimization, patterns |
| Perceiver+ | `actors/perceiver_plus.py` | ⚠️ Character only | Advanced analytics, forecasting |

### 1.2 Core Infrastructure

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| Actor Base | `actors/base.py` | ✅ Complete | Full actor model with mailbox |
| Actor Supervisor | `actors/supervisor.py` | ✅ Complete | Health monitoring, auto-restart |
| Event Mesh | `gateway/event_mesh.py` | ✅ Complete | WebSocket-based |
| NATS Event Mesh | `gateway/nats_event_mesh.py` | ⚠️ Optional | Fallback mode, not primary |
| A2A Protocol | `gateway/a2a_protocol.py` | ✅ Complete | Agent-to-agent communication |
| MAKER Consensus | `consensus/maker.py` | ✅ Complete | First-to-ahead-by-k voting |
| HeavySwarm | `orchestration/heavyswarm.py` | ✅ Complete | 5-phase deliberation |
| Dual-Tier Memory | `memory/unified.py` | ✅ Complete | Ephemeral + Persistent |
| RAG Pipeline | `rag/rag_pipeline.py` | ✅ Complete | Document ingestion + retrieval |
| Tool Registry | `tools/registry.py` | ✅ Complete | Dynamic tool management |
| Runtime Tools | `runtime/tools.py` | ✅ Complete | Built-in tools with security |
| Autonomous Runtime | `runtime/autonomous_runtime.py` | ⚠️ Exists | Not wired to 24/7 loop |
| Workflow Engine | `workflow/engine.py` | ✅ Complete | Graph-based workflows |
| Observability | `observability/` | ✅ Complete | Metrics, tracing, logging |
| Consciousness | `plugins/consciousness.py` | ✅ Complete | GWT, AST implementations |

### 1.3 Critical Gaps

1. **MCP Protocol** - No Model Context Protocol implementation
2. **Channel Groups** - No formal communication channel architecture
3. **Agent Wiring** - Characters defined but not wired into autonomous loop
4. **NATS JetStream** - Available but not integrated as primary event bus
5. **Entry Point** - No clear autonomous loop entry point for 24/7 operation

---

## 2. Autonomous Loop Architecture

### 2.1 Recommended Loop Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTONOMOUS RUNTIME LOOP                              │
│                         (runtime/autonomous_runtime.py)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 0: INGRESS                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Chronos    │  │   Nexus     │  │   Echo      │  │  Perceiver  │         │
│  │ (Scheduled) │  │ (External)  │  │ (Channels)  │  │  (Sensory)  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: TRIAGE (Steward)                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  STEWARD - Classifies and routes all incoming tasks                   │  │
│  │  ───────────────────────────────────────────────────────────────────  │  │
│  │  Task Types:                                                           │  │
│  │  • Deliberation → Triad Channel                                        │  │
│  │  • Research → Exploration Channel                                      │  │
│  │  • Threat → Safety Channel                                             │  │
│  │  • Query → Memory/RAG Channel                                          │  │
│  │  • External → Nexus Channel                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  TRIAD PATH       │    │  EXPLORATION PATH │    │  SAFETY PATH      │
│  (Complex Decisions)│  │  (Discovery)      │    │  (Threats)        │
│                   │    │                   │    │                   │
│  Alpha (Analyze)  │    │  Explorer         │    │  Sentinel         │
│       ↓           │    │       ↓           │    │       ↓           │
│  Beta (Validate)  │    │  Examiner         │    │  Sentinel-Prime   │
│       ↓           │    │       ↓           │    │       ↓           │
│  Charlie (Challenge)│  │  Dreamer/Coder    │    │  Arbiter          │
│       ↓           │    │                   │    │                   │
│  Historian (Context)│  │  Historian (Store)│    │  Historian (Log)  │
└───────────────────┘    └───────────────────┘    └───────────────────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: COORDINATION                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Coordinator │  │   Metis     │  │  Catalyst   │  │   Empath    │         │
│  │(Sync Agents)│  │ (Strategy)  │  │  (Change)   │  │ (Sentiment) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: CONSENSUS (MAKER)                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  MAKER Consensus Engine                                                │  │
│  │  ───────────────────────────────────────────────────────────────────  │  │
│  │  • Collect votes from relevant agents                                  │  │
│  │  • Apply reputation weighting                                          │  │
│  │  • Check red-flag conditions                                           │  │
│  │  • Compute first-to-ahead-by-k winner                                  │  │
│  │  • Return decision with confidence                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: ENHANCEMENT                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │   Prism     │  │ Habit-Forge │  │  Historian  │                          │
│  │(Multi-View) │  │ (Optimize)  │  │  (Persist)  │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: OUTPUT                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │   Echo      │  │   Nexus     │  │ Consciousness│                          │
│  │ (Broadcast) │  │ (External)  │  │  (Metrics)  │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  LOOP BACK    │
                              │  (Continuous) │
                              └───────────────┘
```

### 2.2 Agent Activation Matrix

| Stage | Primary Agents | Secondary Agents | Support Agents |
|-------|---------------|------------------|----------------|
| 0: Ingress | Chronos, Nexus, Perceiver | Echo | - |
| 1: Triage | Steward | - | Historian |
| 2: Processing | Alpha/Beta/Charlie OR Explorer/Examiner OR Sentinel | Dreamer/Coder | Empath, Metis |
| 3: Coordination | Coordinator | Catalyst | Metis, Empath |
| 4: Consensus | Steward, Alpha, Beta, Charlie | - | - |
| 5: Enhancement | Prism, Habit-Forge | - | Historian |
| 6: Output | Echo, Nexus | - | Consciousness |

### 2.3 Task Routing Rules

```python
# Recommended routing logic for Steward
TASK_ROUTING_RULES = {
    # Deliberation tasks → Triad
    "deliberation": {
        "keywords": ["decide", "evaluate", "assess", "recommend", "approve"],
        "path": ["alpha", "beta", "charlie", "historian"],
        "consensus_required": True,
    },
    
    # Research tasks → Exploration
    "research": {
        "keywords": ["research", "investigate", "gather", "discover", "find"],
        "path": ["explorer", "examiner", "historian"],
        "consensus_required": False,
    },
    
    # Implementation tasks → Creation
    "implementation": {
        "keywords": ["build", "create", "implement", "code", "develop"],
        "path": ["dreamer", "coder", "examiner"],
        "consensus_required": False,
    },
    
    # Security tasks → Safety
    "security": {
        "keywords": ["threat", "vulnerability", "attack", "breach", "unsafe"],
        "path": ["sentinel", "sentinel-prime", "arbiter"],
        "consensus_required": True,
        "priority": "critical",
    },
    
    # Query tasks → Memory/RAG
    "query": {
        "keywords": ["what", "when", "where", "who", "find information"],
        "path": ["historian", "perceiver-plus"],
        "consensus_required": False,
    },
    
    # External tasks → Integration
    "external": {
        "keywords": ["api", "webhook", "external", "integration"],
        "path": ["nexus", "echo"],
        "consensus_required": False,
    },
}
```

---

## 3. Communication Channels/Groups

### 3.1 Channel Architecture

I recommend implementing a formal channel subscription system using NATS subjects:

```python
# Recommended NATS Subject Structure
CHANNEL_SUBJECTS = {
    # === INTERNAL AGENT CHANNELS ===
    "swarm.internal.triad": {
        "description": "Core governance deliberation",
        "subscribers": ["steward", "alpha", "beta", "charlie"],
        "message_types": ["proposal", "analysis", "validation", "challenge", "decision"],
        "qos": "at-least-once",
        "retention": "24h",
    },
    
    "swarm.internal.coordination": {
        "description": "Multi-agent task coordination",
        "subscribers": ["coordinator", "catalyst", "chronos", "metis"],
        "message_types": ["task_start", "task_complete", "dependency_ready", "blocker"],
        "qos": "at-least-once",
        "retention": "12h",
    },
    
    "swarm.internal.safety": {
        "description": "Security and safety alerts",
        "subscribers": ["sentinel", "sentinel-prime", "arbiter", "steward"],
        "message_types": ["threat_detected", "quarantine", "all_clear", "incident_report"],
        "qos": "exactly-once",
        "retention": "7d",
        "priority": "critical",
    },
    
    "swarm.internal.memory": {
        "description": "Memory and knowledge operations",
        "subscribers": ["historian", "prism", "habit-forge"],
        "message_types": ["store_request", "retrieve_request", "learn_pattern", "forget"],
        "qos": "at-most-once",
        "retention": "1h",
    },
    
    "swarm.internal.exploration": {
        "description": "Research and implementation",
        "subscribers": ["explorer", "examiner", "dreamer", "coder"],
        "message_types": ["research_task", "analysis_result", "creative_request", "code_review"],
        "qos": "at-least-once",
        "retention": "6h",
    },
    
    "swarm.internal.perception": {
        "description": "Input processing and translation",
        "subscribers": ["perceiver", "perceiver-plus", "empath", "echo"],
        "message_types": ["input_received", "sentiment_analysis", "translation_request", "feature_extracted"],
        "qos": "at-most-once",
        "retention": "1h",
    },
    
    # === SYSTEM CHANNELS ===
    "swarm.system.health": {
        "description": "Health monitoring (all agents)",
        "subscribers": ["*"],  # Wildcard - all agents
        "message_types": ["heartbeat", "health_status", "error_report", "restart_request"],
        "qos": "at-most-once",
        "retention": "1h",
    },
    
    "swarm.system.consciousness": {
        "description": "Consciousness metrics broadcast",
        "subscribers": ["*"],
        "message_types": ["phi_update", "attention_state", "workspace_broadcast", "integration_metric"],
        "qos": "at-most-once",
        "retention": "30m",
    },
    
    "swarm.system.consensus": {
        "description": "MAKER consensus voting",
        "subscribers": ["steward", "alpha", "beta", "charlie"],
        "message_types": ["vote_cast", "consensus_reached", "red_flag", "reputation_update"],
        "qos": "exactly-once",
        "retention": "24h",
    },
    
    # === EXTERNAL CHANNELS ===
    "swarm.external.discord": {
        "description": "Discord integration",
        "subscribers": ["nexus", "echo"],
        "message_types": ["discord_message", "discord_command", "discord_response"],
    },
    
    "swarm.external.slack": {
        "description": "Slack integration",
        "subscribers": ["nexus", "echo"],
        "message_types": ["slack_message", "slack_command", "slack_response"],
    },
    
    "swarm.external.api": {
        "description": "External API requests",
        "subscribers": ["nexus"],
        "message_types": ["api_request", "api_response", "webhook_event"],
    },
}
```

### 3.2 Message Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MESSAGE FLOW ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EXTERNAL INPUT                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ Discord  │  │  Slack   │  │ Telegram │  │  Webhook │                    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │
│       │             │             │             │                            │
│       └─────────────┴─────────────┴─────────────┘                            │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    NEXUS (External Gateway)                          │   │
│  │                    Subject: swarm.external.*                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    STEWARD (Triage)                                  │   │
│  │                    Subject: swarm.internal.triage                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│       ┌───────────────────┼───────────────────┐                             │
│       ▼                   ▼                   ▼                             │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐                         │
│  │  Triad  │        │ Explore │        │  Safety │                         │
│  │ Channel │        │ Channel │        │ Channel │                         │
│  └────┬────┘        └────┬────┘        └────┬────┘                         │
│       │                  │                  │                               │
│       └──────────────────┼──────────────────┘                               │
│                          │                                                   │
│                          ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONSENSUS (MAKER)                                 │   │
│  │                    Subject: swarm.system.consensus                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                   │
│                          ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OUTPUT (Echo/Nexus)                               │   │
│  │                    Subject: swarm.external.*                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Message Type Definitions

```python
# Standardized message structure for all channels
@dataclass
class SwarmMessage:
    """Standard message format for all agent communication."""
    
    # Routing
    subject: str                    # NATS subject / channel
    correlation_id: str             # Unique message ID
    reply_to: Optional[str]         # Response subject (for request-reply)
    
    # Sender/Receiver
    sender_agent: str               # Sending agent ID
    target_agents: List[str]        # Target agent IDs (or ["*"] for broadcast)
    
    # Content
    message_type: str               # Type identifier
    content: Dict[str, Any]         # Message payload
    metadata: Dict[str, Any]        # Additional context
    
    # Timing
    timestamp: str                  # ISO8601 timestamp
    ttl_seconds: Optional[int]      # Time-to-live (optional)
    
    # Priority
    priority: str = "normal"        # low, normal, high, critical
    requires_ack: bool = False      # Require acknowledgment
    
    # Context
    workflow_id: Optional[str]      # Associated workflow
    task_id: Optional[str]          # Associated task
    session_id: Optional[str]       # User/session context
```

---

## 4. MCP Tools Integration

### 4.1 Recommended MCP Implementation

The codebase currently has a tool registry but no MCP (Model Context Protocol) implementation. I recommend adding MCP compatibility:

```python
# src/heretek_swarm/tools/mcp_tools.py

"""
MCP (Model Context Protocol) Tools for Heretek Swarm

Provides standardized tool interface for external AI systems
and agent-to-agent tool sharing.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json

@dataclass
class MCPToolDefinition:
    """MCP-compliant tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    category: str = "general"
    version: str = "1.0.0"


class MCPToolRegistry:
    """Registry for MCP-compatible tools."""
    
    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._tool_stats: Dict[str, Dict] = {}
    
    def register(self, tool: MCPToolDefinition) -> None:
        """Register an MCP tool."""
        self._tools[tool.name] = tool
        self._tool_stats[tool.name] = {
            "calls": 0,
            "errors": 0,
            "last_called": None,
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in MCP format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
                "category": t.category,
                "version": t.version,
            }
            for t in self._tools.values()
        ]
    
    async def invoke(
        self, 
        name: str, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Any:
        """Invoke an MCP tool."""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        
        tool = self._tools[name]
        self._tool_stats[name]["calls"] += 1
        self._tool_stats[name]["last_called"] = datetime.now(timezone.utc).isoformat()
        
        try:
            result = await tool.handler(arguments, context)
            return {"success": True, "result": result}
        except Exception as e:
            self._tool_stats[name]["errors"] += 1
            return {"success": False, "error": str(e)}
```

### 4.2 Core MCP Tools

| Tool Name | Category | Description | Input Schema |
|-----------|----------|-------------|--------------|
| `memory_store` | Memory | Store in collective memory | `{content: str, metadata: object, importance: number}` |
| `memory_retrieve` | Memory | Semantic memory search | `{query: str, limit: int, tier: string}` |
| `agent_message` | Communication | Send message to agent | `{target: str, type: str, content: object}` |
| `agent_handoff` | Communication | Transfer task context | `{to_agent: str, context: object, reason: str}` |
| `consensus_propose` | Consensus | Submit proposal | `{proposal: str, context: object, urgency: string}` |
| `consensus_vote` | Consensus | Cast vote | `{proposal_id: str, vote: string, confidence: number}` |
| `rag_query` | Knowledge | Query RAG system | `{query: str, top_k: int, filters: object}` |
| `rag_ingest` | Knowledge | Ingest document | `{content: str, source: str, metadata: object}` |
| `external_api` | Integration | HTTP API call | `{url: str, method: str, headers: object, body: object}` |
| `notification_send` | Integration | Send notification | `{channel: str, message: str, recipients: array}` |
| `workflow_start` | Orchestration | Start workflow | `{workflow_type: str, params: object}` |
| `workflow_status` | Orchestration | Check workflow status | `{workflow_id: str}` |

### 4.3 Tool Integration with Agents

```python
# Example: Agent using MCP tools
class AgentWithTools(AgentActor):
    """Agent with MCP tool access."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_registry = MCPToolRegistry()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default MCP tools."""
        from heretek_swarm.tools.mcp_tools import MCPToolDefinition
        
        # Memory tools
        self.mcp_registry.register(MCPToolDefinition(
            name="memory_store",
            description="Store information in collective memory",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "metadata": {"type": "object"},
                    "importance": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["content"]
            },
            handler=self._handle_memory_store,
            category="memory"
        ))
        
        # Add more tools...
    
    async def _handle_memory_store(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle memory store request."""
        content = arguments.get("content")
        metadata = arguments.get("metadata", {})
        importance = arguments.get("importance", 0.5)
        
        # Use existing memory system
        result = await self.memory.store(
            content={"text": content, **metadata},
            metadata={"importance": importance, "source": self.agent_id}
        )
        
        return {"memory_id": result.id, "stored_at": result.created_at}
```

---

## 5. Database/RAG Component Wiring

### 5.1 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DOCUMENT INGESTION                                │   │
│  │                                                                      │   │
│  │  External Sources → Perceiver → Document Processor → Chunks         │   │
│  │                                                                      │   │
│  │  Supported Formats:                                                  │   │
│  │  • Text (.txt, .md)                                                  │   │
│  │  • Code (.py, .js, .ts)                                              │   │
│  │  • JSON (.json)                                                      │   │
│  │  • HTML (.html)                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EMBEDDING GENERATION                              │   │
│  │                                                                      │   │
│  │  Chunks → Embedding Service → Vector Embeddings                     │   │
│  │                                                                      │   │
│  │  Providers:                                                          │   │
│  │  • OpenAI (text-embedding-3-small/large)                             │   │
│  │  • Local (sentence-transformers)                                     │   │
│  │  • Custom (configurable)                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    VECTOR STORAGE                                    │   │
│  │                                                                      │   │
│  │  Embeddings → Qdrant/Chroma → Indexed Vectors                       │   │
│  │                                                                      │   │
│  │  Metadata stored in: PostgreSQL                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    HYBRID RETRIEVAL                                  │   │
│  │                                                                      │   │
│  │  Query → [Vector Search + Keyword Search] → Rerank → Results        │   │
│  │                                                                      │   │
│  │  Retrieval Strategies:                                               │   │
│  │  • Pure Vector (cosine similarity)                                   │   │
│  │  • Pure Keyword (BM25)                                               │   │
│  │  • Hybrid (weighted combination)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONTEXT ASSEMBLY                                  │   │
│  │                                                                      │   │
│  │  Results → Token-Aware Assembly → LLM Context                       │   │
│  │                                                                      │   │
│  │  Features:                                                           │   │
│  │  • Configurable max tokens                                           │   │
│  │  • Source attribution                                                │   │
│  │  • Metadata inclusion                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Agent-RAG Integration Points

| Agent | RAG Integration | Use Case |
|-------|----------------|----------|
| **Historian** | Primary consumer | Long-term memory storage, semantic retrieval |
| **Explorer** | Query consumer | Research, information gathering |
| **Examiner** | Query consumer | Fact-checking, verification |
| **Alpha** | Query consumer | Analysis with context |
| **Beta** | Query consumer | Validation against knowledge |
| **Charlie** | Query consumer | Risk assessment with historical data |
| **Perceiver+** | Query + Ingest | Analytics on stored data |
| **Nexus** | Ingest producer | External document ingestion |
| **Echo** | Query consumer | Context for communications |

### 5.3 Memory-RAG Integration

```python
# Recommended integration pattern
class UnifiedKnowledgeAccess:
    """Unified interface for memory and RAG queries."""
    
    def __init__(self, memory_system, rag_pipeline):
        self.memory = memory_system
        self.rag = rag_pipeline
    
    async def query(
        self,
        query: str,
        sources: List[str] = ["memory", "rag"],
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Query both memory and RAG, merge results."""
        results = {
            "memory": [],
            "rag": [],
            "merged": [],
        }
        
        if "memory" in sources:
            memory_results = await self.memory.query(
                query_text=query,
                limit=limit,
            )
            results["memory"] = [
                {
                    "source": "memory",
                    "content": entry.content,
                    "metadata": entry.metadata,
                    "score": getattr(entry, "similarity", 0),
                }
                for entry in memory_results.entries
            ]
        
        if "rag" in sources:
            rag_result = await self.rag.query(
                query=query,
                top_k=limit,
            )
            results["rag"] = [
                {
                    "source": "rag",
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": doc.score,
                }
                for doc in rag_result.documents
            ]
        
        # Merge and rerank
        all_results = results["memory"] + results["rag"]
        results["merged"] = sorted(
            all_results,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:limit]
        
        return results
```

### 5.4 Database Schema Recommendations

```sql
-- Persistent Memory (PostgreSQL with pgvector)
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content JSONB NOT NULL,
    metadata JSONB,
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    agent_id VARCHAR(255),
    workflow_id VARCHAR(255),
    session_id VARCHAR(255),
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ
);

CREATE INDEX idx_memory_embedding ON memory_entries USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_memory_agent ON memory_entries(agent_id);
CREATE INDEX idx_memory_workflow ON memory_entries(workflow_id);
CREATE INDEX idx_memory_expires ON memory_entries(expires_at);

-- RAG Documents
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_path VARCHAR(1024),
    source_type VARCHAR(50),
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES rag_documents(id),
    chunk_index INTEGER,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops);

-- Consensus History
CREATE TABLE consensus_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consensus_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    decision VARCHAR(512) NOT NULL,
    confidence FLOAT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_consensus_id ON consensus_votes(consensus_id);
CREATE INDEX idx_consensus_agent ON consensus_votes(agent_id);

-- Workflow State
CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_type VARCHAR(255) NOT NULL,
    topic TEXT,
    state VARCHAR(50) NOT NULL,
    context JSONB,
    result JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms FLOAT
);

CREATE INDEX idx_workflow_state ON workflow_states(state);
CREATE INDEX idx_workflow_type ON workflow_states(workflow_type);
```

---

## 6. Autonomous Loop Entry Point

### 6.1 Recommended Entry Point

```python
# src/heretek_swarm/runtime/autonomous_entrypoint.py

"""
Autonomous Loop Entry Point

24/7 continuous operation entry point for Heretek Swarm.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import structlog

from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.gateway.nats_event_mesh import NATSEventMesh
from heretek_swarm.memory.unified import DualTierMemory
from heretek_swarm.rag.rag_pipeline import RAGPipeline
from heretek_swarm.consensus.maker import MAKERConsensus
from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow
from heretek_swarm.tools.mcp_tools import MCPToolRegistry

logger = structlog.get_logger(__name__)


class AutonomousSwarm:
    """
    Main entry point for autonomous 24/7 swarm operation.
    
    Coordinates all components into a unified autonomous loop.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Core components
        self.supervisor: Optional[ActorSupervisor] = None
        self.event_mesh: Optional[NATSEventMesh] = None
        self.memory: Optional[DualTierMemory] = None
        self.rag: Optional[RAGPipeline] = None
        self.consensus: Optional[MAKERConsensus] = None
        self.mcp_registry: Optional[MCPToolRegistry] = None
        
        # State
        self._running = False
        self._health_check_interval = config.get("health_check_interval", 30)
        self._loop_interval = config.get("loop_interval", 1)
    
    async def initialize(self) -> None:
        """Initialize all swarm components."""
        logger.info("initializing_autonomous_swarm")
        
        # Initialize event mesh (NATS)
        self.event_mesh = NATSEventMesh(
            servers=self.config.get("nats_servers", ["nats://localhost:4222"]),
            fallback=True,
        )
        await self.event_mesh.connect()
        
        # Initialize memory
        self.memory = DualTierMemory(
            ephemeral_config=self.config.get("ephemeral", {}),
            persistent_config=self.config.get("persistent", {}),
        )
        await self.memory.initialize()
        
        # Initialize RAG
        self.rag = RAGPipeline(
            config=self.config.get("rag", {}),
            memory_backend=self.memory,
        )
        await self.rag.initialize()
        
        # Initialize consensus
        self.consensus = MAKERConsensus(
            ahead_by_k=self.config.get("consensus", {}).get("ahead_by_k", 2),
            min_votes=self.config.get("consensus", {}).get("min_votes", 3),
        )
        
        # Initialize MCP registry
        self.mcp_registry = MCPToolRegistry()
        
        # Initialize supervisor and spawn actors
        self.supervisor = ActorSupervisor()
        await self._spawn_all_actors()
        
        logger.info("autonomous_swarm_initialized")
    
    async def _spawn_all_actors(self) -> None:
        """Spawn all 23 agents."""
        from heretek_swarm.actors.triad import StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
        from heretek_swarm.actors.historian import HistorianAgent
        # ... import all agents
        
        actors = [
            (StewardAgent, "steward", ["triad", "coordination"]),
            (AlphaAgent, "alpha", ["analysis", "decisions"]),
            (BetaAgent, "beta", ["validation", "quality"]),
            (CharlieAgent, "charlie", ["risk", "challenges"]),
            (HistorianAgent, "historian", ["memory", "context"]),
            # ... add all 23 agents
        ]
        
        for agent_class, agent_id, topics in actors:
            agent = agent_class(
                agent_id=agent_id,
                name=agent_id.capitalize(),
                topics=topics,
                memory=self.memory,
            )
            await self.supervisor.spawn_actor_instance(agent, agent_id)
            logger.info("actor_spawned", agent_id=agent_id)
    
    async def run(self) -> None:
        """Main autonomous loop - runs 24/7."""
        logger.info("starting_autonomous_loop")
        self._running = True
        
        # Health check task
        health_task = asyncio.create_task(self._health_monitor())
        
        # Main loop
        while self._running:
            try:
                await self._process_cycle()
                await asyncio.sleep(self._loop_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("autonomous_loop_error", error=str(e))
                await asyncio.sleep(5)  # Backoff on error
        
        # Cleanup
        self._running = False
        health_task.cancel()
        await self.shutdown()
    
    async def _process_cycle(self) -> None:
        """Process one cycle of the autonomous loop."""
        # 1. Check for scheduled tasks (Chronos)
        await self._process_scheduled_tasks()
        
        # 2. Check for external events (Nexus/Echo)
        await self._process_external_events()
        
        # 3. Process pending workflows
        await self._process_workflows()
        
        # 4. Run health checks
        await self._run_health_checks()
    
    async def _process_scheduled_tasks(self) -> None:
        """Process tasks scheduled by Chronos."""
        # Query memory for scheduled tasks
        # Trigger appropriate agents
        pass
    
    async def _process_external_events(self) -> None:
        """Process external events from Discord, Slack, webhooks."""
        # Check event mesh for external messages
        # Route through Steward for triage
        pass
    
    async def _process_workflows(self) -> None:
        """Process pending workflows."""
        # Check for workflows needing execution
        # Execute HeavySwarm workflows as needed
        pass
    
    async def _run_health_checks(self) -> None:
        """Run health checks on all actors."""
        for agent_id, actor in self.supervisor.actors.items():
            status = actor.get_status()
            if status.state.value == "error":
                logger.warning("actor_error", agent_id=agent_id)
                await self.supervisor.restart_actor(agent_id)
    
    async def _health_monitor(self) -> None:
        """Continuous health monitoring."""
        while self._running:
            try:
                # Publish health metrics
                health_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "active_actors": len(self.supervisor.actors),
                    "mailbox_sizes": {
                        agent_id: actor.mailbox_size 
                        for agent_id, actor in self.supervisor.actors.items()
                    },
                }
                
                await self.event_mesh.publish(
                    "swarm.system.health",
                    health_data,
                )
                
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("health_monitor_error", error=str(e))
    
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("shutting_down_autonomous_swarm")
        
        if self.supervisor:
            await self.supervisor.terminate_all()
        
        if self.event_mesh:
            await self.event_mesh.disconnect()
        
        if self.rag:
            await self.rag.shutdown()
        
        logger.info("autonomous_swarm_shutdown_complete")


# Entry point
async def main():
    """Main entry point."""
    config = {
        "nats_servers": ["nats://localhost:4222"],
        "health_check_interval": 30,
        "loop_interval": 1,
        "ephemeral": {"ttl_seconds": 3600},
        "persistent": {
            "connection_string": "postgresql://user:pass@localhost/heretek_swarm",
        },
        "rag": {
            "embedding_provider": "openai",
            "collection_name": "heretek_documents",
        },
        "consensus": {
            "ahead_by_k": 2,
            "min_votes": 3,
        },
    }
    
    swarm = AutonomousSwarm(config)
    await swarm.initialize()
    await swarm.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Docker/Systemd Integration

```dockerfile
# Dockerfile for autonomous operation
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Run autonomous entry point
CMD ["python", "-m", "heretek_swarm.runtime.autonomous_entrypoint"]
```

```ini
# /etc/systemd/system/heretek-swarm.service
[Unit]
Description=Heretek Swarm Autonomous AI Cluster
After=network.target nats-server.service postgresql.service

[Service]
Type=simple
User=heretek
WorkingDirectory=/opt/heretek-swarm
Environment=PATH=/opt/heretek-swarm/.venv/bin
ExecStart=/opt/heretek-swarm/.venv/bin/python -m heretek_swarm.runtime.autonomous_entrypoint
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 7. Summary: Key Wiring Decisions

### 7.1 Critical Recommendations

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Event Bus** | Use NATS JetStream as primary | Persistent, scalable, request-reply support |
| **Memory** | Dual-tier (Redis + PostgreSQL) | Fast ephemeral + persistent semantic search |
| **RAG** | Qdrant/Chroma for vectors | Industry standard, good performance |
| **Consensus** | MAKER with reputation weighting | Proven algorithm, handles disagreement |
| **Tools** | MCP-compatible registry | External compatibility, standardization |
| **Entry Point** | `autonomous_entrypoint.py` | Clear 24/7 operation entry |
| **Channels** | NATS subjects by tier | Organized, scalable routing |
| **Health** | Continuous monitoring + auto-restart | Self-healing operation |

### 7.2 Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | NATS JetStream integration | Medium | High |
| P0 | Autonomous entry point | Low | High |
| P1 | MCP tool registry | Medium | High |
| P1 | Channel subscription system | Low | Medium |
| P2 | Agent wiring (18 remaining) | High | High |
| P2 | Unified knowledge access | Medium | Medium |
| P3 | Database migrations | Low | Medium |
| P3 | Docker/systemd configs | Low | Medium |

### 7.3 Wiring Checklist

- [ ] Configure NATS JetStream streams for all channels
- [ ] Implement channel subscription in all 23 agents
- [ ] Create MCP tool registry with 10+ core tools
- [ ] Wire Historian to RAG pipeline
- [ ] Wire Steward to task routing logic
- [ ] Wire MAKER consensus to Triad agents
- [ ] Implement unified knowledge access layer
- [ ] Create autonomous entry point script
- [ ] Add health monitoring with auto-restart
- [ ] Configure database migrations
- [ ] Create Docker deployment configs
- [ ] Set up systemd service for 24/7 operation

---

## Appendix A: File Reference Map

| Component | Primary File | Secondary Files |
|-----------|-------------|-----------------|
| Agent Base | `actors/base.py` | `actors/supervisor.py`, `actors/validation.py` |
| Triad | `actors/triad.py` | `consensus/maker.py` |
| Historian | `actors/historian.py` | `memory/unified.py`, `rag/rag_pipeline.py` |
| Event Mesh | `gateway/nats_event_mesh.py` | `gateway/event_mesh.py`, `gateway/a2a_protocol.py` |
| Memory | `memory/unified.py` | `memory/ephemeral.py`, `memory/persistent.py` |
| RAG | `rag/rag_pipeline.py` | `rag/embedding_service.py`, `rag/retriever.py` |
| Consensus | `consensus/maker.py` | `orchestration/heavyswarm.py` |
| Tools | `tools/registry.py` | `runtime/tools.py` |
| Runtime | `runtime/autonomous_runtime.py` | `runtime/characters/` |
| Workflow | `workflow/engine.py` | `orchestration/heavyswarm.py` |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **A2A** | Agent-to-Agent communication protocol |
| **MAKER** | Multi-Agent Knowledge Extraction & Reasoning consensus algorithm |
| **MCP** | Model Context Protocol - standardized tool interface |
| **NATS** | High-performance messaging system |
| **JetStream** | NATS persistent streaming layer |
| **RAG** | Retrieval-Augmented Generation |
| **GWT** | Global Workspace Theory (consciousness) |
| **IIT** | Integrated Information Theory (consciousness) |
| **AST** | Attention Schema Theory (consciousness) |
| **FEP** | Free Energy Principle (consciousness) |

---

**Document Version:** 1.0.0  
**Tracking ID:** QWEN  
**Generated:** 2026-04-06  
**Next Review:** After implementation of P0 items
