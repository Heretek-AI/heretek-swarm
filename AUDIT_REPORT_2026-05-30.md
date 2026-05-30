# Heretek Swarm — Comprehensive Security & Quality Audit
**Date:** 2026-05-30  
**Sources:** SonarCloud, GitHub Code Scanning (CodeQL), GitHub Dependabot  
**Project:** `Heretek-AI/heretek-swarm`

---

## Executive Summary

| Source | Open | Closed/Fixed | Critical/Blocker |
|--------|------|-------------|-------------------|
| **SonarCloud** | ~85+ | ~15+ | 20+ CRITICAL, 2 BLOCKER |
| **CodeQL (Code Scanning)** | 12 | 0 | 0 (all error/warning) |
| **Dependabot** | 10 | 20+ | 0 (all pypdf DoS) |

**Top Risks:**
1. **Stack trace exposure** — 10+ CodeQL alerts leaking exception details to external users (CWE-209/CWE-497)
2. **Cognitive complexity** — 15+ functions exceeding the 15-point threshold (hardest: 28 in `external_validator.py`)
3. **ReDoS vulnerabilities** — 3 polynomial regex patterns on user-controlled data (CWE-1333)
4. **Insecure temp directories** — 13 instances of `tempfile.mkdtemp` without safe usage checks in tests
5. **Dependency: pypdf** — 10 open DoS advisories (RAM exhaustion via manipulated PDFs)

---

## 1. GitHub Code Scanning (CodeQL) — 12 Open Alerts

### 1.1 Stack Trace Exposure (`py/stack-trace-exposure`) — 10 alerts
**Severity:** Error | **CWE:** CWE-209, CWE-497 | **Security Level:** Medium

Exception details (stack traces, error messages) are being returned to external users, exposing internal implementation details useful for crafting targeted attacks.

| # | File | Line(s) |
|---|------|---------|
| 126 | `backend/heretek_swarm/api/agents/instances.py` | 269-276 |
| 125 | `backend/heretek_swarm/api/observability/stream.py` | 156 |
| 121 | `backend/heretek_swarm/api/wizard.py` | 710-714 |
| 118 | `backend/heretek_swarm/api/rag.py` | 171-176 |
| 117 | `backend/heretek_swarm/api/providers_config.py` | 539 |
| 116 | `backend/heretek_swarm/api/providers_config.py` | 354 |
| 114 | `backend/heretek_swarm/api/metrics.py` | 224 |
| 110 | `backend/heretek_swarm/api/main.py` | 981-984 |
| 109 | `backend/heretek_swarm/api/main.py` | 933-939 |
| 107 | `backend/heretek_swarm/api/main.py` | 772-783 (6 instances) |
| 106 | `backend/heretek_swarm/api/configuration.py` | 712-716 |
| 105 | `backend/heretek_swarm/api/configuration.py` | 606 |

**Remediation:** Replace `traceback.format_exc()` / raw exception returns with generic error messages. Log the full traceback server-side only. Use a consistent error response wrapper across all API endpoints.

### 1.2 Polynomial ReDoS (`py/polynomial-redos`) — 3 alerts
**Severity:** Warning | **CWE:** CWE-1333, CWE-400, CWE-730 | **Security Level:** High

| # | File | Line |
|---|------|------|
| 124 | `backend/heretek_swarm/rag/knowledge_graph.py` | 97 |
| 101 | `backend/heretek_swarm/rag/knowledge_graph.py` | 122 |
| 100 | `backend/heretek_swarm/rag/knowledge_graph.py` | 108 |

**Remediation:** The regex patterns in `knowledge_graph.py` use ambiguous repetitions on user-provided data. Replace with atomic groups, possessive quantifiers, or use the `re` module with timeout wrappers. Consider using `re2` or pre-validating input length.

---

## 2. GitHub Dependabot — 10 Open Alerts

All 10 open alerts are for **pypdf** (in `uv.lock`). All are Denial-of-Service via manipulated PDF inputs:

| # | Advisory |
|---|----------|
| 36 | Manipulated FlateDecode image dimensions can exhaust RAM |
| 35 | Possible long runtimes for wrong size values in incremental mode |
| 34 | Manipulated FlateDecode predictor parameters can exhaust RAM |
| 33 | Long runtimes for wrong size values in cross-reference and object streams |
| 32 | Manipulated XMP metadata entity declarations can exhaust RAM |
| 28 | Possible infinite loop during recovery attempts in DictionaryObject |
| 27 | Inefficient decoding of array-based streams |
| 26 | Manipulated stream length values can exhaust RAM |
| 25 | Inefficient decoding of ASCIIHexDecode streams |
| 24 | Manipulated RunLengthDecode streams can exhaust RAM |

**Remediation:** Upgrade `pypdf` to the latest version. All these are resource-exhaustion DoS vectors. If pypdf processes user-uploaded PDFs, this is a real risk.

**Previously fixed (20+):** aiohttp (9), litellm (4), urllib3 (2), python-dotenv, idna, mem0ai, python-multipart — all addressed.

---

## 3. SonarCloud — Open Issues by Severity & Category

### 3.1 BLOCKER (2 open)

| Key | Rule | File | Message |
|-----|------|------|---------|
| `AZ52QrPkxhoxqMM91xlf` | `python:S930` | `backend/heretek_swarm/config/crud.py:1029` | Unexpected named argument `include_disabled` |
| `AZ52QrolxhoxqMM91xlu` | `python:S3827` | `backend/heretek_swarm/infrastructure/nats/client.py:241` | `os` used before defined |

### 3.2 CRITICAL — Cognitive Complexity (`python:S3776`) — 15+ open

Functions exceeding the 15-point cognitive complexity threshold:

| File | Line | Score |
|------|------|-------|
| `security/zero_trust/external_validator.py` | 79 | **28** |
| `scripts/check-bandit-severity.py` | 84 | **26** |
| `api/workflows.py` | 456 | **23** |
| `state/models.py` | 802 | **21** |
| `infrastructure/nats/client.py` | 95 | **21** |
| `collective/pattern_library.py` | 433 | **20** |
| `gateway/content_router.py` | 520 | **20** |
| `evaluation/evaluator.py` | 287 | **19** |
| `runtime/steward_pulse.py` | 339 | **19** |
| `config/secrets_loader.py` | 111 | **18** |
| `security/zero_trust/output_validator.py` | 53 | **18** |
| `collective/swarm_intelligence.py` | 660 | **17** |
| `workflow/strategies.py` | 136 | **17** |
| `memory/persistent.py` | 212 | **17** |
| `runtime/deliberation_orchestrator.py` | 117 | **16** |
| `runtime/deliberation_orchestrator.py` | 180 | **27** |
| `memory/persistent.py` | 467 | **16** |

### 3.3 CRITICAL — Other

| Key | Rule | File | Message |
|-----|------|------|---------|
| `AZ53KACOGzJsVDTR-k6J` | `python:S8512` | `actors/perceiver/agent.py:340` | Dead assignment; `_TEXT_FORMATS` reassigned on line 1029 |
| `AZ53KACOGzJsVDTR-k6I` | `python:S1192` | `actors/perceiver/agent.py:391` | Duplicate literal `"data:"` 6× |
| `AZ5293BKoRufhO6yYtYx` | `python:S1192` | `_check_issues.py:9` | Duplicate literal `'heretek-swarm/'` 7× |
| `AZ5z8t4HtNR1yXmd3Opb` | `python:S5727` | `tests/test_secrets.py:318` | Identity check always True |
| `AZ5z8t8WtNR1yXmd3Opc` through `AZ5z8t8WtNR1yXmd3Opo` | `python:S5443` | `tests/test_certificate_generation.py` (13 instances) | Unsafe use of publicly writable directories |

### 3.4 MAJOR — Key Patterns

**Unused parameters (`python:S1172`):**
- `api/agents/chat.py:61` — `deliberation_id`
- `api/agents/chat.py:87` — `queue`
- `infrastructure/a2a/protocol.py:387` — `agent_id`
- `tools/mcp_tools.py:360` — `key`

**Missing HTTPException docs (`python:S8415`):**
- `api/observability/external_calls.py:321` — 500 not documented
- `api/evaluation.py:33` — 503 not documented
- `api/evaluation.py:112` — 404 not documented
- `api/main.py:1140` — 503 not documented

**Deprecated `timeout` parameter (`python:S7483`):**
- `runtime/deliberation_orchestrator.py:90,138,204`
- `cli/status.py:243`
- `workflow/strategies.py:290,310`

**`Annotated` type hints needed (`python:S8410`):**
- `api/evaluation.py:106,131`
- `api/observability/alerts.py:27`
- `api/observability/external_calls.py:49`
- `api/workflows.py:510,546,547`

**Fake `async` functions (`python:S7503`):**
- `runtime/main_loop.py:240,262,279,323,340,361`
- `coordination/sync.py:188`
- `security/zero_trust/orchestrator.py:51,99,127`
- `memory/persistent.py:585`

**GitHub Actions (`githubactions:S8264`):**
- `.github/workflows/load-test.yml:14,15,16` — Move `read` permissions to job level
- `.github/workflows/publish-python.yml:8` — Move `read` permission to job level

**Unpinned Docker image (`githubactions:S6596`):**
- `.github/workflows/semgrep.yml:23` — Use specific version tag

**Shell scripting (`shelldre:S7688`):**
- `backend/entrypoint.sh:12` — Use `[[` instead of `[`
- `scripts/verify-sops-encryption.sh` — 14 instances of `[` instead of `[[`

### 3.5 MINOR — Notable

- `python:S1481` — Unused local variables in `api/configuration.py:299`, `api/agents/chat.py:67`, `security/zero_trust/orchestrator.py:143`, `tests/test_s07_phase_c.py:315,361`
- `python:S1656` — Useless self-assignment in `runtime/autonomous_runtime_config.py:13`
- `python:S3358` — Nested conditional expression in `cli/status.py:330`
- `python:S3457` — f-string with no replacement fields in `runtime/steward_pulse.py:468`
- `python:S7504` — Unnecessary `list()` call in `api/workflows.py:480`
- `docker:S7031` — Merge consecutive RUN instructions in `backend/Dockerfile:60`
- `python:S108` — Empty except block in `actors/base/message_handling.py:1085`

---

## 4. Prioritized Remediation Plan

### 🔴 Immediate (Security)
1. **Fix all 10 stack trace exposures** — Replace `traceback.format_exc()` with generic error responses; log details server-side
2. **Fix 3 ReDoS vulnerabilities** in `knowledge_graph.py` — Use atomic regex or input length limits
3. **Upgrade pypdf** — 10 open DoS advisories
4. **Fix `os` used before definition** in `infrastructure/nats/client.py:241` (BLOCKER)
5. **Fix unexpected argument `include_disabled`** in `config/crud.py:1029` (BLOCKER)

### 🟠 High (Code Quality)
6. **Refactor `external_validator.py:79`** — Cognitive complexity 28 (nearly 2× threshold)
7. **Refactor `deliberation_orchestrator.py:180`** — Cognitive complexity 27
8. **Refactor `check-bandit-severity.py:84`** — Cognitive complexity 26
9. **Fix 13 unsafe `tempfile.mkdtemp` uses** in `test_certificate_generation.py`
10. **Move GitHub Actions permissions** to job level in `load-test.yml` and `publish-python.yml`

### 🟡 Medium (Maintainability)
11. **Replace deprecated `timeout` parameter** with context managers (5 instances)
12. **Add `Annotated` type hints** for FastAPI DI (6 instances)
13. **Fix fake `async` functions** — either add `await` or remove `async` (10 instances)
14. **Document HTTPException responses** in FastAPI endpoints (4 instances)
15. **Pin Semgrep Docker image** to specific version

### 🟢 Low (Cleanup)
16. **Remove unused parameters** (4 instances)
17. **Extract duplicated string literals** into constants
18. **Fix shell scripts** — use `[[` instead of `[`
19. **Merge Dockerfile RUN** instructions
20. **Remove unused local variables**

---

## 5. Quality Gate Status

The SonarCloud Quality Gate status should be checked directly at:
https://sonarcloud.io/dashboard?id=Heretek-AI_heretek-swarm

Based on the volume of CRITICAL cognitive complexity issues and BLOCKER-level bugs, the Quality Gate is likely **failing** on:
- Reliability Rating (BLOCKER bugs)
- Maintainability Rating (15+ CRITICAL complexity issues)

---

*Report generated by automated audit across SonarCloud MCP, GitHub Code Scanning API, and GitHub Dependabot API.*
