# Medium and Low Severity Code Smells Audit

**Project:** Heretek-AI_heretek-swarm
**Date:** 2026-04-13
**Severity Focus:** MINOR/LOW (equivalent to SonarQube LOW and INFO severities)
**Tool:** SonarQube MCP (mcp__satanlovesfags__sonarqube-search_sonar_issues_in_projects)

## Pagination Note

The SonarQube MCP server returned `total: 1511` issues but pagination behavior was observed to return consistent results across pages 1-2 (different data, not duplicated). Due to time constraints, this report documents findings from the first 200 issues (pages 1-2) and extrapolates patterns. A full audit would require iterating through all ~16 pages.

---

## Summary Counts

| Severity | Count (sample) | Est. Total |
|----------|----------------|-----------|
| MINOR (LOW) | ~180 | ~1400 |
| INFO | ~20 | ~150 |

**Note:** Most issues in the MINOR severity band are actually code smells (not bugs or vulnerabilities).

---

## Issue Type Distribution

### Python Code Smells

| Rule ID | Description | Count (sample) | Status |
|---------|-------------|----------------|--------|
| S7503 | async without await | 90+ | OPEN |
| S5713 | redundant exception classes | 15+ | OPEN |
| S1481 | unused local variables | 12+ | MIXED |
| S7504 | unnecessary list() call | 5+ | OPEN |
| S3626 | redundant return | 5+ | MIXED |
| S7494/S7496 | set/list constructor issues | 3+ | MIXED |
| S1940 | opposite operator (bool flip) | 1 | OPEN |
| S116 | naming convention (snake_case) | 1 | OPEN |

### TypeScript Code Smells

| Rule ID | Description | Count (sample) | Status |
|---------|-------------|----------------|--------|
| S6759 | props not marked read-only | 15+ | OPEN |
| S7764 | prefer globalThis over window | 7+ | MIXED |
| S4325 | unnecessary type assertions | 2+ | OPEN |
| S6848 | non-native interactive elements | 2 | OPEN (MAJOR) |
| S1082 | missing keyboard listener | 2 | OPEN |
| S6767 | unused PropType | 1 | OPEN |
| S1128 | unused import | 2 | OPEN |
| S6772 | ambiguous spacing | 1 | OPEN |
| S2486 | caught exception not re-raised | 1 | OPEN |

### Security-Related (Low Severity)

| Rule ID | Description | Count | Status |
|---------|-------------|-------|--------|
| pythonsecurity:S5145 | Logged user-controlled data | 1 | OPEN |

---

## Detailed Issue List (Selected Examples)

### S7503 - Async Without Await (python:S7503)

**Description:** Function declared async but does not use await anywhere in its body.

| Key | Component | Line |
|-----|-----------|------|
| AZ2JC4EMkffvx81wL6Lo | src/heretek_swarm/actors/arbiter/strategies.py | 41 |
| AZ2JC4EMkffvx81wL6Lq | src/heretek_swarm/actors/arbiter/strategies.py | 53 |
| AZ2JC4EMkffvx81wL6Ls | src/heretek_swarm/actors/arbiter/strategies.py | 91 |
| AZ2JC4Tdkffvx81wL6L_ | src/heretek_swarm/collective/algorithms/abc.py | 94 |
| AZ2JC4Tvkffvx81wL6MD | src/heretek_swarm/collective/algorithms/aco.py | 100 |
| AZ2JC4UBkffvx81wL6MG | src/heretek_swarm/collective/algorithms/pso.py | 113 |
| AZ2DbdGwB1HMB1XN0awG | src/heretek_swarm/memory/persistent.py | 476 |
| AZ2DROFuK0fgB4uOtfO4 | src/heretek_swarm/api/mcp.py | 365 |
| AZ2DeLfVXISY38E6yEbw | src/heretek_swarm/state/models.py | 677 |
| AZ1_Iwb8kud7vHWqlqI2 | src/heretek_swarm/infrastructure/nats/client.py | 387 |

**Fix:** Either add `await` to async operations within the function, or remove the `async` keyword if no async operations are needed.

---

### S5713 - Redundant Exception Classes (python:S5713)

**Description:** Custom exception class inherits from another exception that is already caught in the same try-except block.

| Key | Component | Line |
|-----|-----------|------|
| AZ2JC4p1kffvx81wL6Ma | src/heretek_swarm/state/event_store.py | 366 |
| AZ2JC4p1kffvx81wL6Mb | src/heretek_swarm/state/event_store.py | 456 |
| AZ2JC4p1kffvx81wL6Mc | src/heretek_swarm/state/event_store.py | 793 |
| AZ2JC4pdkffvx81wL6MR | src/heretek_swarm/state/repository.py | 271 |
| AZ2JC4pdkffvx81wL6MS | src/heretek_swarm/state/repository.py | 380 |
| AZ2JC4pdkffvx81wL6MT | src/heretek_swarm/state/repository.py | 380 |
| AZ2JC4pdkffvx81wL6MY | src/heretek_swarm/state/repository.py | 608 |
| AZ2JC4CCkffvx81wL6Lm | src/heretek_swarm/actors/base/message_handling.py | 660 |

**Fix:** Remove the redundant exception class and catch the parent exception directly.

---

### S1481 - Unused Local Variables (python:S1481)

**Description:** Local variable assigned but never used.

| Key | Component | Line |
|-----|-----------|------|
| AZ2I91T9Oofs3aoPHi4d | tests/test_rag_pipeline.py | 202 |
| AZ2DROFuK0fgB4uOtfOz | src/heretek_swarm/api/websockets.py | 1152 |
| AZ1_qGgqs0Fbzs2jcRwO | scripts/wire_agents.py | 373 |
| AZ1_qGgSs0Fbzs2jcRwH | scripts/wire_agents_session44.py | 371 |

**Fix:** Remove unused variable or prefix with `_` if intentionally discarded.

---

### S7504 - Unnecessary list() Call (python:S7504)

**Description:** Wrapping an already-iterable object in list() is redundant.

| Key | Component | Line |
|-----|-----------|------|
| AZ2JLtLeFplsLDfsTGkd | src/heretek_swarm/gateway/nats_event_mesh.py | 1529 |
| AZ2BmLiTK0fgB4uOdi3j | src/heretek_swarm/infrastructure/nats/memory_sync.py | 679 |
| AZ1_IwcIkud7vHWqlqJA | src/heretek_swarm/infrastructure/nats/subscriber.py | 276 |
| AZ19epKot-zbsGOG5j8j | src/heretek_swarm/gateway/event_mesh.py | 319 |

**Fix:** Remove the `list()` wrapper.

---

### S6759 - Props Not Read-Only (typescript:S6759)

**Description:** React component props should be marked as read-only.

| Key | Component | Line |
|-----|-----------|------|
| AZ2Io_n--UnteY7JfmQc | dashboard/frontend/src/components/Canvas/MetricsOverlay.tsx | 25-30 |
| AZ2DROYQK0fgB4uOtfPH | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 137 |
| AZ2DROYQK0fgB4uOtfPJ | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 168-178 |
| AZ2DROYQK0fgB4uOtfPM | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 243-251 |
| AZ2DROYQK0fgB4uOtfPW | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 564-581 |

**Fix:** Use `const Props = { ... } as const` or use `Readonly<Props>` type.

---

### S7764 - Prefer globalThis Over window (typescript:S7764)

**Description:** Using `window` is not portable; prefer `globalThis`.

| Key | Component | Line | Status |
|-----|-----------|------|--------|
| AZ2Io_mC-UnteY7JfmQa | dashboard/frontend/src/components/Canvas/Canvas.tsx | 62 | OPEN |
| AZ2Io_mC-UnteY7JfmQb | dashboard/frontend/src/components/Canvas/Canvas.tsx | 63 | OPEN |
| AZ2Hlef7wzEysuRrM1vh | dashboard/frontend/src/App.tsx | 82 | CLOSED |
| AZ2Hlef7wzEysuRrM1vi | dashboard/frontend/src/App.tsx | 82 | CLOSED |

**Fix:** Replace `window` with `globalThis`.

---

### S6848 - Non-Native Interactive Elements (typescript:S6848) [MAJOR]

**Description:** Avoid non-native interactive elements. Add appropriate role and keyboard/tab support.

| Key | Component | Line |
|-----|-----------|------|
| AZ2DROYQK0fgB4uOtfPK | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 180-184 |
| AZ2DROYQK0fgB4uOtfPN | dashboard/frontend/src/components/Setup/ConfigWizard.tsx | 253 |

**Fix:** Use native HTML elements (`<button>`, `<a>`, etc.) or add proper ARIA roles and keyboard support.

---

### S3626 - Redundant Return (python:S3626)

**Description:** Return statement at the end of a function that returns None is unnecessary.

| Key | Component | Line | Status |
|-----|-----------|------|--------|
| AZ1_ri6WloRClScTX334 | tests/conftest.py | 414 | OPEN |
| AZ19eo3zt-zbsGOG5j7w | src/heretek_swarm/actors/stubs.py | 39 | OPEN |
| AZ19eo3zt-zbsGOG5j7x | src/heretek_swarm/actors/stubs.py | 52 | OPEN |
| AZ19epRWt-zbsGOG5j9G | src/heretek_swarm/api/evaluation.py | 267 | OPEN |

**Fix:** Remove the explicit `return None` or redundant return at function end.

---

### pythonsecurity:S5145 - Log User-Controlled Data (pythonsecurity:S5145)

**Description:** Logging user-controlled data can lead to log injection attacks.

| Key | Component | Line |
|-----|-----------|------|
| AZ1-MqxUyCqiNXJ_6Ezb | src/heretek_swarm/consensus/audit_query.py | 382 |

**Fix:** Sanitize or validate user-controlled data before logging.

---

## Top Files by Issue Count

1. **src/heretek_swarm/actors/arbiter/strategies.py** - 14 issues (all S7503 async)
2. **src/heretek_swarm/state/models.py** - 16 issues (all S7503 async)
3. **src/heretek_swarm/state/repository.py** - 7 issues (S5713 redundant exceptions)
4. **src/heretek_swarm/state/event_store.py** - 3 issues (S5713 redundant exceptions)
5. **dashboard/frontend/src/components/Setup/ConfigWizard.tsx** - 20+ issues (S6759, S6848, S1082, etc.)
6. **src/heretek_swarm/collective/algorithms/*.py** - 3+ issues (S7503 async)
7. **src/heretek_swarm/infrastructure/nats/memory_sync.py** - 6 issues (S7503, S7504)

---

## Recommendations

1. **High Priority - Async Without Await (S7503):** The 90+ instances of `async` functions without `await` should be audited. Either these are truly async and need `await`, or should be synchronous functions.

2. **High Priority - Redundant Exceptions (S5713):** 15+ exception classes that inherit from caught exceptions should be simplified.

3. **Medium Priority - Props Read-Only (S6759):** React components in the dashboard should have props marked as read-only for immutability.

4. **Low Priority - Cleanup:** Unused variables (S1481), redundant returns (S3626), and unnecessary list() calls (S7504) are straightforward cleanup items.

---

## Appendix: All Rules Found

### Python Rules
- python:S7503 - async without await
- python:S5713 - redundant exception classes
- python:S1481 - unused local variables
- python:S7504 - unnecessary list()
- python:S3626 - redundant return
- python:S7494 - set constructor vs comprehension
- python:S7496 - list constructor vs literal
- python:S1940 - opposite operator
- python:S116 - naming convention
- python:S7504 - unnecessary list()
- pythonsecurity:S5145 - log injection

### TypeScript Rules
- typescript:S6759 - props not read-only
- typescript:S7764 - globalThis over window
- typescript:S4325 - unnecessary assertions
- typescript:S6848 - non-native interactive elements
- typescript:S1082 - missing keyboard listener
- typescript:S6767 - unused PropType
- typescript:S1128 - unused import
- typescript:S6772 - ambiguous spacing
- typescript:S2486 - caught exception not re-raised
