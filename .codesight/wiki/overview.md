# heretek-swarm — Overview

> **Navigation aid.** This article shows WHERE things live (routes, models, files). Read actual source files before implementing new features or making changes.

**heretek-swarm** is a python project built with fastapi, organized as a microservices repo.

**Services:** `copilotkit-langgraph-template` (`heretek-swarm`), `@heretek-ai/swarm-dashboard` (`swarm-dashboard`)

## Scale

290 API routes · 25 database models · 89 UI components · 389 library files · 12 middleware layers · 121 environment variables

## Subsystems

- **[Auth](./auth.md)** — 5 routes — touches: auth, db, cache
- **[A2a](./a2a.md)** — 2 routes — touches: auth, db, cache, ai
- **[Alerts](./alerts.md)** — 2 routes — touches: auth
- **[Autonomous](./autonomous.md)** — 2 routes — touches: auth, cache
- **[Chat](./chat.md)** — 1 routes — touches: auth, queue
- **[Collective_evolution](./collective_evolution.md)** — 9 routes — touches: auth
- **[Compute_tier](./compute_tier.md)** — 1 routes — touches: auth
- **[Configuration](./configuration.md)** — 28 routes — touches: auth, db, cache, ai
- **[Consciousness](./consciousness.md)** — 27 routes — touches: auth
- **[Consensus](./consensus.md)** — 28 routes — touches: auth, db, cache
- **[Core](./core.md)** — 4 routes — touches: auth, db
- **[Emergent_intelligence](./emergent_intelligence.md)** — 10 routes — touches: auth
- **[Evaluation](./evaluation.md)** — 7 routes — touches: auth, db
- **[Events](./events.md)** — 10 routes — touches: auth, db
- **[External_calls](./external_calls.md)** — 3 routes — touches: auth, db
- **[Health](./health.md)** — 3 routes — touches: auth, db, cache, ai
- **[Historian](./historian.md)** — 1 routes — touches: auth, db, cache, ai
- **[Info](./info.md)** — 1 routes — touches: auth
- **[Instances](./instances.md)** — 10 routes — touches: auth, db
- **[Jetstream](./jetstream.md)** — 7 routes — touches: auth, db, queue
- **[Lifecycle](./lifecycle.md)** — 5 routes — touches: auth
- **[Litellm](./litellm.md)** — 1 routes — touches: auth, db, cache, ai
- **[Memories](./memories.md)** — 9 routes — touches: auth, db
- **[Memory](./memory.md)** — 1 routes — touches: auth, db, cache, ai
- **[Memory_versions](./memory_versions.md)** — 10 routes — touches: auth
- **[Metrics](./metrics.md)** — 1 routes — touches: auth, cache
- **[Perceiver](./perceiver.md)** — 1 routes — touches: auth, queue, upload
- **[Plugins](./plugins.md)** — 7 routes — touches: auth, db
- **[Profiling](./profiling.md)** — 8 routes — touches: auth
- **[Prompt](./prompt.md)** — 1 routes — touches: auth, db, cache, ai
- **[Providers_config](./providers_config.md)** — 10 routes — touches: auth, db, cache, ai
- **[Provisioner](./provisioner.md)** — 1 routes — touches: auth, db, cache
- **[Rag](./rag.md)** — 12 routes — touches: auth, db, upload
- **[Rate_limiting](./rate_limiting.md)** — 1 routes — touches: cache
- **[Routing_control](./routing_control.md)** — 4 routes — touches: auth
- **[Routing_rules](./routing_rules.md)** — 5 routes — touches: auth, db
- **[Skills](./skills.md)** — 8 routes — touches: auth, db
- **[Stream](./stream.md)** — 3 routes — touches: auth
- **[Supervisor](./supervisor.md)** — 4 routes — touches: auth, db, cache, ai
- **[Swarm](./swarm.md)** — 2 routes — touches: auth
- **[Tools](./tools.md)** — 5 routes — touches: auth
- **[Traces](./traces.md)** — 4 routes — touches: auth, db
- **[Wizard](./wizard.md)** — 13 routes — touches: auth, db, cache, ai
- **[Workflows](./workflows.md)** — 9 routes — touches: auth, db, cache
- **[Infra](./infra.md)** — 4 routes — touches: auth, cache, db, ai

**Database:** unknown, 25 models — see [database.md](./database.md)

**UI:** 89 components (react) — see [ui.md](./ui.md)

**Libraries:** 389 files — see [libraries.md](./libraries.md)

## High-Impact Files

Changes to these files have the widest blast radius across the codebase:

- `swarm-dashboard\src\components\UI\Toast.tsx` — imported by **15** files
- `/base.py` — imported by **13** files
- `swarm-dashboard\src\hooks\useWebSocket.ts` — imported by **11** files
- `/db_models.py` — imported by **10** files
- `swarm-dashboard\src\api\client.ts` — imported by **9** files
- `swarm-dashboard\src\components\UI\StatusBadge.tsx` — imported by **9** files

## Required Environment Variables

- `A2A_SECRET_KEY` — `backend\heretek_swarm\gateway\a2a_server.py`
- `ADMIN_API_KEY` — `backend\heretek_swarm\api\memories.py`
- `AGENT_PORT` — `heretek-swarm\serve.py`
- `API_HOST` — `backend\heretek_swarm\runtime\autonomous_runtime_config.py`
- `API_PORT` — `backend\heretek_swarm\runtime\autonomous_runtime_config.py`
- `AUTO_RESTART_ENABLED` — `backend\heretek_swarm\runtime\autonomous_runtime_config.py`
- `CI` — `swarm-dashboard\playwright.config.ts`
- `CONSCIOUSNESS_ENABLED` — `backend\heretek_swarm\runtime\autonomous_runtime_config.py`
- `CONSENSUS_RED_FLAG_THRESHOLD` — `backend\heretek_swarm\api\consensus.py`
- `CONSENSUS_VOTING_TIMEOUT` — `backend\heretek_swarm\api\consensus.py`
- `COPILOTKIT_LICENSE_TOKEN` — `heretek-swarm\.env.example`
- `DB_URL` — `tests\test_secrets.py`
- _...66 more_

---
_Back to [index.md](./index.md) · Generated 2026-05-30_