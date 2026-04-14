# Critical and High Severity Issues Audit

**Project:** Heretek-AI_heretek-swarm
**Scanned:** 2026-04-14
**Tool:** SonarQube (mcp__satanlovesfags__sonarqube)

---

## Summary

| Severity | Total Issues | Open | Closed |
|----------|-------------|------|--------|
| CRITICAL | 42 | 24 | 18 |
| HIGH | 0 | 0 | 0 |

**Total OPEN CRITICAL/HIGH issues: 24**

---

## OPEN CRITICAL Issues

### 1. Cognitive Complexity - message_handling.py (Line 26)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2JC4CCkffvx81wL6Lk |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. |
| **Component** | `src/heretek_swarm/actors/base/message_handling.py:26` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Break down the function at line 26 into smaller, focused functions. Extract nested logic into helper functions to reduce cognitive complexity.

---

### 2. Cognitive Complexity - state_management.py (Line 26)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2JC3_nkffvx81wL6Lg |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/actors/base/state_management.py:26` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Decompose the function into smaller sub-functions. Use early returns for edge cases and extract complex conditional logic.

---

### 3. Cognitive Complexity - abc.py (Line 229)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2JC4Tdkffvx81wL6MC |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. |
| **Component** | `src/heretek_swarm/collective/algorithms/abc.py:229` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract nested loops/conditionals into separate helper methods. Consider using the Strategy pattern if complexity stems from multiple similar branches.

---

### 4. Cognitive Complexity - autonomous_runtime.py (Line 530)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2IUREGkffvx81wFZaB |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/runtime/autonomous_runtime.py:530` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Apply SRP (Single Responsibility Principle). Split into handler functions per message type. Use a dispatch dictionary for message handling.

---

### 5. Cognitive Complexity - main_loop.py (Line 525)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2IURArkffvx81wFZZ- |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed. |
| **Component** | `src/heretek_swarm/runtime/main_loop.py:525` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** CRITICAL - This function has complexity 28 (nearly double the threshold). Extract the main loop body into a state machine with separate handler methods for each state transition.

---

### 6. Cognitive Complexity - metrics.py (Line 265)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2ETeokkud7vHWqG_1_ |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. |
| **Component** | `src/heretek_swarm/observability/metrics.py:265` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Split aggregation logic into separate helper functions. Group metric calculations by type.

---

### 7. Cognitive Complexity - metrics.py (Line 418)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2ETeokkud7vHWqG_2A |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. |
| **Component** | `src/heretek_swarm/observability/metrics.py:418` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract formatting/export logic into separate helper functions.

---

### 8. Cognitive Complexity - evaluator.py (Line 105)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DSg9Nd-wa32bAOAVU |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. |
| **Component** | `src/heretek_swarm/evaluation/evaluator.py:105` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract scoring logic into a dedicated method and simplify branching.

---

### 9. Cognitive Complexity - evaluator.py (Line 213)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DSg9Nd-wa32bAOAVV |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/evaluation/evaluator.py:213` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Break down evaluation criteria into a dictionary-based scoring system to eliminate branching.

---

### 10. Cognitive Complexity - wizard.py (Line 406)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOp |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/api/wizard.py:406` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract wizard step handling into separate handler classes or methods.

---

### 11. Duplicated String Literal - wizard.py (Line 466)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOi |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "API key is required" 5 times. |
| **Component** | `src/heretek_swarm/api/wizard.py:466` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define a module-level constant: `API_KEY_REQUIRED = "API key is required"` and use it wherever needed.

---

### 12. Duplicated String Literal - wizard.py (Line 475)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOj |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "application/json" 4 times. |
| **Component** | `src/heretek_swarm/api/wizard.py:475` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `CONTENT_TYPE_JSON = "application/json"` as a constant.

---

### 13. Duplicated String Literal - wizard.py (Line 489)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOl |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "API key is valid" 5 times. |
| **Component** | `src/heretek_swarm/api/wizard.py:489` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `API_KEY_VALID = "API key is valid"` as a constant.

---

### 14. Duplicated String Literal - wizard.py (Line 493)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOk |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "Invalid API key" 5 times. |
| **Component** | `src/heretek_swarm/api/wizard.py:493` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `INVALID_API_KEY = "Invalid API key"` as a constant.

---

### 15. Duplicated String Literal - wizard.py (Line 497)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROEVK0fgB4uOtfOm |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "Connection timed out" 5 times. |
| **Component** | `src/heretek_swarm/api/wizard.py:497` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `CONNECTION_TIMEOUT = "Connection timed out"` as a constant.

---

### 16. Duplicated String Literal - mcp/client.py (Line 122)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROPXK0fgB4uOtfPD |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "Client not connected" 4 times. |
| **Component** | `src/heretek_swarm/mcp/client.py:122` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `CLIENT_NOT_CONNECTED = "Client not connected"` as a constant.

---

### 17. Cognitive Complexity - mcp/registry.py (Line 324)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DROPiK0fgB4uOtfPF |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 61 to the 15 allowed. |
| **Component** | `src/heretek_swarm/mcp/registry.py:324` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** CRITICAL - This function has complexity 61 (4x the threshold!). This is a major refactoring effort. Split into a registry class with dedicated methods for each registration type. Use a plugin architecture.

---

### 18. Cognitive Complexity - routing/model_router.py (Line 74)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2DIVh9UwL1W3ZIUOpj |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/routing/model_router.py:74` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract routing logic into a separate router class with composition.

---

### 19. Cognitive Complexity - nats/memory_sync.py (Line 342)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2BmLiTK0fgB4uOdi3c |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. |
| **Component** | `src/heretek_swarm/infrastructure/nats/memory_sync.py:342` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Extract sync logic into a dedicated sync manager class.

---

### 20. Cognitive Complexity - nats/memory_sync.py (Line 548)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ2BmLiTK0fgB4uOdi3h |
| **Rule** | python:S3776 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. |
| **Component** | `src/heretek_swarm/infrastructure/nats/memory_sync.py:548` |
| **CleanCode Category** | ADAPTABLE |

**Recommended Fix:** Break down the memory reconciliation logic. Use a state machine pattern.

---

### 21. Duplicated String Literal - api/consensus.py (Line 1118)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ1_16zWt-zbsGOGHn2I |
| **Rule** | python:S1192 |
| **Severity** | CRITICAL |
| **Status** | OPEN |
| **Message** | Define a constant instead of duplicating this literal "Tribunal not available" 6 times. |
| **Component** | `src/heretek_swarm/api/consensus.py:1118` |
| **CleanCode Category** | DISTINCT |

**Recommended Fix:** Define `TRIBUNAL_NOT_AVAILABLE = "Tribunal not available"` as a constant at module level.

---

## OPEN BLOCKER Issues (Included in Critical Count Above)

### 22. Missing Annotated Type Hint - api/consensus.py (Line 1102)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ1_16zWt-zbsGOGHn2J |
| **Rule** | python:S8410 |
| **Severity** | BLOCKER |
| **Status** | OPEN |
| **Message** | Use "Annotated" type hints for FastAPI dependency injection |
| **Component** | `src/heretek_swarm/api/consensus.py:1102` |
| **CleanCode Category** | CLEAR |

**Recommended Fix:** Change `Depends(SomeClass)` to `Annotated[..., Depends(SomeClass)]`

---

### 23. Missing Annotated Type Hint - api/consensus.py (Line 1137)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ1_16zWt-zbsGOGHn2M |
| **Rule** | python:S8410 |
| **Severity** | BLOCKER |
| **Status** | OPEN |
| **Message** | Use "Annotated" type hints for FastAPI dependency injection |
| **Component** | `src/heretek_swarm/api/consensus.py:1137` |
| **CleanCode Category** | CLEAR |

**Recommended Fix:** Change `Depends(SomeClass)` to `Annotated[..., Depends(SomeClass)]`

---

### 24. Missing HTTPException Documentation - api/consensus.py (Line 1118)

| Field | Value |
|-------|-------|
| **Issue Key** | AZ1_16zWt-zbsGOGHn2K |
| **Rule** | python:S8415 |
| **Severity** | MAJOR |
| **Status** | OPEN |
| **Message** | Document this HTTPException with status code 503 in the "responses" parameter. |
| **Component** | `src/heretek_swarm/api/consensus.py:1118` |
| **CleanCode Category** | COMPLETE |

**Recommended Fix:** Add `responses={503: {"description": "Tribunal not available"}}` to the FastAPI endpoint decorator.

---

## Statistics

- **Total CRITICAL issues found:** 42
- **OPEN CRITICAL issues:** 24
- **CLOSED CRITICAL issues:** 18
- **HIGH severity OPEN issues:** 0

## Issue Distribution by Type (Open CRITICAL)

| Rule | Count | Description |
|------|-------|-------------|
| S3776 | 14 | Cognitive Complexity exceeds threshold |
| S1192 | 7 | Duplicated string literals |
| S8410 | 2 | Missing Annotated type hints for FastAPI |
| S8415 | 1 | Missing HTTPException documentation |

## Recommended Priority Actions

1. **Immediate (Blockers):** Fix 2 open `S8410` issues in `api/consensus.py` - these affect FastAPI dependency injection correctness.

2. **High Priority:** Address `mcp/registry.py:324` (complexity 61) - this is severely over threshold and affects core registry functionality.

3. **High Priority:** Address `main_loop.py:525` (complexity 28) - nearly double the threshold.

4. **Medium Priority:** Fix all `S1192` duplicated string literal issues - easy wins that improve maintainability.

5. **Standard Priority:** Address remaining cognitive complexity issues in all files systematically.