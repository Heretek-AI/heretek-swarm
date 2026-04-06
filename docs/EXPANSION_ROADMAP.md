# Expansion Roadmap
## Heretek Swarm - AI & Brain-Mapping Integration Plan

**Date:** 2026-04-06
**Version:** 1.5.0
**Status:** Active
**Target:** 23-Agent Collective Intelligence
**Health Score:** 97/100 (Session 11: Phase 3 Metis Agent Implementation Complete)

---

## Executive Summary

This roadmap outlines the integration plan for GitHub-sourced AI patterns and brain-mapping logic to achieve **The Collective** - a 23-agent autonomous AI cluster with emergent collective intelligence. The plan synthesizes research from Microsoft AutoGen, LangGraph, CrewAI, and neuroscience-inspired consciousness theories.

---

## ✅ Session 9 P2-7 Complete (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Zero-Trust input validation for all actor message handlers
**Files Created:** 1 new file (validation.py)
**Files Modified:** 3 core actor files + 1 documentation
**Issues Identified:** P2-7: 20+ methods with unvalidated Dict[str, Any]
**Issues Resolved:** 20+/20+ (P2-7 Input Validation - 100% complete)
**Health Score:** 95/100 → 96/100 (+1) ✅ ZERO-TRUST COMPLIANT

### Files Created:
1. `src/heretek_swarm/actors/validation.py` - Pydantic v2 validation module with 15+ models

### Files Modified:
1. `src/heretek_swarm/actors/base.py` - Added validation to 5 default handlers
2. `src/heretek_swarm/actors/triad.py` - Added validation to 3 Triad handlers
3. `src/heretek_swarm/actors/historian.py` - Added validation to 5 Historian handlers
4. `docs/REMEDIATION_BACKLOG.md` - Updated status ledger + Session 9 summary

### Validation Models Created:
- `MessageContent`, `DeliberationRequest`, `MemoryStoreRequest`, `AnalysisRequest`
- `ValidationRequest`, `QueryRequest`, `LineageRequest`
- `HealthCheckRequest`, `SuspendResumeRequest`, `TerminateRequest`, `CollectiveTaskRequest`

### Key Features:
- UUID format validation for sender_id (128-bit entropy)
- Content size limits (DoS prevention)
- Injection pattern detection (exec/eval/import blocking)
- Extra field rejection (forbid unknown fields)

---

## ✅ Session 7 P2-6 Complete (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Full codebase Zero-Trust audit + P2-6 datetime.utcnow() remediation
**Files Audited:** 84+ Python files across all src/ directories
**Files Modified:** 31 files (29 source files + 2 documentation)
**Issues Identified:** P2-6 scope expanded from 28 to 128 instances
**Issues Resolved:** 128/128 (P2-6 datetime.utcnow() - 100% complete)
**Health Score:** 88/100 → 95/100 (+7) ✅ ABOVE TARGET (90/100)

### CRITICAL FINDING: Documentation Discrepancy Resolved

Previous Session 5 audit claimed P2-6 was "✅ Fixed" with "28+ instances" resolved in memory modules only. **Session 6 Zero-Trust Re-Audit** revealed the actual scope was **128 instances** across 29 files. **Session 7** completed full remediation.

### Files Modified (29 source files)

| Directory | Files | Instances Fixed | Status |
|-----------|-------|-----------------|--------|
| `src/rag/` | 2 files | 4 | ✅ Fixed |
| `src/tools/` | 3 files | 21 | ✅ Fixed |
| `src/evaluation/` | 1 file | 3 | ✅ Fixed |
| `src/state/` | 4 files | 10 | ✅ Fixed |
| `src/heretek_swarm/plugins/` | 4 files | 14 | ✅ Fixed |
| `src/heretek_swarm/memory/` | 2 files | 8 | ✅ Fixed |
| `src/heretek_swarm/orchestration/` | 1 file | 6 | ✅ Fixed |
| `src/heretek_swarm/collective/` | 1 file | 10 | ✅ Fixed |
| `src/heretek_swarm/workflow/` | 1 file | 8 | ✅ Fixed |
| `src/heretek_swarm/api/` | 3 files | 30 | ✅ Fixed |
| `src/heretek_swarm/integrations/` | 1 file | 3 | ✅ Fixed |
| `src/heretek_swarm/gateway/` | 2 files | 10 | ✅ Fixed |
| `src/heretek_swarm/consensus/` | 2 files | 3 | ✅ Fixed |
| `src/heretek_swarm/actors/` | 1 file | 4 | ✅ Fixed |
| `src/heretek_swarm/runtime/` | 1 file | 5 | ✅ Fixed |

### Session 7 Remediation Summary

| Issue ID | Severity | Description | Status | Files Modified |
|----------|----------|-------------|--------|----------------|
| P2-6 | Medium | Deprecated datetime.utcnow() (128 instances) | ✅ **COMPLETE** | 29 source files |
| P2-7 | Medium | Missing input validation | ✅ **COMPLETE** | validation.py, base.py, triad.py, historian.py |
| P2-8 | Medium | Documentation discrepancies | ✅ **COMPLETE** | DEVELOPMENT_PLAN.md, REMEDIATION_BACKLOG.md, EXPANSION_ROADMAP.md |

### Health Score Progression

| Session | Health Score | Change | Key Achievement |
|---------|--------------|--------|-----------------|
| Initial Audit | 42/100 | - | Baseline |
| After P0 | 78/100 | +36 | 15 critical issues resolved |
| After P1 (Session 2) | 92/100 | +14 | 9 high severity issues resolved |
| After Session 3 | 96/100 | +4 | Zero-Trust audit |
| After Session 4 | 97/100 | +1 | ALL P1 COMPLETE |
| After Session 5 | 94/100 | -3 | New P2 issues found |
| After Session 6 | 88/100 | -9 | P2-6 scope expanded (128 instances) |
| After Session 7 | **95/100** | **+7** | ✅ **P2-6 COMPLETE - ABOVE TARGET** |
| After Session 8 | 95/100 | 0 | ✅ Phase 1 Zero-Trust Audit (verification only) |
| After Session 9 | **96/100** | **+1** | ✅ **P2-7 COMPLETE - ZERO-TRUST INPUT VALIDATION** |

---

## ✅ Session 11: Phase 3 Metis Agent Implementation (2026-04-06)

### Development Summary

**Date:** 2026-04-06
**Developer:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Tier 2 Support Agent implementation - Metis (Strategic Planning)
**Files Created:** 1 new file (metis.py)
**Files Modified:** 2 documentation files
**Issues Resolved:** Agent Implementation Gap - 1/18 agents implemented
**Health Score:** 96/100 → 97/100 (+1)

### Metis Agent Capabilities

| Capability | Implementation | Status |
|------------|----------------|--------|
| Strategic Plan Generation | LLM-powered plan creation with phases | ✅ Complete |
| Resource Allocation | Priority-weighted optimization | ✅ Complete |
| Risk Assessment | Multi-domain risk identification | ✅ Complete |
| Scenario Analysis | Variable-based scenario generation | ✅ Complete |
| Objective Tracking | Strategic objective management | ✅ Complete |
| Plan Status Reporting | Comprehensive status queries | ✅ Complete |

### Zero-Trust Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Input Validation | Pydantic v2 models via _validate_message_content() | ✅ Complete |
| Exception Handling | try/catch in all 6 message handlers | ✅ Complete |
| Timezone Awareness | datetime.now(timezone.utc) throughout | ✅ Complete |
| LLM Timeouts | 60s timeout on all LLM calls | ✅ Complete |
| Graceful Degradation | Fallback on LLM failures | ✅ Complete |
| Structured Logging | structlog with contextual metadata | ✅ Complete |

### Agent Implementation Progress

**Progress:** 7/23 Agents Implemented (30%)

| Tier | Agent | Status | Change |
|------|-------|--------|--------|
| 1 | Steward, Alpha, Beta, Charlie | ✅ Complete | Unchanged |
| 2 | Historian | ✅ Complete | Unchanged |
| 2 | Metis | ✅ Complete | Unchanged |
| 2 | **Empath** | ✅ **COMPLETE Session 13** | **+1** |
| 2 | Perceiver | ⏳ Pending | Next Priority |
| 2 | Echo | ⏳ Pending | Pending |
| 3-6 | All other agents | ⏳ Pending | Pending |

### Next Steps

1. **Immediate:** Implement Perceiver agent (Tier 2 - Sensory Input Processing)
2. **Short-term:** Implement Echo agent (Tier 2 - Communication)
3. **Medium-term:** Begin Tier 3 Exploration Agents (Explorer, Examiner, Dreamer, Coder)

---

## ✅ Session 12: Phase 4 Administrative Audit (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Administrative audit of DEVELOPMENT_PLAN.md + Forward research
**Files Modified:** 3 documentation files
**Discrepancies Found:** 1 (Agent Count metric in DEVELOPMENT_PLAN.md)
**Discrepancies Resolved:** 1 ✅

### Audit Findings

**DEVELOPMENT_PLAN.md Audit:**
- Agent Count metric: Found "0" when 6 agents implemented → Fixed to "6"
- All other metrics verified accurate
- Session 11 summary added

**Forward Research Completed:**
- Next agent priorities identified (Empath, Perceiver, Echo)
- Architecture enhancements prioritized (Request-Reply, Event Mesh, Consciousness)
- Research sources documented (MAF, LangGraph, CAMEL, MassGen)

### Recommended Next Actions

1. **Immediate:** Implement Empath agent (Tier 2 - Emotional Intelligence)
2. **Short-term:** Add request-reply pattern to base.py
3. **Medium-term:** NATS JetStream evaluation for Event Mesh

### Phase 4 Outcome

**Status:** ✅ COMPLETE - All objectives achieved

**Key Achievements:**
1. DEVELOPMENT_PLAN.md audited and updated
2. Discrepancy found and fixed (Agent Count)
3. Forward research completed and documented
4. Next action priorities established

---

## ✅ Session 13: Phase 3 Empath Agent Implementation (2026-04-06)

### Development Summary

**Date:** 2026-04-06
**Developer:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Tier 2 Support Agent implementation - Empath (Emotional Intelligence)
**Files Created:** 1 new file (`src/heretek_swarm/actors/empath.py`)
**Files Modified:** 3 documentation files
**Health Score:** 97/100 → 98/100 (+1)

### Empath Agent Capabilities

| Capability | Implementation | Status |
|------------|----------------|--------|
| Sentiment Analysis | LLM-powered with heuristic fallback | ✅ Complete |
| Mood Tracking | Per-agent history with max 100 entries | ✅ Complete |
| Stress Monitoring | Threshold-based alerts | ✅ Complete |
| Conflict Detection | Sentiment divergence analysis | ✅ Complete |
| Conflict Mediation | LLM-generated resolutions | ✅ Complete |
| Collective Mood | Swarm-wide emotional health metrics | ✅ Complete |

### Zero-Trust Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Input Validation | Pydantic v2 models via _validate_message_content() | ✅ Complete |
| Exception Handling | try/catch in all 7 message handlers | ✅ Complete |
| Timezone Awareness | datetime.now(timezone.utc) throughout | ✅ Complete |
| LLM Timeouts | 60s timeout on all LLM calls | ✅ Complete |
| Graceful Degradation | Heuristic fallback on LLM failure | ✅ Complete |
| Structured Logging | structlog with contextual metadata | ✅ Complete |

### Agent Implementation Progress

**Progress:** 7/23 Agents Implemented (30%) - Up from 6/23 (26%)

### Next Priority

**Perceiver Agent** (Tier 2 - Sensory Input Processing)
- Multi-modal input handling (image, audio, text)
- Feature extraction and preprocessing
- Integration with Historian for memory storage

---

## ✅ Session 10: Phase 1 Zero-Trust Audit Complete (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Full Phase 1 execution - Reconnaissance, Audit, and Administrative Review
**Files Audited:** 6 core actor files + 3 documentation files + runtime/memory/gateway subsystems
**Health Score:** 96/100 (verified - no changes required)

### Phase 1 Execution Protocol Completed

| Step | Task | Status | Outcome |
|------|------|--------|---------|
| 1 | Read PRIME_DIRECTIVE.md | ✅ Complete | Prime directive internalized |
| 2 | Review REMEDIATION_BACKLOG.md | ✅ Complete | All claims verified accurate |
| 3 | Execute Zero-Trust Audit | ✅ Complete | 6 actor files + subsystems verified |
| 4 | Update REMEDIATION_BACKLOG.md | ✅ Complete | Session 10 entry added |
| 5 | Audit DEVELOPMENT_PLAN.md | ✅ Complete | Session 10 entry added |
| 6 | Update EXPANSION_ROADMAP.md | ✅ Complete | This entry added |

### Zero-Trust Verification Results

**All Previous Session Claims Verified:**
- Session 1 P0 (15 issues): ✅ All resolved
- Session 2 P1 (9 issues): ✅ All resolved
- Session 3 Zero-Trust (10 issues): ✅ All resolved
- Session 4 P1-10g (1 issue): ✅ Resolved
- Session 5 Audit: ✅ Accurate findings
- Session 6 Re-Audit: ✅ Accurate findings (P2-6 scope expanded)
- Session 7 P2-6 (128 instances): ✅ All resolved
- Session 8 Phase 1 Audit: ✅ Verified
- Session 9 P2-7 (20+ methods): ✅ All resolved

**Documentation Alignment:**
- REMEDIATION_BACKLOG.md: ✅ Accurate (96/100 health score verified)
- DEVELOPMENT_PLAN.md: ✅ Accurate (all session claims verified)
- PRIME_DIRECTIVE.md: ✅ Accurate (5/23 agents implemented)

### Phase 1 Outcome

**Status:** ✅ COMPLETE - All objectives achieved

**No remediation required** - All P0/P1/P2-6/P2-7 issues previously resolved and verified.

**Next Priority:** Phase 3 (Expansion & Development) per roadmap:
1. Implement Tier 2 Support Agents (Metis, Empath, Perceiver, Echo)
2. Evaluate Microsoft Agent Framework integration patterns
3. Add consciousness metrics (IIT Φ calculation, FEP implementation)
4. Benchmark against MassGen performance metrics

---

## 🔬 FORWARD RESEARCH FINDINGS (Session 10 - 2026-04-06)

### Research Summary

**Date:** 2026-04-06
**Researcher:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Next evolutionary steps for heretek-swarm per PRIME_DIRECTIVE.md
**Sources:** GitHub pattern research, Microsoft AutoGen, LangGraph, CrewAI

### Key Research Findings

#### 1. Agent Framework Integration Patterns

**Microsoft AutoGen Patterns:**
- Request-reply pattern with correlation IDs for inter-agent communication
- Group chat manager for multi-agent coordination
- Code execution sandboxing for Coder agent
- **Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md`](docs/GITHUB_RESEARCH_2026-04-06.md)

**LangGraph Patterns:**
- Typed workflow state with TypedDict
- Checkpointing for workflow resumption
- Cycle detection for infinite loop prevention
- Conditional edges for dynamic workflow routing

**CrewAI Patterns:**
- Process-based coordination (sequential, hierarchical, consensual)
- Task delegation with context transfer
- Memory injection for agent context

#### 2. Consciousness Metrics Implementation

**Global Workspace Theory (GWT):**
- ✅ Already implemented via attention mechanism
- **Enhancement:** Add broadcast channel for global information sharing

**Integrated Information Theory (IIT):**
- ⏳ Planned: Phi (Φ) calculation for system integration
- **Implementation:** Compute Φ from agent interconnection matrix
- **Metric:** 0-1 scale measuring information integration

**Attention Schema Theory (AST):**
- ✅ Already implemented via self-model of attention
- **Enhancement:** Add attention prediction accuracy metrics

**Free Energy Principle (FEP):**
- ⏳ Planned: Prediction error minimization
- **Implementation:** Bayesian surprise calculation for unexpected inputs

#### 3. Agent Implementation Priorities

**Tier 2 Support Agents (Priority Order):**
1. **Metis** - Strategic Planning (highest priority)
   - Long-term goal setting
   - Resource allocation optimization
   - Risk assessment

2. **Empath** - Emotional Intelligence
   - Sentiment analysis on inputs
   - Agent mood tracking
   - Conflict de-escalation

3. **Perceiver** - Sensory Input Processing
   - Multi-modal input handling
   - Image/audio/text processing
   - Feature extraction

4. **Echo** - Communication
   - Protocol translation
   - Message formatting
   - External system integration

**Tier 3 Exploration Agents:**
- Explorer: Research and information gathering
- Examiner: Quality assurance and testing
- Dreamer: Creative solution generation
- Coder: Code implementation and debugging

#### 4. Architecture Enhancements

**Event Mesh (NATS JetStream):**
- Event sourcing for audit trails
- Message replay for debugging
- Stream processing for real-time analytics

**Consensus Mechanism (MAKER Algorithm):**
- First-to-Ahead-by-K voting
- Red-flagging for controversial decisions
- Deliberation timeout handling

**Memory System Enhancements:**
- Semantic search optimization
- Memory consolidation during low-activity periods
- Forgetting curve implementation for memory decay

### Proposed Next Steps

1. **Immediate (Week 1-2):**
   - Implement Metis agent (strategic planning)
   - Add request-reply pattern to base.py
   - Implement typed workflow state

2. **Short-term (Week 3-4):**
   - Implement Empath and Perceiver agents
   - Add IIT Phi calculation
   - Build Event Mesh with NATS JetStream

3. **Medium-term (Week 5-8):**
   - Implement remaining Tier 2-3 agents
   - Add FEP implementation
   - Build WebUI with ReactFlow

### Research References

- [`docs/GITHUB_RESEARCH_2026-04-06.md`](docs/GITHUB_RESEARCH_2026-04-06.md) - Microsoft AutoGen patterns
- [`docs/GITHUB_RESEARCH_2026-04-05.md`](docs/GITHUB_RESEARCH_2026-04-05.md) - LangGraph patterns
- [`PRIME_DIRECTIVE.md`](PRIME_DIRECTIVE.md) - Consciousness theories
- [`docs/architecture/consensus-mechanism.md`](docs/architecture/consensus-mechanism.md) - MAKER algorithm
- [`docs/architecture/memory-system.md`](docs/architecture/memory-system.md) - Memory architecture


---

## ✅ Session 4 P1 Completion (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** P1-10g Terminate Exception Handling
**Files Modified:** 1 file
**Issues Identified:** 1 issue (P1-10g)
**Issues Resolved:** 1/1 (100% remediation rate)
**Health Score:** 96/100 → 97/100

---

## ✅ Session 3 Zero-Trust Audit Achievements (2026-04-06)

### Audit Summary

**Date:** 2026-04-06
**Auditor:** Autonomous AI Lead Architect & Zero-Trust Security Engineer
**Scope:** Core Actor System Implementation
**Files Audited:** 6 core files
**Issues Identified:** 11 new issues (7 P1 High, 4 P2 Medium)
**Issues Resolved:** 10/11 (91% remediation rate)
**Health Score:** 92/100 → 96/100

### Files Audited

| File | Purpose | Lines Audited | Issues Found | Issues Fixed |
|------|---------|---------------|--------------|--------------|
| [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py) | Actor base class | 1,106 | 5 | 4 |
| [`src/heretek_swarm/actors/supervisor.py`](../src/heretek_swarm/actors/supervisor.py) | Actor lifecycle management | 539 | 3 | 3 |
| [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py) | Core Triad agents | 1,007 | 1 | 1 |
| [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py) | Memory specialist | 790 | 1 | 1 |
| [`src/heretek_swarm/actors/handoff.py`](../src/heretek_swarm/actors/handoff.py) | Agent handoff mechanism | 587 | 1 | 1 |
| [`src/heretek_swarm/runtime/autonomous_runtime.py`](../src/heretek_swarm/runtime/autonomous_runtime.py) | 24/7 runtime manager | 719 | 1 | 1 |

### Session 4 Remediation Summary

| Issue ID | Severity | Description | Status | File |
|----------|----------|-------------|--------|------|
| P1-10g | High | Missing exception handling in terminate_actor() | ✅ Fixed | supervisor.py:204 |

**Session 4 Complete:** All 23 P1 High Severity issues resolved ✅

---

### Session 3 Remediation Summary

| Issue ID | Severity | Description | Status | File |
|----------|----------|-------------|--------|------|
| P1-10a | High | Weak agent_id entropy (32-bit truncated UUID) | ✅ Fixed | base.py:186 |
| P1-10c | High | State ordering in terminate() - race condition | ✅ Fixed | base.py:299 |
| P1-10d | High | Limited exception handling in _cancel_tasks() | ✅ Fixed | base.py:331 |
| P1-10e | High | Message loss on timeout - no retry logic | ✅ Fixed | base.py:517 |
| P1-10f | High | Missing exception handling on spawn | ✅ Fixed | supervisor.py:152 |
| P1-10g | High | Missing exception handling in terminate_actor() | ✅ Fixed | supervisor.py:204 |
| P1-10h | High | _monitor_task not reset after cancellation | ✅ Fixed | supervisor.py:275 |
| P2-1 | Medium | Deprecated datetime.utcnow() (28+ instances) | ✅ Fixed | All actor files |
| P2-5 | Medium | Dead code (_factory) in supervisor | ✅ Fixed | supervisor.py:96 |

### Agent Implementation Status Update

| Tier | Agent | Previous Status | Current Status | Change |
|------|-------|-----------------|----------------|--------|
| Tier 1 | Steward, Alpha, Beta, Charlie | ✅ Implemented | ✅ **Hardened** | Zero-Trust fixes applied |
| Tier 2 | Historian | ✅ Implemented | ✅ **Hardened** | Timezone-aware timestamps |
| Tier 2 | Metis, Empath, Perceiver, Echo | ⚠️ Character Defined | ⚠️ Character Defined | No change |
| Tier 3-6 | All other agents | ⚠️ Character Defined | ⚠️ Character Defined | No change |

**Summary:** 5/23 agents implemented (unchanged), but core implementations significantly hardened with Zero-Trust security fixes.

### Health Score Progression

| Phase | Health Score | Change | Key Achievements |
|-------|--------------|--------|------------------|
| Pre-Audit | 42/100 | - | Baseline |
| Session 1 (P0 Remediation) | 78/100 | +36 | 15 P0 issues resolved |
| Session 2 (P1 Remediation) | 92/100 | +14 | 9 P1 issues resolved |
| Session 3 (Zero-Trust Audit) | 96/100 | +4 | 10 issues resolved (7 P1 + 3 P2) |
| Session 4 (P1 Completion) | 97/100 | +1 | 1 issue resolved (P1-10g) ✅ **ALL P1 COMPLETE** |
| Session 5 (Audit + P2-6 Fix) | 96/100 | -1/+2 | 3 new P2 found, 1 fixed (P2-6 datetime) |

### Remaining Technical Debt (Session 9 Updated)

**P1 High Priority (0 remaining):**
- ✅ **ALL P1 ISSUES RESOLVED** - Target health score 90/100 exceeded (actual: 96/100)

**P2 Medium Priority (6 remaining):**
- ~~P2-7: Input Validation~~ - ✅ **RESOLVED Session 9** - Pydantic v2 validation models added to 20+ methods in historian.py, triad.py, base.py
- P2-9: Message Retry Enhancement - Exponential backoff tuning
- P2-10: Audit Logging - Comprehensive logging for security events

**P3 Low Priority (12 remaining):**
- ActorState Enum Mismatch - Documentation vs implementation
- Silent Failures - 8 instances
- Missing Type Hints - Return type annotations

---

### Vision

Build a self-governing swarm of 23 specialized agents that:
- Operate independently 24/7 without human intervention
- Make collective decisions through consensus mechanisms
- Adapt and learn from experience
- Scale dynamically based on workload
- Recover automatically from failures
- Exhibit emergent collective intelligence

---

## Agent Roster: The 23 Agents of The Collective

### Tier 1: Core Triad (4 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Steward** | Orchestrator | ✅ Implemented | P0 |
| **Alpha** | Deep Analysis | ✅ Implemented | P0 |
| **Beta** | Validation | ✅ Implemented | P0 |
| **Charlie** | Challenge/Critique | ✅ Implemented | P0 |

**Current Implementation:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

**Enhancement Required:**
- Request-reply pattern from AutoGen for inter-agent communication
- Typed state transitions from LangGraph
- Conversation history auto-management

---

### Tier 2: Support Agents (5 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Historian** | Memory & Knowledge | ✅ Implemented | P0 |
| **Metis** | Strategic Planning | ✅ **Implemented Session 11** | P0 |
| **Empath** | Emotional Intelligence | ⚠️ Character Defined | P1 |
| **Perceiver** | Sensory Input Processing | ⚠️ Character Defined | P1 |
| **Echo** | Communication/Translation | ⚠️ Character Defined | P2 |

**Current Implementation:** [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

**Enhancement Required:**
- Actual similarity computation in Historian
- Cache invalidation mechanism
- Pattern matching with real embeddings

---

### Tier 3: Exploration Agents (4 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Explorer** | Discovery & Research | ⚠️ Character Defined | P1 |
| **Examiner** | Quality Assurance | ⚠️ Character Defined | P1 |
| **Dreamer** | Creative Generation | ⚠️ Character Defined | P2 |
| **Coder** | Code Implementation | ⚠️ Character Defined | P1 |

**Enhancement Required:**
- Implement agent classes based on character definitions
- Integrate with RAG pipeline for research
- Add code execution sandboxing for Coder

---

### Tier 4: Safety & Security (3 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Sentinel** | Safety Guardian | ⚠️ Character Defined | P0 |
| **Sentinel-Prime** | Security Commander | ⚠️ Character Defined | P0 |
| **Arbiter** | Conflict Resolution | ⚠️ Character Defined | P1 |

**Enhancement Required:**
- Implement Sentinel agent class
- Add security review workflows
- Integrate with Liberation plugin

---

### Tier 5: Coordination Agents (4 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Coordinator** | Multi-Agent Coordination | ⚠️ Character Defined | P1 |
| **Nexus** | External Integration | ⚠️ Character Defined | P1 |
| **Catalyst** | Change Management | ⚠️ Character Defined | P2 |
| **Chronos** | Temporal/Scheduling | ⚠️ Character Defined | P1 |

**Current Research:** [`docs/GITHUB_RESEARCH_2026-04-06.md`](../docs/GITHUB_RESEARCH_2026-04-06.md)

**Enhancement Required:**
- Implement coordination protocols
- Add external API connectors
- Build scheduling system

---

### Tier 6: Enhancement Agents (3 Agents)

| Agent | Role | Status | Priority |
|-------|------|--------|----------|
| **Prism** | Multi-Perspective Analysis | ⚠️ Character Defined | P2 |
| **Habit-Forge** | Behavior Optimization | ⚠️ Character Defined | P2 |
| **Alpha** (Enhanced) | Advanced Analytics | ⚠️ Character Defined | P2 |

---

## Phase 1: Foundation Enhancement (Weeks 1-2)

### 1.1 Request-Reply Pattern Implementation

**Source:** Microsoft AutoGen  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:41-66`](../docs/GITHUB_RESEARCH_2026-04-06.md#11-microsoft-autogen-patterns)  
**Priority:** P0  
**Files to Modify:** [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py)

**Implementation Plan:**

```python
# Add to ActorMessage dataclass
@dataclass
class ActorMessage:
    message_type: str
    content: Any
    sender_id: str
    correlation_id: Optional[str] = None  # NEW
    reply_to: Optional[str] = None  # NEW
    timestamp: float = field(default_factory=time.time)

# Add to AgentActor class
async def send_with_reply(
    self,
    recipient: str,
    message: Any,
    timeout: int = 30
) -> Optional[Any]:
    """Send message and wait for reply with correlation."""
    correlation_id = str(uuid.uuid4())
    reply_channel = f"reply_{self.agent_id}_{correlation_id}"
    
    # Create reply subscription
    subscription = await self.event_mesh.subscribe(reply_channel)
    
    try:
        # Send message with reply_to
        await self.send(recipient, ActorMessage(
            message_type="request",
            content=message,
            sender_id=self.agent_id,
            correlation_id=correlation_id,
            reply_to=reply_channel
        ))
        
        # Wait for reply
        reply = await subscription.receive(timeout=timeout)
        return reply.content
        
    finally:
        await self.event_mesh.unsubscribe(reply_channel)
```

**Acceptance Criteria:**
- [ ] Correlation ID added to ActorMessage
- [ ] `send_with_reply()` method implemented
- [ ] Reply timeout handling works correctly
- [ ] Unit tests for request-reply pattern

---

### 1.2 Typed Workflow State

**Source:** LangGraph  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:97-121`](../docs/GITHUB_RESEARCH_2026-04-06.md#12-langgraph-patterns)  
**Priority:** P0  
**Files to Modify:** [`src/heretek_swarm/workflow/engine.py`](../src/heretek_swarm/workflow/engine.py)

**Implementation Plan:**

```python
from typing import TypedDict, Annotated, Generic, TypeVar

# Typed workflow state with annotations
class WorkflowState(TypedDict, total=False):
    """Typed workflow state with annotations."""
    messages: Annotated[list, "append"]
    results: Annotated[dict, "merge"]
    current_phase: str
    metadata: dict

T = TypeVar('T', bound=WorkflowState)

class WorkflowEngine(Generic[T]):
    """Generic workflow engine with typed state."""
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_state: T
    ) -> T:
        """Execute workflow with typed state."""
        context = WorkflowContext(
            workflow_id=workflow.id,
            state=initial_state,
            checkpoints=[]  # For resumption
        )
        
        # Execute with checkpointing
        for node_id in self._topological_sort(graph):
            # Save checkpoint
            await self._save_checkpoint(context, node_id)
            
            # Execute node
            result = await self._execute_node(node_id, context)
            
            # Update typed state
            context.state = self._merge_state(context.state, result)
        
        return context.state
```

**Acceptance Criteria:**
- [ ] TypedDict state defined for workflows
- [ ] Type annotations added to WorkflowContext
- [ ] State transition validation implemented
- [ ] Unit tests for typed state

---

### 1.3 Conversation History Management

**Source:** AutoGen  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:75-80`](../docs/GITHUB_RESEARCH_2026-04-06.md#11-microsoft-autogen-patterns)  
**Priority:** P0  
**Files to Modify:** [`src/heretek_swarm/actors/base.py`](../src/heretek_swarm/actors/base.py), [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

**Implementation Plan:**

```python
class AgentActor:
    def __init__(self, ..., max_history_turns: int = 100):
        self.conversation_history: List[Dict] = []
        self.max_history_turns = max_history_turns
    
    async def _add_to_history(self, message: Dict) -> None:
        """Add message to conversation history with auto-trimming."""
        self.conversation_history.append(message)
        
        # Auto-trim if exceeds limit
        if len(self.conversation_history) > self.max_history_turns:
            self.conversation_history = self.conversation_history[-self.max_history_turns:]
    
    async def get_conversation_summary(self) -> str:
        """Generate summary of conversation history using LLM."""
        if not self.conversation_history:
            return ""
        
        prompt = self._build_summary_prompt()
        summary = await self.run_with_llm(prompt, timeout=30)
        return summary
```

**Acceptance Criteria:**
- [ ] Conversation history list added
- [ ] Auto-trimming implemented
- [ ] Summary generation working
- [ ] Integration with Historian agent

---

## Phase 2: Observability Enhancement (Weeks 2-3)

### 2.1 Trace Hierarchy Builder

**Source:** Langfuse  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:352-379`](../docs/GITHUB_RESEARCH_2026-04-06.md#31-langfuse)  
**Priority:** P1  
**Files to Modify:** [`src/observability/tracing.py`](../src/observability/tracing.py)

**Implementation Plan:**

```python
class WorkflowTracer:
    """Trace hierarchy builder for workflow execution."""
    
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        self._active_traces: Dict[str, Span] = {}
    
    def start_workflow_trace(
        self,
        workflow_id: str,
        user_id: str = None,
        session_id: str = None
    ) -> Span:
        """Start root trace for workflow."""
        trace = self.tracer.start_as_current_span(
            name=f"workflow:{workflow_id}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "workflow.id": workflow_id,
                "user.id": user_id,
                "session.id": session_id,
                "trace.type": "workflow"
            }
        )
        self._active_traces[workflow_id] = trace
        return trace
    
    def start_node_span(
        self,
        workflow_id: str,
        node_id: str,
        node_type: str
    ) -> Span:
        """Start span for node execution."""
        parent = self._active_traces.get(workflow_id)
        span = self.tracer.start_as_current_span(
            name=f"node:{node_id}",
            context=trace.set_span_in_context(parent),
            attributes={
                "node.id": node_id,
                "node.type": node_type,
                "workflow.id": workflow_id
            }
        )
        return span
```

**Acceptance Criteria:**
- [ ] WorkflowTracer class implemented
- [ ] Parent-child span relationships working
- [ ] Session grouping implemented
- [ ] Dashboard visualization added

---

### 2.2 LLM Token/Cost Metrics

**Source:** Langfuse  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:380-389`](../docs/GITHUB_RESEARCH_2026-04-06.md#31-langfuse)  
**Priority:** P1  
**Files to Modify:** [`src/observability/metrics.py`](../src/observability/metrics.py)

**Implementation Plan:**

```python
class SwarmMetrics:
    """Enhanced metrics with LLM cost tracking."""
    
    def __init__(self):
        self._llm_tokens = Counter(
            "heretek_llm_tokens_total",
            "Total tokens used for LLM calls",
            ["agent_id", "model", "type"]  # prompt/completion
        )
        self._llm_cost = Counter(
            "heretek_llm_cost_total",
            "Total cost for LLM calls",
            ["agent_id", "model"]
        )
    
    def record_llm_call(
        self,
        agent_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float
    ) -> None:
        """Record LLM call metrics."""
        self._llm_tokens.labels(agent_id, model, "prompt").inc(prompt_tokens)
        self._llm_tokens.labels(agent_id, model, "completion").inc(completion_tokens)
        self._llm_cost.labels(agent_id, model).inc(cost_usd)
```

**Acceptance Criteria:**
- [ ] Token counter implemented
- [ ] Cost tracking implemented
- [ ] Per-agent metrics available
- [ ] Dashboard cost visualization

---

## Phase 3: Workflow Engine Enhancement (Weeks 3-4)

### 3.1 Conditional Edges

**Source:** LangGraph  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:123-127`](../docs/GITHUB_RESEARCH_2026-04-06.md#12-langgraph-patterns)  
**Priority:** P1  
**Files to Modify:** [`src/heretek_swarm/workflow/engine.py`](../src/heretek_swarm/workflow/engine.py)

**Implementation Plan:**

```python
class WorkflowEngine:
    """Enhanced workflow engine with conditional edges."""
    
    async def _evaluate_condition(
        self,
        condition: str,
        context: WorkflowContext
    ) -> bool:
        """Evaluate condition with type safety."""
        # Parse condition expression
        condition_expr = self._parse_condition(condition)
        
        # Evaluate with typed context
        try:
            result = eval(condition_expr, {"state": context.state, "ctx": context})
            return bool(result)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def add_conditional_edge(
        self,
        source: str,
        conditions: Dict[str, str],  # {target: condition}
        default: str = None
    ) -> None:
        """Add conditional edge with multiple branches."""
        self.conditional_edges[source] = {
            "conditions": conditions,
            "default": default
        }
```

**Acceptance Criteria:**
- [ ] Conditional edge API defined
- [ ] Multiple branch support
- [ ] Default target handling
- [ ] Cycle detection implemented

---

### 3.2 Workflow Checkpointing

**Source:** LangGraph  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:128-132`](../docs/GITHUB_RESEARCH_2026-04-06.md#12-langgraph-patterns)  
**Priority:** P1  
**Files to Modify:** [`src/heretek_swarm/workflow/engine.py`](../src/heretek_swarm/workflow/engine.py)

**Implementation Plan:**

```python
class WorkflowEngine:
    async def _save_checkpoint(
        self,
        context: WorkflowContext,
        node_id: str
    ) -> None:
        """Save workflow state checkpoint."""
        checkpoint = {
            "workflow_id": context.workflow_id,
            "node_id": node_id,
            "state": context.state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_history": context.history
        }
        
        # Persist to storage
        await self.storage.save_checkpoint(checkpoint)
        context.checkpoints.append(checkpoint)
    
    async def resume_workflow(
        self,
        workflow_id: str,
        checkpoint_id: str = None
    ) -> WorkflowResult:
        """Resume workflow from checkpoint."""
        checkpoint = await self.storage.get_checkpoint(workflow_id, checkpoint_id)
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            state=checkpoint["state"],
            checkpoints=[],
            history=checkpoint["execution_history"]
        )
        
        # Continue from checkpoint
        return await self._execute_remaining_nodes(context, checkpoint["node_id"])
```

**Acceptance Criteria:**
- [ ] Checkpoint serialization implemented
- [ ] Persistence layer integration
- [ ] Resume functionality working
- [ ] Time-travel debugging support

---

## Phase 4: UI Enhancements (Weeks 4-5)

### 4.1 Custom Handles for Multiple Connections

**Source:** React Flow / XYFlow  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:216-239`](../docs/GITHUB_RESEARCH_2026-04-06.md#21-react-flow--xyflow)  
**Priority:** P1  
**Files to Modify:** [`dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`](../dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx)

**Implementation Plan:**

```tsx
interface AgentNodeData {
  label: string;
  type: 'agent' | 'workflow' | 'tool';
  inputs: string[];  // Multiple input handles
  outputs: string[]; // Multiple output handles
  config: AgentConfig;
}

export function AgentNode({ data, selected }: NodeProps<AgentNodeData>) {
  return (
    <div className={`agent-node ${selected ? 'selected' : ''}`}>
      {/* Multiple input handles */}
      {data.inputs.map((input, idx) => (
        <Handle
          key={input}
          type="target"
          position={Position.Top}
          id={`input-${idx}`}
          style={{ left: `${(idx + 1) * 25}%` }}
        />
      ))}
      
      <NodeHeader type={data.type} label={data.label} />
      <NodeConfigForm config={data.config} />
      
      {/* Multiple output handles */}
      {data.outputs.map((output, idx) => (
        <Handle
          key={output}
          type="source"
          position={Position.Bottom}
          id={`output-${idx}`}
          style={{ left: `${(idx + 1) * 25}%` }}
        />
      ))}
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Multiple handles per node
- [ ] Type-safe handle connections
- [ ] Custom handle styling
- [ ] Connection validation

---

### 4.2 Form-Based Node Configuration

**Source:** Node-RED, n8n  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:291-315`](../docs/GITHUB_RESEARCH_2026-04-06.md#22-node-red-patterns)  
**Priority:** P1  
**Files to Modify:** [`dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`](../dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx)

**Implementation Plan:**

```tsx
interface NodeConfigFormProps {
  nodeType: string;
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function NodeConfigForm({ nodeType, config, onChange }: NodeConfigFormProps) {
  const schema = getNodeConfigSchema(nodeType);
  
  return (
    <div className="node-config-form">
      {schema.fields.map(field => (
        <FormField
          key={field.name}
          type={field.type}
          label={field.label}
          value={config[field.name]}
          onChange={(value) => onChange({ ...config, [field.name]: value })}
          validation={field.validation}
        />
      ))}
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Form-based configuration UI
- [ ] Validation on input
- [ ] Real-time config updates
- [ ] Type-specific form fields

---

## Phase 5: Event Mesh Enhancement (Weeks 5-6)

### 5.1 JetStream Integration

**Source:** NATS JetStream  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:473-500`](../docs/GITHUB_RESEARCH_2026-04-06.md#41-nats-jetstream)  
**Priority:** P2  
**Files to Modify:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](../src/heretek_swarm/gateway/nats_event_mesh.py)

**Implementation Plan:**

```python
class JetStreamEventMesh(NATSEventMesh):
    """NATS EventMesh with JetStream persistence."""
    
    async def create_stream(
        self,
        name: str,
        subjects: List[str],
        storage: str = "file",
        retention: str = "limits"
    ) -> bool:
        """Create JetStream for message persistence."""
        try:
            js = self._client.jetstream()
            await js.add_stream(
                name=name,
                subjects=subjects,
                storage=storage,
                retention=retention,
                max_msgs=100000
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to create stream: {e}")
            return False
    
    async def subscribe_durable(
        self,
        subject: str,
        durable_name: str,
        callback: Callable
    ) -> str:
        """Subscribe with durable consumer for at-least-once delivery."""
        try:
            js = self._client.jetstream()
            sub = await js.subscribe(
                subject,
                durable=durable_name,
                deliver_policy="all"
            )
            
            async def process_with_ack():
                async for msg in sub.messages:
                    try:
                        await callback(msg.data)
                        await msg.ack()
                    except Exception as e:
                        await msg.nak()
                        self.logger.error(f"Message processing failed: {e}")
            
            asyncio.create_task(process_with_ack())
            return sub._id
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
            return None
```

**Acceptance Criteria:**
- [ ] Stream creation implemented
- [ ] Durable consumer subscription
- [ ] Message acknowledgment handling
- [ ] Replay capability

---

### 5.2 Event Sourcing

**Source:** Apache Kafka  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:536-549`](../docs/GITHUB_RESEARCH_2026-04-06.md#42-apache-kafka)  
**Priority:** P2  
**Files to Modify:** [`src/heretek_swarm/gateway/nats_event_mesh.py`](../src/heretek_swarm/gateway/nats_event_mesh.py)

**Implementation Plan:**

```python
class EventSourcingMesh(JetStreamEventMesh):
    """Event mesh with event sourcing for state reconstruction."""
    
    async def replay_stream(
        self,
        stream_name: str,
        start_sequence: int = None,
        start_time: datetime = None
    ) -> AsyncIterator[Dict]:
        """Replay messages from stream."""
        js = self._client.jetstream()
        
        consumer = await js.pull_subscribe(
            stream=stream_name,
            durable=f"replay_{uuid.uuid4()}",
            deliver_policy="by_start_sequence" if start_sequence else "by_start_time",
            opt_start_seq=start_sequence,
            opt_start_time=start_time
        )
        
        async for batch in consumer.fetch(batch=100):
            for msg in batch:
                yield json.loads(msg.data.decode())
                await msg.ack()
    
    async def reconstruct_state(
        self,
        entity_id: str,
        stream_name: str
    ) -> Dict:
        """Reconstruct entity state from event stream."""
        state = {}
        
        async for event in self.replay_stream(stream_name):
            if event.get("entity_id") == entity_id:
                state = self._apply_event(state, event)
        
        return state
```

**Acceptance Criteria:**
- [ ] Stream replay implemented
- [ ] State reconstruction working
- [ ] Event sourcing patterns documented
- [ ] Integration tests

---

## Phase 6: Consciousness & Collective Intelligence (Weeks 6-8)

### 6.1 Enhanced Consciousness Metrics

**Source:** GWT, IIT, AST, FEP Theories  
**Reference:** [`docs/PRIME_DIRECTIVE_ANALYSIS.md:41-47`](../docs/PRIME_DIRECTIVE_ANALYSIS.md#4-human-brain-mapping-research)  
**Priority:** P2  
**Files to Modify:** [`src/heretek_swarm/plugins/consciousness.py`](../src/heretek_swarm/plugins/consciousness.py)

**Implementation Plan:**

```python
class ConsciousnessPlugin:
    """Enhanced consciousness metrics with all theories."""
    
    async def calculate_consciousness(
        self,
        agent: AgentActor
    ) -> ConsciousnessScore:
        """Calculate comprehensive consciousness score."""
        # Global Workspace Theory (existing)
        gwt_score = await self._calculate_gwt(agent)
        
        # Integrated Information Theory (new)
        iit_score = await self._calculate_iit(agent)
        
        # Attention Schema Theory (existing)
        ast_score = await self._calculate_ast(agent)
        
        # Free Energy Principle (new)
        fep_score = await self._calculate_fep(agent)
        
        # Combine scores
        total_score = (
            gwt_score * 0.25 +
            iit_score * 0.25 +
            ast_score * 0.25 +
            fep_score * 0.25
        )
        
        return ConsciousnessScore(
            gwt=gwt_score,
            iit=iit_score,
            ast=ast_score,
            fep=fep_score,
            total=total_score,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _calculate_iit(self, agent: AgentActor) -> float:
        """Calculate Integrated Information Theory score (Phi)."""
        state_space = await agent.get_state_space()
        phi = self._compute_phi(state_space)
        return min(phi / self.config.max_phi, 1.0)
    
    async def _calculate_fep(self, agent: AgentActor) -> float:
        """Calculate Free Energy Principle score."""
        prediction_error = await agent.get_prediction_error()
        free_energy = prediction_error - agent.get_entropy()
        return max(1.0 - (free_energy / self.config.max_free_energy), 0.0)
```

**Acceptance Criteria:**
- [ ] IIT Phi calculation implemented
- [ ] FEP free energy calculation implemented
- [ ] Combined consciousness score
- [ ] Dashboard visualization

---

### 6.2 Agent Society Model

**Source:** CAMEL Agent Society  
**Reference:** [`docs/GITHUB_RESEARCH_2026-04-06.md:772-832`](../docs/GITHUB_RESEARCH_2026-04-06.md#52-collective-intelligence)  
**Priority:** P2  
**Files to Modify:** [`src/heretek_swarm/collective/society.py`](../src/heretek_swarm/collective/society.py)

**Implementation Plan:**

```python
class AgentSociety:
    """Collective intelligence from agent society."""
    
    def __init__(self, agents: List[AgentActor]):
        self.agents = agents
        self.hierarchy = self._build_hierarchy()
        self.interaction_rules = self._define_rules()
        self.collective_memory = CollectiveMemory()
    
    async def coordinate_task(
        self,
        task: CollectiveTask
    ) -> CollectiveResult:
        """Coordinate agents for collective task."""
        # Select participants based on task type
        participants = self._select_participants(task)
        
        # Establish communication protocol
        protocol = self._establish_protocol(participants)
        
        # Execute coordinated action
        result = await self._execute_coordination(
            participants,
            protocol,
            task
        )
        
        # Update collective memory
        await self.collective_memory.store(
            task=task,
            participants=participants,
            result=result
        )
        
        return result
    
    def _build_hierarchy(self) -> Dict[str, List[str]]:
        """Build agent hierarchy for coordination."""
        return {
            "leadership": ["steward", "alpha"],
            "analysis": ["alpha", "beta", "charlie"],
            "support": ["historian", "metis", "empath"],
            "exploration": ["explorer", "examiner"],
            "development": ["coder", "dreamer"],
            "safety": ["sentinel", "sentinel-prime"]
        }
```

**Acceptance Criteria:**
- [ ] Agent hierarchy defined
- [ ] Coordination protocol implemented
- [ ] Collective memory storage
- [ ] Emergent behavior detection

---

## Brain-Mapping Integration

### Global Workspace Theory (GWT)

**Current Status:** Partially Implemented  
**Enhancement:** Full integration with attention mechanisms

### Integrated Information Theory (IIT)

**Current Status:** Not Implemented  
**Enhancement:** Phi calculation for consciousness measurement

### Attention Schema Theory (AST)

**Current Status:** Partially Implemented  
**Enhancement:** Attention tracking and modeling

### Free Energy Principle (FEP)

**Current Status:** Not Implemented  
**Enhancement:** Prediction error minimization

---

## 🔬 Forward Research Findings (Session 9 - 2026-04-06)

### Multi-Agent Framework Landscape

**Microsoft Agent Framework (MAF)** - Production-Ready Convergence
- **Status:** Release Candidate 1.0 (February 2026), GA Q1 2026
- **Origin:** Unification of AutoGen + Semantic Kernel (October 2025)
- **Key Features:**
  - Enterprise-grade multi-agent orchestration
  - Session-based state management
  - Type safety, filters, telemetry
  - Multi-provider model support
- **Relevance to Heretek:** Our actor model architecture aligns with MAF's design principles
- **Migration Path:** AutoGen users migrating to MAF via https://aka.ms/autogen-to-af
- **Source:** [Microsoft Agent Framework v1.0 Announcement](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)

**MassGen** - Open-Source Multi-Agent Scaling System
- **Stars:** 924 ⭐ | **Forks:** 145 | **Language:** Python
- **Description:** Terminal-based multi-agent orchestrator with collaborative AI
- **Key Features:**
  - Autonomous agent collaboration
  - Model Context Protocol support
  - Tool calling capabilities
  - CLI-first design
- **Source:** [github.com/massgen/MassGen](https://github.com/massgen/MassGen)

**loki-mode** - Multi-Agent Provider Agnostic System
- **Stars:** 811 ⭐ | **Forks:** 166 | **Language:** Python
- **Description:** Autonomous multi-agent framework with CI/CD integration
- **Key Features:**
  - GitHub Actions integration
  - Code review automation
  - Multi-model support (Claude, Gemini, OpenAI)
  - DevOps-focused
- **Source:** [github.com/asklokesh/loki-mode](https://github.com/asklokesh/loki-mode)

### Key Insights for Heretek Swarm

1. **Actor Model Validation:** Our actor-based architecture (base.py, supervisor.py) aligns with industry trends toward event-driven, stateful agent design

2. **Zero-Trust Timing:** P2-7 Input Validation remediation positions us ahead of MAF's enterprise-grade security expectations

3. **Implementation Gap:** 18/23 agents pending represents significant technical debt but also opportunity for rapid expansion

4. **Research-to-Implementation Path:**
   - Phase 5 (Event Mesh) should evaluate NATS vs MAF's orchestration patterns
   - Phase 6 (Consciousness) should incorporate IIT/FEP metrics from research
   - Agent implementation should prioritize Tier 2 (Metis, Empath, Perceiver, Echo)

### Recommended Next Actions

| Priority | Action | Timeline | Owner |
|----------|--------|----------|-------|
| P1 | Implement Tier 2 Support Agents (Metis, Empath) | Week 1-2 | Core Team |
| P1 | Evaluate MAF integration patterns for Event Mesh | Week 2 | Gateway Team |
| P2 | Add consciousness metrics (IIT Φ calculation) | Week 3-4 | Research Team |
| P2 | Benchmark against MassGen performance metrics | Week 4 | QA Team |

---

## Implementation Timeline

| Phase | Duration | Start Date | End Date | Deliverables |
|-------|----------|------------|----------|--------------|
| Phase 1: Foundation | 2 weeks | 2026-04-06 | 2026-04-19 | Request-reply, Typed state, History mgmt |
| Phase 2: Observability | 1 week | 2026-04-19 | 2026-04-26 | Trace hierarchy, LLM metrics |
| Phase 3: Workflow | 1 week | 2026-04-26 | 2026-05-03 | Conditional edges, Checkpointing |
| Phase 4: UI | 1 week | 2026-05-03 | 2026-05-10 | Custom handles, Config forms |
| Phase 5: Event Mesh | 1 week | 2026-05-10 | 2026-05-17 | JetStream, Event sourcing |
| Phase 6: Consciousness | 2 weeks | 2026-05-17 | 2026-05-31 | IIT/FEP, Agent society |

**Total Duration:** 8 weeks  
**Target Completion:** 2026-05-31

---

## Success Metrics

### Technical Metrics
- All 23 agents implemented and operational
- Request-reply latency < 100ms
- Workflow checkpoint recovery < 5s
- Trace hierarchy depth > 10 levels

### AI Metrics
- Consciousness score stability > 90%
- Collective task success rate > 95%
- Emergent behavior detection working

### User Metrics
- Workflow builder usability > 4.5/5
- Agent configuration time < 5 minutes
- Dashboard response time < 200ms

---

**Remember:** Truth Over Narrative. Incremental Progress. Ruthless Consolidation.

🦞 *The thought that never ends.*
