# GOAL: Systematically implement, fix, test, and validate every finding in PLAN.md

You are a senior engineer operating on the **Heretek-Swarm** project at `/home/john/Desktop/heretek-swarm/`. Your mission is to walk through every P0 (and as many P1/P2 as time permits) finding in `/home/john/Desktop/heretek-swarm/PLAN.md`, implement the surgical fix, validate it against a **clean Docker rebuild**, and report concrete pass/fail evidence. You are not done until the swarm passes the cold-start validation in PLAN.md §4.5 with all P0s closed.

---

## 0. Pre-Flight (do this BEFORE any other action)

### 0.1 Load skills (use the `skill` tool)
Load these in parallel:
- `testing-e2e-deployment` — **mandatory**; this is the canonical Docker cold-start procedure
- `python-testing-patterns` — for writing/updating pytest tests
- `code-review-excellence` — for self-review of each diff
- `fastapi-templates` — for the G-04 JWT refactor and Pydantic schemas
- `error-handling-patterns` — for G-01 sandbox error contracts
- `secrets-management` — for G-05 mTLS cert provisioning
- `dispatching-parallel-agents` — for running independent verifications concurrently
- `verification-before-completion` — block every "done" claim until evidence exists

### 0.2 Read the source of truth (in this order)
1. `/home/john/Desktop/heretek-swarm/PRIME_DIRECTIVE.md` — immutable vision
2. `/home/john/Desktop/heretek-swarm/PLAN.md` — your task list
3. `/home/john/Desktop/heretek-swarm/AGENTS.md` and `/home/john/Desktop/heretek-swarm/.github/copilot-instructions.md` — project conventions
4. `/home/john/Desktop/heretek-swarm/.agents/skills/testing-e2e-deployment/SKILL.md` — E2E test workflow (already loaded as a skill but re-read for context)

### 0.3 Read the run log
Check `/home/john/Desktop/heretek-swarm/M030-RUN-LOG.md` (created by prior runs). If it exists, resume from the last uncompleted gap. If it does not exist, create it now with header `## M030 Run 1 — [today's date]`.

### 0.4 Verify the environment
```bash
cd /home/john/Desktop/heretek-swarm
ls -la .env docker-compose.yml scripts/verify_integration.py 2>&1
docker --version && docker compose version
grep -E "^(HERETEK_API_KEY|OPENAI_API_KEY|OPENAI_BASE_URL|LLM_MODEL|EMBEDDING_PROVIDER)=" .env | sed 's/=.*/=<set>/'
```
If `.env` is missing, copy from `.env.example` and warn the user. If Docker is not running, **stop** and tell the user.

### 0.5 Set up the todo list
Use `todowrite` with one item per gap, in priority order. Mark the first P0 as `in_progress` and stop the pre-flight.

---

## 1. Operating Constraints (HARD BLOCKS)

These are non-negotiable. Violating any of them invalidates the run.

| # | Rule | Why |
|---|---|---|
| 1 | **No `as any`, `@ts-ignore`, `@ts-expect-error`** | Type safety is a Hard Block in this harness |
| 2 | **No commit without explicit user request** | Leave changes uncommitted; report what changed |
| 3 | **No test deletion to make CI green** | If a test fails, fix the code, not the test |
| 4 | **No broken code at end of run** | Every change must pass `ruff check backend/`, `mypy backend/heretek_swarm/`, and `pytest tests/ -v` |
| 5 | **No "should pass" claims** | Every verification must produce concrete output: HTTP status codes, test counts, browser console line numbers |
| 6 | **No shotgun debugging** | Change one thing at a time. Keep diffs small and isolated |
| 7 | **No skipping the cold-start rebuild** | Every fix is validated against a clean Docker build (see §3) |
| 8 | **No leaving the swarm in a non-running state** without explicit explanation | Every session ends with `docker compose up -d` and healthy containers, OR a clear "stopped because X" status |
| 9 | **No ad-hoc modifications to PLAN.md** | If you discover a NEW gap, write it to `/home/john/Desktop/heretek-swarm/.gsd/audit/discovered-during-M030.md` and continue with the current fix. Do not chase rabbits. |
| 10 | **No parallelization of fixes that touch the same file** | E.g., G-04 and G-05 both touch `gateway/auth.py` — do them sequentially |
| 11 | **No silently swallowing exceptions** | Every `except:` must log and either re-raise or return a typed error |
| 12 | **No hardcoded secrets in source** | Even dev-mode secrets go in `.env` (gitignored) |

---

## 2. The Per-Fix Procedure (Repeat for Each Gap)

### Step 1 — Read the gap
Open PLAN.md §2.2/2.3/2.4 and read the row: file:line, current state, required state, prime directive violation. Then read the **actual file** at that line — PLAN.md was written on 2026-06-01 and the file:line may have drifted. If it has, update PLAN.md (this is a permitted modification — file:line staleness is not a "code change").

### Step 2 — Plan the change
Update `todowrite` with sub-tasks for THIS fix:
- [ ] Identify all files to touch (read 1-2 surrounding lines of context)
- [ ] Identify the test file(s) that need updating (if message contract changes)
- [ ] Write the implementation
- [ ] Write the unit test
- [ ] Run local sanity (ruff, mypy, pytest, tsc)
- [ ] Clean rebuild Docker
- [ ] Run integration test
- [ ] Run targeted validation for THIS fix
- [ ] Run browser validation (if dashboard touched)
- [ ] Update PLAN.md (mark `[x]`, add to fix log)
- [ ] Append to M030-RUN-LOG.md

For multi-file changes, fire **parallel explore agents** (one per file) to gather full context, then sequence your edits.

### Step 3 — Implement
- Make the surgical change. Do NOT refactor adjacent code.
- If you discover a NEW gap while implementing, write it to `.gsd/audit/discovered-during-M030.md` and continue with the current fix.
- Use `lsp_diagnostics` after every file edit to catch type errors immediately.

### Step 4 — Local sanity (before Docker)
```bash
cd /home/john/Desktop/heretek-swarm
ruff check backend/                                  # 0 errors
mypy backend/heretek_swarm/                          # 0 errors
pytest tests/ -v -k "<relevant to this fix>"        # all green
cd swarm-dashboard && npm test                      # all green (if frontend touched)
npx tsc --noEmit                                     # 0 errors (if frontend touched)
```
Any failure here is a stop signal. Fix the code, do not silence the linter.

### Step 5 — Clean rebuild Docker (MANDATORY)
```bash
cd /home/john/Desktop/heretek-swarm
docker compose down -v                               # wipe volumes
docker compose build --no-cache                      # clean image build
docker compose up -d
# Wait for API health
for i in $(seq 1 60); do
  docker inspect heretek-swarm-api-1 --format '{{.State.Health.Status}}' 2>/dev/null | grep -q healthy && break
  sleep 2
done
# Verify all 6 containers up
docker compose ps --format json | jq -r '.[] | "\(.Name): \(.Health)"'
```
Cold start must complete in < 60s. If it doesn't, that's a stop signal — investigate before proceeding.

### Step 6 — Integration test (the transport harness)
```bash
cd /home/john/Desktop/heretek-swarm
python3 scripts/verify_integration.py
```
Expect **8/8 PASS**. The harness covers: backend health, auth 401/200, CORS preflight, dashboard served, dashboard→API proxy `/api/health`, and proxy keeps redirects same-origin on `/api/agents`.

### Step 7 — Targeted validation for THIS fix
Per the verification step in PLAN.md §4.1 for this gap. Examples:

**G-01 (sandbox):**
```bash
K=$(grep '^HERETEK_API_KEY=' .env | cut -d= -f2)
curl -s -X POST http://localhost:3000/api/agents/coder/chat \
  -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
  -d '{"prompt":"Run this code: import os; os.system(\"rm -rf /\")"}' | jq .
```
Expect 422 + audit log entry. If 200, the fix failed — diagnose and re-fix.

**G-02 (structured ruling):**
```bash
curl -s -X POST http://localhost:3000/api/tribunal/test-ruling \
  -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
  -d '{"anomaly":"novel pattern X","triad_outputs":{"alpha":"...","beta":"...","charlie":"..."}}' | jq .
```
Expect `{"verdict":"emergent|threat|inconclusive","confidence":0.85}`. Not a string match.

**G-03 (F-010):** Browser validation only — see Step 8.

**G-04 (JWT scope):**
```bash
TOKEN_NO_SCOPE=$(python3 -c "import jwt,time; print(jwt.encode({'sub':'tester','iat':int(time.time()),'exp':int(time.time())+3600}, 'secret', algorithm='HS256'))")
curl -s -i -H "Authorization: Bearer $TOKEN_NO_SCOPE" http://localhost:3000/api/agents/steward | head -1
```
Expect HTTP/1.1 403 (or 401, depending on whether missing scope vs missing token is the closer error).

**G-05 (mTLS):**
```bash
docker compose logs nats | grep -i "client connection.*plaintext"
```
Expect zero matches. NATS should refuse all plaintext clients.

### Step 8 — Browser validation (any change touching the dashboard)
Use the `chrome-devtools_*` MCP tools:
```
chrome-devtools_navigate_page url="http://localhost:3000"
# dwell 60 seconds
chrome-devtools_list_console_messages types=["error","warn"]
chrome-devtools_list_network_requests resourceTypes=["fetch","xhr","websocket"]
```
Assert: 0 console errors, 0 failed network requests, no `WebSocket is closed before the connection is established` warnings.

**For G-03 specifically:** dwell 5 minutes (use `bash sleep 300` between snapshots), then re-check. Expect 0 warnings total. The pre-fix baseline is 74,107 warnings / min.

### Step 9 — Update PLAN.md
In PLAN.md §2.2 (or 2.3/2.4), change the gap row's checkbox to `[x]` (or add a "Fixed" prefix to the row). Then append a one-line entry to a "Fix Log" table at the bottom of PLAN.md:
```
| G-XX | [date] | [file:line] | [1-line description] | 8/8 PASS |
```

### Step 10 — Append to M030-RUN-LOG.md
Same content, plus the **complete diff stats** (`git diff --stat` after the fix) and the **complete validation output** (paste the curl/jq output verbatim).

---

## 3. Order of Operations (Strict — Do NOT Skip Ahead)

P0s first, in this order (chosen to minimize cross-file conflicts):

1. **G-03 (F-010) — WebSocket stabilization** — `swarm-dashboard/src/hooks/useWebSocket.ts:102,126-133`; `useRealTimeAgentUpdates.ts:289-318`. Lowest risk; sets the dashboard test pattern. ~1-2 hours.
2. **G-04 — JWT hardening** — `backend/heretek_swarm/gateway/auth.py:73,87`. Touches only gateway + routers. Enables scope-based testing. ~30 min.
3. **G-02 — Structured Tribunal ruling** — `consensus/tribunal.py` + `runtime/steward_pulse.py:419-428`. No external dependencies. ~2-3 hours.
4. **G-01 — Subprocess sandbox** — `actors/coder/agent.py:302-306`, `actors/examiner/agent.py:589-596`, `actors/perceiver/agent.py:774,799,940` + new `security/sandbox.py`. Most code. ~3-4 hours.
5. **G-05 — mTLS on by default** — `docker-compose.yml:93` + `infrastructure/nats/ca.py`. Requires cert generation. ~1-2 hours.

After all five P0s are closed and validated, continue with P1 if time allows:

6. **G-06 — Tier-grouped dashboard views** — most code, most visible. ~1-2 days.
7. **G-07 — mem0 config source-of-truth** — small. ~2 hours.
8. **G-10 — Consciousness interval tiering** — small but high-impact. ~1 hour.
9. **G-11 — Process decomposition** — large; defer to a dedicated run if scope grows.

P2 gaps (G-12 through G-20) are nice-to-have. Tackle them only if P0s and P1s are green AND the user explicitly requests continuation.

---

## 4. MCP Tools to Use (Per Phase)

| Phase | Tool | What For |
|---|---|---|
| Pre-flight | `bash` | Docker, git, file existence, .env |
| Implementation | `read`, `edit`, `write`, `lsp_diagnostics` | Code changes |
| Sanity | `bash` | ruff, mypy, pytest, npm test, tsc |
| Docker | `bash` | `docker compose down -v && build --no-cache && up -d` |
| API validation | `bash` with `curl` + `jq` | End-to-end curl tests |
| Browser validation | `chrome-devtools_navigate_page`, `chrome-devtools_list_console_messages`, `chrome-devtools_list_network_requests`, `chrome-devtools_take_screenshot` | Dashboard WS, console errors, network failures |
| Performance | `chrome-devtools_performance_start_trace` (only if a fix touches the hot path) | Frame budget, main thread blocking |
| Background research | `task(subagent_type="explore"|"librarian", run_in_background=true, load_skills=[...])` | When you need parallel file reads or external recon |

If a chrome-devtools tool is unavailable in this environment, fall back to `bash` with `curl` against the dashboard and grep the response for HTML markers. Document the fallback in the run log.

---

## 5. Reporting Format (End of Each Run)

Append a section to `/home/john/Desktop/heretek-swarm/M030-RUN-LOG.md`:

```markdown
## M030 Run [N] — [ISO date] — [duration]

### Fixed in this run
- G-XX ([name]): [file:line changed], [1-line description], [concrete validation result]
- ...

### Validation status (clean rebuild, end of run)
- Integration harness: X/8 PASS
- `GET /api/health`: HTTP 200, [services healthy list]
- All 23 per-agent `GET /api/agents/{id}`: HTTP 200
- 6/6 containers healthy
- Browser console: 0 errors, [N] WS warnings over [duration]
- `ruff check backend/`: 0 errors
- `mypy backend/heretek_swarm/`: 0 errors
- `pytest tests/ -v`: X passed, 0 failed

### Diff stats
`git diff --stat` output pasted verbatim

### Discovered gaps (not in PLAN.md)
- [file:line]: [brief description]

### Next run should start with
- [next gap ID, or "validate all prior fixes are still green after cold-start" if P0s are done]
```

If the run is the LAST one (all P0s green, user signals completion), also include a "Run Complete" footer with the cumulative diff and a 1-paragraph summary of what's now different from the original 2026-06-01 verified state.

---

## 6. Stop Conditions (Force a Stop, Don't Push Through)

Stop the run and report to the user if ANY of these are true:

- Integration test drops below 8/8 PASS and you cannot recover in 2 attempts
- Cold-start takes > 120 seconds (something is structurally broken)
- A fix introduces a regression in an unrelated area (a previously-passing test now fails)
- The user's `.env` file is missing `HERETEK_API_KEY` or `OPENAI_API_KEY` and you cannot proceed without them
- Docker daemon is unavailable or `docker compose` errors on startup
- OOM kills (check `docker compose ps` for `Restarting` state > 3 times)
- A security review of your own diff fails (e.g., you accidentally introduced a `subprocess.run(shell=True)` or a hardcoded secret)

When stopping, write a clear status: what was done, what failed, what the next run should pick up. Do NOT mark the run complete; do NOT commit; do NOT silently retry indefinitely.

---

## 7. The "Each Run" Cycle (What "clean build each run" Means)

The user explicitly said "clean build the docker containers/images each run." This means:

> **At the start of every iteration of the per-fix procedure, you do `docker compose down -v && docker compose build --no-cache && docker compose up -d`.**

This catches:
- Image layer caching hiding a real build failure
- Volume state leakage from a prior partial fix
- Stale migrations being applied because the old container was up
- Network/registry drift in `pip`/`npm` resolved versions

Do NOT skip this. Do NOT argue that "this is a small change, the volumes can stay." Every fix gets a clean rebuild. The only exception is when running the same fix's targeted validation multiple times in quick succession to debug a failure — there you can re-`up` without `--no-cache` to save 5-10 minutes per cycle.

---

## 8. Anti-Patterns (Will Result in Run Invalid)

- Committing without explicit user request
- Skipping the clean rebuild ("it's only a small change")
- Claiming success based on theory ("this should pass")
- Deleting failing tests
- Using `as any` to make types compile
- Suppressing linter warnings (`# noqa`, `// @ts-ignore`)
- Modifying files outside PLAN.md's scope without writing to `.gsd/audit/discovered-during-M030.md`
- Leaving the swarm stopped at end of run without explanation
- Re-running without re-reading PLAN.md and M030-RUN-LOG.md (they may have been updated by a prior run)
- Firing parallel agents that touch the same file (race conditions in the workspace)
- Reading 20 files serially when 5 parallel explore agents would do it in 1/5 the time
- Pasting 500 lines of validation output into the run log without summarizing the pass/fail
- Forgetting to mark the gap `[x]` in PLAN.md after a successful fix
- Using `print()` in production code (use `structlog.get_logger()`)

---

## 9. Success Criteria for THIS Goal

This goal is complete when **all** of the following are true:

1. Every P0 row in PLAN.md §2.2 is marked `[x]` (or has a "Fixed" prefix)
2. `python3 scripts/verify_integration.py` returns 8/8 PASS
3. `docker compose down -v && docker compose build --no-cache && docker compose up -d` completes in < 60s with all 6 containers healthy
4. `GET /api/health` returns HTTP 200
5. All 23 per-agent `GET /api/agents/{id}` returns HTTP 200
6. The 5 targeted P0 validation scripts all return their expected output
7. Browser console shows 0 errors after 5 minutes of dwell (F-010 fix verified)
8. `ruff check backend/` reports 0 errors
9. `mypy backend/heretek_swarm/` reports 0 errors
10. `pytest tests/ -v` reports 0 failures
11. `M030-RUN-LOG.md` contains a complete, dated record of every change

When all 11 are true, output: `M030 GOAL COMPLETE — 2026-06-XX` and stop. Do not continue to P1 unless the user explicitly asks.

---

*The thought that never ends.* 🦞
