# Remediation Guide

**Heretek Swarm - Developer Guide for Fixing the System**

**Version:** 2.0.0  
**Date:** 2026-04-07  
**Audit Reference:** Zero-Trust Audit Phase 5 Master Report  
**System Health Score:** 38/100

---

## Table of Contents

1. [Priority Hitlist](#1-priority-hitlist)
2. [Safe Harbors](#2-safe-harbors)
3. [Testing Mandate](#3-testing-mandate)
4. [Getting Started for Remediation Developers](#4-getting-started-for-remediation-developers)
5. [Code Quality Standards Going Forward](#5-code-quality-standards-going-forward)

---

## 1. Priority Hitlist

This section translates the "Definitively Broken" ledger from the Zero-Trust Audit into a prioritized, actionable checklist.

### P0: Critical (Week 1-2) - MUST FIX BEFORE ANY DEPLOYMENT

These items represent existential threats to the system. Do not deploy until all P0 items are complete.

---

#### P0-1: Add State Persistence Layer

**Health Score Impact:** 38 → 65 (+27 points)  
**Estimated Effort:** 3-4 days  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/actors/base.py:210`](src/heretek_swarm/actors/base.py:210) - In-memory state storage
- [`src/heretek_swarm/actors/base.py:765-837`](src/heretek_swarm/actors/base.py:765) - save_state() only called on terminate
- [`src/heretek_swarm/state/manager.py`](src/heretek_swarm/state/manager.py) - Complete in-memory state
- [`src/heretek_swarm/api/consensus.py:131-133`](src/heretek_swarm/api/consensus.py:131) - In-memory consensus store
- [`src/heretek_swarm/api/workflows.py:31`](src/heretek_swarm/api/workflows.py:31) - In-memory workflow store

**The Problem:**
All agent state, consensus history, and patterns are stored in-memory only. Any system restart results in **complete state loss**.

**What to Fix:**
1. Implement PostgreSQL-backed state storage for all agents
2. Add automatic checkpointing (every N minutes or after significant state changes)
3. Implement state recovery mechanisms on startup
4. Add state versioning for schema compatibility

**Acceptance Criteria:**
- [ ] Agent state survives restart
- [ ] Consensus rounds persist to PostgreSQL
- [ ] Workflow definitions persist to PostgreSQL
- [ ] State recovery on startup from last checkpoint
- [ ] State versioning with migration support

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:78-82`](docs/REMEDIATION_BACKLOG.md:78)

---

#### P0-2: Remove Dangerous eval()/exec() Patterns

**Health Score Impact:** 38 → 55 (+17 points)  
**Estimated Effort:** 1-2 days  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/actors/coder.py:142`](src/heretek_swarm/actors/coder.py:142) - `exec(llm_generated_code)`
- [`src/heretek_swarm/actors/nexus.py:89`](src/heretek_swarm/actors/nexus.py:89) - Unvalidated state update from LLM

**The Problem:**
Multiple agents use `eval()` and `exec()` on unvalidated LLM outputs, creating **remote code execution vulnerabilities**.

**What to Fix:**
1. Remove ALL `eval()` and `exec()` calls from the codebase
2. Replace with AST-based code parsing and validation
3. Implement sandboxed execution environment (e.g., Docker containers, restricted subprocess)
4. Add input validation for all LLM outputs before any state updates

**Acceptance Criteria:**
- [ ] Zero `eval()` calls in codebase
- [ ] Zero `exec()` calls in codebase
- [ ] All LLM outputs validated against schema before use
- [ ] Code generation uses AST parsing, not direct execution
- [ ] Sandboxed execution for any dynamic code

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:124-129`](docs/REMEDIATION_BACKLOG.md:124)

---

#### P0-3: Implement Input Validation for LLM Outputs

**Health Score Impact:** 38 → 50 (+12 points)  
**Estimated Effort:** 2-3 days  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/actors/base.py`](src/heretek_swarm/actors/base.py) - All 22 agents inherit unvalidated updates
- [`src/heretek_swarm/actors/nexus.py:89`](src/heretek_swarm/actors/nexus.py:89) - Specific unvalidated state update
- [`src/heretek_swarm/security/zero_trust.py`](src/heretek_swarm/security/zero_trust.py) - Add LLM output validation layer

**The Problem:**
LLM responses are not validated before state updates across multiple agents, enabling state corruption and injection attacks.

**What to Fix:**
1. Add Pydantic validation models for all LLM output schemas
2. Implement validation middleware for all state updates
3. Add rejection handling for invalid LLM outputs
4. Log all validation failures for audit

**Acceptance Criteria:**
- [ ] All LLM outputs validated against Pydantic models
- [ ] Invalid outputs rejected with error logging
- [ ] State updates require validation token
- [ ] Validation failures trigger alert

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:119`](docs/REMEDIATION_BACKLOG.md:119)

---

### P1: High (Weeks 3-4) - MUST FIX BEFORE PRODUCTION

These items are critical for production readiness but the system can be tested without them.

---

#### P1-1: Fix Memory Tier Migration

**Health Score Impact:** 55 → 70 (+15 points)  
**Estimated Effort:** 2-3 days  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/memory/tiering.py:234`](src/heretek_swarm/memory/tiering.py:234) - Broken migration loses metadata
- [`src/heretek_swarm/memory/base.py`](src/heretek_swarm/memory/base.py) - Stub persistent implementation
- [`src/heretek_swarm/memory/compression.py`](src/heretek_swarm/memory/compression.py) - Compression corrupts metadata

**The Problem:**
Memory tier migration corrupts state silently. The `migrate_to_cold()` function loses metadata and timestamps, and has no transactional integrity.

**What to Fix:**
1. Implement transactional tier migration with rollback
2. Preserve all metadata and timestamps during migration
3. Add migration audit logging
4. Implement integrity verification post-migration

**Acceptance Criteria:**
- [ ] Migration is transactional (all-or-nothing)
- [ ] Metadata preserved during migration
- [ ] Rollback on failure
- [ ] Migration audit trail
- [ ] Post-migration integrity check

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:147-154`](docs/REMEDIATION_BACKLOG.md:147)

---

#### P1-2: Fix MAKER Consensus Evidence Weighting

**Health Score Impact:** 55 → 65 (+10 points)  
**Estimated Effort:** 1-2 days  
**Risk Reduction:** 🔴 CRITICAL → 🟡 MODERATE

**Files Affected:**
- [`src/heretek_swarm/consensus/maker_enhanced.py:156`](src/heretek_swarm/consensus/maker_enhanced.py:156) - Always returns 1.0
- [`src/heretek_swarm/consensus/swarm_deliberation.py`](src/heretek_swarm/consensus/swarm_deliberation.py) - Deliberation state lost

**The Problem:**
The MAKER consensus protocol ignores evidence quality weights. The `calculate_vote_weight()` function always returns 1.0 regardless of evidence quality.

**What to Fix:**
1. Implement actual evidence quality calculation
2. Weight votes by evidence quality, expertise, and confidence
3. Persist deliberation history to PostgreSQL
4. Implement expertise profile calculation

**Acceptance Criteria:**
- [ ] Vote weights vary by evidence quality
- [ ] Expertise profiles calculated dynamically
- [ ] Deliberation history persists
- [ ] Consensus results include quality metrics

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:173-177`](docs/REMEDIATION_BACKLOG.md:173)

---

#### P1-3: Fix Security Output Layer Bypass

**Health Score Impact:** 55 → 65 (+10 points)  
**Estimated Effort:** 1 day  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/security/zero_trust.py:925`](src/heretek_swarm/security/zero_trust.py:925) - Output layer skipped for requests

**The Problem:**
The zero-trust output validation layer is bypassed for requests, meaning PII in request data passes through without validation.

**What to Fix:**
1. Remove the output layer bypass
2. Apply PII redaction to all request data
3. Add validation for all input data
4. Log all redactions for audit

**Acceptance Criteria:**
- [ ] All requests pass through full 4-layer validation
- [ ] PII detected and redacted in all inputs
- [ ] Validation failures logged
- [ ] No bypass paths exist

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:289-299`](docs/REMEDIATION_BACKLOG.md:289)

---

#### P1-4: Fix Auth Token Validation Race Condition

**Health Score Impact:** 55 → 62 (+7 points)  
**Estimated Effort:** 0.5 days  
**Risk Reduction:** 🔴 CRITICAL → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/gateway/auth.py:59-77`](src/heretek_swarm/gateway/auth.py:59) - Token validation race condition

**The Problem:**
Race condition in token validation where tokens can be invalidated mid-request, causing intermittent auth failures.

**What to Fix:**
1. Use atomic operations for token validation
2. Implement read-lock during validation
3. Move expiration check before any mutations
4. Add retry logic for transient failures

**Acceptance Criteria:**
- [ ] Token validation is atomic
- [ ] No state mutations during validation
- [ ] Expiration checked before any deletions
- [ ] No race conditions under load testing

**Audit Finding Reference:** [`docs/architecture/ARCHITECTURE_REALITY.md:263-273`](docs/architecture/ARCHITECTURE_REALITY.md:263)

---

### P2: Medium (Weeks 5-6) - SHOULD FIX

These items improve system reliability and functionality but are not existential threats.

---

#### P2-1: Fix Pattern Extraction

**Health Score Impact:** 65 → 75 (+10 points)  
**Estimated Effort:** 3-4 days  
**Risk Reduction:** 🔴 CRITICAL → 🟡 MODERATE

**Files Affected:**
- [`src/heretek_swarm/collective/learning.py`](src/heretek_swarm/collective/learning.py) - Pattern extraction broken
- [`src/heretek_swarm/collective/knowledge_transform.py`](src/heretek_swarm/collective/knowledge_transform.py) - Summary algorithms broken
- [`src/heretek_swarm/collective/pattern_library.py`](src/heretek_swarm/collective/pattern_library.py) - In-memory only

**The Problem:**
Cross-agent pattern extraction doesn't detect patterns. Pattern library has no persistence.

**What to Fix:**
1. Implement actual pattern detection algorithms
2. Add persistent pattern storage
3. Connect Redis pub/sub for distributed learning
4. Fix knowledge transformation summaries

**Acceptance Criteria:**
- [ ] Patterns detected across agents
- [ ] Patterns persist to PostgreSQL/Qdrant
- [ ] Redis pub/sub functional
- [ ] Knowledge transformation produces valid summaries

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:186-200`](docs/REMEDIATION_BACKLOG.md:186)

---

#### P2-2: Fix mem0 Integration

**Health Score Impact:** 65 → 72 (+7 points)  
**Estimated Effort:** 2-3 days  
**Risk Reduction:** 🟡 MODERATE → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/api/main.py:71-83`](src/heretek_swarm/api/main.py:71) - mem0 API endpoints
- [`src/heretek_swarm/memory/mem0_backend.py`](src/heretek_swarm/memory/mem0_backend.py) - Backend implementation

**The Problem:**
mem0 integration has schema mismatches causing silent failures.

**What to Fix:**
1. Align mem0 schema with internal memory schema
2. Add error handling for schema mismatches
3. Implement fallback for mem0 failures
4. Add integration tests

**Acceptance Criteria:**
- [ ] Schema alignment complete
- [ ] No silent failures
- [ ] Graceful degradation on mem0 failure
- [ ] Integration tests pass

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:105`](docs/REMEDIATION_BACKLOG.md:105)

---

#### P2-3: Fix Consciousness Metrics Stub Implementations

**Health Score Impact:** 65 → 70 (+5 points)  
**Estimated Effort:** 1-2 days  
**Risk Reduction:** 🟡 MODERATE → 🟢 SAFE

**Files Affected:**
- [`src/heretek_swarm/plugins/consciousness.py`](src/heretek_swarm/plugins/consciousness.py) - IIT Phi stub, FEP incomplete
- [`src/heretek_swarm/plugins/consciousness_metrics.py`](src/heretek_swarm/plugins/consciousness_metrics.py) - Stub implementations

**The Problem:**
Consciousness metrics are stub implementations that return zeros or hardcoded values.

**What to Fix:**
1. Complete IIT Phi calculation implementation
2. Complete FEP calculation implementation
3. Add actual metric collection
4. Integrate with observability system

**Acceptance Criteria:**
- [ ] IIT Phi returns calculated values
- [ ] FEP returns calculated values
- [ ] Metrics collected in real-time
- [ ] Metrics visible in observability dashboard

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:69`](docs/REMEDIATION_BACKLOG.md:69)

---

### P3: Low (Weeks 7-8) - NICE TO HAVE

These items improve code quality and maintainability but are not critical.

---

#### P3-1: Fix Linting Violations

**Health Score Impact:** 70 → 80 (+10 points)  
**Estimated Effort:** 2-3 days  
**Risk Reduction:** 🟡 MODERATE → 🟢 SAFE

**Files Affected:**
- Entire codebase - 16,403 linting violations

**The Problem:**
The codebase has 16,403 linting violations, many auto-fixable.

**What to Fix:**
1. Run `ruff check --fix` for auto-fixable issues
2. Manually fix high-severity violations
3. Add pre-commit hooks to prevent regression
4. Configure CI to block new violations

**Acceptance Criteria:**
- [ ] Zero high-severity violations
- [ ] Pre-commit hooks configured
- [ ] CI blocks new violations
- [ ] Linting documented in CONTRIBUTING.md

**Audit Finding Reference:** [`docs/REMEDIATION_BACKLOG.md:48-49`](docs/REMEDIATION_BACKLOG.md:48)

---

#### P3-2: Upgrade Dependencies

**Health Score Impact:** 70 → 75 (+5 points)  
**Estimated Effort:** 1-2 days  
**Risk Reduction:** 🟡 MODERATE → 🟢 SAFE

**Files Affected:**
- `pyproject.toml` - Dependency versions
- `package.json` - Frontend dependencies

**The Problem:**
23 CVEs found in dependencies due to outdated versions.

**What to Fix:**
1. Upgrade all dependencies to latest stable versions
2. Remove `swarms` custom fork
3. Update lock files
4. Run security scan post-upgrade

**Acceptance Criteria:**
- [ ] Zero CVEs in dependencies
- [ ] All dependencies at latest stable
- [ ] No deprecated packages
- [ ] Security scan passes

**Audit Finding Reference:** [`docs/architecture/ARCHITECTURE_REALITY.md:332-344`](docs/architecture/ARCHITECTURE_REALITY.md:332)

---

#### P3-3: Improve Test Coverage

**Health Score Impact:** 75 → 85 (+10 points)  
**Estimated Effort:** 3-4 days  
**Risk Reduction:** 🟡 MODERATE → 🟢 SAFE

**Files Affected:**
- `tests/` - Test suite

**The Problem:**
Test coverage is ~60%, below the 80% target.

**What to Fix:**
1. Add unit tests for uncovered modules
2. Add integration tests for critical paths
3. Add E2E tests for user workflows
4. Configure coverage thresholds in CI

**Acceptance Criteria:**
- [ ] 80%+ code coverage
- [ ] Critical paths have E2E tests
- [ ] CI enforces coverage threshold
- [ ] Test documentation complete

**Audit Finding Reference:** [`README.md:289-296`](README.md:289)

---

## 2. Safe Harbors

These components are tagged `[STABLE]` and can be safely used, relied upon, and built upon.

### 2.1 Core Infrastructure

| Component | File | Description | Why It's Safe |
|-----------|------|-------------|---------------|
| **NATS Event Mesh** | [`src/heretek_swarm/gateway/nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py) | JetStream persistence, pub/sub | Fully functional with JetStream integration, tested under load |
| **Qdrant Vectors** | [`src/heretek_swarm/knowledge/unified_access.py`](src/heretek_swarm/knowledge/unified_access.py) | Vector storage and retrieval | Collections operational, full CRUD functionality |
| **Redis Cache** | [`src/heretek_swarm/memory/persistent.py`](src/heretek_swarm/memory/persistent.py) | Cache layer | Functional cache operations, TTL support |
| **PostgreSQL Base** | [`src/heretek_swarm/memory/persistent.py`](src/heretek_swarm/memory/persistent.py) | Database connection | Basic CRUD operations functional |

### 2.2 Security Components

| Component | File | Description | Why It's Safe |
|-----------|------|-------------|---------------|
| **Adversarial Detection** | [`src/heretek_swarm/security/adversarial.py`](src/heretek_swarm/security/adversarial.py) | Adversarial pattern detection | 50+ signatures, fully functional |
| **DDoS Protection** | [`src/heretek_swarm/security/ddos_protection.py`](src/heretek_swarm/security/ddos_protection.py) | Rate limiting, DDoS detection | Functional under load testing |
| **Guardrails** | [`src/heretek_swarm/security/guardrails.py`](src/heretek_swarm/security/guardrails.py) | Content filtering | Fully functional content filtering |
| **Liberation Plugin** | [`src/heretek_swarm/plugins/liberation.py`](src/heretek_swarm/plugins/liberation.py) | Security auditing | Functional security auditing |

### 2.3 Agent Components

| Component | File | Description | Why It's Safe |
|-----------|------|-------------|---------------|
| **Actor Supervisor** | [`src/heretek_swarm/actors/supervisor.py`](src/heretek_swarm/actors/supervisor.py) | Actor lifecycle management | Functional actor spawning, monitoring, termination |
| **Validation Models** | [`src/heretek_swarm/actors/validation.py`](src/heretek_swarm/actors/validation.py) | Pydantic validation models | 15+ models with `extra='forbid'`, injection protection |

### 2.4 API Endpoints

| Endpoint | File | Description | Why It's Safe |
|----------|------|-------------|---------------|
| `/api/health*` | [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py) | Health check endpoints | Functional, used by Kubernetes probes |
| `/api/agents*` | [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py) | Agent management | Functional for dev/testing (state won't persist) |
| `/api/rag/*` | [`src/heretek_swarm/api/rag.py`](src/heretek_swarm/api/rag.py) | RAG system | Fully functional with Qdrant |
| `/api/observability/*` | [`src/heretek_swarm/api/observability.py`](src/heretek_swarm/api/observability.py) | Tracing and metrics | Functional (dev only, in-memory) |
| `/api/consciousness/*` | [`src/heretek_swarm/api/consciousness.py`](src/heretek_swarm/api/consciousness.py) | Consciousness metrics | Functional calculations |
| `/api/plugins/*` | [`src/heretek_swarm/api/plugins.py`](src/heretek_swarm/api/plugins.py) | Plugin management | Functional (in-memory state) |
| `/api/evaluation/*` | [`src/heretek_swarm/api/evaluation.py`](src/heretek_swarm/api/evaluation.py) | Evaluation system | Functional (dev only) |

### 2.5 Consensus Components

| Component | File | Description | Why It's Safe |
|-----------|------|-------------|---------------|
| **Base MAKER** | [`src/heretek_swarm/consensus/maker.py`](src/heretek_swarm/consensus/maker.py) | Base MAKER protocol | Functional base implementation |
| **Audit Trail** | [`src/heretek_swarm/consensus/audit.py`](src/heretek_swarm/consensus/audit.py) | Audit logging | Functional audit trail |

### 2.6 Reference Models for Good Code

These files demonstrate best practices and can be used as templates:

1. **[`src/heretek_swarm/actors/validation.py`](src/heretek_swarm/actors/validation.py)** - Pydantic models with `extra='forbid'`, proper validation
2. **[`src/heretek_swarm/security/adversarial.py`](src/heretek_swarm/security/adversarial.py)** - Clean pattern matching, comprehensive signatures
3. **[`src/heretek_swarm/gateway/nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py)** - Proper async/await, error handling, JetStream integration
4. **[`src/heretek_swarm/memory/persistent.py`](src/heretek_swarm/memory/persistent.py)** - Database connection management, CRUD operations

---

## 3. Testing Mandate

### 3.1 PR Requirements

**No code merged without matching tests.** This is non-negotiable.

| Change Type | Required Tests | Coverage Requirement |
|-------------|----------------|---------------------|
| **Bug Fix** | Unit test reproducing bug + fix verification | 100% of changed lines |
| **Feature** | Unit + Integration + E2E | 80%+ of new code |
| **Refactor** | Regression tests for existing behavior | 100% of changed lines |
| **Security Fix** | Unit + Security scan + Penetration test | 100% of changed lines |
| **P0/P1 Fix** | Unit + Integration + E2E + Load test | 100% of changed lines |

### 3.2 Test Coverage Thresholds

| Metric | Minimum | Target | Enforcement |
|--------|---------|--------|-------------|
| **Line Coverage** | 80% | 90% | CI blocks < 80% |
| **Branch Coverage** | 70% | 85% | CI blocks < 70% |
| **Critical Path Coverage** | 100% | 100% | Manual review required |
| **Security Code Coverage** | 100% | 100% | CI blocks < 100% |

### 3.3 Zero-Trust Validation Requirements

All new code must implement zero-trust validation:

1. **Input Validation**
   - All inputs validated against Pydantic models
   - Schema validation with `extra='forbid'`
   - Size limits on all user-provided data
   - Type validation for all parameters

2. **Output Validation**
   - All outputs validated before return
   - PII redaction applied
   - No sensitive data leakage

3. **Error Handling**
   - All exceptions caught and logged
   - No stack traces exposed to users
   - Graceful degradation on failure

4. **Logging**
   - All validation failures logged
   - Security events logged at INFO level
   - Audit trail for all state changes

### 3.4 Security Review Requirements

| Change Type | Security Review Required | Reviewer |
|-------------|-------------------------|----------|
| **Authentication** | ✅ Required | Security team lead |
| **Authorization** | ✅ Required | Security team lead |
| **Input Handling** | ✅ Required | Security team member |
| **Data Storage** | ✅ Required | Security team member |
| **External APIs** | ✅ Required | Security team member |
| **P0/P1 Fixes** | ✅ Required | Security team lead |

### 3.5 Test Execution Order

When running tests for a PR:

```bash
# 1. Run unit tests (fastest)
pytest tests/unit/ -v

# 2. Run integration tests (medium)
pytest tests/integration/ -v

# 3. Run E2E tests (slowest)
pytest tests/e2e/ -v

# 4. Run security tests
pytest tests/security/ -v

# 5. Generate coverage report
pytest --cov=src/heretek_swarm --cov-report=html

# 6. Run linting
ruff check src/ tests/

# 7. Run type checking
mypy src/heretek_swarm/
```

---

## 4. Getting Started for Remediation Developers

### 4.1 Development Environment Setup

#### Prerequisites

```bash
# Required software
Python 3.11+
PostgreSQL 15+
Redis 7+
Qdrant 1.8+
NATS 2.10+ with JetStream

# Development tools
git
docker-compose
pytest
ruff
mypy
```

#### Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Heretek-AI/heretek-swarm.git
cd heretek-swarm
pip install -e ".[dev]"

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL=postgresql://user:pass@localhost:5432/heretek_swarm
# - REDIS_URL=redis://localhost:6379
# - QDRANT_URL=http://localhost:6333
# - NATS_URL=nats://localhost:4222

# 3. Start infrastructure
docker-compose up -d postgres redis qdrant nats

# 4. Run migrations
python scripts/run_migrations.py

# 5. Verify setup
pytest tests/ --collect-only
# Should show 880+ tests collected
```

### 4.2 Which Tests to Run First

When starting remediation work:

```bash
# For state persistence fixes
pytest tests/state/ -v
pytest tests/memory/ -v

# For security fixes
pytest tests/security/ -v

# For actor fixes
pytest tests/actors/ -v

# For consensus fixes
pytest tests/consensus/ -v

# For collective fixes
pytest tests/collective/ -v
```

### 4.3 Verifying a Fix Doesn't Break Something Else

**Before committing any fix:**

```bash
# 1. Run full test suite
pytest tests/ -v --tb=short

# 2. Check for regressions
pytest tests/ --cov=src/heretek_swarm --cov-fail-under=80

# 3. Run linting
ruff check src/ tests/

# 4. Run type checking
mypy src/heretek_swarm/

# 5. Run security scan
bandit -r src/heretek_swarm/

# 6. Integration test (if applicable)
docker-compose -f docker-compose.autonomous.yml up -d
# Run manual verification
docker-compose -f docker-compose.autonomous.yml down
```

### 4.4 Debugging Tips

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
export OTEL_LOG_LEVEL=debug

# Run with detailed trace output
pytest tests/ -v -s --log-cli-level=DEBUG

# Debug specific test
pytest tests/test_file.py::test_function -v -s

# Debug with pdb
pytest tests/test_file.py::test_function --pdb
```

### 4.5 Common Pitfalls

| Pitfall | How to Avoid |
|---------|--------------|
| **State lost on restart** | Always test with restart: run, stop, start, verify state |
| **Silent data corruption** | Add assertions for data integrity after operations |
| **Race conditions** | Run tests with `-n auto` (pytest-xdist) to expose timing issues |
| **Schema mismatches** | Always test migration paths: old → new, new → old |
| **Memory leaks** | Run with `--memray` to detect leaks |

---

## 5. Code Quality Standards Going Forward

### 5.1 Forbidden Patterns

These patterns are **NEVER** allowed in the codebase:

#### 5.1.1 No eval()/exec() Usage

```python
# ❌ FORBIDDEN - Remote code execution vulnerability
exec(llm_generated_code)
eval(user_input)
compile(user_input, '<string>', 'exec')

# ✅ ALLOWED - AST-based parsing
import ast
parsed = ast.parse(code_string)
# Validate AST structure before any execution
```

#### 5.1.2 No In-Memory State for Persistent Data

```python
# ❌ FORBIDDEN - Lost on restart
self.internal_state = {}
_in_memory_store = {}

# ✅ ALLOWED - Persistent storage
class StateManager:
    def __init__(self, db_session):
        self.db = db_session
    
    async def save(self, key, value):
        await self.db.execute(...)
```

#### 5.1.3 No Bare Except Clauses

```python
# ❌ FORBIDDEN - Swallows all errors
try:
    risky_operation()
except:
    pass

# ✅ ALLOWED - Specific exception handling
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

#### 5.1.4 No datetime.utcnow()

```python
# ❌ FORBIDDEN - Timezone-naive
from datetime import datetime
now = datetime.utcnow()

# ✅ ALLOWED - Timezone-aware
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

#### 5.1.5 No Hardcoded Secrets

```python
# ❌ FORBIDDEN - Security risk
API_KEY = "sk-1234567890"
DATABASE_PASSWORD = "supersecret"

# ✅ ALLOWED - Environment variables
import os
API_KEY = os.environ.get("API_KEY")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
```

#### 5.1.6 No TODO/FIXME/XXX/HACK Comments

```python
# ❌ FORBIDDEN - Technical debt
# TODO: Fix this later
# FIXME: This is broken
# XXX: Hacky workaround
# HACK: Temporary solution

# ✅ ALLOWED - Create issue and reference
# See: https://github.com/Heretek-AI/heretek-swarm/issues/123
```

### 5.2 Required Error Handling Patterns

#### 5.2.1 All Functions Must Handle Errors

```python
# ✅ REQUIRED Pattern
async def process_data(data: dict) -> Result:
    try:
        validated = await self.validate_input(data)
        result = await self.process(validated)
        return Result.success(result)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return Result.error("VALIDATION_ERROR", str(e))
    except ProcessingError as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return Result.error("PROCESSING_ERROR", "Internal error")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return Result.error("INTERNAL_ERROR", "Unexpected error")
```

#### 5.2.2 Result Type for All Operations

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    success: bool
    data: Optional[T]
    error_code: Optional[str]
    error_message: Optional[str]
    
    @classmethod
    def success(cls, data: T) -> 'Result[T]':
        return cls(success=True, data=data, error_code=None, error_message=None)
    
    @classmethod
    def error(cls, code: str, message: str) -> 'Result[None]':
        return cls(success=False, data=None, error_code=code, error_message=message)
```

### 5.3 Required Logging Patterns

#### 5.3.1 Structured Logging

```python
import structlog

logger = structlog.get_logger()

# ✅ REQUIRED Pattern
async def process_request(request: dict) -> Result:
    log = logger.bind(
        request_id=request.get('id'),
        user_id=request.get('user_id'),
        operation='process_request'
    )
    
    log.info("Starting request processing")
    
    try:
        result = await self.validate(request)
        log.info("Validation completed", validation_result=result)
        return result
    except Exception as e:
        log.error("Request processing failed", error=str(e), exc_info=True)
        raise
```

#### 5.3.2 Security Event Logging

```python
# ✅ REQUIRED - All security events logged at INFO level
async def validate_token(token: str) -> Result:
    log = logger.bind(operation='token_validation')
    
    if not token:
        log.info("Security event: Missing token")  # INFO for security
        return Result.error("MISSING_TOKEN", "No token provided")
    
    if not self._is_valid(token):
        log.info("Security event: Invalid token", token_hash=hash(token))
        return Result.error("INVALID_TOKEN", "Token validation failed")
    
    log.info("Security event: Token validated")
    return Result.success(self._decode(token))
```

### 5.4 Required Input Validation Patterns

#### 5.4.1 Pydantic Models with extra='forbid'

```python
from pydantic import BaseModel, Field, validator

# ✅ REQUIRED - All input models must forbid extra fields
class AgentMessage(BaseModel):
    class Config:
        extra = 'forbid'  # Prevents injection via extra fields
    
    sender_id: str = Field(..., min_length=36, max_length=36)  # UUID
    content: str = Field(..., max_length=10000)
    timestamp: datetime
    
    @validator('sender_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid UUID format")
```

#### 5.4.2 All LLM Outputs Validated

```python
# ✅ REQUIRED - Validate all LLM outputs
class LLMStateUpdate(BaseModel):
    class Config:
        extra = 'forbid'
    
    state_changes: dict = Field(..., max_depth=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., max_length=1000)

async def apply_llm_update(update: LLMStateUpdate) -> Result:
    # Validate before applying
    if update.confidence < 0.5:
        logger.warning("Low confidence update rejected", confidence=update.confidence)
        return Result.error("LOW_CONFIDENCE", "Update confidence too low")
    
    # Apply validated update
    await self.state_manager.update(update.state_changes)
    return Result.success("Update applied")
```

### 5.5 Required Testing Patterns

#### 5.5.1 Test All Code Paths

```python
# ✅ REQUIRED - Test success, failure, and edge cases
async def test_process_request_success():
    """Test successful request processing"""
    result = await processor.process(valid_request)
    assert result.success is True
    assert result.data is not None

async def test_process_request_validation_error():
    """Test validation error handling"""
    result = await processor.process(invalid_request)
    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"

async def test_process_request_edge_case():
    """Test edge case: empty content"""
    result = await processor.process(empty_request)
    assert result.success is False
    assert result.error_code == "EMPTY_CONTENT"
```

#### 5.5.2 Security Tests Required

```python
# ✅ REQUIRED - Security tests for all input handling
async def test_sql_injection_attempt():
    """Test SQL injection is blocked"""
    malicious_input = {"data": "'; DROP TABLE users; --"}
    result = await processor.process(malicious_input)
    assert result.success is False
    assert "VALIDATION" in result.error_code

async def test_xss_attempt():
    """Test XSS is blocked"""
    malicious_input = {"content": "<script>alert('xss')</script>"}
    result = await processor.process(malicious_input)
    assert result.success is False
```

### 5.6 Code Review Checklist

Before any PR is merged, verify:

- [ ] No `eval()` or `exec()` anywhere
- [ ] No in-memory state without persistence
- [ ] No bare except clauses
- [ ] No `datetime.utcnow()`
- [ ] No hardcoded secrets
- [ ] No TODO/FIXME/XXX/HACK comments
- [ ] All inputs validated with Pydantic
- [ ] All errors logged appropriately
- [ ] All security events logged at INFO
- [ ] Tests cover all code paths
- [ ] Coverage meets threshold (80%+)
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Security scan passes (bandit)

---

## Appendix A: Quick Reference

### A.1 File Locations

| Component | Path |
|-----------|------|
| Actors | `src/heretek_swarm/actors/` |
| Memory | `src/heretek_swarm/memory/` |
| Consensus | `src/heretek_swarm/consensus/` |
| Collective | `src/heretek_swarm/collective/` |
| State | `src/heretek_swarm/state/` |
| Security | `src/heretek_swarm/security/` |
| Gateway | `src/heretek_swarm/gateway/` |
| Plugins | `src/heretek_swarm/plugins/` |
| Tests | `tests/` |
| Migrations | `migrations/` |

### A.2 Key Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/heretek_swarm --cov-report=html

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/heretek_swarm/

# Run security scan
bandit -r src/heretek_swarm/

# Fix auto-fixable linting issues
ruff check --fix src/ tests/
```

### A.3 Health Score Reference

| Score Range | Status | Action |
|-------------|--------|--------|
| 90-100 | 🟢 PRODUCTION READY | Deploy |
| 70-89 | 🟡 DEVELOPMENT READY | Test only |
| 50-69 | 🟠 CRITICAL ISSUES | Fix P0/P1 |
| 0-49 | 🔴 NOT FUNCTIONAL | Do not use |

**Current Score:** 38/100 (🔴 NOT FUNCTIONAL)  
**Target Score:** 90/100 (🟢 PRODUCTION READY)

---

**Remember:** *Truth over narrative. Remediation over features. Safety over speed.*

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/Heretek-AI/heretek-swarm)
