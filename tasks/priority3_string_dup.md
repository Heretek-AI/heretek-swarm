# Priority 3: MEDIUM - String Literal Duplications

## Objective
Fix 3 string literal duplication issues.

## Files to Fix
| File | Line | Literal | Occurrences |
|------|------|---------|-------------|
| src/heretek_swarm/actors/examiner.py | 686 | "Unnamed Test" | 3 |
| src/heretek_swarm/actors/validation.py | 355 | "Task description" | 3 |
| src/heretek_swarm/api/emergent_intelligence.py | 92 | "Number of history items" | 4 |

## Rule
python:S1192

## Remediation
```python
# BEFORE
name = "Unnamed Test"
# ... later ...
name = "Unnamed Test"

# AFTER
DEFAULT_TEST_NAME = "Unnamed Test"
name = DEFAULT_TEST_NAME
```

## Verification
1. Constants defined at module level
2. All occurrences replaced with constants
3. No functionality changes