# S02: Docker Infrastructure Fix & Build

**Goal:** Fix critical Docker bugs, build all 6 service images, and bring the stack to healthy
**Demo:** `docker compose build` exits 0 for all services, `docker compose up -d` reports all 6 containers healthy within 60s, `curl http://localhost:8000/api/health` returns 200

## Must-Haves

- 1. docker compose build exits 0 for all services
- 2. docker compose up -d — all 6 services healthy within 60s
- 3. curl http://localhost:8000/api/health returns 200
- 4. Fix HEALTHCHECK URL in backend/Dockerfile and docker-compose.yml (/health → /api/health)
- 5. Fix SPA catch-all dist path in main.py (dashboard/frontend/dist → swarm-dashboard/dist)
- 6. Verify dashboard nginx proxy reaches API

## Proof Level

- This slice proves: Verified via docker compose commands and curl health checks

## Integration Closure

All 6 Docker services must pass health checks; inter-service connectivity verified

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [ ] **T01: Fix Dockerfile HEALTHCHECK URL** `est:5m`
  Fix HEALTHCHECK URL in backend/Dockerfile line 68: change http://localhost:8000/health to http://localhost:8000/api/health
  - Files: `backend/Dockerfile`
  - Verify: grep 'health' backend/Dockerfile | grep 'api/health'

- [ ] **T02: Fix docker-compose.yml HEALTHCHECK URL** `est:5m`
  Fix HEALTHCHECK URL in docker-compose.yml line 111: change http://localhost:8000/health to http://localhost:8000/api/health
  - Files: `docker-compose.yml`
  - Verify: grep 'health' docker-compose.yml | grep 'api/health'

- [ ] **T03: Fix SPA catch-all dist path in main.py** `est:15m`
  Fix SPA catch-all dist path in main.py. Change the default DASHBOARD_DIST_PATH from os.path.join(project_root, 'dashboard', 'frontend', 'dist') to os.path.join(project_root, 'swarm-dashboard', 'dist'). There are 3 occurrences around lines 429, 1249, and 1281.
  - Files: `backend/heretek_swarm/api/main.py`
  - Verify: grep -c 'swarm-dashboard.*dist' backend/heretek_swarm/api/main.py

- [ ] **T04: Build all Docker images** `est:30m`
  Run docker compose build for all 6 services. If build fails (e.g. stale uv.lock does not satisfy pyproject.toml), regenerate uv.lock with uv lock and retry.
  - Files: `backend/Dockerfile`, `swarm-dashboard/Dockerfile`
  - Verify: docker compose build 2>&1 | tail -20

- [ ] **T05: Bring stack up and verify health** `est:30m`
  Run docker compose up -d. Wait up to 60s for all 6 services to report healthy. Check logs of any unhealthy services. Verify curl http://localhost:8000/api/health returns 200.
  - Verify: curl -sf http://localhost:8000/api/health && docker compose ps --format '{{.Name}} {{.Status}}' | grep healthy

## Files Likely Touched

- backend/Dockerfile
- docker-compose.yml
- backend/heretek_swarm/api/main.py
- swarm-dashboard/Dockerfile
