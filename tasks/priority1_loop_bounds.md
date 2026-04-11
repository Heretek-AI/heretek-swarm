# Priority 1: CRITICAL - Loop Bounds Vulnerability

## Objective
Fix the loop bounds vulnerability in src/state/snapshots.py:301

## Issue Details
- **Rule:** pythonsecurity:S6680
- **Issue:** Setting loop bounds from user-controlled data can lead to DoS attacks

## Remediation
Add maximum limit to user-provided loop bounds:

```python
MAX_LIMIT = 1000
limit = min(user_provided_limit, MAX_LIMIT) if user_provided_limit else MAX_LIMIT
```

## Verification
1. Test with extremely large limit values
2. Ensure limit is capped at MAX_LIMIT
3. Verify default behavior when no limit provided