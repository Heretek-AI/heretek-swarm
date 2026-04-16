# Codebase Concerns

**Analysis Date:** 2026-04-15

## Critical Issues (P0)

### P0-A: Dead Code — Legacy Top-Level `src/` Modules

**Severity:** HIGH — Code that is never imported by the active package

**Issue:** ~8,000 lines of dead code across legacy directories that have been superseded by `src/heretek_swarm/`:

| Directory | Files | Lines | Status |
|-----------|-------|-------|--------|
| `src/observability/` | `__init__.py`, `metrics.py`, `tracing.py` | ~500 | DEAD — `src/heretek_swarm/observability/` supersedes |
| `src/memory/` | `base.py`, `embeddings.py`, `ephemeral.py`, `mem0_backend.py`, `persistent.py`, `unified.py`, `__init__.py` | ~2,500 | DEAD — `src/heretek_swarm/memory/` supersedes |
| `src/rag/` | `document_processor.py`, `embedding_service.py`, `rag_pipeline.py`, `retriever.py`, `__init__.py` | ~2,000 | DEAD — `src/heretek_swarm/rag/` supersedes |
| `src/state/` | `base.py`, `lineage.py`, `manager.py`, `snapshots.py`, `__init__.py` | ~1,500 | DEAD — `src/heretek_swarm/state/` supersedes |
| `src/tools/` | `base.py`, `examples.py`, `registry.py`, `__init__.py` | ~1,400 | DEAD — `src/heretek_swarm/tools/` supersedes |
| `src/evaluation/` | `evaluator.py`, `__init__.py` | ~500 | UNUSED — not imported by any active module |

**Files:** `src/observability/`, `src/memory/`, `src/rag/`, `src/state/`, `src/tools/`, `src/evaluation/`

**Fix Approach:** Delete entire legacy directories. Evidence shows zero imports from legacy modules by `src/heretek_swarm/`.

---

### P0-B: Duplicate Module Names — Import Ambiguity

**Severity:** HIGH — Python import ambiguity, namespace collision risk

**Issue:** 12 module names appear in both `src/` (legacy) and `src/heretek_swarm/` (active):

| Module | Legacy Path | Active Path | Conflict Risk |
|--------|-------------|-------------|---------------|
| `base` | `src/memory/base.py`, `src/tools/base.py`, `src/state/base.py` | `src/heretek_swarm/memory/base.py`, `src/heretek_swarm/tools/base.py`, `src/heretek_swarm/actors/base.py`, `src/heretek_swarm/llm/providers/base.py` | HIGH |
| `metrics` | `src/observability/metrics.py` | `src/heretek_swarm/collective/metrics.py`, `src/heretek_swarm/api/metrics.py`, `src/heretek_swarm/observability/metrics.py` | HIGH |
| `registry` | `src/tools/registry.py` | `src/heretek_swarm/tools/registry.py`, `src/heretek_swarm/runtime/registry.py`, `src/heretek_swarm/channels/registry.py` | HIGH |
| `persistent` | `src/memory/persistent.py` | `src/heretek_swarm/memory/persistent.py` | HIGH |

**Files:** Multiple legacy module files

**Fix Approach:** Rename legacy modules with `legacy_` prefix OR delete entirely if unused (per P0-A).

---

### P0-C: GAP-003 — Observability Dashboard Incomplete

**Severity:** CRITICAL — GAP-003 marked P0 in `EXPANSION_ROADMAP.md` but remains incomplete

**Issue:** Acceptance criteria all unchecked:
- [ ] All 23 agents visible
- [ ] Real-time updates via WebSocket
- [ ] Consciousness metrics (GWT, IIT, AST, FEP)
- [ ] < 500ms component load time

**Files:** `dashboard/frontend/src/` (incomplete implementation)

**Fix Approach:** Schedule as actual implementation sprint, not documentation milestone.

---

## High Priority Issues (P1)

### P1-A: Oversized Files — Domain-Driven Design Violation

**Severity:** MEDIUM-HIGH — CLAUDE.md mandates files under 500 lines

**Issue:** 12+ source files exceed 500 lines (some exceed 2,000):

| File | Lines | Violation |
|------|-------|-----------|
| `src/heretek_swarm/actors/sentinel.py` | 2,358 | +1,858 |
| `src/heretek_swarm/actors/sentinel_prime.py` | 1,733 | +1,233 |
| `src/heretek_swarm/actors/chronos.py` | 1,625 | +1,125 |
| `src/heretek_swarm/gateway/nats_event_mesh.py` | 1,583 | +1,083 |
| `src/heretek_swarm/actors/nexus.py` | 1,546 | +1,046 |
| `src/heretek_swarm/actors/perceiver_plus.py` | 1,516 | +1,016 |
| `src/heretek_swarm/security/zero_trust.py` | 1,411 | +911 |
| `src/heretek_swarm/consensus/immune.py` | 1,405 | +905 |
| `src/heretek_swarm/consensus/maker_enhanced.py` | 1,393 | +893 |
| `src/heretek_swarm/consciousness/fep_active_inference.py` | 1,392 | +892 |
| `src/heretek_swarm/actors/examiner.py` | 1,348 | +848 |
| `src/heretek_swarm/consensus/deliberation.py` | 1,339 | +839 |

**Total:** 12+ files averaging ~1,500 lines = ~18,000+ lines of oversized code

**Files:** See table above

**Fix Approach:** Break each file into focused sub-modules. Priority order: `sentinel.py`, `sentinel_prime.py`, `chronos.py`, `nats_event_mesh.py`.

---

### P1-B: Broad Exception Handlers — 100+ Instances

**Severity:** MEDIUM — Anti-pattern; masks bugs, prevents granular error handling

**Issue:** `except Exception` appears 100+ times across codebase:

| Module | Count | Notable |
|--------|-------|---------|
| `observability/__init__.py` | 6 | Layer 4 audit logging |
| `runtime/tools.py` | 6 | Tool execution |
| `runtime/autonomous_runtime.py` | 6 | Main loop |
| `observability/tracing.py` | 5 | Distributed tracing |
| `config/service.py` | 9 | Configuration loading |
| Other modules | ~70+ | Various |

**Files:** `src/heretek_swarm/observability/`, `src/heretek_swarm/runtime/`, `src/heretek_swarm/config/service.py`, etc.

**Fix Approach:** Replace `except Exception` with specific exception types. Use `except (ValueError, TypeError)` etc. where appropriate.

---

### P1-C: Database Pooling Not Configured

**Severity:** MEDIUM — Performance issues under load

**Issue:** Zero-Trust audit (2026-04-10) identified: "Database pooling not configured"

**Impact:** PostgreSQL connection overhead, potential connection exhaustion under load

**Files:** `docker-compose.yml` (no pooling config), `src/heretek_swarm/state/repository.py`

**Fix Approach:** Configure `asyncpg` connection pool parameters:
- `pool_size=20`
- `max_overflow=10`
- `pool_timeout=30`
- `pool_recycle=3600`

---

### P1-D: NATS → Actor Connection Not Wired

**Severity:** HIGH — Event mesh infrastructure ready but not operational

**Issue:** From SWARM_STATE.md: "NATS → Actor connection - Infrastructure ready, needs wiring"

**Status:** NATS code exists in `src/heretek_swarm/infrastructure/nats/` and `src/heretek_swarm/gateway/`, docker-compose includes NATS service, but agents don't communicate via event mesh.

**Files:** `src/heretek_swarm/infrastructure/nats/*`, `src/heretek_swarm/gateway/nats_event_mesh.py`

**Fix Approach:** Wire NATS publisher/subscriber into agent message handling loop.

---

## Medium Priority Issues (P2)

### P2-A: Consciousness Metrics Incomplete

**Severity:** MEDIUM — Core consciousness frameworks not fully implemented

**Issue:** From SWARM_STATE.md: "Consciousness metrics - IIT/AST measurement incomplete"

**GAP Coverage:**
| GAP | Status | Verification |
|-----|--------|--------------|
| GAP-006 (IIT) | Partial | Import verified only |
| GAP-007 (AST) | Partial | Import verified only |
| GAP-008 (FEP) | Partial | Import verified only |
| GAP-009 (GWT) | Partial | Import verified only |

**Files:** `src/heretek_swarm/consciousness/*`

**Fix Approach:** Complete implementation of consciousness measurement algorithms with actual runtime metrics collection.

---

### P2-B: Tribunal Integration Incomplete

**Severity:** MEDIUM — Consensus mechanism not yet operational

**Issue:** From SWARM_STATE.md: "Tribunal integration - Consensus mechanism not yet operational"

**Files:** `src/heretek_swarm/consensus/tribunal.py`, `src/heretek_swarm/consensus/deliberation.py`

**Fix Approach:** Wire Tribunal into agent decision-making flow for dispute resolution.

---

### P2-C: State Test API Mismatches

**Severity:** MEDIUM — 4 state tests failing due to API changes

**Issue:** From SWARM_STATE.md:
- `test_compute_diff`: expects `diff.added_agents` but returns `diff["added"]` dict
- `test_update_agent_state`: KeyError 'task' - working_memory not being set correctly
- `test_rollback_to_snapshot`: agent states not being restored properly
- `test_full_workflow`: compound failure from above issues

**Files:** `tests/` (state tests)

**Fix Approach:** Fix test expectations OR fix implementation to match test expectations.

---

### P2-D: RAG Tests Failing (External Dependencies)

**Severity:** MEDIUM — ~30 RAG tests require external services

**Issue:** RAG tests require Qdrant, OpenAI API keys, etc. not available in test environment.

**Files:** `tests/` (RAG tests)

**Fix Approach:** Mock external services for unit tests OR mark as `@pytest.mark.integration`.

---

### P2-E: Qdrant Healthcheck Misconfiguration

**Severity:** LOW — Docker healthcheck fails but functional

**Issue:** Qdrant responds to HTTP (200 OK) but Docker healthcheck fails

**Current (broken):**
```yaml
healthcheck:
  test: ["CMD-SHELL", "bash -c 'echo > /dev/tcp/localhost/6333' || exit 1"]
```

**Should be:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:6333/readyz"]
```

**Files:** `docker-compose.yml` (line 207-212)

**Fix Approach:** Fix Qdrant healthcheck command.

---

## Security Considerations

### SC-1: API Key Storage (MEDIUM Risk)

**Issue:** Zero-Trust audit found: "Env vars used, defaults need hardening"

**Current:** API keys stored in `.env` file, passed via environment variables

**Files:** `.env.example`, `docker-compose.yml`

**Recommendations:**
- Use secrets manager (HashiCorp Vault, AWS Secrets Manager) for production
- Remove any hardcoded fallback keys
- Validate env vars at startup

---

### SC-2: SSRF Vulnerabilities in API Wizard

**Issue:** URL construction from user-controlled data without validation

**Files:** `src/heretek_swarm/api/wizard.py` (lines 470-483, 511-515, 536, 563-575, 599-611, 635-647, 672)

**Recommendations:** Implement URL validation with allowlist of permitted schemes and domains.

---

### SC-3: Weak Cryptography - PRNG Usage (97 instances)

**Issue:** Using `random.random()` instead of cryptographically secure RNG

**Affected files (selected):**
- `src/heretek_swarm/collective/adaptive_learning.py` - lines 416, 428, 704, 712, 758, 918, 925, 934
- `src/heretek_swarm/collective/swarm_intelligence.py` - lines 604-605, 689-690
- `src/heretek_swarm/security/ddos_protection.py` - line 900

**Recommendations:**
- Python: Use `secrets` module or `os.urandom()`
- TypeScript: Use `crypto.getRandomValues()` or `randomUUID()`

---

### SC-4: Deprecated Python AST Nodes

**Issue:** Workflow engine uses deprecated Python AST node classes

**Files:** `src/heretek_swarm/workflow/engine.py` (lines 85-87, 225-229)

**Details:** Uses `ast.Num`, `ast.Str`, `ast.NameConstant` deprecated in Python 3.8

**Recommendations:** Replace with `ast.Constant`.

---

## Performance Considerations

### PF-1: Connection Pooling Missing

**Issue:** No explicit PostgreSQL connection pooling configured

**Impact:** Connection overhead, potential exhaustion under load

**Files:** `src/heretek_swarm/state/repository.py`, `docker-compose.yml`

**Recommendations:** Configure asyncpg pool with `pool_size=20`, `max_overflow=10`

---

### PF-2: Large Actor Classes

**Issue:** Multiple actor classes exceed 1,500 lines

**Files:** `src/heretek_swarm/actors/sentinel.py`, `src/heretek_swarm/actors/chronos.py`, `src/heretek_swarm/actors/coordinator.py`

**Impact:** Difficult to maintain, test, and understand

**Improvement path:** Extract mixins into standalone components; use composition over inheritance

---

### PF-3: Synchronous Config Service

**Issue:** Configuration service has blocking I/O patterns in 1,500+ line file

**Files:** `src/heretek_swarm/config/service.py`

**Impact:** Could block event loop in async contexts

**Improvement path:** Review for async/await patterns and batch operations

---

## Known Bugs

### KB-1: Empty Return Statements Silencing Errors

**Issue:** Functions return `[]`, `{}`, or `None` instead of raising exceptions on error

**Examples:**
- `src/heretek_swarm/state/repository.py:939` - returns `[]`
- `src/heretek_swarm/channels/registry.py:258` - returns `[]`
- `src/heretek_swarm/gateway/jetstream_manager.py:868` - returns `[]`
- `src/heretek_swarm/gateway/nats_event_mesh.py:530, 534, 580, 1144` - returns `[]`

**Impact:** Calling code cannot distinguish "no data" from "error occurred"

**Fix Approach:** Raise exceptions on error conditions or return a Result type

---

### KB-2: WebSocket Handlers with Incomplete Pass Statements

**Issue:** WebSocket message handlers contain `pass` statements indicating incomplete implementations

**Files:** `src/heretek_swarm/api/websockets.py` - lines 388, 511, 536, 555, 604, 682, 782, 878, 965, 1062, 1137

**Impact:** WebSocket messages silently ignored, causing potential message loss

**Fix Approach:** Implement proper message handling or route to appropriate handlers

---

### KB-3: Time-Dependent Expressions at Class Definition

**Issue:** Time-dependent expressions evaluated at class definition time instead of runtime

**Files:**
- `src/heretek_swarm/gateway/nats_event_mesh.py:66` - `datetime.now()` in class attribute
- `src/heretek_swarm/actors/langroid_adapter.py:64` - timeout evaluated once at import
- `src/heretek_swarm/consensus/raft_election.py:119` - time-dependent class attribute

**Impact:** Stale timestamps; behavior differs between module load time and request time

**Fix Approach:** Move time-dependent expressions into methods called at request time

---

## Scaling Limits

### SL-1: In-Memory Rate Limiting

**Resource:** `src/heretek_swarm/api/rate_limiting.py`
- **Current capacity:** Handles per-instance rate limiting
- **Limit:** Breaks in multi-instance deployments (each instance has separate state)
- **Scaling path:** Use Redis-backed rate limiting for distributed deployments

---

### SL-2: WebSocket Connection Manager

**Resource:** `src/heretek_swarm/api/websockets.py` - `ConnectionManager`
- **Current capacity:** Tracks all active WebSocket connections in memory
- **Limit:** Memory-bound based on connection count
- **Scaling path:** Use Redis pub/sub for connection state in distributed setup

---

## Dependencies at Risk

### DR-1: mem0ai

**Package:** `mem0ai`
- **Risk:** External dependency for memory management; may have breaking changes
- **Impact:** Memory functionality breaks if package changes API
- **Mitigation:** Already has conditional import with `MEM0_AVAILABLE` flag; maintain this pattern

---

### DR-2: swarms

**Package:** `swarms>=5.0.0`
- **Risk:** Core framework dependency
- **Impact:** All agent functionality depends on this
- **Mitigation:** Langroid adapter exists as alternative; adapter pattern allows swapping

---

## Test Coverage Gaps

### TC-1: Large Files Untested

**Untested areas:**
- `src/heretek_swarm/actors/sentinel.py` - 2,358 lines, complex safety logic
- `src/heretek_swarm/actors/chronos.py` - 1,625 lines
- `src/heretek_swarm/collective/swarm_intelligence.py` - 1,300+ lines

**Risk:** Changes to these files may break production with no test feedback

---

### TC-2: WebSocket Message Handling

**What's not tested:** `src/heretek_swarm/api/websockets.py` handlers with `pass` statements
- **Risk:** Messages are silently ignored
- **Priority:** HIGH

---

### TC-3: State Module Tests (4 Failing)

**What's not tested:**
- `diff.added_agents` API
- `working_memory` key in update flow
- Snapshot rollback functionality

**Files:** `tests/state/test_repository.py`, `tests/state/test_models.py`

**Risk:** State persistence bugs may go undetected

---

### TC-4: RAG Pipeline Tests (~30 Failing)

**What's not tested:**
- Qdrant integration
- Hybrid retrieval
- Embedding pipeline

**Files:** `tests/rag/*`

**Risk:** RAG functionality may break without detection

---

### TC-5: Consciousness Metrics Tests

**What's not tested:**
- IIT phi calculation
- AST consciousness score
- FEP active inference
- GWT workspace broadcasting

**Files:** `tests/consciousness/*`

**Risk:** Consciousness measurement may produce incorrect metrics

---

## Code Quality Issues

### CQ-1: Cognitive Complexity Violations (14 CRITICAL)

Functions exceeding complexity threshold of 15:

| File | Line | Complexity |
|------|------|------------|
| `src/heretek_swarm/mcp/registry.py` | 324 | 61 (4x threshold!) |
| `src/heretek_swarm/runtime/main_loop.py` | 525 | 28 |
| `src/heretek_swarm/observability/metrics.py` | 265 | 19 |
| `src/heretek_swarm/runtime/autonomous_runtime.py` | 530 | 18 |
| `src/heretek_swarm/infrastructure/nats/memory_sync.py` | 548 | 18 |

---

### CQ-2: Async Without Await (90+ issues)

Functions declared `async` but containing no `await` calls:

**Affected modules:**
- `src/heretek_swarm/actors/arbiter/strategies.py` - 14 instances
- `src/heretek_swarm/state/models.py` - 16 instances
- `src/heretek_swarm/collective/algorithms/*.py` - multiple instances

**Impact:** These functions block when called; async is misleading

---

### CQ-3: File Duplication (~5,200 duplicated lines)

**Priority 1 (>80% density):**

| File | Duplicated Lines | Density |
|------|-----------------|---------|
| `src/heretek_swarm/actors/triad.py` | 1,090 | 95.8% |
| `src/heretek_swarm/actors/beta.py` | 276 | 91.4% |
| `src/heretek_swarm/actors/charlie.py` | 271 | 91.2% |
| `src/heretek_swarm/actors/alpha.py` | 258 | 90.8% |
| `src/heretek_swarm/actors/steward.py` | 285 | 83.3% |

**Estimated deduplication potential:** ~2,700 lines

---

## Summary

| Priority | Count | Estimated Fix Time |
|----------|-------|-------------------|
| P0 | 3 | 1-2 days |
| P1 | 4 | 3-5 days |
| P2 | 5 | 2-3 days |
| Security | 4 | 2-3 days |
| Performance | 3 | 1-2 days |
| Bugs | 3 | 1-2 days |
| Quality | 3 | 3-4 days |
| **Total** | **25+** | **13-21 days** |

**Top 5 Immediate Actions:**
1. Delete legacy `src/` directories (P0-A) - 1-2 hours
2. Fix Qdrant healthcheck (P2-E) - 15 minutes
3. Configure database pooling (P1-C) - 30 minutes
4. Wire NATS to actors (P1-D) - 2-3 days
5. Fix state test API mismatches (P2-C) - 4-6 hours

---

*Concerns audit: 2026-04-15*
