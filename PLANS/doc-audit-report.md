# Documentation Audit Report

**Audit Date:** 2026-04-13
**Auditor:** Documentation Audit Agent
**Files Reviewed:** README.md, PRIME_DIRECTIVE.md, API_REFERENCE.md, API_ENDPOINTS.md, INDEX.md, ARCHITECTURE.md, and architecture/ directory

---

## Executive Summary

The documentation has several outdated references, broken internal links, and version inconsistencies that should be corrected. Most critical issues are in API endpoint documentation and architecture cross-links.

---

## 1. Version Inconsistencies (HIGH PRIORITY)

### Issue 1.1: Conflicting Version Numbers

| Document | Claims Version |
|----------|---------------|
| README.md | 2.2.0 |
| src/heretek_swarm/__init__.py | **0.1.0** (actual) |
| docs/INDEX.md | 1.36.0 |
| docs/ARCHITECTURE.md | 2.1.0 |
| Multiple docs (API_ENDPOINTS.md, MEMORY_SYSTEM.md, etc.) | 2.0.0 |

**Impact:** Users cannot determine actual project version. CI/CD and release processes may use incorrect versions.

**Recommendation:** Standardize on a single source of truth for version. Consider:
- Using `src/heretek_swarm/__init__.py __version__` as authoritative
- Or adding a `VERSION` file at project root
- Update all documentation to match

---

## 2. API Endpoint Discrepancies (HIGH PRIORITY)

### Issue 2.1: Missing Routers in API_ENDPOINTS.md

The actual `main.py` registers these routers NOT documented in API_ENDPOINTS.md:

| Router | Prefix | File |
|--------|--------|------|
| autonomous | `/autonomous` | autonomous.py |
| wizard | `/api/wizard` | wizard.py |
| metrics | `/metrics` | metrics.py |
| collective_evolution | `/api/collective` | collective_evolution.py |
| alerts | `/api/alerts` | alerts.py |
| mcp | `/api/mcp` | mcp.py |

**Recommendation:** Add documentation for these 6 missing routers to API_ENDPOINTS.md

### Issue 2.2: Observability Prefix Mismatch

| Document | Prefix |
|----------|--------|
| API_ENDPOINTS.md | `/api/observability` |
| **Actual code** (observability.py:39) | `/api/v1/observability` |

**Recommendation:** Update API_ENDPOINTS.md to reflect `/api/v1/observability`

### Issue 2.3: Missing `/api/agents/status` Endpoint

API_REFERENCE.md line 67 references `GET /api/agents/status` but this endpoint does not exist in the codebase.

**Actual endpoints found:**
- `GET /api/agents` (line 406)
- `GET /api/agents/{agent_id}` (line 431)
- `GET /api/agents/{agent_id}/metrics` (line 463)
- `POST /api/agents/{agent_id}/terminate` (line 491)

**Recommendation:** Remove reference to `/api/agents/status` or clarify if this was renamed.

---

## 3. Broken Internal Links (MEDIUM PRIORITY)

### Issue 3.1: Architecture Cross-Reference Links

The following links in `docs/architecture/*.md` point to non-existent files:

| Broken Link | Should Be |
|-------------|-----------|
| `./orchestration.md` | `./orchestration-system.md` |
| `./memory.md` | `./memory-system.md` |
| `./state.md` | `./state-management.md` |
| `./consensus.md` | `./consensus-mechanism.md` |

**Files containing broken links:**
- `architecture/actors-system.md` (lines 376-379)
- `architecture/consensus-mechanism.md` (lines 573-575)
- `architecture/memory-system.md` (lines 689-690)
- `architecture/orchestration-system.md` (line 586)

**Recommendation:** Update all four files to use correct `.md` extensions.

---

## 4. Documentation Structure Issues (MEDIUM PRIORITY)

### Issue 4.1: AGENTS.md vs AGENT_REFERENCE.md

CONSCIOUSNESS_PLUGINS.md (line 1011) references `./AGENTS.md` which exists, but the main INDEX.md references `./AGENT_REFERENCE.md`. Both files appear to serve similar purposes.

**Recommendation:** Clarify which is authoritative or consolidate.

### Issue 4.2: API_REFERENCE.md Line Number References

API_ENDPOINTS.md references source code line numbers that are likely outdated:
- Line 28: References main.py
- Line 107: References main.py:327
- Line 744: References main.py:459
- Line 788: References main.py:670

**Recommendation:** Remove specific line number references as they become stale. Keep file references only.

---

## 5. Minor Issues (LOW PRIORITY)

### Issue 5.1: deploy.sh Script Validation

README.md claims `deploy.sh` checks prerequisites and creates `.env`, but if `.env` already exists, the script behavior may differ.

### Issue 5.2: INDEX.md Priority Table Outdated

INDEX.md (lines 100-110) shows P1/P2/P3 priorities with status indicators that may not reflect current implementation state.

**Recommendation:** Verify and update the priority table or remove if redundant with EXPANSION_ROADMAP.md.

---

## Summary of Required Corrections

| Priority | Issue | Files to Modify |
|----------|-------|----------------|
| HIGH | Version standardization | README.md, __init__.py, INDEX.md |
| HIGH | Missing API routers | API_ENDPOINTS.md |
| HIGH | Observability prefix | API_ENDPOINTS.md |
| MEDIUM | Broken architecture links | architecture/*.md (4 files) |
| MEDIUM | /api/agents/status reference | API_REFERENCE.md |
| LOW | Priority table stale | INDEX.md |

---

## Appendix: Verification Commands

```bash
# Check actual version in source
cat src/heretek_swarm/__init__.py | grep __version__

# List all registered API routers
grep "include_router" src/heretek_swarm/api/main.py

# Check observability prefix
grep "prefix=" src/heretek_swarm/api/observability.py

# Verify all architecture links
find docs/architecture -name "*.md" -exec grep -l "\.md)" {} \;
```
