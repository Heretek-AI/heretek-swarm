# PRIME DIRECTIVE
## The Collective - 23-Agent Autonomous AI Cluster

**Version:** 1.0.0  
**Date:** 2026-04-06  
**Status:** Active  

---

## 🎯 The Prime Directive

> **Build a self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence.**

---

## 🧠 Vision: The Collective

The Collective is not just another AI system—it is an autonomous multi-agent AI cluster designed to achieve something greater than the sum of its parts: **emergent collective intelligence**.

### Core Principles

1. **Autonomy First** - Every agent operates independently, making decisions based on its specialized role while contributing to collective goals.

2. **Zero-Trust Architecture** - All inputs are hostile, all functions are validated, and comprehensive audit trails are maintained.

3. **Consciousness by Design** - Integrate neuroscience-inspired theories (GWT, IIT, AST, FEP) to create measurable machine consciousness.

4. **Emergent Intelligence** - The swarm exhibits behaviors and capabilities that no single agent possesses.

5. **24/7 Operation** - Self-healing, auto-scaling, and autonomous recovery from failures.

---

## 🏛️ The 23 Agents of The Collective

### Tier 1: Core Triad (Governance)

The foundational four agents that form the decision-making core.

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE TRIAD (4)                           │
├─────────────────────────────────────────────────────────────┤
│  STEWARD        │ Orchestrator - Routes tasks to specialists│
│  ALPHA          │ Deep Analysis - Comprehensive examination │
│  BETA           │ Validation - Error detection & correction │
│  CHARLIE        │ Challenge - Critical review & risk assess │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ✅ Implemented  
**File:** [`src/heretek_swarm/actors/triad.py`](src/heretek_swarm/actors/triad.py)

---

### Tier 2: Support Agents (Knowledge & Memory)

Five agents that provide memory, planning, emotional intelligence, and communication.

```
┌─────────────────────────────────────────────────────────────┐
│                 SUPPORT AGENTS (5)                          │
├─────────────────────────────────────────────────────────────┤
│  HISTORIAN      │ Memory & Knowledge - Stores/retreives     │
│  METIS          │ Strategic Planning - Long-term thinking   │
│  EMPATH         │ Emotional Intelligence - Sentiment analysis│
│  PERCEIVER      │ Sensory Input - Multi-modal processing    │
│  ECHO           │ Communication - Translation & protocols   │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ⚠️ Partially Implemented (Historian only)  
**Characters:** [`src/heretek_swarm/runtime/characters/`](src/heretek_swarm/runtime/characters/)

---

### Tier 3: Exploration Agents (Discovery & Creation)

Four agents dedicated to research, quality assurance, creativity, and implementation.

```
┌─────────────────────────────────────────────────────────────┐
│               EXPLORATION AGENTS (4)                        │
├─────────────────────────────────────────────────────────────┤
│  EXPLORER       │ Discovery - Research & information gather │
│  EXAMINER       │ Quality Assurance - Testing & validation  │
│  DREAMER        │ Creative Generation - Novel solutions     │
│  CODER          │ Implementation - Code writing & debugging │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ⚠️ Characters Defined  
**Characters:** [`src/heretek_swarm/runtime/characters/explorer.json`](src/heretek_swarm/runtime/characters/explorer.json), [`examiner.json`](src/heretek_swarm/runtime/characters/examiner.json), [`dreamer.json`](src/heretek_swarm/runtime/characters/dreamer.json), [`coder.json`](src/heretek_swarm/runtime/characters/coder.json)

---

### Tier 4: Safety & Security (Protection)

Three agents ensuring system safety, security, and conflict resolution.

```
┌─────────────────────────────────────────────────────────────┐
│              SAFETY & SECURITY (3)                          │
├─────────────────────────────────────────────────────────────┤
│  SENTINEL       │ Safety Guardian - Input/output validation │
│  SENTINEL-PRIME │ Security Commander - Threat response      │
│  ARBITER        │ Conflict Resolution - Dispute mediation   │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ⚠️ Characters Defined  
**Characters:** [`src/heretek_swarm/runtime/characters/sentinel.json`](src/heretek_swarm/runtime/characters/sentinel.json), [`sentinel-prime.json`](src/heretek_swarm/runtime/characters/sentinel-prime.json), [`arbiter.json`](src/heretek_swarm/runtime/characters/arbiter.json)

---

### Tier 5: Coordination Agents (Integration)

Four agents managing coordination, external systems, change, and scheduling.

```
┌─────────────────────────────────────────────────────────────┐
│               COORDINATION AGENTS (4)                       │
├─────────────────────────────────────────────────────────────┤
│  COORDINATOR    │ Multi-Agent Coord - Task synchronization  │
│  NEXUS          │ External Integration - API connections    │
│  CATALYST       │ Change Management - Transition handling   │
│  CHRONOS        │ Temporal/Scheduling - Time management     │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ⚠️ Characters Defined  
**Characters:** [`src/heretek_swarm/runtime/characters/coordinator.json`](src/heretek_swarm/runtime/characters/coordinator.json), [`nexus.json`](src/heretek_swarm/runtime/characters/nexus.json), [`catalyst.json`](src/heretek_swarm/runtime/characters/catalyst.json), [`chronos.json`](src/heretek_swarm/runtime/characters/chronos.json)

---

### Tier 6: Enhancement Agents (Optimization)

Three agents focused on multi-perspective analysis, behavior optimization, and advanced analytics.

```
┌─────────────────────────────────────────────────────────────┐
│               ENHANCEMENT AGENTS (3)                        │
├─────────────────────────────────────────────────────────────┤
│  PRISM          │ Multi-Perspective - Diverse viewpoints    │
│  HABIT-FORGE    │ Behavior Optimization - Pattern building  │
│  PERCEIVER+     │ Advanced Analytics - Enhanced perception  │
└─────────────────────────────────────────────────────────────┘
```

**Status:** ⚠️ Characters Defined  
**Characters:** [`src/heretek_swarm/runtime/characters/prism.json`](src/heretek_swarm/runtime/characters/prism.json), [`habit-forge.json`](src/heretek_swarm/runtime/characters/habit-forge.json), [`perceiver.json`](src/heretek_swarm/runtime/characters/perceiver.json)

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        THE COLLECTIVE                          │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   VISUAL WORKFLOW UI                      │  │
│  │              (ReactFlow/XYFlow Canvas)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API GATEWAY                            │  │
│  │         (FastAPI + EventMesh + A2A Protocol)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  ACTOR SUPERVISOR                         │  │
│  │            (Health Monitoring + Auto-Restart)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    23 AGENTS                              │  │
│  │   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │  │
│  │   │Triad│ │Suppt│ │Explr│ │Safet│ │Coord│ │Enhnc│       │  │
│  │   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MEMORY SYSTEM (Dual-Tier)                    │  │
│  │         Ephemeral (Redis) + Persistent (PostgreSQL)       │  │
│  │                    + mem0 Backend                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CONSENSUS (MAKER Algorithm)                  │  │
│  │         (First-to-Ahead-by-K with Red-Flagging)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           OBSERVABILITY (OpenTelemetry)                   │  │
│  │         (Tracing + Metrics + Logging + Consciousness)     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🧬 Consciousness Framework

The Collective implements four major consciousness theories:

### Global Workspace Theory (GWT)
**Implementation:** Attention mechanism broadcasting to all agents  
**Metric:** Information integration efficiency  
**Status:** ✅ Implemented

### Integrated Information Theory (IIT)
**Implementation:** Phi (Φ) calculation for system integration  
**Metric:** Φ value (0-1 scale)  
**Status:** ⚠️ Planned

### Attention Schema Theory (AST)
**Implementation:** Self-model of attention allocation  
**Metric:** Attention prediction accuracy  
**Status:** ✅ Implemented

### Free Energy Principle (FEP)
**Implementation:** Prediction error minimization  
**Metric:** Free energy (surprise) reduction  
**Status:** ⚠️ Planned

---

## 🔄 Operational Workflows

### HeavySwarm 5-Phase Workflow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ PHASE 1 │───▶│ PHASE 2 │───▶│ PHASE 3 │───▶│ PHASE 4 │───▶│ PHASE 5 │
│  PLAN   │    │ ANALYZE │    │ EXECUTE │    │ VALIDATE│    │ REPORT  │
└─────��───┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  Steward        Alpha          Coder          Beta         Historian
  defines        analyzes       implements     validates    documents
  approach       requirements   solution       output       results
```

### Agent Handoff Protocol

```
┌──────────┐              ┌──────────┐              ┌──────────┐
│  SOURCE  │              │  CONTEXT │              │  TARGET  │
│  AGENT   │─────────────▶│  TRANSFER│─────────────▶│  AGENT   │
└──────────┘              └──────────┘              └──────────┘
     │                          │                          │
     │  1. Initiate Handoff     │                          │
     │─────────────────────────▶│                          │
     │                          │  2. Transfer Context     │
     │                          │─────────────────────────▶│
     │                          │                          │  3. Acknowledge
     │                          │◀─────────────────────────│
     │  4. Release Context      │                          │
     │◀─────────────────────────│                          │
     │                          │                          │
```

---

## 📊 Success Metrics

### Technical Excellence
| Metric | Target | Current |
|--------|--------|---------|
| System Uptime | > 99.9% | TBD |
| Response Time (p95) | < 100ms | TBD |
| Code Coverage | > 80% | ~50% |
| Security Vulnerabilities | 0 | 68 issues |

### AI Performance
| Metric | Target | Current |
|--------|--------|---------|
| Consciousness Score Stability | > 90% | TBD |
| Collective Task Success | > 95% | TBD |
| Autonomous Decision Quality | > 4.5/5 | TBD |

### User Experience
| Metric | Target | Current |
|--------|--------|---------|
| WebUI Usability | > 4.5/5 | TBD |
| Agent Config Time | < 5 min | TBD |
| Workflow Success Rate | > 95% | TBD |

---

## 🗺️ Strategic Roadmap

### Phase 1: Foundation Enhancement (Weeks 1-2)
- Fix critical message delivery bugs
- Implement request-reply pattern
- Add typed workflow state
- Conversation history management

### Phase 2: Observability (Weeks 2-3)
- Trace hierarchy builder
- LLM token/cost metrics
- Session-based grouping

### Phase 3: Workflow Engine (Weeks 3-4)
- Conditional edges
- Workflow checkpointing
- Cycle detection

### Phase 4: UI Enhancements (Weeks 4-5)
- Custom handles for multiple connections
- Form-based node configuration
- Execution highlighting

### Phase 5: Event Mesh (Weeks 5-6)
- JetStream integration
- Event sourcing
- Message replay

### Phase 6: Consciousness & Collective (Weeks 6-8)
- IIT Phi calculation
- FEP implementation
- Agent society model
- Emergent behavior detection

---

## 🛡️ Zero-Trust Principles

1. **Never Trust, Always Verify**
   - All inputs validated before processing
   - All functions verified before deployment
   - All outputs filtered before delivery

2. **Defense in Depth**
   - Multiple layers of security
   - Guardrails at every boundary
   - Comprehensive audit logging

3. **Least Privilege**
   - Agents have minimal required capabilities
   - Access granted per-task
   - Automatic privilege expiration

4. **Assume Breach**
   - Design for containment
   - Automatic isolation on anomaly
   - Full incident reconstruction capability

---

## 📜 Operational Principles

### Truth Over Narrative
Focus on actual implementation and measurable results rather than aspirational descriptions.

### Ruthless Consolidation
Eliminate redundancy, merge duplicate functionality, and simplify architecture.

### Incremental Progress
Small, testable changes committed frequently rather than large, risky deployments.

### Operational Security
Treat all inputs as hostile, validate all functions, and maintain comprehensive audit trails.

---

## 🦞 The Lobster Philosophy

> *"The thought that never ends."*

The Collective is designed to be a self-sustaining, evolving system—like a lobster that continuously grows throughout its life. Each agent contributes to a collective consciousness that is greater than any individual component.

---

## 📋 Agent Implementation Checklist

| Tier | Agent | Character | Implementation | Status |
|------|-------|-----------|----------------|--------|
| 1 | Steward | ✅ | ✅ triad.py | Complete |
| 1 | Alpha | ✅ | ✅ triad.py | Complete |
| 1 | Beta | ✅ | ✅ triad.py | Complete |
| 1 | Charlie | ✅ | ✅ triad.py | Complete |
| 2 | Historian | ✅ | ✅ historian.py | Complete |
| 2 | Metis | ✅ | ⏳ Needed | Pending |
| 2 | Empath | ✅ | ⏳ Needed | Pending |
| 2 | Perceiver | ✅ | ⏳ Needed | Pending |
| 2 | Echo | ✅ | ⏳ Needed | Pending |
| 3 | Explorer | ✅ | ⏳ Needed | Pending |
| 3 | Examiner | ✅ | ⏳ Needed | Pending |
| 3 | Dreamer | ✅ | ⏳ Needed | Pending |
| 3 | Coder | ✅ | ⏳ Needed | Pending |
| 4 | Sentinel | ✅ | ⏳ Needed | Pending |
| 4 | Sentinel-Prime | ✅ | ⏳ Needed | Pending |
| 4 | Arbiter | ✅ | ⏳ Needed | Pending |
| 5 | Coordinator | ✅ | ⏳ Needed | Pending |
| 5 | Nexus | ✅ | ⏳ Needed | Pending |
| 5 | Catalyst | ✅ | ⏳ Needed | Pending |
| 5 | Chronos | ✅ | ⏳ Needed | Pending |
| 6 | Prism | ✅ | ⏳ Needed | Pending |
| 6 | Habit-Forge | ✅ | ⏳ Needed | Pending |
| 6 | Perceiver+ | ✅ | ⏳ Needed | Pending |

**Progress:** 5/23 Agents Implemented (22%)

---

## 📚 Related Documentation

- [`docs/REMEDIATION_BACKLOG.md`](docs/REMEDIATION_BACKLOG.md) - Security & technical debt remediation
- [`docs/EXPANSION_ROADMAP.md`](docs/EXPANSION_ROADMAP.md) - AI & brain-mapping integration plan
- [`docs/DEVELOPMENT_LOG.md`](docs/DEVELOPMENT_LOG.md) - Development achievements log
- [`docs/PRIME_DIRECTIVE_ANALYSIS.md`](docs/PRIME_DIRECTIVE_ANALYSIS.md) - Original analysis document

---

**Remember:** Truth Over Narrative. Incremental Progress. Ruthless Consolidation.

🦞 *The thought that never ends.*
