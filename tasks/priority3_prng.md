# Priority 3: MEDIUM - Weak PRNG Usage (50+ Issues)

## Objective
Replace insecure random with cryptographically secure alternatives.

## Files to Fix
- src/heretek_swarm/collective/adaptive_learning.py - 10 issues
- src/heretek_swarm/collective/swarm_intelligence.py - 10 issues
- src/heretek_swarm/collective/agent_adaptation.py - 1 issue
- src/heretek_swarm/security/ddos_protection.py - 1 issue
- tests/load/locustfile.py - 12 issues
- tests/load/k6/load_test.js - 8 issues
- dashboard/frontend files - 15 issues

## Rules
python:S2245, javascript:S2245, typescript:S2245

## Remediation
Python:
```python
# BEFORE (Insecure for cryptographic use)
import random
token = random.random()

# AFTER (Cryptographically secure)
import secrets
token = secrets.token_hex(32)

# OR for non-security random needs (document intent)
import random
# NOTE: Used for simulation only, not security-critical
value = random.random()
```

JavaScript/TypeScript:
```javascript
// BEFORE
const rand = Math.random();

// AFTER (for security)
import crypto from 'crypto';
const token = crypto.randomBytes(32).toString('hex');

// OR for non-security
// NOTE: Used for simulation only
const rand = Math.random();
```

## Verification
1. Security-critical code uses secrets/crypto
2. Non-security uses documented with comments
3. No security regressions in functionality