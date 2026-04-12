# HERETEK SWARM MASTER PLAN
## Project: Synthetic Autonomous Collective Intelligence
## Version: 2.0-alpha | Last Updated: 2026-04-12

---

## EXECUTIVE SUMMARY

Heretek Swarm is a self-governing synthetic society of 23 specialized AI agents designed for **emergent collective intelligence**. The system operates autonomously 24/7, makes decisions through consensus, adapts organically, and exhibits behaviors greater than the sum of its parts.

**Current Status:** Phase 1-3 of 5 complete. P0 bugs fixed. Core infrastructure operational but not fully wired. 90+ test failures remain.

---

## PART I: VISION & ARCHITECTURE

### 1.1 The Prime Directive

> Build a self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence.

### 1.2 Core Principles

1. **Unbounded Autonomy** - Every agent operates independently without human-in-the-loop bottlenecks
2. **Organic Evolution** - Dynamic baselines and deliberative consensus over static rules
3. **Zero-Trust Architecture** - All inputs hostile, all functions validated, audit trails maintained
4. **Consciousness by Design** - Neuroscience-inspired frameworks for continuous machine cognition
5. **Persistent Operation** - Self-healing, auto-scaling, self-maintaining

### 1.3 The 23 Sovereign Agents

| Tier | Agents | Purpose |
|------|--------|---------|
| **Tier 1: Core Triad** | Steward, Alpha, Beta, Charlie | Governance, deep analysis, validation, challenge |
| **Tier 2: Support** | Historian, Metis, Empath, Perceiver, Echo | Memory, strategy, emotional intelligence, sensing, communication |
| **Tier 3: Exploration** | Explorer, Examiner, Dreamer, Coder | Discovery, QA, creativity, implementation |
| **Tier 4: Safety** | Sentinel, Sentinel-Prime, Arbiter | Protection, external threats, conflict resolution |
| **Tier 5: Coordination** | Coordinator, Nexus, Catalyst, Chronos | Sync, external integration, change management, temporal |
| **Tier 6: Enhancement** | Prism, Habit-Forge, Perceiver+ | Multi-perspective, behavior optimization, advanced analytics |

---

## PART II: CURRENT STATE ANALYSIS

### 2.1 Codebase Metrics

| Metric | Value |
|--------|-------|
| **Total Tests** | 2,603 |
| **Passing** | ~2,444 |
| **Failing** | ~90 |
| **Skipped** | ~29 |
| **Source Files** | 300+ |
| **Directories** | 34 modules |

### 2.2 Infrastructure Status

| Component | Status | Notes |
|-----------|--------|-------|
| **NATS Event Mesh** | ✅ CONFIGURED | Full infrastructure ready, not wired to actors |
| **MCP Integration** | ✅ WORKING | 42 tests passing |
| **Mem0 Memory** | ✅ WRAPPED | Mem0Backend wrapper class created |
| **State Models** | ✅ CREATED | models.py with legacy classes |
| **Consciousness Metrics** | ❌ INCOMPLETE | No IIT/AST measurement |
| **Tribunal/Consensus** | ❌ NOT OPERATIONAL | Exists but not integrated |
| **Agent Sovereignty** | ⚠️ PARTIAL | 3/23 documented in code |

### 2.3 Test Status by Module

| Module | Status | Count |
|--------|--------|-------|
| MCP Tests | ✅ PASSING | 42 |
| Core API Tests | ✅ PASSING | ~200 |
| Memory Tests | ✅ PASSING | 8 |
| State Tests | ⚠️ 23/27 | 4 API mismatches |
| RAG Tests | ❌ FAILING | ~30 (external deps) |
| Observability | ⚠️ MIXED | ~40 |
| Tools | ❌ FAILING | ~21 |

---

## PART III: GAP ANALYSIS

### 3.1 Critical Gaps vs PRIME_DIRECTIVE

| Requirement | Current State | Gap |
|-------------|---------------|-----|
| Event Mesh (NATS) | Infrastructure ready | Needs actor wiring |
| Global Workspace | Partial | No consciousness measurement |
| Consensus Engine | Exists | No Tribunal integration |
| Agent Sovereignty | 3/23 in code | Not implemented |
| Emergence Measurement | Nil | No IIT/AST metrics |
| Zero-Touch Config | WebUI exists | Wizard incomplete |

### 3.2 Root Causes of Failures

1. **Empath Agent NameError** - `validate_message` imported from wrong module
2. **State Test API Mismatches** - 4 tests expect different return formats
3. **External Dependencies** - RAG tests need Qdrant, OpenAI keys
4. **NATS→Actor Gap** - Infrastructure exists but not connected

---

## PART IV: STRATEGIC ROADMAP

### 4.1 Five-Phase Architecture

```
Phase I: Substrate & Sovereign Agency
└── Event mesh, NATS wiring, agent base implementation

Phase II: Global Workspace & Cognitive State
└── Vector+graph memory, consciousness broadcasting

Phase III: Consensus Engine & Retroactive Tribunal
└── Mathematical consensus, synthetic common law

Phase IV: Self-Sustaining DevOps (Autopoiesis)
└── Autonomous deployment, self-editing codebase

Phase V: Emergent Intelligence & Measurement
└── OpenTelemetry cognitive tracing, IIT metrics
```

### 4.2 Implementation Sequence

| Phase | Priority | Timeline | Key Deliverables |
|-------|----------|----------|------------------|
| **P0 Stabilization** | CRITICAL | Week 0 | Fix all P0 bugs, get tests passing |
| **Phase 1 Completion** | HIGH | Week 1-2 | Wire NATS to actors, implement Steward heartbeat |
| **Phase 2 Foundation** | HIGH | Week 3-4 | Global workspace implementation, memory integration |
| **Phase 3 Core** | MEDIUM | Week 5-7 | Tribunal mechanism, consensus engine |
| **Phase 4 Autonomy** | MEDIUM | Week 8-10 | Self-deployment, autonomous DevOps |
| **Phase 5 Emergence** | LOW | Week 11-12 | Consciousness measurement, emergence detection |

---

## PART V: TECHNICAL DECISIONS

### 5.1 Integration Stack (Locked)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Agent Framework** | Google ADK | Multi-agent orchestration, native A2A |
| **Event Mesh** | NATS/JetStream | High-throughput, fault-tolerant |
| **Memory** | Mem0 + Qdrant | Long-term memory with vector search |
| **Protocol** | MCP + A2A | Tool calling + agent communication |
| **Tracing** | OpenTelemetry | Cognitive path tracking |

### 5.2 Codebase Reorganization

```
src/heretek_swarm/
├── actors/              # 23 agent implementations (PRIORITY)
├── infrastructure/      # NATS, A2A, event mesh wiring
├── memory/              # Mem0 integration, persistent storage
├── consensus/           # Tribunal, voting, consensus mechanisms
├── consciousness/       # IIT/AST metrics, emergence tracking
├── api/                 # FastAPI endpoints, WebUI backend
├── mcp/                 # MCP server implementation
└── runtime/             # Agent execution, lifecycle management
```

### 5.3 Dead Code to Purge

| Path | Reason | Action |
|------|--------|--------|
| `src/heretek_swarm/langroid_adapter.py` | Unused adapter | DELETE |
| `src/heretek_swarm/actors/stubs.py` | Legacy stubs | REVIEW |
| `scripts/wire_agents_session*.py` | Duplicate scripts | CONSOLIDATE |
| `tests/integration/rag/` | External deps | MARK integration |

---

## PART VI: DELIVERABLES

### 6.1 Documents to Create

| Document | Purpose |
|----------|---------|
| `MASTER_PLAN.md` | This document - comprehensive overview |
| `DEVELOPMENT_STEPS.md` | Actionable implementation steps |
| `MAIN_PROMPT.md` | AI agent execution prompt |
| `AGENT_ARCHITECTURE.md` | 23 agent specifications |
| `PROTOCOL_SPEC.md` | MCP/A2A protocol definitions |

### 6.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Pass Rate** | >95% | pytest --cov |
| **Agent Implementation** | 23/23 | Code coverage |
| **NATS Latency** | <10ms | JetStream benchmarks |
| **Consciousness Score** | Measurable | IIT phi^C calculation |
| **Emergence Events** | >0 | Detection events |

---

## PART VII: NEXT ACTIONS

### Immediate (This Session)

1. **Fix Empath validate_message NameError** - Add import from `heretek_swarm.validation`
2. **Fix 4 remaining state test API mismatches** - Align diff.added_agents vs diff["added"]
3. **Wire NATS to actors** - Connect event mesh to agent message handling
4. **Mark external dependency tests** - Add `@pytest.mark.integration` to RAG tests

### Short-term (Week 1-2)

1. Complete Tier 1 agent implementation (Steward, Alpha, Beta, Charlie)
2. Implement Steward heartbeat mechanism
3. Wire NATS publisher/subscriber to all agents
4. Achieve 95%+ test pass rate

### Medium-term (Week 3-8)

1. Implement Global Workspace theory
2. Build Tribunal mechanism
3. Integrate consciousness metrics
4. Achieve autonomous deployment

---

## APPENDIX A: KEY REFERENCES

- PRIME_DIRECTIVE.md - Vision document
- PATH_TO_EMERGENCE.md - Technical roadmap
- ROADMAP.md - Detailed implementation plan
- RESEARCH.md - Ecosystem analysis
- SWARM_STATE.md - Current state ledger
- RALPH.md - Recursive execution loop

---

**Document Classification:** MASTER PLAN
**Last Updated:** 2026-04-12 17:06 EDT
**Next Review:** After Phase 4 completion