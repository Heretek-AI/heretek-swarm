# Priority 3: MEDIUM - Time-Dependent Class Body Expressions

## Objective
Fix 3 issues with time expressions evaluated at class definition time.

## Files to Fix
| File | Line | Issue |
|------|------|-------|
| src/heretek_swarm/actors/langroid_adapter.py | 64 | Time expression in class body |
| src/heretek_swarm/consensus/raft_election.py | 119 | Time expression in class body |
| src/heretek_swarm/gateway/nats_event_mesh.py | 64 | Time expression in class body |

## Rule
pythonenterprise:S8434

## Remediation
```python
# BEFORE (Evaluated at class definition time)
class MyClass:
    timeout = time.time()  # Fixed at definition time!

# AFTER (Evaluated at instance creation time)
class MyClass:
    def __init__(self):
        self.timeout = time.time()
    
    # OR for class-level:
    @classmethod
    def get_timeout(cls):
        return time.time()
```

## Verification
1. Time expressions evaluated at correct time
2. Functionality preserved
3. No side effects from the change