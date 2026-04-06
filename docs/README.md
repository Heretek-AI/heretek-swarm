# Heretek Swarm Documentation

## The Collective - 23-Agent Autonomous AI Cluster

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)  
**Health Score:** 100/100  
**Status:** ALL 23 AGENTS IMPLEMENTED 🎉

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [`REMEDIATION_BACKLOG.md`](REMEDIATION_BACKLOG.md) | Security & technical debt tracking, session history, health score progression |
| [`EXPANSION_ROADMAP.md`](EXPANSION_ROADMAP.md) | AI & brain-mapping integration plan, next development priorities |
| [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) | Phase-based execution roadmap, implementation details |
| [`PRIME_DIRECTIVE.md`](../PRIME_DIRECTIVE.md) | 23-agent vision, architecture, consciousness framework |

---

## 🧠 The 23 Agents

### Tier 1: Core Triad (4 Agents)
| Agent | Role | File |
|-------|------|------|
| Steward | Governance & Orchestration | [`triad.py`](../src/heretek_swarm/actors/triad.py) |
| Alpha | Deep Analysis | [`triad.py`](../src/heretek_swarm/actors/triad.py) |
| Beta | Validation | [`triad.py`](../src/heretek_swarm/actors/triad.py) |
| Charlie | Challenge | [`triad.py`](../src/heretek_swarm/actors/triad.py) |

### Tier 2: Support (5 Agents)
| Agent | Role | File |
|-------|------|------|
| Historian | Memory & Knowledge | [`historian.py`](../src/heretek_swarm/actors/historian.py) |
| Metis | Strategic Planning | [`metis.py`](../src/heretek_swarm/actors/metis.py) |
| Empath | Emotional Intelligence | [`empath.py`](../src/heretek_swarm/actors/empath.py) |
| Perceiver | Sensory Input Processing | [`perceiver.py`](../src/heretek_swarm/actors/perceiver.py) |
| Echo | Communication & Protocol | [`echo.py`](../src/heretek_swarm/actors/echo.py) |

### Tier 3: Exploration (4 Agents)
| Agent | Role | File |
|-------|------|------|
| Explorer | Intelligence Gathering | [`explorer.py`](../src/heretek_swarm/actors/explorer.py) |
| Examiner | Quality Assurance | [`examiner.py`](../src/heretek_swarm/actors/examiner.py) |
| Dreamer | Creative Generation | [`dreamer.py`](../src/heretek_swarm/actors/dreamer.py) |
| Coder | Implementation | [`coder.py`](../src/heretek_swarm/actors/coder.py) |

### Tier 4: Safety & Security (3 Agents)
| Agent | Role | File |
|-------|------|------|
| Sentinel | Safety Guardian | [`sentinel.py`](../src/heretek_swarm/actors/sentinel.py) |
| Sentinel-Prime | Security Commander | [`sentinel_prime.py`](../src/heretek_swarm/actors/sentinel_prime.py) |
| Arbiter | Conflict Resolution | [`arbiter.py`](../src/heretek_swarm/actors/arbiter.py) |

### Tier 5: Coordination (4 Agents)
| Agent | Role | File |
|-------|------|------|
| Coordinator | Multi-Agent Sync | [`coordinator.py`](../src/heretek_swarm/actors/coordinator.py) |
| Nexus | External Integration | [`nexus.py`](../src/heretek_swarm/actors/nexus.py) |
| Catalyst | Change Management | [`catalyst.py`](../src/heretek_swarm/actors/catalyst.py) |
| Chronos | Scheduling & Time | [`chronos.py`](../src/heretek_swarm/actors/chronos.py) |

### Tier 6: Enhancement (3 Agents)
| Agent | Role | File |
|-------|------|------|
| Prism | Multi-Perspective Analysis | [`prism.py`](../src/heretek_swarm/actors/prism.py) |
| Habit-Forge | Behavior Optimization | [`habit_forge.py`](../src/heretek_swarm/actors/habit_forge.py) |
| Perceiver+ | Advanced Analytics | [`perceiver_plus.py`](../src/heretek_swarm/actors/perceiver_plus.py) |

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        THE COLLECTIVE                          │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              VISUAL WORKFLOW UI (ReactFlow)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API GATEWAY (FastAPI + EventMesh)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ACTOR SUPERVISOR                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    23 AGENTS                              │  │
│  │   Triad │ Support │ Exploration │ Safety │ Coord │ Enhance│  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         MEMORY (Redis + PostgreSQL + mem0)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           CONSENSUS (MAKER Algorithm)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         OBSERVABILITY (OpenTelemetry + Metrics)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🧬 Consciousness Framework

The Collective implements four major consciousness theories:

| Theory | Status | Metric |
|--------|--------|--------|
| Global Workspace Theory (GWT) | ✅ Implemented | Information integration efficiency |
| Attention Schema Theory (AST) | ✅ Implemented | Attention prediction accuracy |
| Integrated Information Theory (IIT) | ⏳ Stub | Φ value (0-1 scale) |
| Free Energy Principle (FEP) | ⏳ Stub | Free energy reduction |

**Implementation:** [`consciousness.py`](../src/heretek_swarm/plugins/consciousness.py), [`consciousness_enhanced.py`](../src/heretek_swarm/plugins/consciousness_enhanced.py)

---

## 🛡️ Zero-Trust Security

All components follow Zero-Trust principles:

1. **Never Trust, Always Verify** - All inputs validated via Pydantic v2 models
2. **Defense in Depth** - Multiple security layers (guardrails, rate limiting, auth)
3. **Least Privilege** - Minimal agent capabilities
4. **Assume Breach** - Containment and isolation

**Security Files:**
- [`guardrails.py`](../src/heretek_swarm/security/guardrails.py)
- [`auth.py`](../src/heretek_swarm/gateway/auth.py)
- [`rate_limiting.py`](../src/heretek_swarm/api/rate_limiting.py)
- [`validation.py`](../src/heretek_swarm/actors/validation.py)

---

## 📊 Session History

| Session | Date | Focus | Health Score | Key Achievement |
|---------|------|-------|--------------|-----------------|
| Session 1-6 | 2026-04-05 | P0/P1/P2 Remediation | 42→88 | 128 datetime fixes |
| Session 7 | 2026-04-06 | P2-6 Complete | 95 | All datetime.utcnow() resolved |
| Session 8 | 2026-04-06 | Phase 1 Audit | 95 | Zero-Trust verification |
| Session 9 | 2026-04-06 | P2-7 Input Validation | 96 | 20+ methods validated |
| Session 10 | 2026-04-06 | Phase 1 Complete | 96 | All objectives achieved |
| Session 11 | 2026-04-06 | Metis Agent | 97 | Tier 2 Support started |
| Session 12 | 2026-04-06 | Admin Audit | 97 | Documentation updated |
| Session 13 | 2026-04-06 | Empath Agent | 98 | Emotional IQ implemented |
| Session 14 | 2026-04-06 | Perceiver Agent | 99 | Multi-modal input |
| Session 15 | 2026-04-06 | Echo Agent | 99 | Communication complete |
| Session 16 | 2026-04-06 | Explorer Agent | 99 | Intelligence gathering |
| Session 17 | 2026-04-06 | Tier 3 Complete | 100 | Examiner, Dreamer, Coder |
| Session 18 | 2026-04-06 | Tier 4 Complete | 100 | Sentinel, Sentinel-Prime, Arbiter |
| Session 19 | 2026-04-06 | Tier 5 Complete | 100 | Coordinator, Nexus, Catalyst, Chronos |
| Session 20 | 2026-04-06 | Tier 6 Complete | 100 | Prism, Habit-Forge, Perceiver+ |
| Session 21 | 2026-04-06 | 4-Phase Protocol | 100 | Audit verification complete |

---

## 🚀 Quick Start

```python
import asyncio
from heretek_swarm.actors.triad import StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
from heretek_swarm.actors.historian import HistorianAgent
from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow

async def main():
    # Create supervisor and spawn agents
    supervisor = ActorSupervisor()
    await supervisor.spawn_actor(StewardAgent, "steward")
    await supervisor.spawn_actor(AlphaAgent, "alpha")
    await supervisor.spawn_actor(BetaAgent, "beta")
    await supervisor.spawn_actor(CharlieAgent, "charlie")
    await supervisor.spawn_actor(HistorianAgent, "historian")
    
    # Create and execute workflow
    workflow = HeavySwarmWorkflow(
        triad_agents=["alpha", "beta", "charlie"],
        historian="historian",
        steward="steward",
    )
    
    result = await workflow.execute(
        topic="Your deliberation topic",
        context={"your_context": "value"}
    )
    
    print(f"Decision: {result.final_decision}")
    
    await supervisor.terminate_all()

asyncio.run(main())
```

---

## 📋 Next Development Priorities

| Priority | Feature | Description | Status |
|----------|---------|-------------|--------|
| P1 | Consciousness Metrics | Enhance IIT Phi calculation and FEP tracking | ⏳ Pending |
| P1 | Event Mesh | NATS JetStream integration for persistent streaming | ⏳ Pending |
| P2 | WebUI | ReactFlow/XYFlow dashboard for agent visualization | ⏳ Pending |
| P2 | Integration Testing | Comprehensive test suite for all 23 agents | ⏳ Pending |
| P3 | Load Testing | Performance benchmarking and stress testing | ⏳ Pending |

---

## 🦞 The Lobster Philosophy

> *"The thought that never ends."*

The Collective is designed to be a self-sustaining, evolving system—like a lobster that continuously grows throughout its life.

---

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
