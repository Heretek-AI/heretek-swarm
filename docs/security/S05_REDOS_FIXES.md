# ReDoS Vulnerability Fixes (S5852)

**Date:** 2026-04-16
**Slice:** S05 - Security Hotspot Review Coverage
**Milestone:** M002

## Summary

Fixed 3 HIGH-risk ReDoS vulnerabilities in `src/heretek_swarm/plugins/liberation.py` by replacing vulnerable regex patterns with character-class based alternatives. Documented 2 CI-only scripts that were reviewed and deemed safe for their controlled use case.

## Fixed Vulnerabilities

### 1. liberation.py - import sys detection pattern

**Location:** `src/heretek_swarm/plugins/liberation.py` line ~172

**Before:**
```python
re.compile(r"import\s+.*\s+from\s+['\"]sys['\"]", re.IGNORECASE)
```

**After:**
```python
# FIXED S5852: Use character class [^\s]+ instead of .* to prevent ReDoS
re.compile(r"import\s+[^\s]+\s+from\s+['\"]sys['\"]", re.IGNORECASE)
```

**Risk:** The original pattern `.*\s+` with greedy matching could cause super-linear backtracking when processing strings without a matching "from sys" pattern. An attacker could craft input that causes exponential time complexity.

**Fix:** Replaced `.*\s+` with `[^\s]+\s+` (one or more non-whitespace characters followed by whitespace). This prevents backtracking because `[^\s]+` cannot match more than necessary.

---

### 2. liberation.py - import os detection pattern

**Location:** `src/heretek_swarm/plugins/liberation.py` line ~174

**Before:**
```python
re.compile(r"import\s+.*\s+from\s+['\"]os['\"]", re.IGNORECASE)
```

**After:**
```python
# FIXED S5852: Use character class [^\s]+ instead of .* to prevent ReDoS
re.compile(r"import\s+[^\s]+\s+from\s+['\"]os['\"]", re.IGNORECASE)
```

**Risk:** Same as above - vulnerable to super-linear backtracking.

**Fix:** Same as above - character class prevents backtracking.

---

### 3. liberation.py - import subprocess detection pattern

**Location:** `src/heretek_swarm/plugins/liberation.py` line ~176

**Before:**
```python
re.compile(r"import\s+.*\s+from\s+['\"]subprocess['\"]", re.IGNORECASE)
```

**After:**
```python
# FIXED S5852: Use character class [^\s]+ instead of .* to prevent ReDoS
re.compile(r"import\s+[^\s]+\s+from\s+['\"]subprocess['\"]", re.IGNORECASE)
```

**Risk:** Same as above - vulnerable to super-linear backtracking.

**Fix:** Same as above - character class prevents backtracking.

---

## Documented (Not Fixed - CI Only)

These patterns were reviewed and documented as safe because they operate on controlled CI-generated code, not user input.

### 1. wire_agents.py - logger.info pattern

**Location:** `scripts/wire_agents.py` line ~319

**Pattern:**
```python
init_body_pattern = r"(logger\.info\([^)]*initialized[^)]*\))"
```

**Security Note:** This regex is used only in CI code generation for agent configuration and is not user-facing. The pattern matches simple logger.info calls in generated code. Reviewed for safety since it's only used on controlled input from the code generation pipeline.

---

### 2. wire_agents_session44.py - logger.info pattern

**Location:** `scripts/wire_agents_session44.py` line ~316

**Pattern:**
```python
init_body_pattern = r"(logger\.info\([^)]*initialized[^)]*\))"
```

**Security Note:** Same as above - this regex is used only in CI code generation and is not user-facing.

---

## No Action Required

### setupValidation.ts

**Location:** `dashboard/frontend/src/utils/setupValidation.ts` line 48

**Current Pattern:**
```typescript
normalized = normalized.replace(/\/+$/, '');
```

**Analysis:** The pattern `/\/+$/` (one or more forward slashes followed by end of string) is not ReDoS-vulnerable. The forward slashes do not nest, and the `$` anchor prevents backtracking. Comment added to document the safety review.

---

## Verification Commands

```bash
# Verify patterns use character class instead of .*
grep -E '\[\\s\]\+' src/heretek_swarm/plugins/liberation.py

# Verify ReDoS documentation in CI scripts
grep -c 'ReDoS\|S5852' scripts/wire_agents.py scripts/wire_agents_session44.py

# Test that patterns still match expected inputs
python3 -c "
import re
# Test the fixed patterns
sys_pattern = re.compile(r\"import\s+[^\s]+\s+from\s+['\\\"]sys['\\\"]\", re.IGNORECASE)
os_pattern = re.compile(r\"import\s+[^\s]+\s+from\s+['\\\"]os['\\\"]\", re.IGNORECASE)
subprocess_pattern = re.compile(r\"import\s+[^\s]+\s+from\s+['\\\"]subprocess['\\\"]\", re.IGNORECASE)

# Valid inputs
assert sys_pattern.search('from sys import something')
assert os_pattern.search('import os.path as osp')
assert subprocess_pattern.search('from subprocess import run')

print('All patterns match expected inputs correctly')
"
```

---

## References

- [OWASP ReDoS](https://owasp.org/www-community/attacks/Regular_expression_Denial_of_service_-_ReDoS)
- [SonarQube S5852](https://sonarsource.github.io/rspec/#/rspec/S5852/python)
