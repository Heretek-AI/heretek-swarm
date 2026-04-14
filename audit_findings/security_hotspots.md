# Security Hotspots Audit Report

**Project:** Heretek-AI_heretek-swarm
**Date:** 2026-04-13
**Total Hotspots:** 124 (all pending review)

---

## Executive Summary

This audit documents 124 security hotspots identified by SonarQube in the Heretek-AI_heretek-swarm project. All hotspots are in `TO_REVIEW` status and require security engineer assessment.

---

## Category Breakdown

| Category | Count | Risk Level |
|----------|-------|------------|
| weak-cryptography | 97 | MEDIUM |
| dos (Regex DoS) | 5 | MEDIUM |
| auth (Dockerfile) | 4 | HIGH |
| permission (Dockerfile) | 3 | MEDIUM |
| encrypt-data (HTTP) | 5 | LOW |

---

## HIGH Risk Findings (Authentication - Dockerfile)

### 1. ARG Used for Secret Handling
- **Key:** `AZ2IUSAkkffvx81wFZaF`
- **Component:** `dashboard/frontend/Dockerfile`
- **Line:** 10
- **Rule:** `docker:S6472`
- **Message:** Make sure that using ARG to handle a secret is safe here.
- **Recommendation:** **FIX** - Do not pass secrets via ARG. Use `--build-arg` only for non-sensitive values. For secrets, use multi-stage builds with secret mounting or environment variables from a secure vault.

### 2. Write Permissions on Copied Resources (Dockerfiles)

| Key | Component | Line | Rule |
|-----|-----------|------|------|
| `AZ16nYYv1Rn55vnUOvcC` | `docker/Dockerfile` | 50 | docker:S6504 |
| `AZ2JC5Sfkffvx81wL6Me` | `mem0_server/Dockerfile` | 14 | docker:S6504 |
| `AZ2JC5Sfkffvx81wL6Mf` | `mem0_server/Dockerfile` | 19 | docker:S6504 |

- **Message:** Make sure no write permissions are assigned to the copied resource.
- **Recommendation:** **FIX** - Review COPY instructions. Ensure copied files/folders do not have overly broad write permissions. Use `chmod` to restrict permissions in the same RUN instruction.

---

## MEDIUM Risk Findings

### Permission Issues (Dockerfile - Running as Root)

| Key | Component | Line | Rule |
|-----|-----------|------|------|
| `AZ16nYKr1Rn55vnUOvHn` | `dashboard/frontend/Dockerfile` | 21 | docker:S6470 |
| `AZ2HxntPdequgXJ-3D6N` | `dashboard/frontend/Dockerfile` | 30 | docker:S6471 |
| `AZ16nYYv1Rn55vnUOvcA` | `docker/Dockerfile` | 32 | docker:S6471 |

- **Message (S6470):** Copying recursively might inadvertently add sensitive data to the container.
- **Message (S6471):** The "nginx"/"python" image runs with "root" as the default user.
- **Recommendation:** **REVIEW & FIX** - Create a non-root user and switch to it using `USER` instruction. For S6470, review what is being copied recursively and ensure no secrets are included.

### Regex DoS Vulnerabilities

| Key | Component | Line | Rule |
|-----|-----------|------|------|
| `AZ2HuxALrWRHR_Bu0xSE` | `dashboard/frontend/src/utils/setupValidation.ts` | 48 | typescript:S5852 |
| `AZ1_qGgqs0Fbzs2jcRwL` | `scripts/wire_agents.py` | 318 | python:S5852 |
| `AZ1_qGgSs0Fbzs2jcRwE` | `scripts/wire_agents_session44.py` | 316 | python:S5852 |
| `AZ16nXmT1Rn55vnUOuos` | `src/heretek_swarm/plugins/liberation.py` | 170 | python:S5852 |
| `AZ16nXmT1Rn55vnUOuot` | `src/heretek_swarm/plugins/liberation.py` | 171 | python:S5852 |
| `AZ16nXmT1Rn55vnUOuou` | `src/heretek_swarm/plugins/liberation.py` | 172 | python:S5852 |

- **Message:** Make sure the regex used here, which is vulnerable to super-linear/polynomial runtime due to backtracking, cannot lead to denial of service.
- **Recommendation:** **FIX** - Refactor vulnerable regex patterns. Use atomic groups `(?>)` or possessive quantifiers `(?=+, ++, ?+, {n}+)` to prevent backtracking. Alternatively, use regex libraries that are immune to ReDoS.

### Weak Cryptography (PRNG) - 97 Instances

Multiple files use `Math.random()` or `random.random()` instead of cryptographically secure random number generators:

**TypeScript Files:**
- `dashboard/frontend/src/components/Logs/LogsPage.tsx` (lines 56, 58-60)
- `dashboard/frontend/src/components/Observability/A2ATracker.tsx` (lines 82-114, 385-394)
- `dashboard/frontend/src/components/Settings/ModelGarage.tsx` (lines 583-587, 621-623, 637)
- `dashboard/frontend/src/components/Setup/ConfigWizard.tsx` (line 845)
- `dashboard/frontend/src/components/UI/Toast.tsx` (line 112)
- `dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx` (line 222)
- `dashboard/frontend/src/hooks/useNodeGrouping.ts` (line 162)

**Python Files:**
- `src/heretek_swarm/collective/adaptive_learning.py` (lines 416, 428, 704, 712, 758, 918, 925, 934)
- `src/heretek_swarm/collective/agent_adaptation.py` (line 899)
- `src/heretek_swarm/collective/algorithms/abc.py` (lines 191, 220)
- `src/heretek_swarm/collective/algorithms/aco.py` (line 219)
- `src/heretek_swarm/collective/algorithms/pso.py` (lines 209, 214)
- `src/heretek_swarm/collective/swarm_intelligence.py` (lines 604-605, 689-690)
- `src/heretek_swarm/security/ddos_protection.py` (line 900)
- `tests/load/locustfile.py` (lines 123, 147, 155, 198, 218, 240, 243-245, 265-266)
- `tests/load/k6/load_test.js` (lines 130, 134, 139, 163, 256, 280-281)

**Rule:** `S2245` - Using pseudorandom number generator is unsafe for security/cryptographic purposes.

**Recommendation:** **FIX** - Replace with crypto-secure alternatives:
- **TypeScript:** Use `crypto.getRandomValues()` or `randomUUID()` from `crypto` module
- **Python:** Use `secrets` module or `os.urandom()` for cryptographic purposes

---

## LOW Risk Findings (HTTP instead of HTTPS)

| Key | Component | Line | Rule |
|-----|-----------|------|------|
| `AZ16nX_z1Rn55vnUOvAY` | `k8s/configmaps.yaml` | 19-20 | kubernetes:S5332 |
| `AZ16nX_z1Rn55vnUOvAa` | `k8s/configmaps.yaml` | 41 | kubernetes:S5332 |
| `AZ169y3mp0xRuTTSrPgE` | `src/heretek_swarm/api/main.py` | 341 | python:S5332 |
| `AZ169y3mp0xRuTTSrPgF` | `src/heretek_swarm/api/main.py` | 341 | python:S5332 |
| `AZ1_qF4Qs0Fbzs2jcRvz` | `src/heretek_swarm/infrastructure/otel/tracing.py` | 104 | python:S5332 |
| `AZ16xBmSkVtj5U5sWsd4` | `src/heretek_swarm/observability/tracing.py` | 78 | python:S5332 |
| `AZ16nXcM1Rn55vnUOuhs` | `src/heretek_swarm/runtime/autonomous_runtime.py` | 268 | python:S5332 |

- **Message:** Using http protocol is insecure. Use https instead.
- **Recommendation:** **REVIEW** - For internal/trusted networks, HTTP may be acceptable. However, configure TLS for production. Ensure environment variables/URLs can be switched to HTTPS easily.

---

## Recommended Review Actions

### IMMEDIATE (Fix before release)
1. **Dockerfile ARG secret handling** - `dashboard/frontend/Dockerfile:10`
2. **Dockerfile write permissions** - All 3 S6504 findings
3. **Dockerfile root user** - All 3 findings (S6470, S6471)
4. **Regex DoS vulnerabilities** - All 6 findings (especially production code in `liberation.py`)

### SHORT-TERM (Review and fix in sprint)
5. **Weak cryptography (PRNG)** - Prioritize production code over test/load files:
   - `adaptive_learning.py`
   - `agent_adaptation.py`
   - `swarm_intelligence.py`
   - `ddos_protection.py`
   - Frontend components

### LOW-PRIORITY (Document and monitor)
6. **HTTP usage** - Evaluate if HTTPS migration is feasible for all endpoints

---

## Verification Commands

Review each file at the specified line numbers and verify:
1. For Dockerfiles: Check ARG usage and add USER instruction
2. For Regex: Test inputs against malicious patterns
3. For PRNG: Replace with `secrets` module (Python) or `crypto` module (TypeScript)
4. For HTTP: Ensure TLS configuration exists for production

---

*Report generated by worker-2 for team "codebase-audit"*
