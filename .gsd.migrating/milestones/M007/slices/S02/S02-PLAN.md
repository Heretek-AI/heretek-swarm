# S02: Rewrite imports and CI paths

**Goal:** Update all Python imports referencing heretek_swarm to point to the new location. Update CI workflows to reference backend/ instead of heretek-swarm/. Update Docker and config files too.
**Demo:** All Python imports use the new backend/ path; CI passes.

## Must-Haves

- All Python imports updated from `heretek_swarm.` to `backend.heretek_swarm.` (or relative paths)
- All GitHub workflow files updated to reference `backend/`
- All Docker/config files updated
- Tests pass with new paths

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

```bash
# Python imports work at new path
cd backend && python -c "from heretek_swarm.actors.base.core import AgentActor; print('OK')"

# All Python files pass import check
python -c "import heretek_swarm; print('heretek_swarm imports OK')"

# pytest passes
pytest tests/ -x -q

# CI workflow syntax check
python -c "import yaml; [yaml.safe_load(open(f)) for f in ['backend/.github/workflows/*.yml', 'swarm-dashboard/.github/workflows/*.yml']]"
```

## Tasks

- [ ] **T01: Update Python imports in backend/** `est:30m`
  - Why: Python files still import from `heretek_swarm.*` but the package is now under `backend/`
  - Files: `backend/heretek_swarm/**/*.py`
  - Do: Run the audit_imports.py script from M006-S01 to get the full list. Use sed or a Python script to update all `from heretek_swarm.` imports. For files INSIDE the backend/ package, prefer relative imports or `backend.heretek_swarm.` prefix. Be careful not to change import strings that are actual code (e.g., string literals in __all__).
  - Verify: `cd backend && python -c "import heretek_swarm; print('OK')"`
  - Done when: All Python imports resolve at new paths

- [ ] **T02: Update CI workflow files** `est:20m`
  - Why: GitHub workflows reference `heretek-swarm/` paths
  - Files: `.github/workflows/*.yml`, `docker-compose.yml`, `Dockerfile`, `pyproject.toml`
  - Do: Update all `heretek-swarm/` path references to `backend/`. Update `cd heretek-swarm/` to `cd backend/` in workflow steps. Update any `pip install -e heretek-swarm/` to `pip install -e backend/`.
  - Verify: `grep -r "heretek-swarm" .github/workflows/ docker-compose.yml Dockerfile backend/.github/workflows/ | grep -v ".git" || echo "No old paths remaining"`
  - Done when: No `heretek-swarm/` references remain in CI files

- [ ] **T03: Update Docker/config files in backend/** `est:15m`
  - Why: Docker and config files inside backend/ may reference paths that changed
  - Files: `backend/docker-compose.yml`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/setup.py`, `backend/setup.cfg`
  - Do: Check each config file for path references to `../` or old heretek-swarm paths. Update WORKDIR, COPY, and path references.
  - Verify: All config files load without path errors
  - Done when: Docker builds and config files reference correct paths

## Files Likely Touched

- `backend/heretek_swarm/**/*.py` (import rewrites)
- `.github/workflows/*.yml` (path updates)
- `docker-compose.yml` (path updates)
- `Dockerfile` (path updates)
- `pyproject.toml` (if it exists in root)

## Integration Closure

`backend/heretek_swarm/` imports resolve correctly. CI uses `backend/` paths. The npm frontend at `swarm-dashboard/` connects to `backend/heretek_swarm/`.

---
id: M007-S02
provides:
  - All imports updated
  - CI paths fixed
key_decisions:
  - For internal imports, prefer `from heretek_swarm.` (unchanged) since Python resolves relative to PYTHONPATH — only external callers need `backend.heretek_swarm.`
  - Workflow files must use `backend/` since they're outside the package
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: ~1.5h
verification_result: pending
completed_at: pending
