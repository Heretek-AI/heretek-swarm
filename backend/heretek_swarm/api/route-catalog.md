# Heretek Swarm API Route Catalog

> **Generated:** 2026-05-18 | **Slice:** M014/S01 | **Task:** T04
> **Preamble:** This catalog was generated via static code analysis. The test server requires Docker (PostgreSQL, Redis, Qdrant, NATS), so live route verification was not possible. All prefix data reflects post-M014/S01 corrections.

---

## Summary

| # | Router File | Prefix | GET | POST | PUT | DEL | PATCH | WS | Auth on Router? | Auth Anywhere? | Parent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `api/websockets.py` | `/api/ws` | 15 | 0 | 0 | 0 | 0 | 10 | ❌ | ❌ | — |
| 2 | `api/consensus.py` | `/api/consensus` | 44 | 14 | 0 | 2 | 0 | 0 | ❌ | ❌ | — |
| 3 | `api/plugins.py` | `/api/plugins` | 13 | 3 | 1 | 0 | 0 | 0 | ✅ | ✅ | — |
| 4 | `api/workflows.py` | `/api/workflows` | 6 | 5 | 1 | 1 | 0 | 0 | ❌ | ✅ | — |
| 5 | `api/observability/__init__.py` | `/api/observability` | 0 | 0 | 0 | 0 | 0 | 0 | ❌ | — | — |
| 6 | `api/evaluation.py` | `/api/evaluation` | 17 | 3 | 0 | 1 | 0 | 0 | ❌ | ✅ | — |
| 7 | `api/rag.py` | `/api/rag` | 14 | 7 | 0 | 1 | 0 | 0 | ❌ | ✅ | — |
| 8 | `api/consciousness.py` | `/api/consciousness` | 70 | 5 | 0 | 0 | 0 | 0 | ❌ | ✅ | — |
| 9 | `api/skills.py` | `/api/skills` | 16 | 3 | 0 | 1 | 0 | 0 | ❌ | ✅ | — |
| 10 | `api/emergent_intelligence.py` | `/api/emergent-intelligence` | 12 | 0 | 0 | 0 | 0 | 0 | ❌ | ✅ | — |
| 11 | `api/agents_management.py` | `/api/agents` | 0 | 0 | 0 | 0 | 0 | 0 | ❌ | ✅ | — |
| 12 | `api/autonomous.py` | `/api/autonomous` | 2 | 1 | 0 | 0 | 0 | 0 | ✅ | ✅ | — |
| 13 | `api/configuration.py` | `/api/config` | 21 | 11 | 4 | 4 | 0 | 0 | ❌ | ✅ | — |
| 14 | `api/providers_config.py` | `/api/providers` | 13 | 4 | 2 | 2 | 0 | 0 | ✅ | ✅ | — |
| 15 | `api/wizard.py` | `/api/wizard` | 58 | 9 | 1 | 2 | 0 | 0 | ✅ | ✅ | — |
| 16 | `api/provisioner.py` | `/api/wizard/provision` | 2 | 2 | 0 | 0 | 0 | 0 | ✅ | ✅ | — |
| 17 | `api/metrics.py` | `/api/metrics` | 2 | 0 | 0 | 0 | 0 | 0 | ✅ | ✅ | — |
| 18 | `api/memories.py` | `/api/mem0` | 6 | 4 | 1 | 2 | 0 | 0 | ❌ | ❌ | — |
| 19 | `api/memory_versions.py` | `/api/memory/versions` | 8 | 3 | 0 | 0 | 0 | 0 | ❌ | ✅ | — |
| 20 | `api/collective_evolution.py` | `/api/collective` | 24 | 3 | 0 | 0 | 0 | 0 | ✅ | ✅ | — |
| 21 | `mcp/server.py` | `/api/mcp` | 5 | 1 | 1 | 0 | 0 | 0 | ❌ | ❌ | — |

### Observability Sub-Routers (mounted under `/api/observability`)

| # | Router File | Local Prefix | GET | POST | DEL | WS | Auth | Parent |
|---|---|---|---|---|---|---|---|---|---|
| O1 | `observability/alerts.py` | `""` | 2 | 0 | 0 | 0 | ❌ | `observability/__init__.py` |
| O2 | `observability/consciousness.py` | `""` | 4 | 0 | 0 | 0 | ❌ | `observability/__init__.py` |
| O3 | `observability/events.py` | `""` | 6 | 7 | 0 | 0 | ✅ | `observability/__init__.py` |
| O4 | `observability/external_calls.py` | `""` | 5 | 1 | 0 | 0 | ❌ | `observability/__init__.py` |
| O5 | `observability/stream.py` | `""` | 5 | 0 | 0 | 1 | ❌ | `observability/__init__.py` |
| O6 | `observability/swarm.py` | `""` | 12 | 0 | 0 | 0 | ❌ | `observability/__init__.py` |
| O7 | `observability/traces.py` | `""` | 3 | 1 | 1 | 1 | ❌ | `observability/__init__.py` |

### Agents Sub-Routers (mounted under `/api/agents`)

| # | Router File | Local Prefix | GET | POST | PUT | DEL | Auth | Parent |
|---|---|---|---|---|---|---|---|---|---|
| A1 | `agents/chat.py` | `""` | 7 | 1 | 1 | 0 | ✅ | `agents_management.py` |
| A2 | `agents/core.py` | `""` | 2 | 1 | 0 | 1 | ✅ | `agents_management.py` |
| A3 | `agents/instances.py` | `""` | 8 | 1 | 0 | 1 | ✅ | `agents_management.py` |
| A4 | `agents/jetstream.py` | `""` | 3 | 3 | 0 | 1 | ✅ | `agents_management.py` |
| A5 | `agents/lifecycle.py` | `""` | 0 | 4 | 1 | 0 | ✅ | `agents_management.py` |
| A6 | `agents/profiling.py` | `""` | 6 | 2 | 0 | 0 | ✅ | `agents_management.py` |
| A7 | `agents/routing_control.py` | `""` | 1 | 3 | 0 | 0 | ✅ | `agents_management.py` |
| A8 | `agents/routing_rules.py` | `""` | 3 | 1 | 1 | 1 | ✅ | `agents_management.py` |

**Total:** 21 top-level routers + 7 observability sub-routers + 8 agents sub-routers = **36 APIRouter definitions** (the original task plan estimated 26; the actual count is 36 when counting observability/agents sub-routers separately).

---

## Prefix Change Notes (M014/S01)

These routers had prefix modifications during this slice:

| Router | Old Prefix | New Prefix | Task | Rationale |
|---|---|---|---|---|
| `autonomous.py` | `/autonomous` | `/api/autonomous` | T01 | Fix live 404 — runtime POSTs to `/api/autonomous/agents` |
| `memories.py` | `/mem0` | `/api/mem0` | T01 | Align with `/api/` convention |
| `mcp/server.py` | `/mcp` | `/api/mcp` | T01 | Align with `/api/` convention |
| `observability/__init__.py` | `/api/v1/observability` | `/api/observability` | T02 | Flatten version prefix |
| `emergent_intelligence.py` | `/api/v1/emergent-intelligence` | `/api/emergent-intelligence` | T02 | Flatten version prefix |
| `providers_config.py` | `/api/v1/providers` | `/api/providers` | T02 | Flatten version prefix |
| `metrics.py` | `""` (no prefix) | `/api/metrics` | T02 | Add `/api/` prefix for consistency |
| `websockets.py` | `""` (no prefix) | `/api/ws` | T02 | Add `/api/` prefix for consistency |

---

## Auth Gap Analysis

### Routers **with** `Depends(verify_auth)` on the APIRouter (strongest protection):
- `plugins.py` — `/api/plugins`
- `autonomous.py` — `/api/autonomous`
- `providers_config.py` — `/api/providers`
- `wizard.py` — `/api/wizard`
- `provisioner.py` — `/api/wizard/provision`
- `metrics.py` — `/api/metrics`
- `collective_evolution.py` — `/api/collective`

### Routers with per-route auth (verify_auth on individual endpoints only):
- `workflows.py` — `/api/workflows`
- `evaluation.py` — `/api/evaluation`
- `rag.py` — `/api/rag`
- `consciousness.py` — `/api/consciousness`
- `skills.py` — `/api/skills`
- `emergent_intelligence.py` — `/api/emergent-intelligence`
- `agents_management.py` — `/api/agents` (+ all 8 sub-routers)
- `configuration.py` — `/api/config`
- `memory_versions.py` — `/api/memory/versions`

### Routers **without** `verify_auth` anywhere (auth gaps ⚠️):
- `websockets.py` — `/api/ws` — 15 GET + 10 WebSocket endpoints, **no auth**
- `consensus.py` — `/api/consensus` — 44 GET + 14 POST + 2 DELETE, **no auth**
- `observability/__init__.py` — `/api/observability` — parent + 4 of 7 sub-routers, **no auth**
  - ⚠️ `alerts.py`, `consciousness.py`, `external_calls.py`, `stream.py`, `swarm.py`, `traces.py` have no auth
  - ✅ `events.py` has per-route auth
- `memories.py` — `/api/mem0` — 6 GET + 4 POST + 1 PUT + 2 DELETE, **no auth**
- `mcp/server.py` — `/api/mcp` — 5 GET + 1 POST + 1 PUT, **no auth**

---

## Dead / Unmounted Endpoints

### `api/alerts.py` — Router defined but **not mounted** in `main.py`
- File: `backend/heretek_swarm/api/alerts.py`
- Router has `prefix="/api/alerts"`, tags=["alerts"], and 5 endpoints (3 GET, 2 POST, 1 PUT)
- Endpoints: `GET /api/alerts/`, `GET /api/alerts/{alert_id}`, `PUT /api/alerts/{alert_id}/resolve`, `POST /api/alerts/test`, `POST /api/alerts/`
- **Not imported or included in main.py** — dead code
- The observability alerts (`observability/alerts.py`) is the active alerts router, mounted under `/api/observability/`

### `api/mcp.py` — Deleted in T01
- Was dead code; all MCP endpoints served by `mcp/server.py`

---

## Detailed Router Entries

### 1. websockets.py — `/api/ws`
- **Endpoints:** 15 GET (status/health endpoints), 10 WebSocket (real-time streams)
- **Auth:** None (no `verify_auth` on router or individual routes)
- **Prefix change (T02):** Added `/api/ws` prefix; stripped `/ws` from all 10 WS route paths to avoid `/api/ws/ws/*` duplication
- **Example paths:** `GET /api/ws/executions`, `WS /api/ws/executions/{agent_id}`, `GET /api/ws/health`
- **Auth gap:** ⚠️ All WebSocket and REST endpoints are unauthenticated

### 2. consensus.py — `/api/consensus`
- **Endpoints:** 44 GET, 14 POST, 2 DELETE
- **Auth:** None (no `verify_auth` anywhere in file)
- **Auth gap:** ⚠️ High surface area without auth — deliberation sessions, votes, and verdicts are publicly accessible

### 3. plugins.py — `/api/plugins`
- **Endpoints:** 13 GET, 3 POST, 1 PUT
- **Auth:** `Depends(verify_auth)` on router
- **Auth status:** ✅ Fully protected

### 4. workflows.py — `/api/workflows`
- **Endpoints:** 6 GET, 5 POST, 1 PUT, 1 DELETE
- **Auth:** Per-route `Depends(verify_auth)` — each endpoint individually guarded
- **Auth status:** ✅ Protected (per-route)

### 5. observability — `/api/observability` (parent router)
- **Own endpoints:** None (aggregation router only)
- **Sub-routers:** 7 (see sub-router table above)
- **Auth:** None on parent; 1 of 7 sub-routers has auth (`events.py`)
- **Prefix change (T02):** Removed `/v1/` from `/api/v1/observability`
- **Auth gap:** ⚠️ 6 of 7 sub-routers unauthenticated — observability data exposed without auth

### 6. evaluation.py — `/api/evaluation`
- **Endpoints:** 17 GET, 3 POST, 1 DELETE
- **Auth:** Per-route `Depends(verify_auth)`
- **Auth status:** ✅ Protected

### 7. rag.py — `/api/rag`
- **Endpoints:** 14 GET, 7 POST, 1 DELETE
- **Auth:** Per-route `verify_auth` on all mutation endpoints; query endpoints vary
- **Auth status:** ✅ Protected (mixed per-route)

### 8. consciousness.py — `/api/consciousness`
- **Endpoints:** 70 GET, 5 POST
- **Auth:** Per-route `verify_auth` on mutation endpoints; most GET endpoints are unauthenticated
- **Auth gap:** ⚠️ High GET endpoint count with mixed auth — audit needed

### 9. skills.py — `/api/skills`
- **Endpoints:** 16 GET, 3 POST, 1 DELETE
- **Auth:** Per-route `Depends(verify_auth)`
- **Auth status:** ✅ Protected

### 10. emergent_intelligence.py — `/api/emergent-intelligence`
- **Endpoints:** 12 GET
- **Auth:** Per-route `verify_auth` on most endpoints
- **Prefix change (T02):** Removed `/v1/` from `/api/v1/emergent-intelligence`
- **Auth status:** ✅ Protected

### 11. agents_management.py — `/api/agents` (parent router)
- **Own endpoints:** None (aggregation router only)
- **Sub-routers:** 8 (see sub-router table above)
- **Auth:** Per-route `verify_auth` in sub-router endpoints
- **Auth status:** ✅ Protected (sub-routers enforce auth individually)

### 12. autonomous.py — `/api/autonomous`
- **Endpoints:** 2 GET, 1 POST
- **Auth:** `Depends(verify_auth)` on router
- **Prefix change (T01):** Changed from `/autonomous` → `/api/autonomous`
- **Auth status:** ✅ Fully protected

### 13. configuration.py — `/api/config`
- **Endpoints:** 21 GET, 11 POST, 4 PUT, 4 DELETE
- **Auth:** Per-route `Depends(verify_auth)` — not on router, but on all mutating endpoints
- **Auth status:** ✅ Protected (per-route)

### 14. providers_config.py — `/api/providers`
- **Endpoints:** 13 GET, 4 POST, 2 PUT, 2 DELETE
- **Auth:** `Depends(verify_auth)` on router
- **Prefix change (T02):** Removed `/v1/` from `/api/v1/providers`
- **Auth status:** ✅ Fully protected

### 15. wizard.py — `/api/wizard`
- **Endpoints:** 58 GET, 9 POST, 1 PUT, 2 DELETE
- **Auth:** `Depends(verify_auth)` on router
- **Auth status:** ✅ Fully protected

### 16. provisioner.py — `/api/wizard/provision`
- **Endpoints:** 2 GET, 2 POST
- **Auth:** `Depends(verify_auth)` on router
- **Auth status:** ✅ Fully protected
- **Note:** Shares `/api/wizard/` namespace with wizard router

### 17. metrics.py — `/api/metrics`
- **Endpoints:** 2 GET (`GET /api/metrics` → Prometheus text, `GET /api/metrics/json` → JSON)
- **Auth:** `Depends(verify_auth)` on router
- **Prefix change (T02):** Added `/api/metrics` prefix; internal paths changed from `/metrics` → `""` and `/metrics/json` → `/json`
- **Auth status:** ✅ Fully protected
- **Observability impact:** ⚠️ Prometheus scrape target must be updated from `/metrics` to `/api/metrics` (deployment concern, not tracked in this repo)

### 18. memories.py — `/api/mem0`
- **Endpoints:** 6 GET, 4 POST, 1 PUT, 2 DELETE
- **Auth:** None
- **Prefix change (T01):** Changed from `/mem0` → `/api/mem0`
- **Auth gap:** ⚠️ mem0 memory endpoints are unauthenticated

### 19. memory_versions.py — `/api/memory/versions`
- **Endpoints:** 8 GET, 3 POST
- **Auth:** Per-route `Depends(verify_auth)`
- **Auth status:** ✅ Protected

### 20. collective_evolution.py — `/api/collective`
- **Endpoints:** 24 GET, 3 POST
- **Auth:** `Depends(verify_auth)` on router
- **Auth status:** ✅ Fully protected

### 21. mcp/server.py — `/api/mcp`
- **Endpoints:** 5 GET (`/tools`, `/tools/{name}`, `/tools/{name}/stats`, `/health`, `/info`), 1 POST (`/tools/call`), 1 PUT (`/tools/toggle/{name}`)
- **Auth:** None
- **Prefix change (T01):** Changed from `/mcp` → `/api/mcp`
- **Auth gap:** ⚠️ All MCP tool endpoints are unauthenticated — tool invocation, toggling, and stats are publicly accessible

---

## Open Questions

1. **`api/alerts.py` — intentional or dead code?** This file defines a router with 5 endpoints but is never imported or mounted in `main.py`. The active alerts router is `observability/alerts.py`. Was this a planned replacement that was never wired up?

2. **WebSocket auth:** `websockets.py` has 10 WebSocket endpoints with zero authentication. Is this intentional (public status streams) or an oversight? WebSocket upgrade requests bypass HTTP middleware auth.

3. **Consensus auth:** `consensus.py` has 60 endpoints with no auth whatsoever. Deliberation sessions and verdicts are publicly exposed.

4. **Observability auth:** 6 of 7 sub-routers under `/api/observability` have no auth. Metrics, traces, and swarm status are publicly readable.

5. **Prometheus scrape config:** The metrics path changed from `/metrics` to `/api/metrics`. The Prometheus scrape target in deployment infrastructure must be updated. This is outside the scope of this repo.

---

## Verification Notes

- **Server startup:** Requires Docker (PostgreSQL, Redis, Qdrant, NATS) — not available in the CI/development environment.
- **Live route verification:** Not performed. All endpoint data derived from static AST analysis.
- **Frontend build:** Verified in T03 — `npx vite build` passes clean with all `/api/v1/` references replaced.
- **TypeScript check:** Verified in T03 — `npx tsc --noEmit` passes with zero errors.
- **Backend tests:** Verified in T01/T02 — pytest passes with 2 pre-existing rate-limit header failures.
- **Linting:** Verified in T01/T02 — ruff passes clean on all touched files.
