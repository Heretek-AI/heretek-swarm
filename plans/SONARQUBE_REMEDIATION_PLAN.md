# SonarQube Codebase Review - Remediation Plan

## Executive Summary

**Project:** Heretek-AI_heretek-swarm  
**Analysis Date:** 2026-04-11  
**Total Issues:** 2,849  
**Code Size:** 139,780 lines of code  

### Quality Gate Status: ❌ FAILED

| Condition | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| New Reliability Rating | ≤ 1 | 5 | ❌ ERROR |
| New Security Rating | ≤ 1 | 5 | ❌ ERROR |
| New Maintainability Rating | ≤ 1 | 1 | ✅ OK |
| Security Hotspots Reviewed | 100% | 0% | ❌ ERROR |

### Key Metrics

| Metric | Value |
|--------|-------|
| Bugs | 438 |
| Vulnerabilities | 27 |
| Code Smells | 2,384 |
| Security Hotspots | 91 |
| Duplicated Lines | 2.7% |
| Total Cyclomatic Complexity | 18,995 |

---

## Priority 1: CRITICAL Issues (Immediate Action Required)

### 1.1 Exposed Secrets - 6 BLOCKER Issues

**Risk:** Hardcoded credentials in source code can lead to unauthorized database access.

| File | Line | Issue |
|------|------|-------|
| [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py:285) | 285 | PostgreSQL password exposed |
| [`src/memory/persistent.py`](src/memory/persistent.py:87) | 87 | PostgreSQL password exposed |
| [`docker-compose.yml`](docker-compose.yml:14) | 14 | PostgreSQL password exposed |
| [`scripts/run_migration.py`](scripts/run_migration.py:24) | 24 | PostgreSQL password exposed |
| [`scripts/run_migrations.py`](scripts/run_migrations.py:27) | 27 | PostgreSQL password exposed |
| [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml:133) | 133 | PostgreSQL password exposed |

**Remediation:**
1. Immediately rotate all exposed passwords
2. Replace hardcoded values with environment variables
3. Use secrets management (GitHub Secrets, Vault, AWS Secrets Manager)
4. Add `.env` files to `.gitignore` (verify `.env.example` pattern is followed)
5. Run `git filter-branch` or BFG Repo-Cleaner to remove secrets from git history

---

### 1.2 Path Traversal Vulnerability - BLOCKER

**File:** [`src/rag/document_processor.py`](src/rag/document_processor.py:340)  
**Rule:** pythonsecurity:S2083  
**Issue:** Constructing file paths from user-controlled data allows directory traversal attacks.

**Remediation:**
```python
# BEFORE (Vulnerable)
path = base_dir / user_input

# AFTER (Secure)
from pathlib import Path
import os

def safe_path(base_dir: Path, user_input: str) -> Path:
    resolved_base = base_dir.resolve()
    requested_path = (base_dir / user_input).resolve()
    if not str(requested_path).startswith(str(resolved_base)):
        raise ValueError("Path traversal detected")
    return requested_path
```

---

### 1.3 Loop Bounds Vulnerability - CRITICAL

**File:** [`src/state/snapshots.py`](src/state/snapshots.py:301)  
**Rule:** pythonsecurity:S6680  
**Issue:** Setting loop bounds from user-controlled data can lead to DoS attacks.

**Remediation:**
```python
# BEFORE (Vulnerable)
limit = user_provided_limit
for i in range(limit):
    process(item)

# AFTER (Secure)
MAX_LIMIT = 1000
limit = min(user_provided_limit, MAX_LIMIT) if user_provided_limit else MAX_LIMIT
for i in range(limit):
    process(item)
```

---

## Priority 2: HIGH Severity Issues

### 2.1 FastAPI Dependency Injection - 30+ BLOCKER Issues

**Primary Files:**
- [`src/heretek_swarm/api/consciousness.py`](src/heretek_swarm/api/consciousness.py) - 20 issues
- [`src/heretek_swarm/api/emergent_intelligence.py`](src/heretek_swarm/api/emergent_intelligence.py) - 15 issues
- [`src/heretek_swarm/api/rag.py`](src/heretek_swarm/api/rag.py) - 2 issues
- [`src/heretek_swarm/api/plugins.py`](src/heretek_swarm/api/plugins.py) - 0 (documented only)

**Rule:** python:S8410  
**Issue:** Using deprecated FastAPI dependency injection syntax instead of `Annotated` type hints.

**Remediation:**
```python
# BEFORE (Deprecated)
from fastapi import Depends

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    pass

# AFTER (Recommended)
from typing import Annotated
from fastapi import Depends

@app.get("/items")
def get_items(db: Annotated[Session, Depends(get_db)]):
    pass
```

**Affected Endpoints in consciousness.py:**
- Lines: 77, 116, 149, 186, 205-213, 236, 257, 337, 374, 403, 425, 452, 482-483, 515, 536, 565-567, 599, 626, 653, 679, 701, 744-746

---

### 2.2 Undocumented HTTPException Responses - 20+ Issues

**Files Affected:**
- [`src/heretek_swarm/api/consciousness.py`](src/heretek_swarm/api/consciousness.py)
- [`src/heretek_swarm/api/emergent_intelligence.py`](src/heretek_swarm/api/emergent_intelligence.py)
- [`src/heretek_swarm/api/plugins.py`](src/heretek_swarm/api/plugins.py)

**Rule:** python:S8415  
**Issue:** HTTPException status codes not documented in OpenAPI `responses` parameter.

**Remediation:**
```python
# BEFORE
from fastapi import HTTPException

@app.get("/items/{item_id}")
def get_item(item_id: str):
    if not found:
        raise HTTPException(status_code=404)
    return item

# AFTER
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.get(
    "/items/{item_id}",
    responses={
        404: {"description": "Item not found", "model": ErrorModel}
    }
)
def get_item(item_id: str):
    if not found:
        raise HTTPException(status_code=404)
    return item
```

---

### 2.3 High Cognitive Complexity - 17 Functions

**Rule:** python:S3776  
**Threshold:** 15 (functions range from 16-35)

| File | Function | Line | Complexity |
|------|----------|------|------------|
| [`scripts/wire_agents.py`](scripts/wire_agents.py:275) | (unnamed) | 275 | 35 |
| [`scripts/wire_agents_session44.py`](scripts/wire_agents_session44.py:273) | (unnamed) | 273 | 35 |
| [`src/heretek_swarm/actors/perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py:696) | (unnamed) | 696 | 27 |
| [`serverless/handler.py`](serverless/handler.py:275) | (unnamed) | 275 | 25 |
| [`src/heretek_swarm/actors/profiling.py`](src/heretek_swarm/actors/profiling.py:419) | (unnamed) | 419 | 25 |
| [`src/heretek_swarm/actors/perceiver.py`](src/heretek_swarm/actors/perceiver.py:332) | (unnamed) | 332 | 22 |
| [`src/heretek_swarm/actors/perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py:868) | (unnamed) | 868 | 22 |
| [`src/heretek_swarm/actors/sentinel.py`](src/heretek_swarm/actors/sentinel.py:639) | (unnamed) | 639 | 21 |
| [`src/heretek_swarm/actors/perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py:787) | (unnamed) | 787 | 20 |
| [`src/heretek_swarm/actors/sentinel_prime.py`](src/heretek_swarm/actors/sentinel_prime.py:1023) | (unnamed) | 1023 | 20 |
| [`src/heretek_swarm/actors/evaluation.py`](src/heretek_swarm/actors/evaluation.py:391) | (unnamed) | 391 | 19 |
| [`src/heretek_swarm/actors/coordinator.py`](src/heretek_swarm/actors/coordinator.py:220) | (unnamed) | 220 | 17 |
| [`src/heretek_swarm/actors/perceiver.py`](src/heretek_swarm/actors/perceiver.py:461) | (unnamed) | 461 | 17 |
| [`src/heretek_swarm/actors/coordinator.py`](src/heretek_swarm/actors/coordinator.py:328) | (unnamed) | 328 | 16 |
| [`src/heretek_swarm/actors/empath.py`](src/heretek_swarm/actors/empath.py:577) | (unnamed) | 577 | 16 |
| [`src/heretek_swarm/actors/perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py:462) | (unnamed) | 462 | 16 |
| [`src/heretek_swarm/actors/profiling.py`](src/heretek_swarm/actors/profiling.py:854) | (unnamed) | 854 | 16 |

**Remediation Strategies:**
1. **Extract Methods:** Break large functions into smaller, single-responsibility functions
2. **Early Returns:** Replace nested conditionals with guard clauses
3. **Strategy Pattern:** Replace complex conditional logic with polymorphic strategies
4. **Helper Classes:** Extract related logic into dedicated helper classes

---

## Priority 3: MEDIUM Severity Issues

### 3.1 Security Hotspots Requiring Review - 91 Items

**Categories:**

| Category | Count | Risk Level |
|----------|-------|------------|
| Weak Cryptography (PRNG) | 50+ | MEDIUM |
| Regex DoS (ReDoS) | 7 | MEDIUM |
| Docker Permissions | 4 | MEDIUM |
| Insecure HTTP Protocol | 6 | LOW |
| GitHub Actions Security | 15 | LOW |
| Others | 9 | LOW |

#### 3.1.1 Regex Denial of Service (ReDoS) - 7 Issues

**Files:**
- [`scripts/wire_agents.py`](scripts/wire_agents.py:321)
- [`scripts/wire_agents_session44.py`](scripts/wire_agents_session44.py:319)
- [`src/heretek_swarm/plugins/liberation.py`](src/heretek_swarm/plugins/liberation.py) - 5 issues (lines 124, 133, 170-172)

**Rule:** python:S5852

**Remediation:**
```python
# BEFORE (Vulnerable to ReDoS)
pattern = r'(a+)+$'  # Exponential backtracking

# AFTER (Safe)
import re
pattern = r'a+$'  # Linear time
# Or use atomic groups via regex module
# pip install regex
import regex
pattern = r'(?>a+)$'
```

#### 3.1.2 Weak Pseudorandom Number Generator - 50+ Issues

**Primary Files:**
- [`src/heretek_swarm/collective/adaptive_learning.py`](src/heretek_swarm/collective/adaptive_learning.py) - 10 issues
- [`src/heretek_swarm/collective/swarm_intelligence.py`](src/heretek_swarm/collective/swarm_intelligence.py) - 10 issues
- [`src/heretek_swarm/collective/agent_adaptation.py`](src/heretek_swarm/collective/agent_adaptation.py) - 1 issue
- [`src/heretek_swarm/security/ddos_protection.py`](src/heretek_swarm/security/ddos_protection.py) - 1 issue
- `tests/load/locustfile.py` - 12 issues
- `tests/load/k6/load_test.js` - 8 issues
- Dashboard frontend files - 15 issues

**Rule:** python:S2245, javascript:S2245, typescript:S2245

**Remediation:**
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

#### 3.1.3 Docker Security Issues

| File | Line | Issue | Rule |
|------|------|-------|------|
| [`docker/Dockerfile`](docker/Dockerfile) | 32 | Root user | docker:S6471 |
| [`docker/Dockerfile`](docker/Dockerfile) | 50 | File permissions | docker:S6504 |
| [`dashboard/frontend/Dockerfile`](dashboard/frontend/Dockerfile) | 20 | Recursive copy | docker:S6470 |
| [`dashboard/frontend/Dockerfile`](dashboard/frontend/Dockerfile) | 29 | Root user | docker:S6471 |

**Remediation:**
```dockerfile
# BEFORE
FROM python:3.11
COPY . /app

# AFTER
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
COPY --chown=appuser:appuser . /app
USER appuser
WORKDIR /app
```

---

### 3.2 String Literal Duplications - 3 Issues

| File | Line | Literal | Occurrences |
|------|------|---------|-------------|
| [`src/heretek_swarm/actors/examiner.py`](src/heretek_swarm/actors/examiner.py:686) | 686 | "Unnamed Test" | 3 |
| [`src/heretek_swarm/actors/validation.py`](src/heretek_swarm/actors/validation.py:355) | 355 | "Task description" | 3 |
| [`src/heretek_swarm/api/emergent_intelligence.py`](src/heretek_swarm/api/emergent_intelligence.py:92) | 92 | "Number of history items" | 4 |

**Rule:** python:S1192

**Remediation:**
```python
# BEFORE
name = "Unnamed Test"
# ... later ...
name = "Unnamed Test"

# AFTER
DEFAULT_TEST_NAME = "Unnamed Test"
name = DEFAULT_TEST_NAME
```

---

### 3.3 Time-Dependent Class Body Expressions - 3 Issues

**Rule:** pythonenterprise:S8434

| File | Line | Issue |
|------|------|-------|
| [`src/heretek_swarm/actors/langroid_adapter.py`](src/heretek_swarm/actors/langroid_adapter.py:64) | 64 | Time expression in class body |
| [`src/heretek_swarm/consensus/raft_election.py`](src/heretek_swarm/consensus/raft_election.py:119) | 119 | Time expression in class body |
| [`src/heretek_swarm/gateway/nats_event_mesh.py`](src/heretek_swarm/gateway/nats_event_mesh.py:64) | 64 | Time expression in class body |

**Remediation:**
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

---

## Priority 4: LOW Severity Issues

### 4.1 GitHub Actions - Unpinned Dependencies - 20+ Issues

**Files:**
- [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) - 12 issues
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) - 7 issues

**Rule:** githubactions:S7637, githubactions:S7636

**Current Issues:**
1. Using tag names instead of full SHA hashes (e.g., `@v3` instead of `@abc123...`)
2. Expanding secrets in run blocks

**Remediation:**
```yaml
# BEFORE (Vulnerable to tag moving)
uses: actions/checkout@v3

# AFTER (Pinned to SHA)
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# BEFORE (Secret in run block)
run: echo "${{ secrets.MY_SECRET }}"

# AFTER (Use env)
env:
  MY_SECRET: ${{ secrets.MY_SECRET }}
run: echo "$MY_SECRET"
```

---

### 4.2 Insecure HTTP Protocol - 6 Issues

| File | Line | Issue |
|------|------|-------|
| [`src/heretek_swarm/api/main.py`](src/heretek_swarm/api/main.py:324) | 324 | HTTP URL |
| [`src/heretek_swarm/observability/tracing.py`](src/heretek_swarm/observability/tracing.py:78) | 78 | HTTP URL |
| [`src/heretek_swarm/runtime/autonomous_runtime.py`](src/heretek_swarm/runtime/autonomous_runtime.py:266) | 266 | HTTP URL |
| [`k8s/configmaps.yaml`](k8s/configmaps.yaml) | 19, 20, 41 | HTTP URLs |

**Rule:** python:S5332, kubernetes:S5332

**Remediation:**
- Replace `http://` with `https://` where possible
- For local development, document the security implications
- Use environment variables to configure protocol based on environment

---

## Implementation Roadmap

### Phase 1: Critical Security Fixes (Week 1)
- [ ] 1.1 Remove all exposed secrets
- [ ] 1.2 Fix path traversal vulnerability
- [ ] 1.3 Fix loop bounds vulnerability
- [ ] Rotate all compromised credentials

### Phase 2: High Priority API Fixes (Week 2-3)
- [ ] 2.1 Update FastAPI dependency injection (30+ endpoints)
- [ ] 2.2 Document HTTPException responses
- [ ] Begin cognitive complexity refactoring (target: 5 functions)

### Phase 3: Security Hotspot Review (Week 3-4)
- [ ] 3.1.1 Fix ReDoS vulnerabilities
- [ ] 3.1.2 Audit and fix PRNG usage (security-critical first)
- [ ] 3.1.3 Harden Dockerfiles
- [ ] Review remaining security hotspots

### Phase 4: Code Quality Improvements (Week 4-6)
- [ ] Complete cognitive complexity refactoring
- [ ] Fix string literal duplications
- [ ] Fix time-dependent class expressions
- [ ] Pin GitHub Actions dependencies

### Phase 5: Documentation & Monitoring (Ongoing)
- [ ] Update security documentation
- [ ] Configure pre-commit hooks for secrets detection
- [ ] Set up automated security scanning in CI/CD
- [ ] Establish code review checklist for security

---

## Recommended Tools & Pre-commit Hooks

```yaml
# .pre-commit-config.yaml additions
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
```

---

## Success Criteria

1. **Quality Gate Pass:**
   - New Reliability Rating ≤ 1
   - New Security Rating ≤ 1
   - Security Hotspots Reviewed = 100%

2. **Security Metrics:**
   - 0 BLOCKER issues
   - 0 exposed secrets
   - All security hotspots reviewed and resolved

3. **Code Quality:**
   - Cognitive complexity ≤ 15 for all functions
   - Duplication density < 3%
   - Coverage maintained or improved

---

## Appendix: Issue Distribution by File

### Top 10 Files by Issue Count

| File | Issues | Severity Distribution |
|------|--------|----------------------|
| `src/heretek_swarm/api/consciousness.py` | 40+ | 20 BLOCKER, 20 MAJOR |
| `src/heretek_swarm/api/emergent_intelligence.py` | 25+ | 12 BLOCKER, 13 MAJOR/CRITICAL |
| `src/heretek_swarm/collective/adaptive_learning.py` | 15+ | MEDIUM (PRNG) |
| `src/heretek_swarm/collective/swarm_intelligence.py` | 12+ | MEDIUM (PRNG) |
| `src/heretek_swarm/actors/perceiver_plus.py` | 8 | HIGH (Complexity) |
| `.github/workflows/ci-cd.yml` | 15+ | LOW |
| `tests/load/locustfile.py` | 12+ | MEDIUM (PRNG) |
| `src/heretek_swarm/plugins/liberation.py` | 7 | MEDIUM (ReDoS) |
| `dashboard/frontend/src/components/...` | 15+ | MEDIUM (PRNG) |
| `src/heretek_swarm/actors/coordinator.py` | 4 | HIGH (Complexity) |

---

*Generated from SonarQube analysis on 2026-04-11*
