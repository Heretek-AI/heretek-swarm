---
name: testing-e2e-deployment
description: End-to-end test the Heretek Swarm Docker stack — first-time deploy, the dashboard setup wizard via the nginx proxy, and the multi-agent LLM deliberation. Use when verifying deployment, frontend↔backend communication, migrations, or LLM routing changes.
---

# E2E testing: first-time deploy + frontend↔backend communication

## Stack
`docker compose up` brings up 6 services: postgres, redis, qdrant, nats, FastAPI `api` (`:8000`), and the React dashboard served by nginx (`:3000`). nginx proxies `/api/*` and `/ws` to `api:8000`.

## Ports — important
- **`:3000` = dashboard + nginx proxy (the real production path).** Enter `http://localhost:3000` in the wizard so calls traverse nginx, exactly like a deployed user.
- **`:8000` = API direct (cross-origin from the browser).** Only use for harness/curl checks.
- A connection/port mismatch shows the browser error **"Failed to fetch"**; an HTTP 500 means the request reached the API and the API itself errored (e.g. a missing table) — these are different failure classes, don't conflate them.

## First-time deploy = fresh volumes
To simulate a true first-time deploy, wipe volumes first: `docker compose down -v && docker compose build && docker compose up -d`. Then confirm migrations applied: `docker compose logs api | grep -i 'migration(s) applied'` should say `11 migration(s) applied successfully` (count grows as migrations are added). `scripts/run_migrations.py` runs ALL migrations in ONE transaction, so a single failure rolls back everything and leaves the DB with **zero tables** — and the entrypoint logs `Migration runner failed ... Continuing anyway`, masking it. If `/api/config` returns 500 with `relation "..." does not exist`, suspect an aborted migration run, not the proxy.

## Transport harness (fast, shell-only sanity check)
`python3 scripts/verify_integration.py` → expect **8/8 PASS** (backend health/liveness, auth 401 w/o token + 200 w/ Bearer, CORS preflight, dashboard served, dashboard→API proxy `/api/health`, and proxy keeps redirects same-origin on `/api/agents`). Run this before the UI test to localize failures.

## Test A — setup wizard via proxy (record this)
1. Open `http://localhost:3000`. If mid-wizard from a prior run, click **Reset** or reload to start at Welcome.
2. Get Started → API endpoint: ensure `http://localhost:3000` → Continue.
3. API key: paste the Bearer key from `.env` (`HERETEK_API_KEY`) → **Test API Key**.
   - Expect green **"API key is valid!"** (this is `GET /api/config` 200 through the proxy).
4. Continue → Connection Verification: expect green **"Core connections verified"** (REST API + Postgres + Redis healthy). **WebSocket "Failed" is expected/optional** in this setup.
5. Continue → Agent Health: on a fresh deploy expect the benign **"○ No Agents / No agent instances found"** — NOT a red **"Failed to fetch"** (that red error is the cross-origin-redirect bug; nginx must use `proxy_set_header Host $http_host;` not `$host` so the port survives FastAPI's 307 trailing-slash redirect).
6. Complete Setup → main dashboard renders (nav + "System Healthy").

## Test B — multi-agent LLM deliberation
`POST /api/prompt` spins up 5 ephemeral agents (steward, alpha, beta, charlie, historian), so it works even with 0 agents deployed (unlike the dashboard Chat page, which hits `/api/agents/{id}/chat` and needs a deployed agent).

```bash
K=$(grep '^HERETEK_API_KEY=' .env | cut -d= -f2)
curl -s -X POST http://localhost:3000/api/prompt \
  -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
  -d '{"prompt":"Name one concrete risk of deploying to production on a Friday afternoon."}'
```
Expect HTTP 200 (~40-50s of real calls), `llm_available=true`, 5 distinct, on-topic `opinions[].reasoning` (>100 chars each), `consensus_score` ~0.8. If `llm_available=false` or every reasoning is a template stem ("Stewarding '", "Alpha perspective on '", ...), the LLM isn't being called — check `_ensure_provider_prefix` in `backend/heretek_swarm/agents/agent_factory.py` (bare model names like `MiniMax-M2.7` must be prefixed to `openai/...` for litellm).

### Swagger /docs is blank in restricted sandboxes
FastAPI's `/docs` loads Swagger UI JS/CSS from `cdn.jsdelivr.net`. If outbound CDN is blocked, `/docs` renders blank — this is an environment limit, not an app bug (`/openapi.json` still returns 200). Workaround: test `/api/prompt` via curl (above) with the Bearer key (the intended auth path) instead of the Swagger form.

## Known pre-existing issue (not a deploy/migration bug)
During the api-key step a red toast **"API Error — Authentication failed"** may briefly appear. It's a background `GET /api/providers/llm` poll firing before the key is attached to the axios client (returns 200 *with* key, 401 *without*). The wizard's own `/api/config` check still succeeds. Treat as a benign frontend race; a fix would gate that poll on the key being set. It might be fixed in future — re-check whether the toast still appears.

## LLM config (.env, gitignored)
`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL` drive the default LLM. Verify the key is live before Test B: `curl -s -X POST "$OPENAI_BASE_URL/chat/completions" -H "Authorization: Bearer $OPENAI_API_KEY" -d '{"model":"'$LLM_MODEL'","messages":[{"role":"user","content":"ping"}],"max_tokens":10}'` should return 200, not 401 (bad key) or 429 `insufficient_balance` (unfunded account).

## Devin Secrets Needed
- None stored as Devin secrets currently. The LLM key and `HERETEK_API_KEY` live in the gitignored `.env` on the box. If persisting across sessions, save the LLM key as an org/user secret (e.g. `HERETEK_LLM_API_KEY`) and the API auth key (e.g. `HERETEK_API_KEY`).
