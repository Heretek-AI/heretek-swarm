# M007: Execute repository restructure

**Gathered:** 2026-05-10
**Status:** Ready for planning

## Project Description

Rename the `heretek-swarm/` project subdirectory to `backend/` via `git mv`, update all tooling paths, consolidate scattered test files and duplicate workspace directories, and clean up tracked garbage — producing a clean `backend/` + `swarm-dashboard/` repository structure with zero Python code changes.

The current `heretek-swarm/heretek_swarm/` nesting (dash-vs-underscore) reads as a typo. The target `backend/heretek_swarm/` makes the role explicit: this is the Python backend living alongside `swarm-dashboard/` (frontend), `docs/`, `migrations/`, and root-level infrastructure.

## Why This Milestone

The nested dash-vs-underscore naming is semantically confusing and causes cognitive overhead for every new contributor. Additionally, artifacts are duplicated across root and inner levels: `tests/` (root 46 files, inner 16), `agent_workspace/` (root 9 agents, inner 6 + src/ copy), and `docs/` (root ~20 files, inner only `actors/README.md`). The root `src/` directory contains an older partial copy of the CLI entry point. M006 produced a complete migration plan (FILE_INVENTORY.md, IMPORT_MAP.md, CI_IMPACT.md, M006-PLAN.md) — this milestone executes it with expanded cleanup scope.

## Why Now

M005 completed architectural documentation and compressed the actor API surface. M006 audited every file and produced a line-level migration plan. The repository is stable with 370 passing tests and a clean CI pipeline. This is the right time — before building further features on top of a confusing directory structure.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `pip install -e .` from repo root and import `heretek_swarm` — all imports resolve from the new `backend/heretek_swarm/` location
- Run `pytest tests/ -v` and have all 62 test files (46 original + 16 consolidated from inner) pass
- Run `docker compose build` successfully with paths pointing to `backend/Dockerfile`
- Run `ruff check backend/ tests/` with no path errors
- Clone the repo fresh and have everything work at the new paths

### Entry point / environment

- Entry point: `heretek-swarm` CLI (via `pyproject.toml` console_scripts → `heretek_swarm.cli:cli`)
- Environment: Local dev
- Live dependencies involved: Docker (build verification), GitHub Actions CI (path updates)

## Completion Class

- Contract complete means: `backend/heretek_swarm/` is the only Python source directory; root `tests/` contains all 62 test files; `docker compose config` parses; no `heretek-swarm/` filesystem path references remain in tracked files
- Integration complete means: `pip install -e .` works, full test suite passes, `ruff check` passes, `docker compose build` succeeds
- Operational complete means: CI pipelines on push/PR pass with updated paths; fresh clone of the repo works

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `pytest tests/ -v --cov=backend --cov-report=xml` passes with all 62 test files and non-zero coverage
- `docker compose build` succeeds from repo root (proves Dockerfile COPY paths are correct)
- `git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/'` returns only URL/historical references (no filesystem paths)

## Architectural Decisions

### Rename heretek-swarm/ → backend/ via git mv

**Decision:** Rename the project subdirectory using `git mv` to preserve git history. Zero Python import changes — Python resolves modules by package name (`heretek_swarm`), not filesystem directory name.

**Rationale:** The name `backend/` makes the directory's role explicit. `heretek-swarm` (dash) looks like a typo for `heretek_swarm` (underscore). Target `backend/heretek_swarm/` is clear: backend project containing the `heretek_swarm` package, paired with `swarm-dashboard/` (frontend).

**Alternatives Considered:**
- Keep `heretek-swarm/` — rejected because the dash-vs-underscore confusion is real and causes cognitive overhead
- Rename to `python/` or `server/` — rejected; `backend/` is the conventional pairing with frontend

### Consolidate all tests into root tests/

**Decision:** Move the 16 inner test files (`heretek-swarm/tests/`) into root `tests/` before the directory rename. After consolidation, root `tests/` contains all 62 test files.

**Rationale:** Having two test directories at different levels creates confusion about where tests belong. All tests import from `heretek_swarm.*` (package path, unchanged by filesystem rename), so no test code changes are needed. CI already references root `tests/` only.

**Alternatives Considered:**
- Keep split across root and backend/tests/ — rejected; two test locations with no separation rationale
- Consolidate into backend/tests/ — rejected; tests at repo root is more conventional and CI already expects them there

### Delete src/ directory entirely

**Decision:** Remove the root `src/` directory containing `cli.py` (partial/older copy of `heretek_swarm/cli.py`), `__init__.py`, and `agent_workspace/`.

**Rationale:** `src/cli.py` is a partial copy sharing many identical `_check_*` helper functions with the canonical `heretek_swarm/cli.py`. The canonical CLI uses proper versioning (`__version__` vs hardcoded `"0.1.0"`) and a richer command set with `GroupedGroup`. The `pyproject.toml` console_scripts entry points to `heretek_swarm.cli:cli` — deleting `src/` has zero impact on CLI functionality.

**Alternatives Considered:**
- Keep src/ at root — rejected; fragments the Python surface across two directory levels
- Merge src/cli.py into heretek_swarm/ — rejected; src/cli.py is older/partial, not additive

### Delete inner docs/ and agent_workspace/ copies

**Decision:** Remove inner `heretek-swarm/docs/` (only `actors/README.md`) and inner `heretek-swarm/agent_workspace/` (partial, 6 agents). Root copies are the canonical, complete locations.

**Rationale:** Root `docs/` (~20 files) is the canonical documentation location — standard convention for discoverability. Root `agent_workspace/` (9 agents) is shared with `swarm-dashboard/` and is the complete copy. No Python code references the inner `agent_workspace/` path — agents use it only at runtime. No CI references the inner `docs/`.

**Alternatives Considered:**
- Keep both copies — rejected; adds confusion about which is canonical
- Move everything into backend/ — rejected; docs/ at repo root is standard, and agent_workspace/ is shared infrastructure

### Execution order: pre-mv consolidation

**Decision:** Consolidate tests and delete inner copies BEFORE the `git mv`. This ensures `backend/` only contains `heretek_swarm/`, `Dockerfile`, and `LICENSE` after the rename — no stale subdirectories.

**Rationale:** Doing cleanup before the rename means we're not cleaning up paths under `backend/` after the fact. The `git mv` moves a clean directory tree. Config edits (Phase 3) must happen before the rename so pip install resolves correctly during verification.

**Alternatives Considered:**
- Rename first, cleanup after — rejected; leaves a messy intermediate state and requires cleanup under the new path
- Two-commit approach — rejected; a single well-sequenced branch is simpler to review and roll back

## Error Handling Strategy

- All steps are reversible via `git checkout` at any phase boundary
- Pre-flight: create `backup-before-m007` branch before any changes
- `git mv` preserves full history — `git log --follow backend/heretek_swarm/__init__.py` shows pre-rename history
- If pyproject.toml edits break `pip install -e .`, revert that commit and fix — this is the highest-risk step
- If docker build fails, check COPY paths in Dockerfile — the most likely failure point
- CI path changes can be verified with `act` or manual command simulation before pushing
- Garbage file deletion is the lowest-risk step — `git rm` is trivially reversible

## Risks and Unknowns

- **pyproject.toml path mismatch** — If `where = ["backend"]` doesn't find `heretek_swarm/` inside `backend/`, pip install fails. Mitigation: verify immediately after edit with `pip install -e . && python -c "import heretek_swarm"`
- **CI workflow path stragglers** — M006 cataloged 22 path-change sites, but ci-cd.yml and load-test.yml weren't freshly verified. Mitigation: `git grep "heretek-swarm/" .github/` after all edits
- **Docker build cache invalidation** — First build after rename is a full rebuild. Acceptable — this is a build-time cost, not a correctness risk
- **Inner test file conflicts** — If inner tests have name collisions with root tests (both directories have unique test files per M006 audit — no collisions expected)
- **src/ has runtime consumers** — If any script or workflow references `src/cli.py` directly (not via console_scripts), it will break. Mitigation: `git grep "src/" -- ':!.gsd/'` before deletion

## Existing Codebase / Prior Art

- `heretek-swarm/heretek_swarm/` — canonical Python package (~40 subpackages, 430+ .py files), moves to `backend/heretek_swarm/` with zero import changes
- `heretek-swarm/tests/` — 16 consensus/goal/workflow test files, consolidated into root `tests/` before rename
- `heretek-swarm/docs/` — inner `actors/README.md` only, deleted (root `docs/` is canonical)
- `heretek-swarm/agent_workspace/` — partial copy (6 agents), deleted (root `agent_workspace/` is canonical with 9 agents)
- `heretek-swarm/Dockerfile` — backend container, moves with rename; 3 COPY lines updated post-mv
- `heretek-swarm/LICENSE` — moves with rename, no edits needed
- `src/cli.py` — older partial CLI copy (19KB), deleted
- `src/__init__.py` — package marker, deleted with src/
- `src/agent_workspace/` — third workspace copy, deleted with src/
- `swarm-dashboard/` — frontend, fully decoupled, zero changes
- `.github/workflows/ci.yml` — 2 path references updated
- `.github/workflows/ci-cd.yml` — 5+ path references updated
- `.github/workflows/load-test.yml` — audited and updated if needed
- `.github/workflows/publish-python.yml` — no changes (builds from pyproject.toml)
- `.github/workflows/publish-npm.yml` — no changes (frontend-only)
- `docker-compose.yml` — 1 Dockerfile path reference updated
- `pyproject.toml` — `where`, `source`, `src` directives updated; package `name` stays `heretek-swarm`
- `migrations/` — stays at root, no changes
- `audit/` — stays at root, no changes
- `agent_workspace/` (root) — canonical, stays at root
- `docs/` (root) — canonical, stays at root

## Relevant Requirements

- This milestone is pure infrastructure — it does not directly advance any functional requirements
- It is a prerequisite for any future milestone that adds new packages or restructures Python module layout
- It completes the work scoped and planned in M006

## Scope

### In Scope

- Consolidate inner `heretek-swarm/tests/` (16 files) into root `tests/`
- Delete inner `heretek-swarm/docs/` (actors/README.md only)
- Delete inner `heretek-swarm/agent_workspace/` (partial copy)
- Delete zero-byte `.db` files from `heretek-swarm/`
- Edit `pyproject.toml`: `where`, `source`, `src` directives (4 lines)
- `git mv heretek-swarm backend` (preserves history)
- Edit `backend/Dockerfile`: COPY paths (3 lines)
- Edit `docker-compose.yml`: Dockerfile path (1 line)
- Edit `.github/workflows/ci.yml`: ruff + pytest + bandit + mypy paths
- Edit `.github/workflows/ci-cd.yml`: ruff + mypy + bandit + pytest paths
- Audit and update `.github/workflows/load-test.yml`
- Delete `src/` directory entirely (`cli.py`, `__init__.py`, `agent_workspace/`)
- `git rm` 12 tracked garbage `=X.Y.Z` files
- Full verification: pip install, import check, ruff, pytest, docker compose build, git grep

### Out of Scope / Non-Goals

- Changing Python package internals — only directory structure and tooling paths
- Modifying `swarm-dashboard/` code — fully decoupled, no changes needed
- Changing `pyproject.toml` `name` field — stays `heretek-swarm` (PyPI package name)
- Moving `migrations/`, `audit/`, or root `docs/` — they stay at repo root
- Adding or modifying tests
- Deploying or publishing — M007 is local-only verification

## Technical Constraints

- All directory moves use `git mv` to preserve git history
- Python imports remain `from heretek_swarm.*` throughout — package name does not change
- `pyproject.toml` stays at repo root for `pip install -e .`
- GitHub Actions workflows stay under `.github/` at repo root
- Dockerfile and docker-compose.yml paths reference from repo root, not from inside the package
- Console scripts entry point (`heretek-swarm` CLI) resolves via `heretek_swarm.cli:cli` — unchanged

## Integration Points

- `.github/workflows/ci.yml` — path references updated for ruff check, bandit, mypy, pytest --cov
- `.github/workflows/ci-cd.yml` — path references updated for ruff, mypy, bandit, pytest coverage
- `.github/workflows/load-test.yml` — audited for path references
- `docker-compose.yml` — `dockerfile:` path updated from `heretek-swarm/Dockerfile` to `backend/Dockerfile`
- `backend/Dockerfile` — COPY paths updated from `heretek-swarm` to `backend`
- `pyproject.toml` — `where`, `source`, `src` directives updated; package name unchanged

## Testing Requirements

- All 62 test files (46 root + 16 consolidated) must pass: `pytest tests/ -v --timeout=120`
- Coverage reports must resolve source: `pytest tests/ --cov=backend --cov-report=xml` returns non-zero coverage
- Unit test marker isolation must work: `pytest -m "not integration" -x -q`
- Ruff check must pass on new paths: `ruff check backend/ tests/`
- Docker compose config must parse: `docker compose config`
- Docker build must succeed: `docker compose build`
- No stale filesystem path references: `git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/'` returns empty

## Acceptance Criteria

- `backend/heretek_swarm/` exists and is the only Python source directory
- `pip install -e .` succeeds from repo root
- `python -c "import heretek_swarm; print(heretek_swarm.__file__)"` prints path containing `backend/heretek_swarm/`
- `heretek-swarm --help` succeeds (CLI wired correctly)
- `pytest tests/ -v` passes all 62 test files
- `ruff check backend/ tests/` passes
- `docker compose build` succeeds
- `git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/'` returns only URL references (GitHub URLs in pyproject.toml)
- `src/` directory no longer exists
- No garbage `=X.Y.Z` files at repo root
- No inner `docs/` or `agent_workspace/` under `backend/`

## Open Questions

- **ci-cd.yml and load-test.yml exact path references** — M006 cataloged them but they weren't freshly read in this session. Must audit during execution before edits. Current assumption: they match the patterns documented in M006-PLAN.md §4 (Phase E).
- **Docker build time** — First build after rename invalidates all cached layers. Expected ~5-10 minutes for full rebuild. Acceptable — one-time cost.
