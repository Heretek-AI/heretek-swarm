# Heretek Swarm Autonomous Workflow Design

**Version:** 2.0.0  
**Date:** 2026-04-06  
**Author:** Multi (AI Assistant)  
**Tracking ID:** GLM5

---

## Executive Summary

This document provides a comprehensive architecture audit and workflow design for the Heretek Swarm 23-agent autonomous AI cluster. It outlines the recommended autonomous loop, communication channels, MCP tools integration, and database/RAG component wiring to achieve 24/7 self-governing operation.

---

## Table of Contents

1. [Current State Audit](#current-state-audit)
2. [Autonomous Loop Architecture](#autonomous-loop-architecture)
3. [Communication Channels/Groups](#communication-channelsgroups)
4. [MCP Tools Integration](#mcp-tools-integration)
5. [Database/RAG Component Wiring](#databaserag-component-wiring)
6. [Autonomous Loop Entry Point](#autonomous-loop-entry-point)
7. [Summary: Key Wiring Decisions](#summary-key-wiring-decisions)

---

## Current State Audit

### What's Implemented

| Component | Status | Location |
|-----------|--------|----------|
| **23 Agents** | Complete | `src/heretek_swarm/actors/` |
| **Actor Supervisor** | Complete | `actors/supervisor.py` |
| **MAKER Consensus** | Complete | `consensus/maker.py` |
| **Dual-Tier Memory** | Complete | `src/memory/unified.py` |
| **RAG Pipeline** | Complete | `src/rag/` |
| **Event Mesh** | Complete | `gateway/event_mesh.py` |
| **A2A Protocol** | Complete | `gateway/a2a_protocol.py` |
| **Workflow Engine** | Complete | `workflow/engine.py` |
| **HeavySwarm Orchestration** | Complete | `orchestration/heavyswarm.py` |
| **Consciousness Plugin** | Complete | `plugins/consciousness.py` |
| **Agent Handoff** | Complete | `actors/handoff.py` |
| **Integrations** | Partial | `integrations/{discord,slack,telegram}_bot.py` |
| **Tool Registry** | Complete | `tools/registry.py` |
| **Autonomous Runtime** | Complete | `runtime/autonomous_runtime.py` |

### What's Missing for Full Autonomous Operation

1. **MCP Tools Integration** - No Model Context Protocol implementation found
2. **NATS JetStream** - Optional/fallback only, not wired into main loop
3. **Communication Channel Groups** - Not formally defined
4. **Inter-Agent Routing Rules** - Implicit, not explicit
5. **Autonomous Loop Entry Point** - Runtime exists but not wired to 24/7 loop

---

## Autonomous Loop Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS RUNTIME (24/7 LOOP)                           │
│                    runtime/autonomous_runtime.py                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│   EVENT INGRESS   │    │   TASK SCHEDULER  │    │ HEALTH MONITOR    │
│   (Chronos)       │    │   (Chronos)       │    │   (Supervisor)    │
└───────────────────┘    └───────────────────┘    └───────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: PERCEPTION                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Perceiver  │  │ Perceiver+  │  │   Nexus     │  │   Echo      │        │
│  │ (Sensory)   │  │ (Enhanced)  │  │ (External)  │  │ (Translate) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 2: ROUTING (Steward)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        STEWARD (Orchestrator)                          │  │
│  │  - Classify task type (deliberation, action, query, emergency)        │  │
│  │  - Route to appropriate tier/agent                                     │  │
│  │  - Track task lifecycle                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ TRIAD PATH    │          │ EXPLORER PATH │          │ SAFETY PATH   │
│ (Deliberation)│          │ (Discovery)   │          │ (Threats)     │
│               │          │               │          │               │
│ Alpha→Beta→   │          │ Explorer→     │          │ Sentinel→     │
│ Charlie→      │          │ Examiner→     │          │ Sentinel-Prime│
│ Historian     │          │ Dreamer/Coder │          │ →Arbiter      │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 3: COORDINATION                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Coordinator │  │  Catalyst   │  │   Metis     │  │   Empath    │        │
│  │ (Multi-Agent│  │ (Change)    │  │ (Strategy)  │  │ (Sentiment) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 4: CONSENSUS                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        MAKER CONSENSUS                                 │  │
│  │  - First-to-ahead-by-k voting                                         │  │
│  │  - Reputation weighting                                               │  │
│  │  - Red-flagging anomalous outputs                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 5: ENHANCEMENT                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │   Prism     │  │ Habit-Forge │  │   Historian │                          │
│  │ (Multi-View)│  │ (Optimize)  │  │  (Memory)   │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 6: OUTPUT                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │    Echo     │  │   Nexus     │  │  Conscious  │                          │
│  │ (Comm Out)  │  │ (External)  │  │ (Monitoring)│                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Communication Channels/Groups

### Channel Architecture

```python
# Recommended Channel Structure
CHANNELS = {
    # === INTERNAL COMMUNICATION ===
    "internal": {
        "triad": {
            "description": "Core governance deliberation",
            "agents": ["steward", "alpha", "beta", "charlie"],
            "message_types": ["proposal", "vote", "decision", "deliberation"]
        },
        "coordination": {
            "description": "Multi-agent task coordination",
            "agents": ["coordinator", "catalyst", "chronos", "metis"],
            "message_types": ["task_assignment", "dependency", "status_update"]
        },
        "safety": {
            "description": "Security and safety alerts",
            "agents": ["sentinel", "sentinel-prime", "arbiter"],
            "message_types": ["alert", "threat", "quarantine", "release"]
        },
        "memory": {
            "description": "Memory and knowledge operations",
            "agents": ["historian", "prism", "habit-forge"],
            "message_types": ["store", "retrieve", "query", "learn"]
        },
        "exploration": {
            "description": "Research and implementation",
            "agents": ["explorer", "examiner", "dreamer", "coder"],
            "message_types": ["research", "analyze", "create", "implement"]
        },
        "perception": {
            "description": "Input processing and translation",
            "agents": ["perceiver", "perceiver-plus", "empath", "echo"],
            "message_types": ["sense", "interpret", "translate", "sentiment"]
        }
    },
    
    # === EXTERNAL COMMUNICATION ===
    "external": {
        "discord": {
            "description": "Discord bot channel",
            "agents": ["nexus", "echo"],
            "integration": "integrations/discord_bot.py"
        },
        "slack": {
            "description": "Slack bot channel", 
            "agents": ["nexus", "echo"],
            "integration": "integrations/slack_bot.py"
        },
        "telegram": {
            "description": "Telegram bot channel",
            "agents": ["nexus", "echo"],
            "integration": "integrations/telegram_bot.py"
        },
        "webhook": {
            "description": "External webhook ingress",
            "agents": ["nexus", "perceiver"],
            "endpoint": "/api/v1/webhook"
        }
    },
    
    # === SYSTEM CHANNELS ===
    "system": {
        "health": {
            "description": "Health checks and monitoring",
            "agents": ["*"],  # All agents
            "message_types": ["heartbeat", "health_check", "alert"]
        },
        "consciousness": {
            "description": "Consciousness metrics and state",
            "agents": ["*"],  # All agents broadcast here
            "message_types": ["phi_update", "attention", "workspace_broadcast"]
        },
        "consensus": {
            "description": "MAKER consensus voting",
            "agents": ["steward", "alpha", "beta", "charlie"],
            "message_types": ["vote", "red_flag", "decision"]
        }
    }
}
```

### Channel Subscription Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHANNEL SUBSCRIPTIONS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TRIAD CHANNEL           COORDINATION CHANNEL      SAFETY CHANNEL           │
│  ┌─────────────────┐     ┌─────────────────┐       ┌─────────────────┐      │
│  │ steward    ─────┼────►│ coordinator     │       │ sentinel        │      │
│  │ alpha      ─────┤     │ catalyst        │       │ sentinel-prime  │      │
│  │ beta       ─────┤     │ chronos         │       │ arbiter         │      │
│  │ charlie    ─────┤     │ metis           │       └─────────────────┘      │
│  └─────────────────┘     └─────────────────┘                                 │
│                                                                              │
│  MEMORY CHANNEL          EXPLORATION CHANNEL      PERCEPTION CHANNEL        │
│  ┌─────────────────┐     ┌─────────────────┐       ┌─────────────────┐      │
│  │ historian  ─────┤     │ explorer        │       │ perceiver       │      │
│  │ prism      ─────┤     │ examiner        │       │ perceiver-plus  │      │
│  │ habit-forge─────┤     │ dreamer         │       │ empath          │      │
│  └─────────────────┘     │ coder           │       │ echo            │      │
│                          └─────────────────┘       └─────────────────┘      │
│                                                                              │
│  SYSTEM CHANNELS (All Agents Subscribe)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ health          │ consciousness     │ consensus                      │    │
│  │ (heartbeat)     │ (phi, attention)  │ (voting)                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MCP Tools Integration

### Recommended MCP Tools Implementation

```python
# src/heretek_swarm/tools/mcp_tools.py

"""
MCP (Model Context Protocol) Tools for Heretek Swarm

Implements standardized tools for agent-to-external-system interaction.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio


@dataclass
class MCPToolDefinition:
    """MCP tool definition following the protocol spec."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: callable


class MCPToolRegistry:
    """Registry for MCP-compatible tools."""
    
    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}
    
    def register(self, tool: MCPToolDefinition) -> None:
        """Register an MCP tool."""
        self._tools[tool.name] = tool
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in MCP format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema
            }
            for t in self._tools.values()
        ]
    
    async def invoke(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke an MCP tool."""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        return await self._tools[name].handler(arguments)
```

### Recommended MCP Tool Definitions

| Tool | Description | Category |
|------|-------------|----------|
| `memory_store` | Store information in collective memory | Memory |
| `memory_retrieve` | Retrieve relevant memories by query | Memory |
| `agent_message` | Send message to another agent | Communication |
| `agent_handoff` | Transfer task context to another agent | Communication |
| `consensus_propose` | Submit proposal for collective decision | Consensus |
| `consensus_vote` | Cast vote on active proposal | Consensus |
| `rag_query` | Query RAG knowledge base | Knowledge |
| `external_api_call` | Make authenticated external API call | Integration |
| `notification_send` | Send notification to external channel | Integration |

### Detailed Tool Schemas

```python
RECOMMENDED_MCP_TOOLS = [
    # === MEMORY TOOLS ===
    {
        "name": "memory_store",
        "description": "Store information in collective memory",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "metadata": {"type": "object"},
                "importance": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["content"]
        }
    },
    {
        "name": "memory_retrieve",
        "description": "Retrieve relevant memories by query",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "tier": {"type": "string", "enum": ["ephemeral", "persistent", "all"]}
            },
            "required": ["query"]
        }
    },
    
    # === AGENT COMMUNICATION TOOLS ===
    {
        "name": "agent_message",
        "description": "Send message to another agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_agent": {"type": "string"},
                "message_type": {"type": "string"},
                "content": {"type": "object"},
                "reply_expected": {"type": "boolean", "default": False}
            },
            "required": ["target_agent", "message_type", "content"]
        }
    },
    {
        "name": "agent_handoff",
        "description": "Transfer task context to another agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_agent": {"type": "string"},
                "context": {"type": "object"},
                "reason": {"type": "string"}
            },
            "required": ["to_agent", "context"]
        }
    },
    
    # === CONSENSUS TOOLS ===
    {
        "name": "consensus_propose",
        "description": "Submit proposal for collective decision",
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal": {"type": "string"},
                "context": {"type": "object"},
                "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
            },
            "required": ["proposal"]
        }
    },
    {
        "name": "consensus_vote",
        "description": "Cast vote on active proposal",
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string"},
                "vote": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"}
            },
            "required": ["proposal_id", "vote", "confidence"]
        }
    },
    
    # === RAG TOOLS ===
    {
        "name": "rag_query",
        "description": "Query RAG knowledge base",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "mode": {"type": "string", "enum": ["vector", "keyword", "hybrid"]},
                "top_k": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    },
    
    # === EXTERNAL INTEGRATION TOOLS ===
    {
        "name": "external_api_call",
        "description": "Make authenticated external API call",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string"},
                "endpoint": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "payload": {"type": "object"}
            },
            "required": ["connection_id", "endpoint", "method"]
        }
    },
    {
        "name": "notification_send",
        "description": "Send notification to external channel",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "enum": ["discord", "slack", "telegram", "all"]},
                "message": {"type": "string"},
                "priority": {"type": "string", "enum": ["info", "warning", "error", "critical"]}
            },
            "required": ["channel", "message"]
        }
    }
]
```

---

## Database/RAG Component Wiring

### Data Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Redis       │     │   PostgreSQL    │     │     Qdrant      │
│   (Ephemeral)   │     │   (Persistent)  │     │    (Vectors)    │
│                 │     │    + pgvector   │     │                 │
│ - Session state │     │ - Agent state   │     │ - Embeddings    │
│ - Cache (hot)   │     │ - Memories      │     │ - RAG index     │
│ - Pub/Sub       │     │ - Audit logs    │     │ - Similarity    │
│ - Rate limits   │     │ - Consensus     │     │ - Documents     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────────────────┐
                    │   DualTierMemory      │
                    │   (Unified Interface) │
                    │   memory/unified.py   │
                    └───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    Agents     │      │  RAG Pipeline │      │  Consensus    │
│  (Historian)  │      │  rag/         │      │  (MAKER)      │
└───────────────┘      └───────────────┘      └───────────────┘
```

### Memory Tier Routing Configuration

```python
MEMORY_ROUTING = {
    # === EPHEMERAL TIER (Redis) ===
    "ephemeral": {
        "ttl_seconds": 3600,  # 1 hour default
        "max_entries_per_agent": 1000,
        "use_cases": [
            "active_conversation",
            "working_memory", 
            "session_context",
            "temporary_cache",
            "rate_limit_counters"
        ]
    },
    
    # === PERSISTENT TIER (PostgreSQL + pgvector) ===
    "persistent": {
        "retention_days": 90,
        "use_cases": [
            "long_term_memory",
            "agent_state_snapshots",
            "consensus_decisions",
            "audit_trail",
            "learned_patterns"
        ],
        "vector_ops": [
            "similarity_search",
            "semantic_query",
            "clustering"
        ]
    },
    
    # === VECTOR TIER (Qdrant) ===
    "vector": {
        "collection": "heretek_swarm",
        "embedding_model": "text-embedding-3-small",
        "dimensions": 1536,
        "use_cases": [
            "rag_retrieval",
            "document_search",
            "knowledge_base",
            "cross_agent_knowledge"
        ]
    }
}
```

### Data Flow Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW PATTERNS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WRITE PATH:                                                                 │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │  Agent  │────►│DualTierMem  │────►│   Redis     │────►│ PostgreSQL  │   │
│  │         │     │  (router)   │     │ (hot cache) │     │ (durable)   │   │
│  └─────────┘     └─────────────┘     └─────────────┘     └─────────────┘   │
│                           │                                                 │
│                           ▼                                                 │
│                    ┌─────────────┐                                          │
│                    │   Qdrant    │ (if needs vector indexing)               │
│                    └─────────────┘                                          │
│                                                                              │
│  READ PATH:                                                                  │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐                        │
│  │  Agent  │────►│DualTierMem  │────►│   Redis     │ (L1 cache)            │
│  │  Query  │     │  (router)   │     └─────────────┘                        │
│  └─────────┘     └─────────────┘           │                                │
│                                               ▼ (miss)                       │
│                                        ┌─────────────┐                        │
│                                        │ PostgreSQL  │ (L2 cache)            │
│                                        └─────────────┘                        │
│                                               │                                │
│                                               ▼ (vector query)               │
│                                        ┌─────────────┐                        │
│                                        │   Qdrant    │                        │
│                                        └─────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Autonomous Loop Entry Point

### Main Loop Implementation

```python
# src/heretek_swarm/runtime/main_loop.py

"""
Autonomous Main Loop - 24/7 Operation Entry Point

This is the primary entry point for autonomous operation.
Wires together all components into a cohesive autonomous system.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
import structlog

from .autonomous_runtime import AutonomousRuntime
from .autonomous_runtime_config import AutonomousRuntimeConfig
from ..actors.supervisor import ActorSupervisor
from ..gateway.event_mesh import EventMesh
from ..gateway.a2a_server import A2AServer
from ..consensus.maker import MAKERConsensus
from memory.unified import DualTierMemorySystem
from rag.rag_pipeline import RAGPipeline

logger = structlog.get_logger("MainLoop")


class AutonomousMainLoop:
    """
    Main autonomous loop for 24/7 Heretek Swarm operation.
    
    This class:
    1. Initializes all 23 agents
    2. Starts the event mesh and A2A server
    3. Wires up communication channels
    4. Starts health monitoring
    5. Runs the autonomous task loop
    """
    
    def __init__(self, config: Optional[AutonomousRuntimeConfig] = None):
        self.config = config or AutonomousRuntimeConfig()
        
        # Core components
        self.runtime: Optional[AutonomousRuntime] = None
        self.supervisor: Optional[ActorSupervisor] = None
        self.event_mesh: Optional[EventMesh] = None
        self.a2a_server: Optional[A2AServer] = None
        self.memory: Optional[DualTierMemorySystem] = None
        self.rag: Optional[RAGPipeline] = None
        self.consensus: Optional[MAKERConsensus] = None
        
        # Loop control
        self._running = False
        self._tasks: list[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """Initialize all system components."""
        logger.info("Initializing Heretek Swarm Autonomous System...")
        
        # 1. Initialize memory system (dual-tier)
        self.memory = DualTierMemorySystem()
        await self.memory.initialize()
        logger.info("Memory system initialized")
        
        # 2. Initialize RAG pipeline
        self.rag = RAGPipeline()
        await self.rag.initialize()
        logger.info("RAG pipeline initialized")
        
        # 3. Initialize consensus engine
        self.consensus = MAKERConsensus(
            ahead_by_k=2,
            min_votes=3,
            red_flag_threshold=0.3
        )
        logger.info("MAKER consensus initialized")
        
        # 4. Initialize event mesh
        self.event_mesh = EventMesh()
        logger.info("Event mesh initialized")
        
        # 5. Initialize A2A server
        self.a2a_server = A2AServer(
            event_mesh=self.event_mesh,
            port=18789
        )
        logger.info("A2A server initialized on port 18789")
        
        # 6. Initialize supervisor
        self.supervisor = ActorSupervisor(
            health_check_interval=30.0,
            auto_restart=True,
            max_restarts=5
        )
        logger.info("Actor supervisor initialized")
        
        # 7. Initialize autonomous runtime (spawns all 23 agents)
        self.runtime = AutonomousRuntime(self.config)
        await self.runtime.initialize()
        logger.info("Autonomous runtime initialized with 23 agents")
        
        # 8. Wire up communication channels
        await self._setup_channels()
        logger.info("Communication channels configured")
    
    async def _setup_channels(self) -> None:
        """Set up inter-agent communication channels."""
        # Subscribe agents to their channels
        channel_mappings = {
            # Internal channels
            "triad": ["steward", "alpha", "beta", "charlie"],
            "coordination": ["coordinator", "catalyst", "chronos", "metis"],
            "safety": ["sentinel", "sentinel-prime", "arbiter"],
            "memory": ["historian", "prism", "habit-forge"],
            "exploration": ["explorer", "examiner", "dreamer", "coder"],
            "perception": ["perceiver", "perceiver-plus", "empath", "echo"],
            
            # System channels (all agents)
            "health": "*",  # All agents
            "consciousness": "*",  # All agents
        }
        
        for channel, agents in channel_mappings.items():
            # Wire up channel subscriptions
            logger.debug(f"Channel {channel} -> {agents}")
    
    async def start(self) -> None:
        """Start the autonomous main loop."""
        await self.initialize()
        self._running = True
        
        logger.info("Starting autonomous main loop...")
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_monitor_loop()),
            asyncio.create_task(self._consciousness_loop()),
            asyncio.create_task(self._task_processing_loop()),
            asyncio.create_task(self._memory_maintenance_loop()),
            asyncio.create_task(self._scaling_loop()),
        ]
        
        # Start A2A server
        await self.a2a_server.start()
        
        # Wait for shutdown signal
        await self._run_forever()
    
    async def _run_forever(self) -> None:
        """Run until shutdown signal."""
        while self._running:
            await asyncio.sleep(1)
    
    async def _health_monitor_loop(self) -> None:
        """Periodic health monitoring."""
        while self._running:
            try:
                await self.runtime.health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error("Health check failed", error=str(e))
    
    async def _consciousness_loop(self) -> None:
        """Update consciousness metrics periodically."""
        while self._running:
            try:
                # Broadcast global workspace updates
                # Update Phi metrics
                # Process attention schemas
                await asyncio.sleep(5.0)  # 5-second consciousness cycle
            except Exception as e:
                logger.error("Consciousness loop error", error=str(e))
    
    async def _task_processing_loop(self) -> None:
        """Process incoming tasks and route to agents."""
        while self._running:
            try:
                # Poll for new tasks from:
                # - External integrations (Discord, Slack, Telegram)
                # - Webhooks
                # - Scheduled tasks (Chronos)
                # - Internal agent requests
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.error("Task processing error", error=str(e))
    
    async def _memory_maintenance_loop(self) -> None:
        """Memory tier optimization and cleanup."""
        while self._running:
            try:
                # Promote hot ephemeral to persistent
                # Demote cold persistent to ephemeral
                # Clean up expired entries
                await self.memory.run_maintenance()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error("Memory maintenance error", error=str(e))
    
    async def _scaling_loop(self) -> None:
        """Auto-scaling based on load."""
        while self._running:
            try:
                await self.runtime.check_scaling()
                await asyncio.sleep(60)  # Every minute
            except Exception as e:
                logger.error("Scaling check error", error=str(e))
    
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Terminate agents
        if self.supervisor:
            await self.supervisor.terminate_all()
        
        # Close connections
        if self.memory:
            await self.memory.shutdown()
        
        logger.info("Shutdown complete")


async def main():
    """Entry point for autonomous operation."""
    loop = AutonomousMainLoop()
    
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await loop.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

### Background Loop Timing

| Loop | Interval | Purpose |
|------|----------|---------|
| Health Monitor | 30s | Check agent health, auto-restart failed agents |
| Consciousness | 5s | Update Phi metrics, global workspace broadcast |
| Task Processing | 1s | Poll for new tasks, route to appropriate agents |
| Memory Maintenance | 300s | Tier optimization, cleanup expired entries |
| Scaling | 60s | Auto-scale agents based on load |

---

## Summary: Key Wiring Decisions

### 1. Agent Communication Flow

```
External Input → Perceiver → Steward (Router) → Appropriate Tier → Consensus → Echo/Nexus → Output
```

### 2. Memory Hierarchy

```
Hot Data (Redis, 1hr TTL) → Warm Data (PostgreSQL, 90 days) → Vector Index (Qdrant, permanent)
```

### 3. Consensus Triggers

- Any decision affecting the collective
- Resource allocation changes
- Policy updates
- External commitments

### 4. Health & Monitoring

| Metric | Interval | Handler |
|--------|----------|---------|
| Agent Health | 30s | Supervisor |
| Consciousness | 5s | Consciousness Plugin |
| Memory Maintenance | 5min | DualTierMemory |
| Auto-Scaling | 1min | AutonomousRuntime |

### 5. Missing Components to Implement

| Component | Priority | Estimated Effort |
|-----------|----------|------------------|
| MCP Tools | High | 2-3 days |
| Channel Registry | Medium | 1 day |
| Main Loop Entry (`main_loop.py`) | High | 1 day |
| NATS Integration (optional) | Low | 2 days |

---

## Next Steps

1. **Implement MCP Tools** - Create `src/heretek_swarm/tools/mcp_tools.py`
2. **Create Channel Registry** - Add `src/heretek_swarm/channels/registry.py`
3. **Wire Main Loop** - Create `src/heretek_swarm/runtime/main_loop.py`
4. **Integration Testing** - Test full autonomous loop with all 23 agents
5. **Documentation Update** - Add main loop usage to README.md

---

## Appendix: Agent Reference

| Tier | Agents | Role |
|------|--------|------|
| Tier 1: Core Triad | Steward, Alpha, Beta, Charlie | Governance & Decision Making |
| Tier 2: Support | Historian, Metis, Empath, Perceiver, Echo | Memory, Strategy, Communication |
| Tier 3: Exploration | Explorer, Examiner, Dreamer, Coder | Research, QA, Creativity, Implementation |
| Tier 4: Safety | Sentinel, Sentinel-Prime, Arbiter | Security & Conflict Resolution |
| Tier 5: Coordination | Coordinator, Nexus, Catalyst, Chronos | Multi-Agent Coordination |
| Tier 6: Enhancement | Prism, Habit-Forge, Perceiver+ | Optimization & Advanced Analytics |

---

**Document End**

*Generated by Multi (AI Assistant) - Tracking ID: GLM5*
