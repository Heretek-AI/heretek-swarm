# S03: Live E2E & Embedding Edge Cases

**Goal:** Prove a live prompt produces a real swarm deliberation response and the dashboard serves correctly, with graceful handling when embedding server is unavailable
**Demo:** `curl -X POST http://localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}'` returns 200 with JSON deliberation output; browser at localhost:3000 shows the swarm dashboard; embedding-dependent features fail gracefully when server is down

## Must-Haves

- 1. curl -X POST localhost:8000/v1/prompt -d '{"prompt":"Hello swarm"}' returns 200 with structured JSON response
- 2. Response contains agent deliberation output (opinions, votes, synthesis)
- 3. Dashboard at http://localhost:3000 serves the React app
- 4. Dashboard can connect to the API (no CORS/proxy errors)
- 5. When embedding server is unavailable, non-embedding flows still work
- 6. No unhandled exceptions in api logs during prompt flow

## Proof Level

- This slice proves: Verified via curl, browser, and docker compose logs

## Integration Closure

Full stack: LLM → API → NATS → agents → PostgreSQL → Redis → Qdrant; dashboard serves and connects

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [ ] **T01: Verify live prompt → swarm response** `est:30m`
  Verify the prompt endpoint works. Send a POST to localhost:8000/v1/prompt with a test prompt. Check that the response is structured JSON containing agent deliberation output (opinions, votes, synthesis). If the LLM endpoint is unreachable, diagnose and fix (check .env OPENAI_API_KEY value, check MiniMax provider config).
  - Verify: curl -sf -X POST http://localhost:8000/v1/prompt -H 'Content-Type: application/json' -d '{"prompt":"Hello swarm"}' | python -m json.tool | head -20

- [ ] **T02: Verify dashboard serves and connects** `est:15m`
  Verify the swarm dashboard at http://localhost:3000 serves correctly. If it doesn't load, check dashboard container logs and nginx config. Check that VITE_API_URL is correct (api:8000 or host-level URL). Fix any nginx proxy misconfiguration.
  - Verify: curl -sf http://localhost:3000 | head -5

- [ ] **T03: Handle missing embedding server gracefully** `est:30m`
  Verify the system handles embedding server absence gracefully. Check that non-embedding API flows and agent deliberation complete even when embedding endpoint is unreachable. If embedding failures cause crashes, add graceful fallback handling.
  - Verify: docker compose logs api | grep -i 'embedding\|embed' | tail -10
