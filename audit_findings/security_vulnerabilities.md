# Security Vulnerabilities Audit Report

**Project:** Heretek-AI_heretek-swarm  
**Date:** 2026-04-13  
**Total Security Issues:** 26

---

## Summary by Severity

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 3 | Time-dependent expression (class attribute) |
| MAJOR | 18 | SSRF (7), Hard-coded credentials (2), Kubernetes RBAC (7), Kubernetes storage limits (2) |
| MINOR | 1 | Log injection |

---

## Critical Issues

### 1. Time-Dependent Expression in Class Attribute

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ19epLGt-zbsGOG5j8k` |
| **Component** | `src/heretek_swarm/gateway/nats_event_mesh.py:66` |
| **Line** | 66 |
| **Severity** | CRITICAL |
| **Type** | Bug (time-dependent code) |
| **CWE** | N/A (code quality issue) |
| **Security Category** | Time-dependent code |
| **CleanCode Attribute** | LOGICAL |
| **Author** | heretek-bot@users.noreply.github.com |

**Description:**  
A time-dependent expression (`datetime.now()` or similar) is used in a class attribute. This causes the expression to be evaluated once at module import time rather than at each request, leading to stale data.

**Recommended Fix:**  
Move time-dependent logic from class attributes into methods that are called at request time:

```python
# Noncompliant (class attribute):
class NatsEventMesh:
    last_check = datetime.now()  # Evaluated once at import

# Compliant (method):
class NatsEventMesh:
    def get_last_check(self):
        return datetime.now()  # Evaluated at each call
```

---

### 2. Time-Dependent Expression in Class Attribute

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ16nXXp1Rn55vnUOufh` |
| **Component** | `src/heretek_swarm/actors/langroid_adapter.py:64` |
| **Line** | 64 |
| **Severity** | CRITICAL |
| **Type** | Bug (time-dependent code) |
| **CWE** | N/A (code quality issue) |
| **Security Category** | Time-dependent code |
| **CleanCode Attribute** | LOGICAL |
| **Author** | heretek-bot@users.noreply.github.com |

**Recommended Fix:**  
Move time-dependent expressions into class methods:

```python
# Noncompliant:
class LangroidAdapter:
    timeout = some_time_related_call()  # Evaluated once

# Compliant:
class LangroidAdapter:
    def get_timeout(self):
        return some_time_related_call()  # Evaluated per-request
```

---

### 3. Time-Dependent Expression in Class Attribute

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ16nXhM1Rn55vnUOulI` |
| **Component** | `src/heretek_swarm/consensus/raft_election.py:119` |
| **Line** | 119 |
| **Severity** | CRITICAL |
| **Type** | Bug (time-dependent code) |
| **CWE** | N/A (code quality issue) |
| **Security Category** | Time-dependent code |
| **CleanCode Attribute** | LOGICAL |
| **Author** | heretek-bot@users.noreply.github.com |

**Recommended Fix:**  
Move time-dependent expressions into methods called at request time.

---

## Major Issues - SSRF Vulnerabilities

### 4. Server-Side Request Forgery (SSRF)

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ2DROEVK0fgB4uOtfOs` |
| **Component** | `src/heretek_swarm/api/wizard.py:470-483` |
| **Severity** | MAJOR |
| **Vulnerability Type** | SSRF (CWE-918) |
| **CWE** | CWE-918 (Server-Side Request Forgery), CWE-20 (Improper Input Validation) |
| **Security Category** | Injection |
| **OWASP** | Top 10 2021 Category A10 - SSRF |
| **Author** | johndoe@example.com |

**Description:**  
The code constructs a URL from user-controlled data without proper validation, making it vulnerable to SSRF attacks.

**Recommended Fix:**  
Implement URL validation with an allowlist:

```python
from urllib.parse import urlparse

SCHEMES_ALLOWLIST = ['https']
DOMAINS_ALLOWLIST = ['trusted.example.com']

def safe_request(url):
    parsed = urlparse(url)
    if parsed.scheme not in SCHEMES_ALLOWLIST:
        raise ValueError("Invalid scheme")
    if parsed.hostname not in DOMAINS_ALLOWLIST:
        raise ValueError("Invalid hostname")
    return make_request(url)
```

---

### 5-7. Additional SSRF Vulnerabilities

| Issue Key | Line Range | Message |
|-----------|-----------|---------|
| `AZ2DROEVK0fgB4uOtfOw` | 511-515 | Change this code to not construct the URL from user-controlled data. |
| `AZ2DROEVK0fgB4uOtfOy` | 536 | Change this code to not construct the URL from user-controlled data. |
| `AZ2DROEVK0fgB4uOtfOx` | 563-575 | Change this code to not construct the URL from user-controlled data. |
| `AZ2DROEVK0fgB4uOtfOu` | 599-611 | Change this code to not construct the URL from user-controlled data. |
| `AZ2DROEVK0fgB4uOtfOt` | 635-647 | Change this code to not construct the URL from user-controlled data. |
| `AZ2DROEVK0fgB4uOtfOv` | 672 | Change this code to not construct the URL from user-controlled data. |

**All located in:** `src/heretek_swarm/api/wizard.py`  
**Recommended Fix:** Same as issue #4 - implement URL allowlist validation.

---

## Major Issues - Hard-coded Credentials

### 8. Hard-coded Password Detected

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ16nYPd1Rn55vnUOvPI` |
| **Component** | `tests/state/test_repository.py:61` |
| **Line** | 61 |
| **Severity** | MAJOR |
| **Vulnerability Type** | Hard-coded credentials |
| **CWE** | CWE-798 (Use of Hard-coded Credentials), CWE-259 (Use of Hard-coded Password) |
| **Security Category** | Authentication |
| **OWASP** | Top 10 2021 Category A7 - Identification and Authentication Failures |
| **Author** | heretek-bot@users.noreply.github.com |

**Description:**  
A hard-coded password was detected in test code.

**Recommended Fix:**  
Use environment variables or a secrets manager:

```python
# Noncompliant:
password = "admin"

# Compliant:
import os
password = os.getenv("TEST_PASSWORD")
```

---

### 9. Hard-coded Password Detected

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ16nYRl1Rn55vnUOvRA` |
| **Component** | `tests/collective/test_session46_emergent_intelligence.py:683` |
| **Line** | 683 |
| **Severity** | MAJOR |
| **Vulnerability Type** | Hard-coded credentials |
| **CWE** | CWE-798, CWE-259 |
| **Security Category** | Authentication |
| **Author** | heretek-bot@users.noreply.github.com |

**Recommended Fix:**  
Same as issue #8 - use environment variables instead of hard-coded passwords.

---

## Major Issues - Kubernetes RBAC

### 10-16. Service Account Not Bound to RBAC

| Issue Key | Component | Line |
|-----------|-----------|------|
| `AZ16nX_I1Rn55vnUOvAK` | k8s/autonomous-deployment.yaml | 26 |
| `AZ16nYAD1Rn55vnUOvAg` | k8s/dashboard-deployment.yaml | 29 |
| `AZ16nX_s1Rn55vnUOvAV` | k8s/grafana-deployment.yaml | 19 |
| `AZ16nX_R1Rn55vnUOvAM` | k8s/postgres-deployment.yaml | 20 |
| `AZ16nX_71Rn55vnUOvAc` | k8s/qdrant-deployment.yaml | 20 |
| `AZ16nYAK1Rn55vnUOvAi` | k8s/redis-deployment.yaml | 20 |
| `AZ16nX_Y1Rn55vnUOvAP` | k8s/api-deployment.yaml | 28 |

**Severity:** MAJOR  
**Vulnerability Type:** Missing RBAC binding  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**Security Category:** Kubernetes Security - Service Account Permissions  

**Description:**  
Service account tokens are mounted by default. If a pod is compromised, an attacker could use this token to access the Kubernetes API.

**Recommended Fix:**  
Disable automounting or bind service account to RBAC:

```yaml
# Option 1: Disable automounting at pod level
spec:
  automountServiceAccountToken: false

# Option 2: Bind service account to least-privilege Role
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: minimal-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
subjects:
- kind: ServiceAccount
  name: your-sa
roleRef:
  kind: Role
  name: minimal-reader
```

---

## Major Issues - Missing Storage Limits

### 17-20. Ephemeral Storage Not Limited

| Issue Key | Component | Line |
|-----------|-----------|------|
| `AZ16nX_s1Rn55vnUOvAW` | k8s/grafana-deployment.yaml | 20 |
| `AZ16nX_R1Rn55vnUOvAN` | k8s/postgres-deployment.yaml | 21 |
| `AZ16nX_k1Rn55vnUOvAS` | k8s/prometheus-deployment.yaml | 21 |
| `AZ16nYAK1Rn55vnUOvAj` | k8s/redis-deployment.yaml | 21 |
| `AZ16nX_71Rn55vnUOvAd` | k8s/qdrant-deployment.yaml | 21 |
| `AZ16nX_Y1Rn55vnUOvAQ` | k8s/api-deployment.yaml | 29 |

**Severity:** MAJOR  
**Vulnerability Type:** Missing resource limits  
**CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)  
**Security Category:** Resource Management  

**Description:**  
Container has no ephemeral storage limit, which can lead to resource exhaustion.

**Recommended Fix:**  
Add `ephemeral-storage` limits to container spec:

```yaml
spec:
  containers:
    - name: grafana
      image: grafana/grafana
      resources:
        limits:
          ephemeral-storage: "2Gi"
        requests:
          ephemeral-storage: "1Gi"
```

---

## Minor Issues - Log Injection

### 21. Log Injection Vulnerability

| Field | Value |
|-------|-------|
| **Issue Key** | `AZ1-MqxUyCqiNXJ_6Ezb` |
| **Component** | `src/heretek_swarm/consensus/audit_query.py:382` |
| **Line** | 382 |
| **Severity** | MINOR |
| **Vulnerability Type** | Log Injection (CWE-117) |
| **CWE** | CWE-117 (Improper Output Neutralization for Logs), CWE-20 |
| **Security Category** | Injection |
| **OWASP** | Top 10 2021 Category A3 - Injection, A9 - Security Logging and Monitoring Failures |
| **Author** | heretek-bot@users.noreply.github.com |

**Description:**  
User-controlled data is logged without sanitization, enabling log injection attacks.

**Recommended Fix:**  
Sanitize log input or use structured logging:

```python
import base64

def safe_log(logger, data):
    if data.isalnum():
        logger.info("%s", data)
    else:
        logger.info("Invalid Input: %s", base64.b64encode(data.encode('UTF-8')))
```

---

## Remediation Priority

| Priority | Count | Issues |
|----------|-------|--------|
| **P1 - Critical** | 3 | Time-dependent expressions (lines 66, 64, 119) |
| **P2 - High** | 16 | SSRF vulnerabilities (7), Hard-coded credentials (2), Kubernetes RBAC (7) |
| **P3 - Medium** | 7 | Kubernetes storage limits (7) |
| **P4 - Low** | 1 | Log injection |

---

## References

- [OWASP Top 10 2021 - SSRF](https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/)
- [OWASP Top 10 2021 - Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [CWE-918: Server-Side Request Forgery](https://cwe.mitre.org/data/definitions/918.html)
- [CWE-798: Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)
- [CWE-306: Missing Authentication for Critical Function](https://cwe.mitre.org/data/definitions/306.html)
- [CWE-770: Allocation of Resources Without Limits](https://cwe.mitre.org/data/definitions/770.html)
- [Kubernetes Documentation - Configure Service Accounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)