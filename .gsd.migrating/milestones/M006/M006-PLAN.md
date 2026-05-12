# M006-PLAN: Repository Restructure — Migration Plan

**Status:** Ready for execution (M007)
**Generated:** 2026-05-12
**Sources:** FILE_INVENTORY.md (856 files), IMPORT_MAP.md (429 .py files), CI_IMPACT.md (22 path-change sites)

---

## Executive Summary

This document specifies the exact file moves, import rewrites, and CI/configuration updates needed to restructure the repository from its current layout to a clean `backend/` + `frontend/` separation. The change is a **single directory rename** — `heretek-swarm/` → `backend/` — with coordinated path updates across tooling config files.

**Net impact:** One `git mv` of a directory + 22 line-level edits across 8 config files. Zero Python code changes.

---

## 1. Target Directory Structure

```
heretek-swarm/                        # Repository root
├── backend/                          # ← NEW: was heretek-swarm/
│   ├── heretek_swarm/                # Python package (name UNCHANGED)
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── actors/                   # 23 actor types + mixins
│   │   ├── agents/
│   │   ├── api/                      # FastAPI application surface
│   │   ├── channels/
│   │   ├── cli/                      # CLI package
│   │   ├── collective/
│   │   ├── config/
│   │   ├── consciousness/
│   │   ├── consensus/
│   │   ├── coordination/
│   │   ├── creativity/
│   │   ├── embeddings/
│   │   ├── evaluation/
│   │   ├── gateway/
│   │   ├── goals/
│   │   ├── governance/
│   │   ├── infrastructure/
│   │   ├── integrations/
│   │   ├── interfaces/
│   │   ├── knowledge/
│   │   ├── llm/
│   │   ├── logging/
│   │   ├── mcp/
│   │   ├── memory/
│   │   ├── models/
│   │   ├── observability/
│   │   ├── orchestration/
│   │   ├── plugins/
│   │   ├── rag/
│   │   ├── routing/
│   │   ├── runtime/
│   │   ├── schemas/
│   │   ├── security/
│   │   ├── slices/
│   │   ├── state/
│   │   ├── testing/
│   │   ├── tools/
│   │   ├── utils/
│   │   ├── validation/
│   │   └── workflow/
│   ├── docs/                         # Package-local docs (moves with dir)
│   ├── agent_workspace/              # Agent workspace (moves with dir)
│   ├── heretek_swarm.egg-info/       # Build artifact (gitignored)
│   ├── Dockerfile                    # ← MOVED from heretek-swarm/Dockerfile
│   └── LICENSE                       # ← stays (moves with dir)
├── migrations/                       # DB migrations (UNMOVED)
├── tests/                            # Test suite (UNMOVED)
├── src/                              # External CLI launcher (UNMOVED)
├── swarm-dashboard/                  # Frontend (UNMOVED)
├── docs/                             # Repo-level docs (UNMOVED)
├── audit/                            # Audit tools (UNMOVED)
├── agent_workspace/                  # Root agent workspace (UNMOVED)
├── pyproject.toml                    # Build config (UNMOVED, paths updated)
├── docker-compose.yml                # Compose config (UNMOVED, paths updated)
├── uv.lock                           # Lockfile (UNMOVED, regenerated)
├── .github/                          # CI workflows (UNMOVED, paths updated)
│   └── workflows/
│       ├── ci.yml                    # Paths updated
│       ├── ci-cd.yml                 # Paths updated
│       ├── load-test.yml             # Paths updated
│       ├── publish-python.yml        # NO changes needed
│       ├── publish-npm.yml           # NO changes needed
│       └── codeboarding.yml          # NO changes needed
└── .pre-commit-config.yaml           # Paths updated
```

### What Changes vs What Doesn't

| Component | Change | Reason |
|-----------|--------|--------|
| `heretek-swarm/` dir | Renamed to `backend/` | Clean backend/frontend separation |
| `heretek_swarm/` package | **NO change** | Python import paths stay identical |
| `tests/` | **NO change** | Stays at repo root; imports unchanged |
| `src/cli.py` | **NO change** | Stays at repo root; imports unchanged |
| `swarm-dashboard/` | **NO change** | Fully decoupled from backend paths |
| `migrations/` | **NO change** | Stays at repo root |
| `docs/` (root) | **NO change** | Repo-level docs |
| `pyproject.toml` | 5 line edits | Tooling config paths |
| CI workflows | 16 line edits | Command paths |
| `docker-compose.yml` | 1 line edit | Dockerfile path |
| `Dockerfile` | Moves with dir + 3 line edits | COPY commands |

---

## 2. File Move Catalog

### 2.1 Bulk Move: `heretek-swarm/` → `backend/`

The entire directory tree is relocated via a single git operation:

```bash
git mv heretek-swarm backend
```

This moves approximately **460 files** in one atomic rename. Every file inside `heretek-swarm/` goes to the equivalent path under `backend/`:

| Current Path (current path before move) | Target Path | Action | Import Rewrite |
|---|---|---|---|
| `heretek-swarm/Dockerfile` | `backend/Dockerfile` | `move` | Internal COPY paths (see §4) |
| `heretek-swarm/LICENSE` | `backend/LICENSE` | `move` | None |
| `heretek-swarm/heretek_swarm/` | `backend/heretek_swarm/` | `move` | **None** — package name unchanged |
| `heretek-swarm/docs/` | `backend/docs/` | `move` | None |
| `heretek-swarm/agent_workspace/` | `backend/agent_workspace/` | `move` | None |
| `heretek-swarm/heretek_swarm.egg-info/` | `backend/heretek_swarm.egg-info/` | `move` | None (build artifact) |

### 2.2 Files Requiring Content Edits (Post-Move)

These files change internally because they reference their own location:

| File (at target) | What Changes | Details |
|---|---|---|
| `backend/Dockerfile` | 3 COPY lines | `heretek-swarm` → `backend` in paths |

### 2.3 Root-Level Files: No Moves

| File | Action | Reason |
|---|---|---|
| `pyproject.toml` | `keep` | Must stay at repo root for `pip install -e .` |
| `docker-compose.yml` | `keep` | Must stay at repo root |
| `.github/workflows/*.yml` | `keep` | GitHub requires `.github/` at repo root |
| `.pre-commit-config.yaml` | `keep` | Must stay at repo root |
| `uv.lock` | `keep` | Must stay at repo root |
| `tests/` | `keep` | All test imports use `heretek_swarm` (package), not `heretek-swarm` (directory) |
| `src/cli.py` | `keep` | Uses `import heretek_swarm` — package path, unchanged |
| `swarm-dashboard/` | `keep` | No backend path references |
| `migrations/` | `keep` | Alembic config references remain valid |
| `agent_workspace/` | `keep` | Not path-dependent |
| `docs/` | `keep` | Repo-level docs |
| `audit/` | `keep` | Not path-dependent |

### 2.4 Items to Delete

| Path | Reason |
|---|---|
| `src/` (empty or redundant) | If `src/cli.py` is the only content, evaluate deletion in M007; current `src/` directory contains stale `bandit -r src/` references in CI |
| `=` (garbage files matching `=X.Y.Z` pattern) | Root directory contains ~12 zero-byte garbage files like `=0.2.0`, `=8.0.0` — delete during migration cleanup |

---

## 3. Import Rewrite Catalog

### 3.1 Zero Python Import Changes

**The Python package name `heretek_swarm` does not change.** All imports remain identical:

```python
# These ALL stay exactly as-is:
from heretek_swarm.actors.base import BaseAgent
from heretek_swarm.consensus.maker import ConsensusMaker
import heretek_swarm.cli
from heretek_swarm.api.main import app
```

This is the critical insight that makes this migration safe: **Python resolves modules by package name, not by filesystem directory name.** As long as the `pyproject.toml` `where` directive points to the correct source tree (`backend/`), all `import heretek_swarm.*` statements resolve correctly.

### 3.2 Files That Reference Directory (Not Package) Paths

Only 8 files have hardcoded filesystem paths that need updating:

| File | Current Reference | New Reference |
|---|---|---|
| `pyproject.toml:82` | `where = ["heretek-swarm"]` | `where = ["backend"]` |
| `pyproject.toml:131` | `source = ["heretek-swarm"]` | `source = ["backend"]` |
| `pyproject.toml:142` | `source = ["heretek-swarm/"]` | `source = ["backend/"]` |
| `pyproject.toml:158` | `src = ["heretek-swarm", "tests"]` | `src = ["backend", "tests"]` |
| `docker-compose.yml:81` | `dockerfile: heretek-swarm/Dockerfile` | `dockerfile: backend/Dockerfile` |
| `Dockerfile:23` | `COPY heretek-swarm ./heretek-swarm` | `COPY backend ./backend` |
| `Dockerfile:29` | `/app/heretek-swarm` (×2 occurrences) | `/app/backend` |
| `.github/workflows/ci.yml:35` | `ruff check heretek-swarm/ tests/` | `ruff check backend/ tests/` |

### 3.3 Test File Import Survey

All 16 test files import from `heretek_swarm.*` (the package), not `heretek-swarm/` (the directory):

```yaml
tests/test_auto_routing_integration.py:    from heretek_swarm.cli import ...
tests/test_complexity_heuristic.py:        from heretek_swarm.consensus.complexity import ...
tests/test_consciousness_api.py:           from heretek_swarm.api import ...
tests/test_consensus_audit_jsonl.py:       from heretek_swarm.consensus.audit_models import ...
tests/test_consensus_cli.py:               from heretek_swarm.cli import ...
tests/test_consensus_coordinator.py:       from heretek_swarm.consensus.consensus_coordinator import ...
tests/test_consensus_runtime.py:           from heretek_swarm.consensus.maker import ...
tests/test_consensus_websocket.py:         from heretek_swarm.api.consensus import ...
tests/test_domain_selector.py:             from heretek_swarm.consensus.domain_selector import ...
tests/test_goal_cli.py:                    from heretek_swarm.cli import ...
tests/test_goal_consensus.py:              from heretek_swarm.goals.consensus import ...
tests/test_goal_pipeline.py:               from heretek_swarm.goals.pipeline import ...
tests/test_goal_proposer.py:               from heretek_swarm.goals.models import ...
tests/test_goal_store.py:                  from heretek_swarm.goals.models import ...
tests/test_goal_translator.py:             from heretek_swarm.goals.models import ...
tests/test_workflow_persistence.py:        from heretek_swarm.workflow.store import ...
```

**Verdict:** Zero test import rewrites needed.

---

## 4. CI/Deployment Update Catalog

### 4.1 Execution Phases

Changes must be applied in this order to avoid leaving the repo in a broken state:

#### Phase A: `pyproject.toml` (CRITICAL — must be committed first)

All tooling (ruff, mypy, pytest, coverage, bandit, pip) reads from `pyproject.toml`. Update these before moving files:

```diff
# Line 82: Package discovery root
 [tool.setuptools.packages.find]
-where = ["heretek-swarm"]
+where = ["backend"]

# Line 131: Coverage run source
 [tool.coverage.run]
-source = ["heretek-swarm"]
+source = ["backend"]

# Line 142: Coverage path remapping
 [tool.coverage.paths]
 source = [
-    "heretek-swarm/",
+    "backend/",
 ]

# Line 158: Ruff source directories
 [tool.ruff]
-src = ["heretek-swarm", "tests"]
+src = ["backend", "tests"]
```

#### Phase B: Directory Move

```bash
git mv heretek-swarm backend
```

#### Phase C: Dockerfile Content (moved to `backend/Dockerfile`)

```diff
# Line 23: Source tree copy
-COPY heretek-swarm ./heretek-swarm
+COPY backend ./backend

# Line 29: Builder-to-runtime copy (TWO occurrences)
-COPY --from=builder --chown=appuser:appgroup /app/heretek-swarm /app/heretek-swarm
+COPY --from=builder --chown=appuser:appgroup /app/backend /app/backend
```

#### Phase D: `docker-compose.yml`

```diff
# Line 81: Dockerfile path
   build:
     context: .
-    dockerfile: heretek-swarm/Dockerfile
+    dockerfile: backend/Dockerfile
```

#### Phase E: GitHub Actions Workflows

**`.github/workflows/ci.yml`:**

```diff
# Line 18: bandit security scan
-        bandit -r src/
+        bandit -r backend/

# Line 31: ruff check (first occurrence — stale `src/`)
-        ruff check src/ tests/
+        ruff check backend/ tests/

# Line 35: ruff check (second occurrence — current `heretek-swarm/`)
-        ruff check heretek-swarm/ tests/
+        ruff check backend/ tests/

# Line 43: mypy type check
-        mypy src/
+        mypy backend/

# Line 87: pytest coverage source
-        pytest tests/ -v --cov=heretek-swarm --cov-report=xml --timeout=120
+        pytest tests/ -v --cov=backend --cov-report=xml --timeout=120
```

**`.github/workflows/ci-cd.yml`:**

```diff
# Line 35: ruff check
-        ruff check src/ tests/
+        ruff check backend/ tests/

# Line 38: ruff format
-        ruff format --check src/ tests/
+        ruff format --check backend/ tests/

# Line 41: mypy
-        mypy src/
+        mypy backend/

# Line 44: bandit
-        bandit -r src/
+        bandit -r backend/

# Line 106: pytest coverage
-        pytest tests/ -v --cov=src --cov-report=xml --timeout=120
+        pytest tests/ -v --cov=backend --cov-report=xml --timeout=120
```

**`.github/workflows/load-test.yml`:**

```diff
# Line 39: pip install (works if pyproject.toml is correct)
# No change needed — installs from root
```

#### Phase F: `.pre-commit-config.yaml` (if present with path references)

Verify and update any `heretek-swarm/` path references (typically `entry:` or `files:` regex patterns).

#### Files Requiring NO Changes

| File | Verdict |
|---|---|
| `.github/workflows/publish-python.yml` | Builds from `pyproject.toml` — auto-resolves |
| `.github/workflows/publish-npm.yml` | Frontend-only |
| `.github/workflows/codeboarding.yml` | Docs output path unchanged |
| `.env.example` | Environment variables, no filesystem paths |
| `.dockerignore` | Pattern-based, directory-agnostic |
| `.gitignore` | Pattern-based, directory-agnostic |

---

## 5. Execution Order

### 5.1 Pre-Flight Checklist (Before Any Changes)

- [ ] All local changes committed or stashed
- [ ] Clean working tree (`git status` shows nothing)
- [ ] Current CI passing on `main`
- [ ] Take a snapshot of current state: `git branch backup-before-m006 $(git rev-parse HEAD)`

### 5.2 Ordered Steps

```
Step 1: pyproject.toml edits (Phase A)
  ├─ Depends on: nothing
  ├─ Edits: 4 lines
  ├─ Verify: `pip install -e . && python -c "import heretek_swarm"`
  └─ Commit: "chore: update pyproject.toml paths for backend/ restructure"

Step 2: Directory rename (Phase B)
  ├─ Depends on: Step 1
  ├─ Command: `git mv heretek-swarm backend`
  ├─ Verify: `ls backend/heretek_swarm/__init__.py` exists
  └─ Commit: "refactor: rename heretek-swarm/ → backend/"

Step 3: Dockerfile content (Phase C)
  ├─ Depends on: Step 2 (needs file at new path)
  ├─ Edits: 3 lines in `backend/Dockerfile`
  ├─ Verify: `grep -c "heretek-swarm" backend/Dockerfile` returns 0
  └─ Commit: "fix: update Dockerfile paths for backend/ restructure"

Step 4: docker-compose.yml (Phase D)
  ├─ Depends on: Step 2
  ├─ Edits: 1 line
  ├─ Verify: `docker compose config` succeeds
  └─ Amend to Step 2 commit (or separate)

Step 5: CI workflows (Phase E)
  ├─ Depends on: Step 1 (needs pyproject.toml correct)
  ├─ Edits: 16 lines across 3 files
  ├─ Verify: `grep -r "heretek-swarm/" .github/` returns empty
  └─ Commit: "ci: update workflow paths for backend/ restructure"

Step 6: Optional cleanup
  ├─ Depends on: Steps 1-5
  ├─ Remove garbage `=X.Y.Z` files from root
  ├─ Remove stale `src/` directory (if empty/obsolete)
  └─ Commit: "chore: cleanup obsolete files after restructure"
```

### 5.3 Parallelism Opportunities

Steps 3, 4, and 5 can be done **in any order** after Step 2 completes. They touch different files with no mutual dependencies.

The commits can be squashed into a single commit or kept separate for auditability. Recommendation: **keep pyproject.toml edit as a separate first commit** for clean rollback capability.

---

## 6. Rollback Plan

### Fast Path: Single Commit Revert

If the entire migration was committed as a chain, revert the top N commits:

```bash
git revert --no-commit HEAD~N   # where N = number of migration commits
git commit -m "revert: undo repository restructure"
```

### Granular Rollback

| Failure At | Rollback Action |
|---|---|
| After Step 1 only | `git checkout -- pyproject.toml` |
| After Step 2 | `git checkout HEAD~1` (undoes rename + Step 1) |
| After Step 3 | `git checkout HEAD~1` then re-apply Steps 1-2 correctly |
| After Step 4-5 | Same as above — revert to pre-migration state |

### Critical Safety Net

The `backup-before-m006` branch created in pre-flight provides a hard reset target:

```bash
git reset --hard backup-before-m006   # Nuclear option
```

### What Does NOT Need Rollback

- Python code: never changed
- Test files: never changed
- Frontend: never changed
- Database: never affected (migrations/ stays at root)

---

## 7. Verification Checklist

### 7.1 Development Environment

```bash
# 1. Package installs from new location
pip install -e .
echo $?  # must be 0

# 2. Import resolution works
python -c "import heretek_swarm; print(heretek_swarm.__file__)"
# Must print path containing .../backend/heretek_swarm/__init__.py

# 3. CLI entry point works
heretek-swarm --help
echo $?  # must be 0
```

### 7.2 Lint & Type Checking

```bash
# 4. Ruff finds the right directory
ruff check backend/ tests/
echo $?  # 0 = clean, else list findings

# 5. Ruff format (dry-run)
ruff format --check backend/ tests/
echo $?  # 0 = correctly formatted

# 6. Mypy finds the right directory
mypy backend/ --ignore-missing-imports
echo $?  # may have warnings; confirm no increase from baseline

# 7. Bandit finds the right directory
bandit -r backend/
echo $?  # reports findings; no "file not found" errors
```

### 7.3 Tests & Coverage

```bash
# 8. Full test suite
pytest tests/ -v --timeout=120
echo $?  # must be 0

# 9. Coverage report confirms source resolution
pytest tests/ --cov=backend --cov-report=term --cov-report=html
echo $?  # must be 0; coverage > 0% (confirms source found)

# 10. Check coverage percentage vs baseline
# Compare htmlcov/index.html percentage to pre-migration value
```

### 7.4 Docker Build

```bash
# 11. Docker image builds
docker build -f backend/Dockerfile -t heretek-swarm-test .
echo $?  # must be 0

# 12. Compose validates
docker compose config
echo $?  # must be 0; no path errors

# 13. Quick smoke test (if containers available)
docker compose up -d postgres redis
docker compose run --rm api python -c "import heretek_swarm; print('OK')"
docker compose down
```

### 7.5 Git Sanity

```bash
# 14. No stale heretek-swarm/ references in tracked files
git grep "heretek-swarm/" -- ':!.gsd/' ':!.git/'
# Must return empty or only historical/non-path references

# 15. No leftover heretek-swarm/ directory
test -d heretek-swarm && echo "FAIL: directory still exists" || echo "PASS"
```

### 7.6 CI Simulation (Optional)

```bash
# 16. Run the same commands CI will run
act -j lint       # if using nektos/act for local CI simulation
# OR manually:
ruff check backend/ tests/ && ruff format --check backend/ tests/ && \
  mypy backend/ --ignore-missing-imports && \
  bandit -r backend/ && \
  pytest tests/ -v --cov=backend --cov-report=xml --timeout=120
```

---

## 8. Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|------|------------|--------|------------|
| R1 | `pip install -e .` breaks after rename | Low | High | Step 1 verification catches this immediately |
| R2 | Coverage drops to 0% (config mismatch) | Medium | Medium | Step 9-10 verification confirms coverage |
| R3 | Stale `src/` references linger in CI | Medium | Low | `git grep` after Phase E finds stragglers |
| R4 | Docker build cache invalidation | Certain | Low | Acceptable — first build after rename is full rebuild |
| R5 | `heretek-swarm/` references in .gsd/ plans | Medium | Low | `.gsd/` is gitignored; plans reference relative paths |
| R6 | Someone pushes to old structure during migration | Low | High | Do migration in single session; communicate to team |

---

## 9. Impact on M007 Task Decomposition

M007 will execute this plan as independent tasks:

| M007 Task | Scope | Depends On |
|-----------|-------|-----------|
| M007-T01 | Edit `pyproject.toml` (4 lines) | None |
| M007-T02 | `git mv heretek-swarm backend` | T01 |
| M007-T03 | Edit `backend/Dockerfile` (3 lines) | T02 |
| M007-T04 | Edit `docker-compose.yml` (1 line) | T02 |
| M007-T05 | Edit `.github/workflows/ci.yml` (5 lines) | T01 |
| M007-T06 | Edit `.github/workflows/ci-cd.yml` (5 lines) | T01 |
| M007-T07 | Audit `.github/workflows/load-test.yml` + `.pre-commit-config.yaml` | T02 |
| M007-T08 | Verify: install + import + lint + typecheck + test + docker build | T01-T07 |
| M007-T09 | Cleanup: remove root garbage files, audit stale directories | T08 |

**Total estimated work:** ~30 line edits across 8 files, 1 directory rename, verification suite.

---

## 10. Appendix: Key File Reference Index

| File | Current Path | Post-Migration Path |
|---|---|---|
| Package `__init__.py` | `heretek-swarm/heretek_swarm/__init__.py` | `backend/heretek_swarm/__init__.py` |
| CLI entry | `heretek-swarm/heretek_swarm/cli.py` | `backend/heretek_swarm/cli.py` |
| API surface | `heretek-swarm/heretek_swarm/api/main.py` | `backend/heretek_swarm/api/main.py` |
| Dockerfile | `heretek-swarm/Dockerfile` | `backend/Dockerfile` |
| Build config | `pyproject.toml` | `pyproject.toml` (unchanged) |
| Compose file | `docker-compose.yml` | `docker-compose.yml` (unchanged) |
| Test suite | `tests/` | `tests/` (unchanged) |
| External CLI | `src/cli.py` | `src/cli.py` (unchanged, if kept) |
| Migrations | `migrations/` | `migrations/` (unchanged) |

---

*End of M006-PLAN.md — ready for M007 execution*
