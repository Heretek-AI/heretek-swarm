# Code Optimization Plan — Heretek Swarm

**Generated**: 2026-06-01
**Source**: Full codebase audit across 15 optimization domains (database, memory, algorithmic complexity, concurrency, bundle, dead code, I/O, rendering, data structures, error handling, caching, build, security, logging, infrastructure)

---

## Summary

| Priority | Domain | Actions | Effort |
|----------|--------|---------|--------|
| P0 | Security | 4 docker-compose defaults fixes | 5 min |
| P1 | Algorithmic Complexity | 4 sorted() → min()/max() replacements | 10 min |
| P2 | Infrastructure | 6 Dockerfile/compose improvements | 20 min |
| P3 | Caching | lru_cache + useMemo/useCallback additions | 30 min |
| P4 | Dead Code | Remove 2 deprecated shim functions | 5 min |
| P5 | Observability | Replace 6 print() with structured logging | 10 min |
| P6 | Concurrency | Batch 2+ sequential await chains | 15 min |
| P7 | Bundle | Vite manualChunks config | 5 min |

**Total estimated effort**: ~100 minutes

---

## P0 — Security Hardening (docker-compose defaults) ⚡ 5 min

**Files**: `docker-compose.yml`

| # | Action | Current | Fix |
|---|--------|---------|-----|
| 1 | Remove default JWT_SECRET | `JWT_SECRET=${JWT_SECRET:-jwt_secret_heretek_deploy_2026_random_string}` | `JWT_SECRET=${JWT_SECRET}` — no fallback |
| 2 | Remove default POSTGRES_PASSWORD | `POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}` | `POSTGRES_PASSWORD=${POSTGRES_PASSWORD}` — no fallback |
| 3 | Set explicit CORS origins | `CORS_ORIGINS: ${CORS_ORIGINS:-*}` | `CORS_ORIGINS: ${CORS_ORIGINS}` — no wildcard fallback |
| 4 | Verify HERETEK_API_KEY default | `HERETEK_API_KEY:-htsk_your_api_key_here}` | Same approach — remove meaningful default |

---

## P1 — Algorithmic Complexity (sorted() misuse) ⚡ 10 min

**Files**: `backend/heretek_swarm/actors/catalyst/agent.py`, `backend/heretek_swarm/runtime/deliberation_orchestrator.py`

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 5 | `catalyst/agent.py` | 746 | `sorted(self._notifications.keys())[0]` | `min(self._notifications)` |
| 6 | `catalyst/agent.py` | 790 | `sorted(self._notifications.keys())[0]` | `min(self._notifications)` |
| 7 | `deliberation_orchestrator.py` | 229 | `sorted(tasks.keys())[-1]` | `max(tasks)` |
| 8 | `deliberation_orchestrator.py` | 240 | `sorted(snippets.keys())[-1]` | `max(snippets)` |

**Impact**: O(n log n) → O(n) for finding min/max in a dictionary.

---

## P2 — Infrastructure (Docker) 🔄 20 min

**Files**: `docker-compose.yml`, `backend/Dockerfile`, `swarm-dashboard/Dockerfile`

| # | Action | File | Why |
|---|--------|------|-----|
| 9 | Add `mem_limit`/`cpus` to all 6 services | `docker-compose.yml` | Prevent OOM under load |
| 10 | Pin Qdrant (`qdrant/qdrant:v1.9.0`) | `docker-compose.yml` | Mutable `latest` tag breaks on updates |
| 11 | Define explicit Docker networks | `docker-compose.yml` | Better service isolation |
| 12 | Install uv via multi-stage COPY | `backend/Dockerfile` | Faster, avoids pip-to-install-uv |
| 13 | Move post-uv-sync pip installs into pyproject.toml | `backend/Dockerfile` + `pyproject.toml` | uv manages all deps |
| 14 | Flex Node.js version pin | `swarm-dashboard/Dockerfile` | `node:26-alpine` vs `node:26.2.0-alpine` |

---

## P3 — Caching & Memoization 🧠 30 min

**Files**: Multiple backend Python + frontend React

| # | Action | Scope | Details |
|---|--------|-------|---------|
| 15 | Audit hot-path pure functions for `@lru_cache` | Backend `backend/heretek_swarm/` | Search for expensive pure computations (string processing, data transforms, model serialization) |
| 16 | Add `useMemo`/`useCallback` to React components | Frontend `swarm-dashboard/src/` | Currently zero usage — identify derived data and callback props |

**Note**: Requires code reading to identify the best candidates. Start with the most-frequently-called pure functions and the most-rendered React components.

---

## P4 — Dead Code Removal 🗑️ 5 min

**Files**: `backend/heretek_swarm/actors/validation.py`

| # | Line | Current | Action |
|---|------|---------|--------|
| 17 | 40-60 | `get_immutable_rules()` and `get_baseline_config()` deprecated wrappers | Remove after verifying no external callers |

**Check**: Grep for imports of `get_immutable_rules` and `get_baseline_config` from this module.

---

## P5 — Logging: print() → structlog 📋 10 min

**Files**: 6 locations across 5 files

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 18 | `gateway/nats_event_mesh.py` | 99 | `print(f"Received: {data}")` | `logger.info("nats_msg_received", data=data)` |
| 19 | `orchestration/heavyswarm.py` | 126 | `print(f"Decision: ...")` | `logger.info("heavyswarm_decision", decision=...)` |
| 20 | `orchestration/heavyswarm.py` | 127 | `print(f"Confidence: ...")` | `logger.info("heavyswarm_confidence", confidence=...)` |
| 21 | `consciousness/iit_phi.py` | 184 | `print(f"System Phi: {result.phi}")` | `logger.info("phi_computed", phi=result.phi)` |
| 22 | `llm/providers/base.py` | 160 | `print(chunk, end="")` | Needs streaming logger or yield pattern |
| 23 | `infrastructure/nats/memory_sync.py` | 242 | `print(f"Updated: {update}")` | `logger.info("memory_synced", update=update)` |

---

## P6 — Concurrency: Batch sequential awaits ⚡ 15 min

**Files**: `echo/agent.py`, `perceiver_plus/agent.py`, plus any other file with sequential independent awaits

**Action**: Find `await ... await ... await` sequences where calls are independent and batch with `asyncio.gather()`.

**Check pattern**: `grep -n 'await.*\n.*await.*\n.*await' **/*.py` and manually inspect each for independence.

---

## P7 — Bundle: Vite code splitting 📦 5 min

**File**: `swarm-dashboard/vite.config.ts`

**Action**: Add `build.rollupOptions.output.manualChunks` to split vendor deps from app code.

```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom', 'zustand', 'axios'],
      },
    },
  },
},
```

**Impact**: Smaller initial bundle, better caching of vendor code.

---

## Execution Order

```
P0 (5 min) → P1 (10 min) → P4 (5 min) → P2 (20 min) → P5 (10 min) → P7 (5 min) → P6 (15 min) → P3 (30 min)
```

P0-P1-P4-P2-P5-P7 first (55 min total) — these are mechanical, well-understood changes.
P6 next — requires manual inspection of await chains.
P3 last — requires the most code reading and judgment.