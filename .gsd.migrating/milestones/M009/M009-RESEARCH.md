# M009 Research: Runtime Hardening & Live Verification

## Investigation Scope & Method

This research covered the entire codebase surface relevant to M009's acceptance criteria:

| Area | Documents Inspected | Key Finding |
|------|-------------------|-------------|
| Build & packaging | `pyproject.toml`, `uv.lock`, `backend/Dockerfile`, `swarm-dashboard/Dockerfile`, `.env.example` | ✅ All paths correct post-restructure; **1 critical HEALTHCHECK bug** |
| Docker orchestration | `docker-compose.yml`, backend/Dockerfile HEALTHCHECK | ✅ 6 services, all health-checked; **1 URL mismatch bug** |
| API surface | `backend/heretek_swarm/api/main.py` (1392 lines) | ✅ 21 routers, clean lifespan pattern; **1 SPA path bug** |
| Test infrastructure | `tests/conftest.py`, `pyproject.toml` test config, 62 test files | ✅ ~370 tests, marker isolation, autouse cleanup |
| CI/CD | `.github/workflows/ci.yml`, 4 other workflows | ✅ Unit-only pytest, ruff gate, mypy, frontend lint |
| Environment | `.env.example` (exists), `.gitignore` (.env listed), actual `.env` | ⚠️ `.env` must be created |
| Agent startup | `api/main.py` `_spawn_all_agents()` | ✅ 23 agents in 6 tiers, all imported from canonical paths |

## Critical Regression Risks (Must-Fix)

### 1. Docker HEALTHCHECK URL Mismatch — **BLOCKING**

The Docker HEALTHCHECK in both `docker-compose.yml` and `backend/Dockerfile` uses:

```
CMD curl -sf http://localhost:8000/health || exit 1
```

But the actual FastAPI endpoint is at **`/api/health`**, not `/health`.

- **File:** `docker-compose.yml` line (api service healthcheck)
- **File:** `backend/Dockerfile` line (Dockerfile HEALTHCHECK directive)
- **Impact:** The api container is never marked healthy. `docker compose up` stalls indefinitely waiting for the api health check to pass.
- **Fix:** Change both to `http://localhost:8000/api/health`.

### 2. SPA Catch-all Path Mismatch — **BLOCKING**

The SPA catch-all route in `main.py` resolves the dashboard dist path as:

```python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
dist_path = os.environ.get(
    "DASHBOARD_DIST_PATH",
    os.path.join(project_root, "dashboard", "frontend", "dist")
)
```

This defaults to `dashboard/frontend/dist` but the actual Docker build mounts `swarm-dashboard/dist`. The `DASHBOARD_DIST_PATH` env var is **not set** in `docker-compose.yml`.

- **File:** `backend/heretek_swarm/api/main.py` (SPA catch-all, ~line 1310)
- **Impact:** The dashboard SPA returns 404. The API root and all non-API paths fail to serve the React app.
- **Fix:** Either set `DASHBOARD_DIST_PATH=/usr/share/nginx/html` in docker-compose (but the API container doesn't have the dashboard dist mounted — it's in the separate dashboard container), or remove the SPA catch-all entirely since the dashboard is served separately by nginx in the dashboard container. This is a **design artifact** — the SPA catch-all was for an earlier single-container deployment model.

### 3. Embedding Server Unavailability — **Medium Risk**

The embedding provider defaults to `http://127.0.0.1:13305/api/v1` with `nomic-embed-text-v2-moe-GGUF` model and `lemonade` API key. This is an external service.

- All embedding-dependent features (vector search, semantic memory, mem0) will fail if lemonade isn't running.
- The API gracefully handles this with try/except in initialization, but individual embedding calls during runtime may still fail loudly.
- **Recommendation:** Add a mock/fallback embedding provider for development when the external server is unavailable. Document in the `.env` comments.

## Environment Assessment

### What must be created

| Item | Status | Action |
|------|--------|--------|
| `.env` | ❌ Missing | Copy `.env.example`, fill in `OPENAI_API_KEY` and other values |
| Docker Desktop WSL2 integration | ⚠️ Not configured | Must enable WSL2 integration for the WSL distro in Docker Desktop settings |
| Python venv with dev deps | ⚠️ Not installed | `pip install -e ".[dev]"` — may need `uv lock --refresh` first |

### Known good

- `.env.example` is thorough (90+ lines, well-commented, covers all 6 services)
- `.gitignore` has `.env` listed — safe to create
- `pyproject.toml` `where = ["backend"]` maps correctly to the post-restructure layout
- `backend/heretek_swarm/__init__.py` exists — package is importable
- All 24 agent classes use canonical import paths from `heretek_swarm.actors`

## Test Infrastructure Analysis

### Test Suite Profile (62 files, ~370 tests)

- **conftest.py** has autouse fixture to clear supervisor actors between tests — prevents state leakage
- **Marker isolation:** `unit` (fast/isolated), `integration` (requires services), `load`, `slow`, `a2a`, `consensus`, `latency`, `security`
- **CI runs:** `pytest -m "not integration"` — integration tests skipped in CI
- **Lifecycle smoke tests:** 26 parameterized tests covering all 24 AgentActor subclasses
- **Warning handling:** `ResourceWarning` from unclosed `aiohttp.ClientSession` is explicitly suppressed (documented as benign — heartbeat cleanup races with event loop teardown)
- **Coverage target:** 80% minimum

### Key test files:
- `test_lifecycle_basic.py` (26 parameterized smoke tests)
- `test_consensus_*.py` (deliberation flow, voting, tribunal)
- `test_api_*.py` (auth, websocket, health endpoints)
- `test_cli.py` (CLI commands)
- `test_ws_status_pump.py` / `test_ws_status_pump_integration.py`

### Docker Build Analysis

#### API Dockerfile (`backend/Dockerfile`)
- **Base image:** `python:3.11-slim`
- **Build system:** uv + pip (`uv sync --frozen --no-dev --no-editable`)
- **Extra runtime deps:** `prometheus-client`, `psycopg2-binary`, `asyncpg`
- **Non-root user:** `appuser:appgroup` (uid 1001)
- **Entry point:** `heretek-swarm serve --host 0.0.0.0 --port 8000`
- **COPY paths:** `pyproject.toml`, `uv.lock` (from repo root), `backend/` (from repo root), `migrations/` (from repo root)
- **HEALTHCHECK:** `curl -sf http://localhost:8000/health` — **BUG: should be /api/health**
- **Concern:** `uv sync --frozen` with pre-restructure `uv.lock` may fail if dependency metadata changed

#### Frontend Dockerfile (`swarm-dashboard/Dockerfile`)
- **Base:** Two-stage: `node:20-alpine` builder + `nginx:alpine` production
- **Build:** `npm ci` + `npm run build`
- **Serve:** nginx with custom config, non-root user
- **HEALTHCHECK:** `wget --spider http://127.0.0.1/` — correct
- **nginx.conf** serves on port 80, proxies `/api/` to `VITE_API_URL` (not set in docker-compose for the dashboard service)

#### Dashboard nginx proxy concern
The dashboard service in docker-compose does **not** set `VITE_API_URL`. The nginx config likely proxies `/api/` requests — needs verification that the dashboard can reach the API at runtime. Since `api` is a docker service, the dashboard container should use `http://api:8000` but the Vite build-time env var `VITE_API_URL` is embedded at build time, not runtime. This is a classic Vite + Docker issue.

## Slice Ordering Recommendation

Based on risk and dependency analysis, the work should be ordered as follows:

### Slice 1: Fix Critical Regressions (HIGHEST RISK, DO FIRST)
- Fix Docker HEALTHCHECK URL (`/health` → `/api/health`) in docker-compose.yml and backend/Dockerfile
- Fix SPA catch-all path mismatch or remove the dead SPA catch-all route
- Set `VITE_API_URL` properly in docker-compose.yml for the dashboard service
- **Rationale:** These are hard blocks. Fixing them first prevents wasted debugging cycles.

### Slice 2: Local Python Verification
- Create `.env` from `.env.example`
- `pip install -e ".[dev]"` — verify `uv lock --refresh` needed
- `pytest tests/` — fix all import/path/type regressions
- `ruff check backend/heretek_swarm/ tests/` — zero violations
- `mypy backend/heretek_swarm` — zero type errors
- **Rationale:** Fastest feedback loop. Catches import breakage, lint, and type issues without Docker complexity.

### Slice 3: Docker Build & Startup
- `docker compose build` — verify all Dockerfiles compile
- `docker compose up -d` — all 6 containers healthy
- `curl http://localhost:8000/api/health` — API health check
- Fix any Docker build failures (uv.lock refresh, path issues)
- **Rationale:** Docker adds containerization complexity; fix Python issues first.

### Slice 4: E2E Verification
- `curl -X POST http://localhost:8000/api/...` — verify API responds to prompt endpoint
- Verify dashboard at `http://localhost:3000`
- Handle embedding server absence gracefully
- **Rationale:** Highest value, highest risk — requires all previous slices to pass.

## Boundary Contracts

### What each slice proves to the next

| From | To | Contract |
|------|-----|----------|
| Slice 1 | Slice 2 | HEALTHCHECK URL is correct, Docker will eventually pass after build |
| Slice 2 | Slice 3 | `pip install` works, all ~370 tests pass, ruff/mypy zero | 
| Slice 3 | Slice 4 | All 6 containers build and start healthy |
| Slice 4 | Milestone Complete | API responds, prompt produces swarm response, dashboard serves |

### External dependencies (not verifiable locally):
- OpenAI-compatible LLM endpoint (MiniMax) — needs real `OPENAI_API_KEY` in `.env`
- Local embedding server (lemonade, port 13305) — may not be running; must not block non-embedding flows

## Known Failure Modes (Preventing Slices)

| Failure Mode | Catch In | Fallback |
|-------------|----------|----------|
| `uv sync --frozen` fails (lockfile stale) | Slice 3 | Run `uv lock --refresh` locally, commit updated `uv.lock` |
| Health check timeout on postgres/redis/qdrant | Slice 3 | Check `docker compose logs <service>`; port conflicts on Windows |
| mem0 import error (`from memory import...`) | Slice 2 | Graceful — the code has `try/except ImportError` |
| Dashboard doesn't reach API | Slice 4 | Set `VITE_API_URL=http://api:8000` in docker-compose; rebuild if needed |
| Embedding calls fail in runtime | Slice 4 | Should not crash the agent — but may silently degrade responses; add fallback |

## Technology Stack Summary

| Layer | Technology | Version | Status |
|-------|-----------|---------|--------|
| Language | Python | 3.11+ | ✅ |
| Package manager | pip + uv | lockfile exists | ⚠️ Pre-restructure |
| Web framework | FastAPI + Uvicorn | ≥0.109, ≥0.25 | ✅ |
| ORM/DB | SQLAlchemy + asyncpg + PostgreSQL 15 | ✅ | Containerized |
| Cache | Redis 7 Alpine | ✅ | Containerized |
| Vector DB | Qdrant | latest | ✅ |
| Event Mesh | NATS with JetStream | latest | ✅ |
| Memory | mem0ai | ≥1.0.0 | ⚠️ Optional dependency |
| Frontend | React + Vite + Vitest | Node 20 | ✅ |
| Container | Docker + Docker Compose v2 | WSL2 | ⚠️ WSL integration needed |
| LLM | MiniMax-M2.7 (OpenAI-compatible) | API-driven | ⚠️ Needs API key |

## Candidate Requirements

Based on findings, the following should be considered for REQUIREMENTS.md:

1. **R_M009_01** (core-capability): Docker HEALTHCHECK must use the correct FastAPI route path. The `/api/health` endpoint must be used instead of `/health` in both `docker-compose.yml` and `backend/Dockerfile`.

2. **R_M009_02** (core-capability): The SPA catch-all route in `main.py` must either be removed (since the dashboard is served by a separate nginx container) or corrected to point at the actual dist path. No dead code should serve 404 errors in production paths.

3. **R_M009_03** (quality-attribute): Non-service endpoints (health, root, SPA catch-all) should NOT require authentication so Docker HEALTHCHECK passes. Currently `verify_auth` is not applied to health endpoints — confirmed correct.

4. **R_M009_04** (failure-visibility): The dashboard service in docker-compose must have `VITE_API_URL` set so the React app can reach the API. Build-time env vars embedded via Vite may require rebuild to update.

5. **R_M009_05** (continuity): The `uv.lock` file must be refreshed post-restructure via `uv lock --refresh` before Docker builds will succeed.

6. **R_M009_06** (anti-feature): The local embedding server (lemonade, port 13305) must NOT be a hard requirement for E2E verification. Non-embedding flows (health check, agent deliberation, CLI) must work without it.
