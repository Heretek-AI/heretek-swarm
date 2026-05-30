# Phase 1.2 — Quality & Security Baseline Report
**Date:** 2026-05-30  
**Project:** Heretek-AI/heretek-swarm  
**Status:** PARTIAL — Several tools unavailable

---

## Executive Summary

| Scan | Tool | Status | Issues Found |
|------|------|--------|-------------|
| SAST (Code) | Snyk Code | ✅ Complete | **121 issues** |
| SCA (Dependencies) | Snyk SCA | ✅ Complete | **111 issues** |
| Container Scan | Snyk Container | ❌ Disabled | — |
| IaC Scan | Snyk IaC | ❌ Disabled | — |
| Dependency Vulns | GitHub Advanced Security | ❌ Disabled | — |
| Secret Scanning | GitHub Advanced Security | ❌ Disabled | — |
| Security Audit | Rigour | ❌ Disabled | — |
| SonarQube Quality Gate | SonarQube MCP | ❌ Disabled | — |

**Total: 232 issues found** (121 code + 111 dependencies)

---

## 1. SAST Findings — Snyk Code (121 issues)

### Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| Medium | 2 | Code Injection (CWE-94) |
| Low | 119 | Path Traversal (CWE-23) |

### Critical Findings

#### 🔴 Code Injection (Medium — 2 issues)

**File: `swarm-dashboard/src/components/Home/HomePage.tsx` (Line 227)**
- **CWE-94**: Unsanitized input from remote resource flows into `setInterval`
- **Data flow**: Remote data → `setInterval` call with dynamic code execution
- **Fix**: Never pass dynamic content to `setInterval`/`setTimeout` string form; use function references only

**File: `swarm-dashboard/src/hooks/useWebSocket.ts` (Line 80)**
- **CWE-94**: Unsanitized input from browser storage flows into `setTimeout`
- **Data flow**: `localStorage`/`sessionStorage` → `setTimeout` string execution
- **Fix**: Parse stored data as JSON and pass to function reference, never as string code

#### 🟡 Path Traversal (Low — 119 issues)

All 119 path traversal issues are in **agent skill scripts** (`.agents/skills/`), NOT in core application code:

| File | Count |
|------|-------|
| `.agents/skills/pptx/scripts/add_slide.py` | 5 |
| `.agents/skills/pptx/scripts/clean.py` | 1 |
| `.agents/skills/pptx/scripts/office/unpack.py` | 2 |
| `.agents/skills/docx/scripts/accept_changes.py` | 1 |
| `.agents/skills/docx/scripts/comment.py` | 2 |
| `.agents/skills/docx/scripts/office/unpack.py` | 2 |
| `.agents/skills/skill-creator/scripts/quick_validate.py` | 1 |
| `.agents/skills/xlsx/scripts/office/unpack.py` | (remaining) |

**Root Cause**: These scripts accept file paths from CLI arguments and pass them to `shutil.copy2()` or `path concatenation` without sanitization. An attacker could use `../` sequences to escape the intended directory.

**Fix**: Use `os.path.realpath()` + `os.path.commonpath()` validation, or `pathlib.Path.resolve()` with whitelist checking.

---

## 2. SCA Findings — Snyk SCA (111 issues)

### HIGH Severity (7 distinct CVEs)

| CVE | Package | Current | Fixed | Impact |
|-----|---------|---------|-------|--------|
| CVE-2026-32597 | pyjwt | 2.10.1 | 2.12.0 | Improper Cryptographic Signature Verification |
| CVE-2026-34070 | langchain-core | 1.2.18 | 1.2.22 | Directory Traversal |
| CVE-2026-27794 | langgraph-checkpoint | 3.0.1 | 4.0.0 | Deserialization of Untrusted Data |
| CVE-2026-7246 | click | 8.3.1 | 8.3.3 | Command Injection |
| CVE-2026-44432 | urllib3 | 2.6.3 | 2.7.0 | Decompression Bomb |
| CVE-2026-28277 | langgraph | 1.0.5 | 1.0.10rc1 | Deserialization of Untrusted Data |
| CVE-2026-45134 | langsmith | 0.6.8 | 0.8.0 | Deserialization of Untrusted Data |

### MEDIUM Severity (4 distinct CVEs)

| CVE | Package | Current | Fixed |
|-----|---------|---------|-------|
| CVE-2026-41182 | langsmith | 0.6.8 | 0.7.31 |
| CVE-2026-26013 | langchain-openai | 1.1.7 | 1.1.9 |
| CVE-2025-67221 | orjson | 3.11.5 | 3.11.6 |
| CVE-2026-3219 | pip | 26.0.1 | 26.1 |

### LOW Severity (2 distinct CVEs)

| CVE | Package | Current | Fixed |
|-----|---------|---------|-------|
| CVE-2026-41488 | langchain-openai | 1.1.7 | 1.1.14 |
| CVE-2026-48522 | pyjwt | 2.10.1 | 2.13.0 |

### Source File

All SCA findings originate from: `heretek-swarm/apps/agent/pyproject.toml`

---

## 3. Gap Analysis

### Tools That Were Unavailable

The following scans could not be completed due to MCP tool restrictions:

1. **SonarQube** — Quality gate status, code smells, bugs, duplications, coverage
2. **GitHub Advanced Security** — Dependency vulnerabilities, secret scanning
3. **Rigour** — Security audit on project dependencies
4. **Snyk Container** — Docker image vulnerability scanning
5. **Snyk IaC** — docker-compose.yml infrastructure scanning

### Recommended Actions

1. Enable the disabled MCP tools in VS Code settings and re-run
2. Run `pip install --upgrade` for all HIGH severity packages
3. Fix the 2 Code Injection issues in TypeScript frontend code
4. Apply path sanitization to agent skill scripts (119 Low issues)

---

## 4. Prioritized Remediation Queue

### Immediate (Phase 2.1)
1. Upgrade pyjwt to ≥2.12.0 (CVE-2026-32597)
2. Upgrade langgraph to ≥1.0.10rc1 (CVE-2026-28277)
3. Upgrade langgraph-checkpoint to ≥4.0.0 (CVE-2026-27794)
4. Upgrade langsmith to ≥0.8.0 (CVE-2026-45134)
5. Upgrade langchain-core to ≥1.2.22 (CVE-2026-34070)
6. Upgrade click to ≥8.3.3 (CVE-2026-7246)
7. Upgrade urllib3 to ≥2.7.0 (CVE-2026-44432)
8. Fix Code Injection in HomePage.tsx and useWebSocket.ts

### Short-term (Phase 2.2)
9. Upgrade langchain-openai to ≥1.1.14
10. Upgrade orjson to ≥3.11.6
11. Upgrade pip to ≥26.1
12. Apply path traversal fixes to agent skill scripts

### Deferred
13. Re-run disabled scans when tools become available
14. Container and IaC scanning
