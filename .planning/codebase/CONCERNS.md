# Codebase Concerns

**Analysis Date:** 2026-04-13

## Tech Debt

### Large Files (Violating Single Responsibility)

**Issue:** Multiple files exceed 1000 lines, making them difficult to maintain, test, and understand.

- `src/heretek_swarm/actors/arbiter.py` - 1792 lines
- `src/heretek_swarm/config/service.py` - 1531 lines
- `src/heretek_swarm/actors/base.py` - 1527 lines
- `src/heretek_swarm/actors/perceiver_plus.py` - 1477 lines
- `src/heretek_swarm/collective/swarm_intelligence.py` - 1469 lines
- `src/heretek_swarm/consensus/maker_enhanced.py` - 1393 lines
- `src/heretek_swarm/consciousness/fep_active_inference.py` - 1392 lines
- `src/heretek_swarm/api/observability.py` - 1314 lines
- `src/heretek_swarm/actors/habit_forge.py` - 1306 lines

**Fix approach:** Break these into smaller, focused modules with clear responsibilities. Each file should ideally be under 500 lines.

### Deprecated Python AST Nodes

**Issue:** The workflow engine uses deprecated Python AST node classes for backward compatibility.

- **Files:** `src/heretek_swarm/workflow/engine.py` (lines 85-87, 225-229)
- **Details:** Uses `ast.Num`, `ast.Str`, `ast.NameConstant` which were deprecated in Python 3.8

**Impact:** Code may break with future Python versions and generates deprecation warnings.

**Fix approach:** Replace with `ast.Constant` which is the unified node type for all constants.

### Stub Functions Returning None

**Issue:** Actor stubs module provides functions that return None, relying on tests to patch them.

- **File:** `src/heretek_swarm/actors/stubs.py`
- **Functions:** `get_nats_event_mesh()`, `get_llm_provider()`, `get_db_pool()` all return `None`

**Impact:** Runtime errors if stubs are not properly patched; difficult to trace dependency initialization.

**Fix approach:** Implement proper dependency injection or use a service locator pattern.

## Known Bugs

### Broad Exception Handling

**Issue:** Multiple locations catch `Exception` broadly without specific handling.

**Files with `except Exception`:**
- `src/heretek_swarm/observability/alerting.py` - lines 148, 188
- `src/heretek_swarm/observability/tracing.py` - lines 89, 156, 173, 213, 397
- `src/heretek_swarm/state/repository.py` - lines 271, 380, 442, 475, 511, 569, 608, 653
- `src/heretek_swarm/workflow/engine.py` - lines 752, 840, 898
- `src/heretek_swarm/collective/knowledge_transform.py` - lines 305, 803

**Impact:** Errors are silently masked, making debugging difficult. May also impact performance due to exception unwinding.

**Fix approach:** Catch specific exceptions and handle each appropriately. Log errors with context.

### Empty Return Statements

**Issue:** Multiple functions return empty collections instead of raising appropriate exceptions or propagating errors.

**Examples:**
- `src/heretek_swarm/state/repository.py:939` - returns `[]`
- `src/heretek_swarm/channels/registry.py:258` - returns `[]`
- `src/heretek_swarm/gateway/jetstream_manager.py:868` - returns `[]`
- `src/heretek_swarm/gateway/nats_event_mesh.py:530, 534, 580, 1144` - returns `[]`
- `src/heretek_swarm/gateway/message_replay.py:427, 605` - returns `[]` or `{}`

**Impact:** Calling code may not distinguish between "no data" and "error occurred."

**Fix approach:** Either raise exceptions on error conditions or return a Result type that distinguishes success from failure.

### Incomplete Pass Statements

**Issue:** WebSocket handlers contain many `pass` statements indicating incomplete implementations.

- **File:** `src/heretek_swarm/api/websockets.py` - lines 388, 511, 536, 555, 604, 682, 782, 878, 965, 1062, 1137

**Impact:** WebSocket message handlers silently ignore messages, causing potential message loss.

**Fix approach:** Implement proper message handling or route to appropriate handlers.

## Security Considerations

### Critical Time-Dependent Expressions (CRITICAL)

**Issue:** Time-dependent expressions evaluated at class definition time instead of runtime.

- `src/heretek_swarm/gateway/nats_event_mesh.py:66` - `datetime.now()` in class attribute
- `src/heretek_swarm/actors/langroid_adapter.py:64` - timeout evaluated once at import
- `src/heretek_swarm/consensus/raft_election.py:119` - time-dependent class attribute

**Impact:** Stale timestamps; behavior differs between module load time and request time.

**Fix approach:** Move time-dependent expressions into methods that are called at request time.

### SSRF Vulnerabilities in API Wizard (MAJOR)

**Issue:** URL construction from user-controlled data without validation in multiple locations.

- **File:** `src/heretek_swarm/api/wizard.py`
- **Lines:** 470-483, 511-515, 536, 563-575, 599-611, 635-647, 672

**Impact:** Attacker could induce server to make requests to internal services or external untrusted URLs.

**Fix approach:** Implement URL validation with allowlist of permitted schemes and domains.

### Hard-coded Credentials in Tests (MAJOR)

**Issue:** Test files contain hard-coded passwords.

- `tests/state/test_repository.py:61`
- `tests/collective/test_session46_emergent_intelligence.py:683`

**Fix approach:** Use environment variables for test credentials.

### Weak Cryptography - PRNG Usage (97 instances)

**Issue:** Using `random.random()` or `Math.random()` instead of cryptographically secure RNG.

**Affected files (selected):**
- `src/heretek_swarm/collective/adaptive_learning.py` - lines 416, 428, 704, 712, 758, 918, 925, 934
- `src/heretek_swarm/collective/agent_adaptation.py` - line 899
- `src/heretek_swarm/collective/swarm_intelligence.py` - lines 604-605, 689-690
- `src/heretek_swarm/security/ddos_protection.py` - line 900
- `dashboard/frontend/src/components/Observability/A2ATracker.tsx` - lines 82-114, 385-394
- `dashboard/frontend/src/components/Settings/ModelGarage.tsx` - lines 583-587, 621-623, 637

**Fix approach:**
- Python: Use `secrets` module or `os.urandom()`
- TypeScript: Use `crypto.getRandomValues()` or `randomUUID()`

### Regex DoS Vulnerabilities (6 instances)

**Issue:** Regex patterns vulnerable to super-linear/polynomial runtime due to backtracking.

- `dashboard/frontend/src/utils/setupValidation.ts:48`
- `scripts/wire_agents.py:318`
- `scripts/wire_agents_session44.py:316`
- `src/heretek_swarm/plugins/liberation.py:170, 171, 172`

**Fix approach:** Use atomic groups `(?>)` or possessive quantifiers to prevent backtracking.

### Kubernetes Security Issues

**RBAC (7 instances):** Service accounts not bound to RBAC roles in k8s deployments.

**Storage Limits (7 instances):** Missing `ephemeral-storage` limits in container specs.

### Log Injection Vulnerability (MINOR)

**File:** `src/heretek_swarm/consensus/audit_query.py:382`

**Impact:** User-controlled data logged without sanitization enables log injection attacks.

**Fix approach:** Sanitize log input or use structured logging with base64 encoding for non-alphanumeric data.

## Performance Bottlenecks

### Large Actor Classes

**Problem:** The `AgentActor` base class (1527 lines) and derived actors like `Arbiter` (1792 lines) are very large.

- **Files:** `src/heretek_swarm/actors/base.py`, `src/heretek_swarm/actors/arbiter.py`
- **Cause:** Multiple responsibilities mixed into single classes (messaging, state, lifecycle, validation)
- **Improvement path:** Extract mixins into standalone components; use composition over inheritance

### Synchronous Config Service

**Problem:** Configuration service appears to have blocking I/O patterns in large file.

- **File:** `src/heretek_swarm/config/service.py` - 1531 lines
- **Impact:** Could block event loop in async contexts
- **Improvement path:** Review for async/await patterns and batch operations

### Memory Tiering Not Fully Implemented

**Area:** `src/heretek_swarm/memory/tiering.py`
- **Problem:** Memory tiering exists but may not be fully utilized across the codebase
- **Impact:** Memory usage may be higher than necessary
- **Improvement path:** Audit memory access patterns and ensure tiering is properly applied

## Fragile Areas

### Langroid Adapter (Optional Dependency)

**Files:** `src/heretek_swarm/actors/langroid_adapter.py`
- **Why fragile:** Uses try/except ImportError pattern; code may run without Langroid installed
- **Safe modification:** Test both with and without Langroid installed
- **Test coverage:** Verify behavior when `LANGROID_AVAILABLE` is True and False

### MCP Client Error Handling

**File:** `src/heretek_swarm/mcp/client.py`
- **Why fragile:** Connection failures may not properly clean up HTTP clients
- **Safe modification:** Ensure `_http_client` is always closed on error
- **Test coverage:** Test connection failures and reconnection logic

### Zero Trust Validator

**File:** `src/heretek_swarm/security/zero_trust.py`
- **Why fragile:** Complex validation logic with many exception handlers
- **Safe modification:** Add comprehensive error cases and logging
- **Test coverage:** Verify all exception paths are tested

## Scaling Limits

### In-Memory Rate Limiting

**Resource:** `src/heretek_swarm/api/rate_limiting.py`
- **Current capacity:** Handles per-instance rate limiting
- **Limit:** Breaks in multi-instance deployments (each instance has separate state)
- **Scaling path:** Use Redis-backed rate limiting for distributed deployments

### Actor Supervisor

**Resource:** `src/heretek_swarm/actors/supervisor.py`
- **Current capacity:** Manages actor lifecycle
- **Limit:** Unknown maximum actor count; may hit memory limits
- **Scaling path:** Implement actor pooling and load shedding

### WebSocket Connection Manager

**Resource:** `src/heretek_swarm/api/websockets.py` - `ConnectionManager`
- **Current capacity:** Tracks all active WebSocket connections in memory
- **Limit:** Memory-bound based on connection count
- **Scaling path:** Use Redis pub/sub for connection state in distributed setup

## Dependencies at Risk

### mem0ai

**Package:** `mem0ai`
- **Risk:** External dependency for memory management; may have breaking changes
- **Impact:** Memory functionality breaks if package changes API
- **Migration plan:** Already has conditional import with `MEM0_AVAILABLE` flag; maintain this pattern

### swarms

**Package:** `swarms>=5.0.0`
- **Risk:** Core framework dependency
- **Impact:** All agent functionality depends on this
- **Migration plan:** Langroid adapter exists as alternative; adapter pattern allows swapping

### Optional Dependency Pattern

**Pattern found:** Multiple files use try/except for optional imports (Langroid, slowapi, mem0)
- **Risk:** Code may run in degraded state without clear indication
- **Impact:** Features silently disabled instead of failing fast
- **Recommendation:** Add startup validation that reports missing optional dependencies

## Missing Critical Features

### Health Checks for All Dependencies

**Gap:** Not all external services have health check endpoints
- **Files:** `src/heretek_swarm/api/main.py` references health checks
- **Blocks:** Deployment automation and readiness probes

### Graceful Degradation Documentation

**Gap:** No documented behavior when Redis, NATS, or other services are unavailable
- **Impact:** Unclear what works vs what fails in partial outage scenarios

### Circuit Breakers Not Fully Integrated

**Gap:** `circuitbreaker>=2.0.0` is a dependency but may not be consistently applied
- **Impact:** Cascading failures possible under partial outage

## Test Coverage Gaps

### Large Files Untested

**Untested areas:**
- `src/heretek_swarm/actors/arbiter.py` - 1792 lines, complex conflict resolution logic
- `src/heretek_swarm/config/service.py` - 1531 lines, configuration loading
- `src/heretek_swarm/collective/swarm_intelligence.py` - 1469 lines

**Risk:** Changes to these files may break production with no test feedback.

**Priority:** HIGH

### WebSocket Message Handling

**What's not tested:** `src/heretek_swarm/api/websockets.py` handlers with `pass` statements
- **Risk:** Messages are silently ignored
- **Priority:** HIGH

### MCP Client Reconnection

**What's not tested:** `src/heretek_swarm/mcp/client.py` connection failure and recovery
- **Risk:** Production connection issues may not be handled gracefully
- **Priority:** MEDIUM

## Code Quality Issues (SonarQube Findings)

### Cognitive Complexity Violations (14 open CRITICAL issues)

Functions exceeding complexity threshold of 15:

| File | Line | Complexity |
|------|------|------------|
| `src/heretek_swarm/mcp/registry.py` | 324 | 61 (4x threshold!) |
| `src/heretek_swarm/runtime/main_loop.py` | 525 | 28 |
| `src/heretek_swarm/observability/metrics.py` | 265 | 19 |
| `src/heretek_swarm/evaluation/evaluator.py` | 213 | 18 |
| `src/heretek_swarm/runtime/autonomous_runtime.py` | 530 | 18 |
| `src/heretek_swarm/actors/base/state_management.py` | 26 | 18 |
| `src/heretek_swarm/infrastructure/nats/memory_sync.py` | 548 | 18 |
| `src/heretek_swarm/consensus/audit.py` | 229 | 16 |
| `src/heretek_swarm/actors/base/message_handling.py` | 26 | 16 |
| `src/heretek_swarm/infrastructure/nats/memory_sync.py` | 342 | 16 |

### Duplicated String Literals (7 open CRITICAL issues)

- `src/heretek_swarm/api/wizard.py` - "API key is required" (5x), "application/json" (4x), "API key is valid" (5x), "Invalid API key" (5x), "Connection timed out" (5x)
- `src/heretek_swarm/mcp/client.py:122` - "Client not connected" (4x)
- `src/heretek_swarm/api/consensus.py:1118` - "Tribunal not available" (6x)

### Async Without Await (90+ open issues)

Functions declared `async` but containing no `await` calls:

- `src/heretek_swarm/actors/arbiter/strategies.py` - 14 instances
- `src/heretek_swarm/state/models.py` - 16 instances
- `src/heretek_swarm/collective/algorithms/*.py` - multiple instances

**Impact:** These functions block when called; async is misleading.

### Redundant Exception Classes (15+ open issues)

Custom exception classes that inherit from parent exceptions already caught in same try-except:

- `src/heretek_swarm/state/event_store.py` - 3 instances
- `src/heretek_swarm/state/repository.py` - 7 instances

## File Duplication (5,203 duplicated lines)

**Priority 1 (>80% density) - Immediate refactoring needed:**

| File | Duplicated Lines | Density |
|------|-----------------|---------|
| `src/heretek_swarm/actors/triad.py` | 1,090 | 95.8% |
| `src/heretek_swarm/actors/beta.py` | 276 | 91.4% |
| `src/heretek_swarm/actors/charlie.py` | 271 | 91.2% |
| `src/heretek_swarm/actors/alpha.py` | 258 | 90.8% |
| `src/heretek_swarm/actors/steward.py` | 285 | 83.3% |
| `src/heretek_swarm/collective/emergence_analyzer.py` | 80 | 83.3% |

**Estimated deduplication potential:** ~2,700 lines (52% of current duplication)

---

*Concerns audit: 2026-04-13*
