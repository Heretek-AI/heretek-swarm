# S03: Verify clean clone and full integration

**Goal:** Verify a clean clone of the repo at the new paths — install deps, run tests, verify dev server works. Verify the npm frontend still works with the backend at its new location.
**Demo:** Fresh clone of the repo works perfectly at new paths.

## Must-Haves

- Python package installs cleanly from new path
- pytest passes
- npm frontend still connects to backend at new path
- Docker build works

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes (optional)

## Verification

```bash
# Python package imports
cd backend && python -c "from heretek_swarm.actors.base.core import AgentActor; print('OK')"

# pytest passes
pytest backend/tests/ -x -q --tb=short

# Docker builds
docker compose build

# npm frontend still works
cd swarm-dashboard && npm run build -- --mode production
```

## Tasks

- [ ] **T01: Python package import check** `est:10m`
  - Why: Final verification that Python code works at new paths
  - Files: `backend/heretek_swarm/`
  - Do: Run `cd backend && python -c "import heretek_swarm; from heretek_swarm.actors.base.core import AgentActor; print('OK')"` and `pytest backend/tests/ -x -q --tb=short`
  - Verify: All imports succeed, all tests pass
  - Done when: Python package imports cleanly, pytest passes

- [ ] **T02: Docker build check** `est:10m`
  - Why: Docker deployment must work at new paths
  - Files: `docker-compose.yml`, `backend/Dockerfile`
  - Do: Run `docker compose build` to verify the Docker build still works at new paths. Check that WORKDIR, COPY, and pip install paths are correct.
  - Verify: `docker compose build` completes without errors
  - Done when: Docker image builds successfully

- [ ] **T03: Frontend integration check** `est:15m`
  - Why: Frontend may connect to backend via HTTP or file imports — verify it still works
  - Files: `swarm-dashboard/src/`, `backend/heretek_swarm/runtime/`
  - Do: Check if swarm-dashboard imports from the backend Python package. Look for `import heretek_swarm` or subprocess calls to the Python server. Update any backend URL references (e.g., `http://localhost:8000`) if needed. Run `cd swarm-dashboard && npm run build -- --mode production` to verify the frontend still builds.
  - Verify: `npm run build` succeeds
  - Done when: Frontend builds successfully

## Files Likely Touched

- Likely none if everything is correctly configured
- May need updates to `swarm-dashboard/.env` or backend URL config

## Integration Closure

Full monorepo works at new structure. The npm frontend connects to the Python backend at its new location.

---
id: M007-S03
provides:
  - Verified clean integration
key_decisions:
  - No path changes needed if frontend uses HTTP to connect to backend (doesn't import Python directly)
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: ~35m
verification_result: pending
completed_at: pending
