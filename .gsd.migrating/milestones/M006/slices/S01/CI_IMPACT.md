# CI IMPACT — Build, Deploy, and Config Path Dependency Audit

**Generated:** 2026-05-12  
**Purpose:** Catalog every path reference in CI workflows, Docker configs, and build tooling that must change for the `heretek-swarm/` → `backend/` restructure.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Files analyzed | 10 |
| Files requiring changes | 8 |
| Hard blockers | 22 |
| Cosmetic/optional | 3 |
| Unaffected files | 2 |

**High-confidence finding:** Most path references are concentrated in two patterns: (a) `src/` paths in lint/test CI commands that should already be `heretek-swarm/`, and (b) `heretek-swarm/` filesystem paths that need to become `backend/`. No changes are needed to import paths (Python module resolution is independent of filesystem layout when the package is installed).

---

## 1. Per-File Analysis

### 1.1 `.github/workflows/ci.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 1 | 18 | `bandit -r src/` | `bandit -r backend/` | ✅ HARD | `src/` is a stale/incorrect path; code lives in `heretek-swarm/heretek_swarm/` |
| 2 | 31 | `ruff check src/ tests/` | `ruff check backend/ tests/` | ✅ HARD | Same stale `src/` pattern |
| 3 | 35 | `ruff check heretek-swarm/ tests/` | `ruff check backend/ tests/` | ✅ HARD | Uses correct current path; needs updating to `backend/` |
| 4 | 43 | `mypy src/` | `mypy backend/` | ✅ HARD | Same stale `src/` pattern |
| 5 | 87 | `--cov=heretek-swarm` | `--cov=backend` | ✅ HARD | Coverage source path |

**Note:** Lines 1-4 reveal a latent inconsistency — the project uses `src/` in most commands but `heretek-swarm/` in the Ruff Warning Gate (line 35). Both must be fixed.

### 1.2 `.github/workflows/ci-cd.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 6 | 35 | `ruff check src/ tests/` | `ruff check backend/ tests/` | ✅ HARD | Stale `src/` |
| 7 | 38 | `ruff format --check src/ tests/` | `ruff format --check backend/ tests/` | ✅ HARD | Stale `src/` |
| 8 | 41 | `mypy src/` | `mypy backend/` | ✅ HARD | Stale `src/` |
| 9 | 44 | `bandit -r src/` | `bandit -r backend/` | ✅ HARD | Stale `src/` |
| 10 | 106 | `pytest tests/ -v --cov=src` | `pytest tests/ -v --cov=backend` | ✅ HARD | Coverage source; different convention from ci.yml |

### 1.3 `.github/workflows/publish-python.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 11 | 32 | `open('pyproject.toml', 'rb')` | unchanged | — | `pyproject.toml` stays at repo root |
| 12 | 54 | `heretek-swarm --help` | unchanged | — | CLI entry-point name unchanged |

**Verdict:** No changes needed. The package build chain (`python -m build`) reads from the installed source tree; as long as `pyproject.toml` paths point to the correct source directory, the build works.

### 1.4 `.github/workflows/publish-npm.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| — | all | `swarm-dashboard/` | unchanged | — | Frontend-only; no backend path dependencies |

**Verdict:** No changes needed. All paths reference `swarm-dashboard/` which is not affected by the backend restructure.

### 1.5 `.github/workflows/load-test.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 13 | 39 | `pip install -e .` | unchanged (works if pyproject.toml + source dir correct) | ✅ HARD | Editable install must resolve package from new location |
| 14 | 52 | `tests/load/` | unchanged | — | Tests stay at repo root |
| 15 | 103 | `tests/load/locustfile.py` | unchanged | — | Test file path unaffected |
| 16 | 118 | `tests/load/k6/load_test.js` | unchanged | — | Test file path unaffected |

### 1.6 `.github/workflows/codeboarding.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| — | 28 | `output_directory: 'docs'` | unchanged | — | Docs directory stays at repo root |

**Verdict:** No changes needed.

### 1.7 `docker-compose.yml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 17 | 80 | `context: .` | unchanged | — | Build context stays at repo root |
| 18 | 81 | `dockerfile: heretek-swarm/Dockerfile` | `dockerfile: backend/Dockerfile` | ✅ HARD | Dockerfile moves with the restructure |
| 19 | 112 | `context: ./swarm-dashboard` | unchanged | — | Dashboard context unaffected |

### 1.8 `heretek-swarm/Dockerfile`

This file itself moves from `heretek-swarm/Dockerfile` → `backend/Dockerfile`.

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 20 | 22 | `COPY pyproject.toml uv.lock ./` | unchanged | — | Root-level files; paths resolve from build context |
| 21 | 23 | `COPY heretek-swarm ./heretek-swarm` | `COPY backend ./backend` | ✅ HARD | Source tree copy |
| 22 | 29 | `/app/heretek-swarm` (COPY --from=builder) | `/app/backend` | ✅ HARD | Path inside builder image; must match (21) |
| 23 | 29 | `/app/heretek-swarm` (dest) | `/app/backend` | ✅ HARD | Runtime copy destination |
| 24 | 33 | `migrations` | unchanged | — | Migrations stay at repo root |

**Note:** The WORKDIR stays at `/app`. No entry-point module paths change.

### 1.9 `pyproject.toml`

| # | Line | Current Reference | Target | Blocker? | Notes |
|---|------|------------------|--------|----------|-------|
| 25 | 82 | `where = ["heretek-swarm"]` | `where = ["backend"]` | ✅ HARD | Package discovery root |
| 26 | 83 | `include = ["heretek_swarm*"]` | unchanged | — | Module name glob, not filesystem path |
| 27 | 86 | `heretek-swarm = "heretek_swarm.cli:cli"` | unchanged | — | Python import path, not filesystem |
| 28 | 131 | `source = ["heretek-swarm"]` | `source = ["backend"]` | ✅ HARD | Coverage source path (run) |
| 29 | 142 | `source = ["heretek-swarm/"]` | `source = ["backend/"]` | ✅ HARD | Coverage path remapping (paths) |
| 30 | 158 | `src = ["heretek-swarm", "tests"]` | `src = ["backend", "tests"]` | ✅ HARD | Ruff source directories |

### 1.10 `swarm-dashboard/`

| # | Reference | Verdict |
|---|-----------|---------|
| — | All source `.tsx` files | No backend path dependencies |
| — | `regression.config.ts:41` | Contains `/home/john/Projects/heretek-swarm` — personal dev path; cosmetic |
| — | GitHub URLs in Layout/Settings components | Point to `github.com/heretek/heretek-swarm` — unaffected |
| — | E2E tests (`m028-*.spec.ts`) | Reference `heretek-swarm` CLI command name and `heretek_swarm` database name — unchanged constants |

**Verdict:** No structural changes needed. The frontend is fully decoupled from the backend filesystem layout.

---

## 2. Consolidated Change List (Execution Order for M007)

### Phase A: `pyproject.toml` (MUST be first — all tooling reads this)

```diff
[tool.setuptools.packages.find]
-where = ["heretek-swarm"]
+where = ["backend"]

[tool.coverage.run]
-source = ["heretek-swarm"]
+source = ["backend"]

[tool.coverage.paths]
-source = ["heretek-swarm/"]
+source = ["backend/"]

[tool.ruff]
-src = ["heretek-swarm", "tests"]
+src = ["backend", "tests"]
```

### Phase B: Docker (depends on Phase A for correct build)

```diff
# docker-compose.yml — api service
  build:
    context: .
-   dockerfile: heretek-swarm/Dockerfile
+   dockerfile: backend/Dockerfile

# Dockerfile (moved to backend/Dockerfile)
-COPY heretek-swarm ./heretek-swarm
+COPY backend ./backend

-COPY --from=builder --chown=appuser:appgroup /app/heretek-swarm /app/heretek-swarm
+COPY --from=builder --chown=appuser:appgroup /app/backend /app/backend
```

### Phase C: GitHub Actions (depends on Phase A)

```diff
# All workflows: replace stale "src/" references
-ruff check src/ tests/
+ruff check backend/ tests/

-ruff format --check src/ tests/
+ruff format --check backend/ tests/

-mypy src/
+mypy backend/

-bandit -r src/
+bandit -r backend/

-pytest ... --cov=src
+pytest ... --cov=backend

-pytest ... --cov=heretek-swarm
+pytest ... --cov=backend

# ci.yml Ruff Warning Gate (lines 35-42): already uses "heretek-swarm/"
-ruff check heretek-swarm/ tests/
+ruff check backend/ tests/

# load-test.yml: pip install -e . at repo root — works if pyproject.toml is correct
```

---

## 3. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| `src/` vs `heretek-swarm/` inconsistency | Commands fail silently (bandit/mypy scan wrong dir) | Audit all workflow YAML after restructure |
| Coverage paths misconfigured | Codecov reports 0% | Run `pytest --cov=backend --cov-report=term` to verify before pushing |
| Docker build cache invalidation | Full rebuild on first push after change | Acceptable — layer cache rebuilds once |
| `pip install -e .` breaks if `pyproject.toml` `where` is wrong | Can't run tests in CI | Verify with `pip install -e . && python -c "import heretek_swarm"` |
| `ruff check` scans wrong directory | Lint findings drop to 0 or jump unexpectedly | Run locally before pushing |

---

## 4. Verification Checklist for M007

- [ ] `pip install -e .` succeeds from repo root
- [ ] `python -c "import heretek_swarm; print(heretek_swarm.__file__)"` shows correct path
- [ ] `ruff check backend/ tests/` runs successfully
- [ ] `mypy backend/ --ignore-missing-imports` runs (warnings OK)
- [ ] `bandit -r backend/` runs
- [ ] `pytest tests/ --cov=backend --cov-report=term` produces coverage report
- [ ] `docker build -f backend/Dockerfile -t test-build .` succeeds
- [ ] `docker compose config` validates without errors

---

## 5. Summary Table

| File | Hard Blockers | Cosmetic | Unchanged |
|------|-------------|----------|-----------|
| `.github/workflows/ci.yml` | 5 | 0 | 0 |
| `.github/workflows/ci-cd.yml` | 5 | 0 | 0 |
| `.github/workflows/publish-python.yml` | 0 | 0 | 2 |
| `.github/workflows/publish-npm.yml` | 0 | 0 | all |
| `.github/workflows/load-test.yml` | 1 | 0 | 3 |
| `.github/workflows/codeboarding.yml` | 0 | 0 | all |
| `docker-compose.yml` | 1 | 0 | 2 |
| `heretek-swarm/Dockerfile` | 4 | 0 | 2 |
| `pyproject.toml` | 5 | 0 | 2 |
| `swarm-dashboard/` | 0 | 0 | all |
| **TOTAL** | **21** | **0** | — |

---

*End of CI_IMPACT.md*
