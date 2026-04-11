# Consolidated Audit Report — Heretek Swarm

**Date:** 2026-04-11
**Sources:** 5 audit reports (lint, dead code, documentation, functionality, simplification)
**Codebase:** 122,849 lines across ~175 source files, 2,499 tests

---

## Executive Summary

The codebase is functional but carries significant structural debt. Five audit tracks identified overlapping issues that converge on three themes:

1. **A single syntax bug blocks all API functionality** — `websockets.py` has duplicate keyword arguments at 6 locations
2. **~6,000 lint issues are auto-fixable in seconds** — 53% are trailing whitespace alone
3. **~15,000-20,000 lines of code are pure duplication or dead weight** — actor boilerplate, duplicate config services, orphaned modules

Addressing P0 items (estimated 2-3 hours total) would: unblock 18 API files, fix 2 broken imports, delete 6 dead files, and standardize documentation. No behavioral changes.

---

## Cross-Cutting Issues

These issues appear in 3+ audit reports and represent the highest leverage fixes:

### CC-1: `websockets.py` Syntax Errors (6 locations)

| Report | Severity | Detail |
|--------|----------|--------|
| Dead Code | P0 Immediate | 6 duplicate `exc_info=True` kwargs cause SyntaxError |
| Functionality | CRITICAL | Blocks entire `api` package (18 endpoint files) from loading |
| Lint | G201 (140 total) | Pattern of `logger.error(..., exc_info=True)` instead of `logger.exception()` |

**Lines:** 389, 512, 605, 683, 783, 879 in `src/heretek_swarm/api/websockets.py`

**Fix:** Remove duplicate `exc_info` from each call. Consider replacing all `logger.error(..., exc_info=True)` with `logger.exception()` project-wide (140 occurrences).

### CC-2: Broken Import Paths

| Report | File | Issue |
|--------|------|-------|
| Functionality | `tools/__init__.py` | Imports from `tools.` instead of `heretek_swarm.tools.` |
| Functionality | `state/__init__.py` | Adds parent `src/` to `sys.path`, uses legacy paths |
| Dead Code | `actors/prism.py:29` | F811: `AgentActor` redefined from line 22 |

**Fix:** Correct import paths, remove `sys.path` manipulation, deduplicate prism.py import.

### CC-3: Documentation Inconsistency

| Report | Finding |
|--------|---------|
| Documentation | 6 different version numbers across key docs |
| Documentation | 4 different health scores (85, 95, 98, 100) |
| Documentation | NATS listed as "Operational" in ARCHITECTURE.md but "NOT DEPLOYED" in README |
| Documentation | DEVELOPMENT_PLAN.md claims "All Phases Complete" — false per REMEDIATION_BACKLOG.md |
| Documentation | CLAUDE.md says `npm test` / `npm run lint` — neither script exists in package.json |

**Canonical values:** Version from `pyproject.toml`, health score 85/100 per REMEDIATION_BACKLOG.md.

### CC-4: Duplicate Config Services

| Report | Finding |
|--------|---------|
| Simplification | `service.py` (1,588 lines) + `service_manager.py` (1,292 lines) = 2,880 lines |
| Functionality | Combined ~103KB with 11 overlapping functions, zero test coverage |
| Functionality | Both handle caching, encryption, provider key retrieval |

**Fix:** Merge into single `config/service.py`, extract caching to `config/cache.py` (~100 lines). Estimated recovery: ~1,280 lines.

### CC-5: Actor Method Duplication

| Report | Finding |
|--------|---------|
| Simplification | 12 methods copy-pasted across 15-21 actor classes |
| Simplification | ~4,995 lines of pure boilerplate duplication |
| Simplification | 27 of 39 oversized files are actors |

**Fix:** Extract `DeliberationMixin`, `PatternMixin`, `MemoryMixin`, `LearningMixin` into `actors/mixins/`. Estimated recovery: ~5,000 lines.

---

## Prioritized Action Plan

### P0 — Immediate (blocks other work, ~2-3 hours)

| # | Action | Source | Effort | Impact |
|---|--------|--------|--------|--------|
| 1 | Fix 6 syntax errors in `websockets.py` | CC-1 | 15 min | Unblocks 18 API files |
| 2 | Fix `tools/__init__.py` import path | CC-2 | 5 min | Unblocks tools module |
| 3 | Fix `prism.py` F811 duplicate import | CC-2 | 2 min | Clean import |
| 4 | Delete 6 root-level temp files | Dead Code | 5 min | Removes 641+ lines |
| 5 | Standardize version/health in all docs | CC-3 | 1 hour | Eliminates 7 inaccuracies |
| 6 | Fix CLAUDE.md test/lint commands | CC-3 | 5 min | Fixes broken instructions |

### P1 — This Sprint (~2-3 days)

| # | Action | Source | Effort | Impact |
|---|--------|--------|--------|--------|
| 7 | Run `ruff check --fix --select W293,I001,F401` | Lint | 30 sec | Fixes ~5,758 issues (59%) |
| 8 | Replace `logger.error(..., exc_info=True)` with `logger.exception()` | Lint | 30 min | Fixes 140 G201 issues |
| 9 | Fix B008 FastAPI `Depends()` in defaults (127 locations) | Lint | 2 hours | Removes bug risk |
| 10 | Merge config services into single file | CC-4 | 4-6 hours | Recovers ~1,280 lines |
| 11 | Delete 17 stale root-level markdown files | Docs | 30 min | Removes duplication |
| 12 | Fix NATS status in ARCHITECTURE.md | CC-3 | 5 min | Corrects false claim |
| 13 | Fix DEVELOPMENT_PLAN.md "All Phases Complete" | CC-3 | 5 min | Corrects false claim |
| 14 | Fix `state/__init__.py` legacy imports | CC-2 | 30 min | Removes sys.path hack |
| 15 | Move `.benchmarks/` out of package | Simplification | 15 min | Package hygiene |

### P2 — Next Sprint (~1 week)

| # | Action | Source | Effort | Impact |
|---|--------|--------|--------|--------|
| 16 | Extract actor boilerplate into mixins | CC-5 | 2-3 days | Recovers ~5,000 lines |
| 17 | Archive `agent_workspace/` and `embeddings/` | Dead Code | 30 min | Removes empty/incomplete modules |
| 18 | Add tests for `config/` (140KB, zero coverage) | Functionality | 2-3 days | Critical security-sensitive code |
| 19 | Add tests for `orchestration/` (50KB, zero coverage) | Functionality | 1-2 days | Core logic |
| 20 | Add tests for `llm/` (32KB, zero coverage) | Functionality | 1-2 days | Core integration |
| 21 | Verify and prune unused dependencies | Simplification | 2-3 hours | Dependency hygiene |
| 22 | Split EXPANSION_ROADMAP.md (352KB) into active + archive | Docs | 2 hours | Usability |
| 23 | Add ESLint for JS/TS code | Lint | 1 hour | Frontend quality |

### P3 — Backlog

| # | Action | Source | Effort |
|---|--------|--------|--------|
| 24 | Add method docstrings (top 3 files: 160 missing) | Docs | 4-6 hours |
| 25 | Split oversized API/consensus/collective files | Simplification | 2-3 days |
| 26 | Prune `.outdated_docs/` | Docs | 15 min |
| 27 | Remove or populate `docs/integrations/` | Docs | 5 min |
| 28 | Full ruff G004 pass (709 f-string logging) | Lint | 2-3 hours |
| 29 | Investigate SLF001 private member access (705) | Lint | Case-by-case |
| 30 | Create `docs/STATUS.md` as canonical source | Docs | 1 hour |
| 31 | Add "Last Verified" timestamps to docs | Docs | 1 hour |
| 32 | Audit plugins/ dead symbols (12+) | Dead Code | 2 hours |
| 33 | Verify memory/ dead symbols against `.dead_code/memory/` | Dead Code | 1 hour |

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total lint issues | 9,802 across 243 files |
| Auto-fixable lint issues | ~5,758 (59%) |
| Files exceeding 500-line guideline | 39 |
| Dead/temp files at root | 6 (641+ lines) |
| Duplicate actor method lines | ~4,995 |
| Duplicate config service lines | ~1,280 (recoverable) |
| Modules with zero test coverage | 10 (~222KB untested) |
| Broken module imports | 2 (blocking) |
| Syntax errors blocking functionality | 6 (single file) |
| Stale/duplicate root markdown files | 17 |
| Docstring coverage | 92.2% |
| Critical doc inaccuracies | 7 |
| Estimated P0+P1 line recovery | ~6,920 lines |
| Estimated full refactor line recovery | ~15,000-20,000 lines |

---

## Source Reports

| Report | File | Size |
|--------|------|------|
| Lint & Type Check | `docs/audit-lint.md` | 4.4KB |
| Dead Code | `docs/audit-deadcode.md` | 8.9KB |
| Documentation | `docs/audit-documentation.md` | 16.6KB |
| Functionality | `docs/audit-functionality.md` | 8.9KB |
| Simplification | `docs/audit-simplification.md` | 12.1KB |

---

*Consolidated by team-lead agent. Next action: Begin P0 remediation.*
