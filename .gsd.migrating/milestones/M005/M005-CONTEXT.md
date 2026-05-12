# M005: Document architecture and compress flat actor API surface

**Gathered:** 2026-05-10
**Status:** Ready for planning

## Project Description

The Heretek Swarm has undergone significant structural refactors across M001–M004: the dual `actors/` directories were collapsed, the ActorMessage Pydantic models were unified into `schemas/actors.py`, stub injection was made first-class, validation was consolidated into ValidationMixin, and a 658-test CI scaffold was established. The documentation and file layout have not kept pace.

This milestone brings the documentation up to date and finishes the mechanical compression of flat actor files into the subpackage convention that M001 started.

## Why This Milestone

The existing `docs/ARCHITECTURE.md` (671 lines) is stale — it references `src/heretek_swarm/` paths that don't exist, points to `triad.py` instead of `actors/triad/agent.py`, predates the 10-mixin extraction, and has 34 broken `src/`-prefixed links. Meanwhile, 12 flat actor files (`alpha.py`, `beta.py`, `charlie.py`, `steward.py`, `historian.py`, `metis.py`, `empath.py`, `perceiver.py`, `echo.py`, `coder.py`, `explorer.py`, `catalyst.py`) still carry real implementation code despite already-existing subpackage directories for triad, explorer, and perceiver_plus. And `base/core.py` has an inline `structlog.configure()` call that duplicates the logging infrastructure in `logging/config.py`.

Without this milestone, new contributors face broken docs, an inconsistent flat-vs-subpackage convention, and two places where structlog is configured.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Read a single `docs/ARCHITECTURE.md` that accurately reflects the current codebase structure with correct file paths
- Follow a practical guide at `docs/actors/README.md` to create a custom agent in under 30 minutes
- Import `from heretek_swarm.logging.config import configure_logging` as the single entry point for structlog config
- Find every flat actor file containing only a thin re-export (no implementation) — any agent's core logic lives in its subpackage directory

### Entry point / environment

- Entry point: `docs/ARCHITECTURE.md`, `docs/actors/README.md`
- Environment: local dev (docs are read as markdown)
- Live dependencies involved: none (documentation + refactoring slices; tests validate correctness)

## Completion Class

- **Contract complete** means: ARCHITECTURE.md has 10+ sections reflecting current codebase; actors/README.md has 6+ sections with a working code example and agent reference table; `configure_logging()` is the single entry point used by `core.py`; all flat actor files with an existing or created subpackage are thin re-exports
- **Integration complete** means: all 658 existing tests still pass after structlog extraction (import order still works) and after flat actor compression (imports still resolve)
- **Operational complete** means: the `heretek-swarm run` CLI still works from end to end after structlog reconfiguration; all 23 agents still import from `heretek_swarm.actors` without circular imports

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `pytest -m "not integration"` passes with 0 failures (same 658-test baseline)
- `from heretek_swarm.logging.config import configure_logging` works and `core.py` calls it instead of inline `structlog.configure()`
- `from heretek_swarm.actors import <every agent class>` works without ImportError for all 23 agents after flat→subpackage migration
- No `src/`-prefixed paths remain in `docs/ARCHITECTURE.md`
- No `TBD` or `TODO` markers remain in either document

## Architectural Decisions

### S03 subpackage mapping for flat actor compression

**Decision:** Extract all flat actor files that carry implementation into matching subpackages. The mapping is:

| Flat file | Lines | Target subpackage | Status |
|-----------|-------|-------------------|--------|
| alpha.py | 282 | actors/triad/agent.py | Already exists |
| beta.py | 299 | actors/triad/agent.py | Already exists |
| charlie.py | 393 | actors/triad/agent.py | Already exists |
| steward.py | 840 | actors/triad/agent.py | Already exists |
| historian.py | 1353 | actors/historian/ (new) | New subpackage |
| metis.py | 1110 | actors/metis/ (new) | New subpackage |
| empath.py | 1085 | actors/empath/ (new) | New subpackage |
| echo.py | 749 | actors/echo/ (new) | New subpackage |
| coder.py | 979 | actors/coder/ (new) | New subpackage |
| perceiver.py | 911 | actors/perceiver_plus/ (already exists) | Re-export |
| explorer.py | 1317 | actors/explorer/ (already exists) | Re-export |
| catalyst.py | 1135 | actors/catalyst/ (new) | New subpackage |
| handoff.py | 599 | actors/handoff/ (new) | New subpackage |
| handoff_handlers.py | 243 | actors/handoff/ (new) | New subpackage |

Existing subpackages (triad, chronos, coordinator, dreamer, examiner, explorer, habit_forge, nexus, perceiver_plus, prism, sentinel, sentinel_prime) already have their `__init__.py` exposing the agent class. The new subpackages each need: `__init__.py` re-export, the implementation file(s), and the flat file replaced with a thin re-import.

**Rationale:** Completes the M001 refactor direction. After S03, every agent imports from a subpackage directory matching its name, making the file tree navigable by agent name. The `actors/__init__.py` re-export surface already points to the right module; only the target module path moves.

**Alternatives Considered:**
- Leave flat files as-is — defeats the navigation benefit of the subpackage convention
- Move everything into the base module — would create a 15,000-line file

### S02 structlog configuration extraction

**Decision:** The inline `structlog.configure(...)` with 8 processors in `base/core.py` is replaced by a single import and call:

```python
from heretek_swarm.logging.config import configure_logging
configure_logging()
logger = structlog.get_logger("AgentActor")
```

The `logging/config.py` `setup_logging()` function already has a similar processor set (uses `CallsiteParameterAdder`, `ContextAdder`, etc.). S02 reconciles the two and ensures the first call to `configure_logging()` globally configures structlog exactly once.

**Rationale:** Eliminates duplicate structlog configuration. The `logging/config.py` already provides `setup_logging()` with all needed processors (TimeStamper, JSONRenderer, context vars, caller info). The inline copy in `core.py` was a leftover from before `logging/config.py` existed.

**Alternatives Considered:**
- Keep inline config and delete `logging/config.py` — losing structured logging infrastructure
- Documentation-only — doesn't reduce the duplication

### ARCHITECTURE.md rewrite: comprehensive system reference

**Decision:** Full rewrite rather than path fixup. The new document covers:

1. System Overview (updated)
2. Package Structure (NEW — annotated directory tree)
3. Actor Architecture (updated paths, subpackage convention, tier table)
4. Actor Base Class & Mixins (NEW — AgentActor lifecycle + 10-mixin reference)
5. ActorFactory & ActorSupervisor (NEW)
6. Memory System (updated paths)
7. Event Mesh (updated paths)
8. Configuration System (updated paths)
9. Security (updated paths)
10. Observability (updated paths)
11. References (updated)

Zero `src/`-prefixed paths. All paths use the `heretek-swarm/heretek_swarm/` prefix.

**Rationale:** The old doc has 34 stale paths, references dead file locations, and predates the mixin architecture. A fresh write is less error-prone than fixing 34 scattered references in a 671-line document.

## Error Handling Strategy

Documentation writes are verified by grep-based checks (no stale paths, no TBD/TODO markers). Structlog extraction is verified by running the full test suite — `setup_logging()` is idempotent (has `_configured` flag internally) so double-calls are safe. Flat actor compression is the riskiest: if any import path is wrong, the test suite catches it immediately. Each subpackage gets a `__init__.py` that mirrors the flat file's public API, and the flat file becomes a `from X import Y` re-export.

## Risks and Unknowns

- **Circular imports after S03:** The flat files currently import from `heretek_swarm.actors.base`, `heretek_swarm.actors.validation`, etc. After extraction, the subpackage `__init__.py` must not import from the flat re-export stub (which would create a cycle). The pattern is: subpackage internal code imports directly; the flat stub imports from the subpackage. Verified by test suite.
- **Structlog import order:** If `logging/config.py` imports something that itself triggers `structlog.get_logger()` before `configure_logging()` is called, the default (console) processors will be applied. Guard: `setup_logging()` has an internal `_configured` flag.
- **docs/actors/ directory:** The `docs/actors/` directory does NOT currently exist at the docs level (only `heretek_swarm/actors/docs/` exists). Must create `docs/actors/README.md` as a new file.

## Existing Codebase / Prior Art

- `docs/ARCHITECTURE.md` (671L) — the document to rewrite; 34 stale `src/` paths
- `actors/base/core.py` (557L) — contains inline `structlog.configure()` with 8 processors; this is extracted in S02
- `logging/config.py` — already has `setup_logging()` with near-identical processor list; target for `configure_logging()`
- `actors/__init__.py` (81L) — canonical re-export surface listing all 23 agents
- `actors/triad/agent.py` — the only subpackage that already holds 4 agents (Steward, Alpha, Beta, Charlie)
- `actors/explorer/` — existing subpackage that explorer.py should re-export from
- `actors/perceiver_plus/` — existing subpackage that perceiver.py should re-export from
- `heretek_swarm/actors/docs/EXTRACTION_PATTERN.md` — existing doc in actors/docs/

## Scope

### In Scope

- **S01:** Rewrite `docs/ARCHITECTURE.md` (full rewrite, comprehensive system reference, 10+ sections); create `docs/actors/README.md` (practical creation guide with code example, agent reference table, local execution guide)
- **S02:** Extract inline `structlog.configure()` from `base/core.py` into `logging/config.py` as `configure_logging()`; verify all tests pass
- **S03:** Extract all 12-14 flat actor files into matching subpackages (new subpackages for historian, metis, empath, echo, coder, catalyst, handoff + re-export from existing subpackages triad, explorer, perceiver_plus); each flat file becomes a thin re-export; verify all imports resolve and tests pass

### Out of Scope / Non-Goals

- Writing new code beyond re-exports and structlog extraction
- Adding new actor types or modifying agent behavior
- Renaming agent classes or changing the public API
- Writing integration or E2E tests for the agents
- Modifying any `__init__.py` re-export surface in `actors/__init__.py` (the imports stay the same; only the target module path changes)

## Technical Constraints

- All 658 existing tests must pass after S02 and S03 changes
- No circular imports may be introduced — subpackage `__init__.py` files must import module-internally, not via the flat re-export stub
- `configure_logging()` must be idempotent (safe to call multiple times)
- The `actors/__init__.py` public API surface must not change — all 23 agent classes must be importable from `heretek_swarm.actors`

## Integration Points

- `heretek_swarm.actors.__init__` — the re-export surface; must not change, only the target paths behind it change
- `heretek_swarm.actors.base.core` — structlog import is extracted, logger still obtained the same way
- `pytest` — the full test suite is the integration validation for S02 and S03

## Testing Requirements

- S01: grep-based verification (no stale paths, ≥6 sections, no TBD/TODO markers)
- S02: full pytest suite passes; manually verify `logging/config.py` is the single structlog entry point
- S03: full pytest suite passes; verify each flat file is a thin re-export (grep for `from` / `import` pattern, no `class` definition)

## Acceptance Criteria

### S01
- `docs/ARCHITECTURE.md` exists with ≥10 sections, all paths using `heretek-swarm/heretek_swarm/` prefix
- `docs/actors/README.md` exists with ≥6 sections including a code example and agent reference table
- No `src/heretek_swarm/` paths, no `TBD`/`TODO` markers in either document
- Documented Actor Base Class & Mixins section lists all 10 mixins

### S02
- `from heretek_swarm.logging.config import configure_logging` is importable
- `base/core.py` calls `configure_logging()` instead of inline `structlog.configure()`
- Old inline `structlog.configure()` with 8 processors is removed from `core.py`
- All 658 tests pass

### S03
- Every flat actor file with a subpackage target contains only re-export stubs (no `class` definition, no implementation beyond the `from ... import` line)
- All 23 agents still importable from `heretek_swarm.actors`
- 12+ flat files are compressed; new subpackages (historian, metis, empath, echo, coder, catalyst, handoff) have proper `__init__.py`
- All 658 tests pass

## Open Questions

- None — all architectural decisions resolved during discussion. M005 context is complete.
