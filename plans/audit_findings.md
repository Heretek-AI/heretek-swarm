# Phase 1 Audit Findings - OVERNIGHT_LOOP.md

**Date**: 2026-04-11  
**Protocol**: OVERNIGHT_LOOP.md Phase 1 → Phase 2  
**Status**: Remediation In Progress

## Executive Summary

| Check | Result | Status |
|-------|--------|--------|
| `datetime.utcnow()` | 28 instances | ❌ FAIL |
| TODO/FIXME/XXX/HACK | 0 instances | ✅ PASS |
| Hardcoded passwords | 0 instances | ✅ PASS |
| Test collection | 1906 collected, 15 errors | ⚠️ NEEDS FIX |
| Ruff linting | 2586 errors | ⚠️ NEEDS TRIAGE |
| Bandit security | 68 findings (63 LOW, 5 MEDIUM) | ⚠️ REVIEW |
| Mypy | 1 error (consciousness.py:214) | ❌ FAIL |

## Critical Findings

### CRIT-001: datetime.utcnow() — 28 Instances
**Severity**: HIGH  
**Detail**: `datetime.utcnow()` is deprecated since Python 3.12. Must replace with `datetime.now(timezone.utc)`.  
**Action**: Automated find-and-replace across all source files.

### CRIT-002: Mypy Error — consciousness.py:214
**Severity**: HIGH  
**Detail**: Parameter ordering violation — `authenticated: Annotated[str, Depends(verify_auth)]` (no default) follows `window_seconds: Optional[int] = Query(None, ...)` (has default).  
**Action**: Move `authenticated` parameter before Query parameters with defaults.

### CRIT-003: Test Collection Errors — 15 Files
**Severity**: MEDIUM  
**Detail**: `TypeError: unsupported operand type(s) for |: 'NoneType' and 'NoneType'` — likely Python 3.13 compatibility issue with `X | None` syntax in type hints where `X` may not be properly imported.  
**Action**: Fix type hint syntax in affected test files.

### INFO-001: Ruff — 2586 Errors
**Severity**: LOW (mostly style)  
**Detail**: E402 (import placement), E501 (line length), SIM102 (simplifiable if), etc.  
**Action**: Auto-fix safe rules, manually review remaining.

### INFO-002: Bandit — 68 Findings
**Severity**: LOW  
**Detail**: B311 (random module) ~40+, B104 (bind all interfaces) 5, B110 (try/except/pass) 8, B608 (SQL) 2 (already nosec'd).  
**Action**: Add `# nosec` annotations where appropriate, review B104 instances.

## Remediation Priority

1. **CRIT-002**: Fix consciousness.py parameter ordering (blocks bandit AST parsing)
2. **CRIT-001**: Replace 28 datetime.utcnow() instances
3. **CRIT-003**: Fix 15 test collection errors
4. **INFO-001**: Auto-fix ruff errors (safe rules only)
5. **INFO-002**: Review bandit findings
