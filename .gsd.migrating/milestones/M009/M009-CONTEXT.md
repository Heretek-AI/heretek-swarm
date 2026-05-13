# M009: Runtime Hardening & Live Verification

**Gathered:** 2026-05-12
**Status:** Ready for planning

## Project Description

M009 closes the runtime verification gap deferred from M008. After 8 structural milestones (M001–M008) that unified directories, type-sealed mixin contracts, added test scaffolding, documented architecture, restructured the repository, and performed cleanup — the swarm has never actually been run post-restructure. M009 is the proof that everything works: from `pip install` through `docker compose up` to a live LLM prompt and collective swarm response, on this Windows machine with Docker Desktop.

## Why This Milestone

M008's pytest, ruff, and docker compose verification were explicitly deferred to "dev environment" because the sandbox couldn't run them. The repository restructure touched 463 files across a git mv rename (M007), 429 Python imports were re-mapped (M006), and 22 doc files plus 4 Python source files had path references updated (M008). The probability of silent breakage is non-trivial. M009 is the first time anyone actually runs the system after all of this work.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `docker compose up -d` and see all 6 services (postgres, redis, qdrant, nats, api, dashboard) healthy
- Send a prompt via `curl -X POST http://localhost:8000/v1/prompt` and receive a collective swarm response from the deliberating agents
- Run `pytest tests/` and see all ~370 tests pass with zero failures
- Run `ruff check backend/heretek_swarm/ tests/` and `mypy backend/heretek_swarm` with zero violations

### Entry point / environment

- Entry point: `docker compose up` (Docker), `pip install -e .` + `pytest` + `ruff` + `mypy` (local Python)
- Environment: Windows 10/11 with Docker Desktop (WSL2 backend), Python 3.11+
- Live dependencies involved: PostgreSQL, Redis, Qdrant, NATS, OpenAI-compatible LLM API (MiniMax or user's choice), local embedding server (lemonade on port 13305)

## Completion Class

- Contract complete means: pip install succeeds, all pytest tests pass, ruff and mypy produce zero errors
- Integration complete means: docker compose brings up all 6 services with passing health checks, API responds to health and prompt endpoints
- Operational complete means: a live prompt through the API produces a real swarm deliberation and response from the agent collective

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `pip install -e .` from repo root installs the `heretek-swarm` package with zero errors
- `docker compose up -d` with a real `OPENAI_API_KEY` in `.env` starts all 6 services healthy, and `curl -X POST localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}'` returns a collective response
- The full CI-quality gate passes: `pytest tests/` (all ~370 tests), `ruff check`, and `mypy` with zero violations — any regressions found are fixed, not deferred

## Architectural Decisions

### Fix-everything policy

**Decision:** Every regression, broken import, lint violation, type error, and docker build failure discovered during verification is fixed within M009 — zero tolerance for deferral.

**Rationale:** M001–M008 were structural. Deferring fixes to M010 would mean shipping a known-broken milestone. M009 is the gate that proves the foundation is solid.

**Alternatives Considered:**
- Audit-only (diagnose + document, fix in M010) — wastes a milestone handoff cycle and leaves the repo in a known-broken state

### Verification order: local Python first, then Docker

**Decision:** Run `pip install -e .`, pytest, ruff, and mypy locally before attempting `docker compose up`. Python-level breakage is faster to fix and surfaces the most import/path issues.

**Rationale:** Docker builds add containerization complexity on top of Python issues. Fixing Python regressions first reduces the debugging surface when Docker fails.

**Alternatives Considered:**
- Docker-first — a Dockerfile failure might be caused by a Python issue that's harder to diagnose inside a container

### .env: create from .env.example, not checked in

**Decision:** `.env` is created by copying `.env.example` and filling in real values (OPENAI_API_KEY, etc.). `.env` stays in `.gitignore` and is never committed.

**Rationale:** Standard security practice. `.env.example` already exists with thorough comments and sensible defaults.

**Alternatives Considered:**
- Use `secure_env_collect` to inject values at runtime — adds indirection; simpler to have the user create `.env` once

---

## Error Handling Strategy

- **pip install failure**: Diagnose `pyproject.toml` `where`/`source` directives. Check that `backend/heretek_swarm/` exists and has `__init__.py`. Fix path issues directly.
- **Import errors in pytest**: Trace each failure to its source. Most likely causes: stale import paths, missing re-exports in `__init__.py`, or module-renaming edge cases from M007. Fix by correcting the import or the package structure.
- **Docker build failure**: Check Dockerfile paths against actual filesystem. The Dockerfile references `pyproject.toml`, `uv.lock`, `backend/`, and `migrations/` — all from repo root context. Fix path mismatches.
- **Docker health check failure**: Check service logs (`docker compose logs <service>`). Infrastructure services (postgres, redis, qdrant, nats) are stock images — failures likely configuration (env vars, port conflicts).
- **API returns error on prompt**: Check API logs. Possible causes: missing/invalid OPENAI_API_KEY, LLM endpoint unreachable, agent initialization failure. Fix and re-verify.
- **Embedding server unavailable**: If the local lemonade embedding server on port 13305 is not running, document as a known limitation and verify that non-embedding flows still work. Consider adding a mock/fallback for embedding in tests.

## Risks and Unknowns

- `.env` does not exist (only `.env.example`) — must be created with a real `OPENAI_API_KEY` before docker compose — blocks the entire Docker verification path
- Local embedding server (`http://127.0.0.1:13305/api/v1` with `nomic-embed-text-v2-moe-GGUF`) may not be running — could cause embedding-dependent features to fail; need fallback or mock strategy
- ~370 tests importing from `heretek_swarm.*` may have import breakage from the restructure — pytest is the first runtime validation of the import graph
- Dockerfile uses `uv sync --frozen` with `uv.lock` — the lockfile exists (4,200+ lines) but was generated pre-restructure; may need regeneration if dependencies or paths changed
- The swarm-dashboard (React/Vite) was not touched during M006–M008 and should be structurally sound, but its API dependency (`VITE_API_URL`) must point at the running API container
- Mypy strict mode on 463+ files — high probability of type errors that have never been caught

## Existing Codebase / Prior Art

- `pyproject.toml` (root) — package config with `where = ["backend"]`, pytest/ruff/mypy/coverage config, all dependency groups
- `uv.lock` (root) — frozen dependency lockfile for reproducible Docker builds
- `.env.example` (root) — template with all required env vars and comments; `.env` is gitignored
- `docker-compose.yml` (root) — 6 services (postgres, redis, qdrant, nats, api, dashboard) with health checks
- `backend/Dockerfile` — multi-stage build (builder + production) with uv sync and non-root user
- `tests/` (root) — 62 test files with ~370 tests, `conftest.py`, marker-based isolation
- `backend/heretek_swarm/actors/__init__.py` — canonical import surface for all 24 agent classes
- `docs/ARCHITECTURE.md` — 12-section architecture reference (validated in M005, path-updated in M008)

## Relevant Requirements

- *(No requirements registered yet — M009 is the first milestone that could populate REQUIREMENTS.md with validated runtime requirements)*

## Scope

### In Scope

- Create `.env` from `.env.example` with real `OPENAI_API_KEY` (and other required values)
- `pip install -e .` from repo root — verify editable install works
- `pytest tests/` — run all ~370 tests, fix all failures
- `ruff check backend/heretek_swarm/ tests/` — zero lint violations
- `mypy backend/heretek_swarm` — strict mode, zero type errors
- `docker compose build` — verify all Dockerfiles compile
- `docker compose up -d` — all 6 services healthy
- `curl http://localhost:8000/health` — API health check
- `curl -X POST http://localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}'` — E2E prompt → swarm response
- Fix all regressions found (import breakage, path mismatches, type errors, lint violations, docker failures)
- Update `pyproject.toml` or `uv.lock` if needed for dependency resolution

### Out of Scope / Non-Goals

- New agent features or mixin capabilities
- Swarm-dashboard UI changes (verify it serves, don't redesign)
- Production deployment (staging/prod environments, CI/CD pipeline changes)
- Performance benchmarking or optimization
- Documentation updates beyond what's needed to reflect fixes
- Setting up or debugging the local embedding server (lemonade) — if unavailable, document as limitation and ensure non-embedding paths work

## Technical Constraints

- Must run on Windows with Docker Desktop (WSL2) — Docker Compose v2
- Python 3.11+ required by pyproject.toml
- `OPENAI_API_KEY` must point at a real, funded LLM endpoint (MiniMax or user's choice)
- The embedding server at `127.0.0.1:13305` may or may not be running — the milestone must handle both cases
- `uv.lock` was generated pre-restructure; may need `uv lock --refresh` if dependency resolution fails
- All fixes must be functional-only — no opportunistic refactoring or style changes beyond what lint rules enforce

## Integration Points

- **MiniMax API** (or user's chosen OpenAI-compatible provider) — LLM inference for agent deliberation
- **PostgreSQL 15** — state persistence, Mem0 metadata storage
- **Redis 7** — caching layer
- **Qdrant** — vector storage for embeddings
- **NATS with JetStream** — event mesh for inter-agent messaging
- **Local embedding server** (lemonade, port 13305) — optional; embedding generation for vector search
- **Swarm Dashboard** (React/Vite, port 3000) — frontend served by nginx in Docker

## Testing Requirements

All existing tests must pass. The test suite includes:

- **Unit tests**: ~370 tests across 62 files, with marker isolation (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
- **Lifecycle smoke tests**: 26 parameterized tests covering all 24 AgentActor subclasses
- **Consensus tests**: Deliberation flow, voting, tribunal patterns
- **CLI tests**: help output, config commands
- **API tests**: auth, websocket, health endpoints

No new tests are required unless needed to verify a fix. If a regression is found that had no test coverage, add a regression test to prevent recurrence.

## Acceptance Criteria

Per-slice acceptance criteria will be gathered during planning. High-level criteria:

1. `pip install -e .` exits 0 and `heretek-swarm --help` produces expected output
2. `pytest tests/` — zero failures, zero errors
3. `ruff check backend/heretek_swarm/ tests/` — zero violations
4. `mypy backend/heretek_swarm` — zero errors (strict mode)
5. `docker compose build` exits 0 for all services
6. `docker compose up -d` — all 6 containers report healthy within 60s
7. `curl http://localhost:8000/health` returns 200
8. `curl -X POST http://localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}'` returns 200 with a JSON response containing agent deliberation output
9. All regressions found during verification are fixed with commits
10. Dashboard at `http://localhost:3000` serves the React app

## Open Questions

- What specific LLM provider/model will be used? (default: MiniMax-M2.7 from `.env.example`) — determined at .env creation time
- Is the local embedding server (lemonade on port 13305) available and running? — to be discovered during verification
- Does `uv.lock` need regeneration post-restructure? — to be discovered during `pip install`/Docker build
