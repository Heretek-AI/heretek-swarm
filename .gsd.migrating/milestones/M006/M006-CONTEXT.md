# M006: Audit and plan repository restructure

**Gathered:** 2026-05-10
**Status:** Ready for planning

## Project Description

Rename the confusing `heretek-swarm/` project subdirectory to `backend/`, consolidate scattered artifacts (tests, workspace, CLI entry points) that are duplicated across root and inner levels, and produce an actionable migration plan for M007 execution.

The current structure `heretek-swarm/heretek_swarm/` uses dash-vs-underscore naming that looks like a typo. The target `backend/heretek_swarm/` makes the role explicit: this is the Python backend, living alongside `swarm-dashboard/` (frontend), `docs/`, and root-level infrastructure.

## Why This Milestone

The nested `heretek-swarm/` directory is semantically confusing — it contains the Python package `heretek_swarm/` but the dash-vs-underscore naming reads as a mistake. Additionally, artifacts are duplicated across root and inner levels: `tests/` (root ~50 files, inner ~16), `agent_workspace/` (root 9 agents, inner 6 with missing agents), `docs/` (root ~20 files, inner only `actors/`), `.actor_states/`, and `.benchmarks/`. The root `src/` directory contains a separate `cli.py` entry point that may shadow or duplicate `heretek_swarm/cli.py`.

This milestone audits everything, produces a complete file manifest, import dependency map, CI impact analysis, and an actionable plan — but does NOT execute any moves. Execution is deferred to M007.

## Why Now

M005 completed architectural documentation and compressed the actor API surface. The repository is stable and well-understood. This is the right time to clean up the repo shape before building further features on top of a confusing directory structure.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Read a complete file inventory (FILE_INVENTORY.md) showing every file in the repo, its type, size, purpose, and current→target path
- Read an import dependency map (IMPORT_MAP.md) showing which packages depend on which, with all `from heretek_swarm.` imports cataloged
- Read a CI/workflow impact list (CI_IMPACT.md) showing every path reference in workflows, docker-compose, and build configs that will break
- Read the final migration plan (M006-PLAN.md) that M007 can execute directly — exact file moves, import rewrites, CI path updates, and ordering constraints

### Entry point / environment

- Entry point: Read-only audit — `docs/`, `.gsd/milestones/M006/` artifacts
- Environment: Local dev
- Live dependencies involved: none

## Completion Class

- Contract complete means: FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md, and M006-PLAN.md exist with complete, validated content
- Integration complete means: The plan is verified against the actual repo tree and all CI workflow files
- Operational complete means: M007 can decompose M006-PLAN.md directly into execution tasks without re-auditing

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- FILE_INVENTORY.md catalogs every source, config, doc, test, CI, and deployment file (excluding .git/, .gsd/, node_modules/, .venv/, __pycache__/)
- IMPORT_MAP.md shows all Python import dependencies between packages with special attention to `src/` → `heretek_swarm/` cross-references and `swarm-dashboard/` references to the Python package
- CI_IMPACT.md catalogs all 6 workflow files plus docker-compose.yml, Dockerfile, and pyproject.toml path references that would break under the target structure
- M006-PLAN.md is the single source of truth for M007 — every file move, import rewrite, and CI fix is specified with ordering constraints

## Architectural Decisions

### Target structure: `heretek-swarm/` → `backend/`

**Decision:** Rename the project subdirectory `heretek-swarm/` to `backend/` using `git mv` to preserve history.

**Rationale:** The name `backend/` makes the directory's role explicit. `heretek-swarm` (with dash) looks like a typo for `heretek_swarm` (with underscore). The target `backend/heretek_swarm/` is clear: backend Python project containing the `heretek_swarm` package.

**Alternatives Considered:**
- Keep `heretek-swarm/` — rejected because the dash-vs-underscore confusion is real and causes cognitive overhead
- Rename to `python/` or `server/` — rejected; `backend/` is the conventional pairing with `swarm-dashboard/` (frontend)

### Consolidate root `src/` into `backend/`

**Decision:** Move the root-level `src/` directory (containing `cli.py`, `__init__.py`) into `backend/` alongside `heretek_swarm/`, and consolidate the two CLI surfaces.

**Rationale:** Root `src/cli.py` (19KB) and `heretek_swarm/cli.py` (63KB) appear to be two entry points for the same system. Having a CLI package at root when the backend lives in a subdirectory fragments the codebase. After consolidation, `backend/` is the single home for all Python code.

**Alternatives Considered:**
- Delete `src/` entirely — rejected pending investigation of whether `src/` has unique entry points not in `heretek_swarm/cli.py`
- Leave `src/` at root — rejected; fragments the Python surface across two directory levels

### Consolidate all tests into `backend/tests/`

**Decision:** Move root `tests/` (~50 files) and inner `heretek-swarm/tests/` (~16 files) into a single `backend/tests/` directory.

**Rationale:** Having two test directories at different levels with no clear separation of concerns creates confusion about where tests belong. CI already references `heretek-swarm/` path prefixes.

**Alternatives Considered:**
- Keep separate — rejected; no clear separation rationale exists (both directories contain integration-style tests)
- Only keep inner tests — rejected; the root test suite is far larger and likely the canonical one

### Root `docs/` and `agent_workspace/` stay at root; inner copies deleted

**Decision:** Root-level `docs/` (~20 files) and `agent_workspace/` (9 agents) are the canonical locations. Delete the partial inner copies (`heretek-swarm/docs/` with only `actors/`, `heretek-swarm/agent_workspace/` with only 6 agents).

**Rationale:** The root copies are larger and more complete. `docs/` at repo root is conventional for discoverability. `agent_workspace/` at root is shared with `swarm-dashboard/`. The inner copies appear to be stale partial mirrors.

**Alternatives Considered:**
- Move everything into `backend/` — rejected; `docs/` at repo root is standard convention, and `agent_workspace/` is shared infrastructure
- Keep both with symlinks — rejected; adds complexity without benefit

## Error Handling Strategy

M006 is read-only audit work. No error handling is needed for the audit scripts themselves. If a file cannot be read (permissions, encoding), the inventory script should record it as `unreadable` rather than crashing. The produced plan (M006-PLAN.md) should include rollback instructions for M007 execution.

## Risks and Unknowns

- **Two CLI entry points** — `src/cli.py` and `heretek_swarm/cli.py` may have overlapping or divergent functionality. The audit must determine whether both are needed or one supersedes the other.
- **Import path breakage** — `from heretek_swarm.` imports inside `backend/` may work if PYTHONPATH is set correctly, but any absolute path references in scripts or CI will break.
- **`swarm-dashboard/` dependencies** — The frontend may import or shell out to the Python package. The audit must check for `subprocess`, `import`, or file-path references crossing the dashboard→backend boundary.
- **`.actor_states/` and `.benchmarks/` duplication** — Both exist at root and inner levels. It's unclear which is canonical. These are runtime state directories and may need to merge or one deleted.
- **Inner `pyproject.toml` and `Dockerfile`** — These define the backend package and build. They must move with the rename and have their internal paths updated.

## Existing Codebase / Prior Art

- `heretek-swarm/heretek_swarm/` — canonical Python package (~40 subpackages), moves to `backend/heretek_swarm/`
- `src/cli.py` — separate CLI entry point (19KB), moves into `backend/`
- `heretek-swarm/pyproject.toml` — backend package definition, moves with rename
- `heretek-swarm/Dockerfile` — backend container, moves with rename
- `swarm-dashboard/` — frontend, already correctly placed, stays at root
- `.github/workflows/` — 6 workflow files with `heretek-swarm/` path references
- `docker-compose.yml` — references `heretek-swarm/` paths
- `docs/` — canonical documentation at root
- `agent_workspace/` — canonical shared workspace at root (9 agents)

## Relevant Requirements

- This milestone is pure infrastructure — it does not directly advance any functional requirements
- It is a prerequisite for any future milestone that adds new packages or restructures Python module layout

## Scope

### In Scope

- Complete file inventory of the repository (excluding build artifacts and tool caches)
- Python import dependency graph across all packages
- CI, Docker, and build configuration path audit
- Actionable migration plan (M006-PLAN.md) for M007 execution
- Identifying the relationship between the two CLI entry points (`src/cli.py` vs `heretek_swarm/cli.py`)

### Out of Scope / Non-Goals

- Executing any file moves, renames, or import rewrites — deferred to M007
- Changing Python package internals — only directory structure and import paths
- Modifying `swarm-dashboard/` code — only auditing whether it references the backend
- Adding or modifying tests

## Technical Constraints

- All moves must use `git mv` to preserve git history
- Python imports inside `backend/` using `from heretek_swarm.` should continue to work if PYTHONPATH is set correctly
- CI workflows outside `backend/` must reference files with `backend/` prefix after the rename
- Docker compose and Dockerfile paths reference from repo root, not from inside the package

## Integration Points

- `.github/workflows/*.yml` — 6 workflow files with hardcoded `heretek-swarm/` paths that must be updated in M007
- `docker-compose.yml` — references `heretek-swarm/` build context
- `swarm-dashboard/` — may reference the Python package via import, subprocess, or file path
- `pyproject.toml` — package metadata and tool configs that may reference `heretek-swarm/` paths

## Testing Requirements

M006 produces documents, not code changes. Verification is:

- FILE_INVENTORY.md: counts match actual file tree; every line has type, size, path, purpose
- IMPORT_MAP.md: at least one entry for every `.py` file; cross-package dependencies are flagged
- CI_IMPACT.md: every workflow file is represented; every `heretek-swarm/` path reference is cataloged
- M006-PLAN.md: every file move, import rewrite, and CI fix is specified with ordering; `backend/` appears throughout

## Acceptance Criteria

- FILE_INVENTORY.md is complete and verifiable against `find` output
- IMPORT_MAP.md covers all Python files with import statements
- CI_IMPACT.md covers all 6 workflow files, docker-compose.yml, Dockerfile, pyproject.toml
- M006-PLAN.md is self-contained — a fresh agent can execute it without re-auditing
- The two CLI surfaces (`src/cli.py` vs `heretek_swarm/cli.py`) are analyzed and a consolidation decision is documented in the plan

## Open Questions

- **Are `src/cli.py` and `heretek_swarm/cli.py` redundant, or do they serve different entry points?** — The audit must diff their functionality and recommend consolidation or deduplication
- **Which `.actor_states/` and `.benchmarks/` directories are canonical?** — The inner copies may be legacy; the audit should check modification times and content
- **Does `swarm-dashboard/` import or shell out to the Python package?** — Must be checked before the rename, as path changes could break the frontend
- **Should root `migrations/` and `audit/` directories move into `backend/`?** — Pending investigation of their contents and purpose
