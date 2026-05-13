# M009: Runtime Hardening & Live Verification

**Vision:** Prove that the entire post-restructure swarm actually runs — from pip install through docker compose up to a live LLM prompt with collective agent deliberation. Close the runtime verification gap deferred from M008 with zero tolerance for regressions.

## Success Criteria

- S01: pip install -e . exits 0 and heretek-swarm --help produces expected output
- S01: pytest tests/ — zero failures, zero errors
- S01: ruff check backend/heretek_swarm/ tests/ — zero violations
- S01: mypy backend/heretek_swarm — zero type errors (strict mode)
- S02: docker compose build exits 0 for all services
- S02: docker compose up -d — all 6 containers healthy within 60s
- S02: curl http://localhost:8000/api/health returns 200
- S03: curl -X POST localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}' returns 200 with JSON deliberation output
- S03: Dashboard at http://localhost:3000 serves the React app
- S03: Non-embedding flows work when embedding server is unavailable

## Slices

- [ ] **S01: S01** `risk:High — 62 test files with ~1000 test functions importing from the restructured package; mypy strict mode on 463+ files; stale uv.lock may break pip install` `depends:[]`
  > After this: `pip install -e .` exits 0, `heretek-swarm --help` shows help output, `pytest tests/` shows zero failures, `ruff check backend/heretek_swarm/ tests/` shows zero violations, `mypy backend/heretek_swarm` shows zero type errors

- [ ] **S02: Docker Infrastructure Fix & Build** `risk:High — two confirmed blocking bugs (HEALTHCHECK URL uses /health instead of /api/health; SPA catch-all path points to wrong dist directory); stale uv.lock may fail docker build; dashboard nginx proxy may not reach API` `depends:[S01]`
  > After this: `docker compose build` exits 0 for all services, `docker compose up -d` reports all 6 containers healthy within 60s, `curl http://localhost:8000/api/health` returns 200

- [ ] **S03: Live E2E & Embedding Edge Cases** `risk:Medium — requires real OPENAI_API_KEY; local embedding server (lemonade on port 13305) may be unavailable; live LLM call may timeout or fail` `depends:[S02]`
  > After this: `curl -X POST http://localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}'` returns 200 with JSON deliberation output; browser at localhost:3000 shows the swarm dashboard; embedding-dependent features fail gracefully when server is down

## Boundary Map

Not provided.
