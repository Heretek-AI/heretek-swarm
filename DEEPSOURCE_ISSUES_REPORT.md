# DeepSource Issues Report - Heretek-AI/heretek-swarm

**Generated:** 2026-04-10  
**Source:** https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/issues

---

## Executive Summary

| Category | Total Issues | Critical | Major | Minor |
|----------|-------------|----------|-------|-------|
| **Anti-pattern** | 1.4k | 1 | ~1.4k | 2 |
| **Performance** | 2.3k | 0 | ~2.3k | 100 |
| **Bug Risk** | 421 | 3 | ~418 | 0 |
| **Security** | 14 | 0 | 3 | 11 |
| **Secrets** | 46 | - | - | - |
| **Total** | **4.2k** | **4** | **~4.1k** | **~113** |

---

## Critical Severity Issues (Priority 1)

### 1. PYL-W0101 - Statement not reachable on execution
- **Category:** Anti-pattern
- **Severity:** Critical
- **Occurrences:** 1
- **File:** [`tests/observability/test_dashboard_api.py`](tests/observability/test_dashboard_api.py:129)
- **Description:** Code after a `return` statement that will never execute
- **Remediation:** Remove unreachable code after return statement

### 2. PYL-W0706 - Except handler raises immediately
- **Category:** Bug Risk
- **Severity:** Critical
- **Occurrences:** 3
- **Files:**
  - [`src/heretek_swarm/collective/society.py`](src/heretek_swarm/collective/society.py:736)
  - [`src/heretek_swarm/actors/perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py:628, 566)
- **Description:** Using `raise` as the first or only operator in an except handler is useless
- **Remediation:** Remove the raise operator or the entire try-except-raise block

---

## Security Issues (Priority 2)

### 1. BAN-B104 - Binding to all interfaces detected with hardcoded values
- **Severity:** Major
- **Occurrences:** 5
- **File:** [`src/heretek_swarm/runtime/autonomous_runtime_config.py`](src/heretek_swarm/runtime/autonomous_runtime_config.py:272, 227, 175)
- **Description:** Binding to `0.0.0.0` opens service to all network interfaces
- **Remediation:** Use `127.0.0.1` for local-only access or configure via environment variables

### 2. PTC-W1003 - Audit required: Insecure hash function
- **Severity:** Major
- **Occurrences:** 2
- **Files:** 2 files (details require further investigation)
- **Description:** Use of cryptographically weak hash functions
- **Remediation:** Replace with SHA-256 or stronger hash functions

### 3. PYL-W0122 - Audit required: Use of exec
- **Severity:** Major
- **Occurrences:** 1
- **Description:** Dynamic code execution with `exec()` is a security risk
- **Remediation:** Avoid `exec()` or implement strict input validation

### 4. PTC-W6004 - External control of file name or path
- **Severity:** Minor
- **Occurrences:** 5
- **Files:** 3 files
- **Description:** User-controlled file paths can lead to path traversal attacks
- **Remediation:** Validate and sanitize file paths, use allowlists

### 5. PY-A6006 - Configuring loggers can be security-sensitive
- **Severity:** Minor
- **Occurrences:** 1
- **Description:** Logger configuration may expose sensitive information
- **Remediation:** Review logger configuration for sensitive data exposure

---

## Bug Risk Issues (Priority 2)

### 1. PYL-W0404 - Multiple imports for an import name detected
- **Severity:** Major
- **Occurrences:** 31
- **Files:** 18 files
- **Description:** Same name imported multiple times, may cause confusion
- **Remediation:** Consolidate imports or use aliases

### 2. PTC-W0027 - f-string used without any expression
- **Severity:** Major
- **Occurrences:** 45
- **Files:** 19 files
- **Description:** f-string without variables is just a regular string
- **Remediation:** Use regular strings or add expressions to f-strings

### 3. PTC-W0068 - Consider using identity comparison with singleton
- **Severity:** Major
- **Occurrences:** 2
- **Files:** 1 file
- **Description:** Using `==` instead of `is` for singleton comparison
- **Remediation:** Use `is` for comparing with `None`, `True`, `False`

### 4. PYL-W0602 - Global variable is declared but not used
- **Severity:** Major
- **Occurrences:** 4
- **Files:** 1 file
- **Description:** Unused global variable declaration
- **Remediation:** Remove unused global declarations

### 5. PYL-W0109 - Duplicate dictionary keys
- **Severity:** Major
- **Occurrences:** 1
- **Files:** 1 file
- **Description:** Duplicate keys in dictionary literal
- **Remediation:** Remove duplicate keys

### 6. SH-2086 - Use double quote to prevent globbing and word splitting
- **Severity:** Major
- **Occurrences:** 7
- **Files:** 2 shell script files
- **Description:** Unquoted variables in shell scripts
- **Remediation:** Quote all variable expansions in shell scripts

---

## Performance Issues (Priority 3)

### 1. PYL-R0201 - Consider decorating method with @staticmethod
- **Severity:** Major
- **Occurrences:** 2,200
- **Files:** 173 files
- **Description:** Methods that don't use `self` could be static
- **Remediation:** Add `@staticmethod` decorator to methods not using `self`

### 2. PYL-R1714 - Consider using in
- **Severity:** Major
- **Occurrences:** 1
- **Files:** 1 file
- **Description:** Multiple equality comparisons can be simplified with `in`
- **Remediation:** Use `x in (a, b, c)` instead of `x == a or x == b or x == c`

---

## Anti-pattern Issues (Priority 3)

### 1. PTC-W0048 - if statements can be merged
- **Severity:** Major
- **Occurrences:** 38
- **Files:** 24 files
- **Example File:** [`src/heretek_swarm/api/consciousness.py`](src/heretek_swarm/api/consciousness.py:583)
- **Description:** Nested if statements can be collapsed using `and` operator
- **Remediation:** Merge nested conditions: `if cond1 and cond2:`

### 2. PY-W2000 - Imported name is not used anywhere in the module
- **Severity:** Major
- **Occurrences:** 406
- **Files:** 108 files
- **Description:** Unused imports clutter the namespace
- **Remediation:** Remove unused imports

### 3. PTC-W0015 - Unnecessary generator
- **Severity:** Major
- **Occurrences:** 19
- **Files:** 6 files
- **Description:** Generator expression used where list comprehension is more appropriate
- **Remediation:** Use list comprehension when immediate evaluation is needed

### 4. PTC-W0062 - with statements can be merged
- **Severity:** Major
- **Occurrences:** 14
- **Files:** 12 files
- **Description:** Multiple consecutive with statements can be combined
- **Remediation:** Use single with statement with multiple context managers

### 5. PTC-W0047 - Empty block of code found
- **Severity:** Major
- **Occurrences:** 4
- **Files:** 3 files
- **Description:** Empty code blocks (pass-only)
- **Remediation:** Remove empty blocks or add meaningful implementation

### 6. PY-W0070 - Appending to list immediately following its definition
- **Severity:** Major
- **Occurrences:** 4
- **Files:** 4 files
- **Description:** List defined then immediately appended to
- **Remediation:** Initialize list with initial values: `my_list = [value]`

### 7. PTC-W0049 - Function/method with an empty body
- **Severity:** Major
- **Occurrences:** 9
- **Files:** 1 file
- **Description:** Function with only `pass` statement
- **Remediation:** Implement function or remove if unnecessary

### 8. PY-W0069 - Consider removing the commented out code block
- **Severity:** Major
- **Occurrences:** 3
- **Files:** 3 files
- **Description:** Dead code left in comments
- **Remediation:** Remove commented-out code blocks

### 9. PYL-C0201 - Consider iterating dictionary
- **Severity:** Major
- **Occurrences:** 2
- **Files:** 2 files
- **Description:** Inefficient dictionary iteration pattern
- **Remediation:** Use `.items()` for key-value iteration

### 10. PY-W0075 - Consider using all
- **Severity:** Major
- **Occurrences:** 1
- **Files:** 1 file
- **Description:** Manual loop can be replaced with `all()` builtin
- **Remediation:** Use `all()` for checking all conditions

### 11. PTC-W0018 - Unnecessary literal
- **Severity:** Minor
- **Occurrences:** 1
- **Files:** 1 file
- **Description:** Unnecessary literal in code
- **Remediation:** Remove or simplify

### 12. PYL-W0127 - Variable assigned to itself
- **Severity:** Minor
- **Occurrences:** 1
- **Files:** 1 file
- **Description:** Self-assignment has no effect
- **Remediation:** Remove self-assignment

### 13. JS-R1005 - Function with cyclomatic complexity higher than threshold
- **Severity:** Minor
- **Occurrences:** 100
- **Files:** 52 files (JavaScript/TypeScript)
- **Description:** Complex functions are hard to maintain
- **Remediation:** Refactor complex functions into smaller units

### 14. JS-W1041 - Found complex boolean return
- **Severity:** Major
- **Occurrences:** 1
- **Files:** 1 file (JavaScript/TypeScript)
- **Description:** Complex boolean logic in return statement
- **Remediation:** Simplify boolean expressions

### 15. JS-R1004 - Useless template literal found
- **Severity:** Minor
- **Occurrences:** 4
- **Files:** 3 files (JavaScript/TypeScript)
- **Description:** Template literal without variables
- **Remediation:** Use regular string literals

---

## Recommendations by Priority

### Immediate Action (Critical)
1. Fix unreachable code in test files
2. Remove useless exception re-raises in production code

### High Priority (Security)
1. Review and fix hardcoded `0.0.0.0` bindings
2. Audit use of insecure hash functions
3. Review any `exec()` usage
4. Validate file path handling

### Medium Priority (Bug Risk)
1. Remove unused imports (406 occurrences)
2. Fix f-string misuse (45 occurrences)
3. Quote shell script variables
4. Fix duplicate dictionary keys

### Low Priority (Code Quality)
1. Add `@staticmethod` decorators where appropriate (2,200 occurrences)
2. Merge nested if statements (38 occurrences)
3. Remove commented-out code
4. Simplify complex functions

---

## Files Requiring Most Attention

| File | Issues | Categories |
|------|--------|------------|
| `src/heretek_swarm/runtime/autonomous_runtime_config.py` | 5+ | Security |
| `src/heretek_swarm/collective/society.py` | 3+ | Bug Risk |
| `src/heretek_swarm/actors/perceiver_plus.py` | 3+ | Bug Risk |
| `src/heretek_swarm/api/consciousness.py` | Multiple | Anti-pattern |
| `tests/observability/test_dashboard_api.py` | 1 | Critical |

---

## Notes

- Total of 4.2k issues detected across the repository
- Security category shows 14 issues (5 Major, 9 Minor)
- Secrets category shows 46 issues (requires separate investigation)
- Performance issues are dominated by `@staticmethod` recommendations (2.2k)
- Anti-pattern issues include many unused imports (406) and f-string misuse (45)
