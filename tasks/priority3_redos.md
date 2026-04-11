# Priority 3: MEDIUM - Regex DoS (ReDoS) Vulnerabilities

## Objective
Fix 7 ReDoS vulnerabilities in regex patterns.

## Files to Fix
- scripts/wire_agents.py (Line 321)
- scripts/wire_agents_session44.py (Line 319)
- src/heretek_swarm/plugins/liberation.py - 5 issues (lines 124, 133, 170-172)

## Rule
python:S5852

## Remediation
Replace vulnerable patterns with safe alternatives:

```python
# BEFORE (Vulnerable to ReDoS)
pattern = r'(a+)+$'  # Exponential backtracking

# AFTER (Safe)
pattern = r'a+$'  # Linear time
# Or use atomic groups via regex module
import regex
pattern = r'(?>a+)$'
```

## Verification
1. No nested quantifiers in regex patterns
2. Patterns tested with malicious input
3. Performance acceptable for legitimate use