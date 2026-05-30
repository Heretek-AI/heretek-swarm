# heretek-swarm — Wiki

_Generated 2026-05-30 — re-run `npx codesight --wiki` if the codebase has changed._

Structural map compiled from source code via AST. No LLM — deterministic, 200ms.

> **How to use safely:** These articles tell you WHERE things live and WHAT exists. They do not show full implementation logic. Always read the actual source files before implementing new features or making changes. Never infer how a function works from the wiki alone.

## Articles

- [Overview](./overview.md)
- [Database](./database.md)
- [Auth](./auth.md)
- [A2a](./a2a.md)
- [Alerts](./alerts.md)
- [Autonomous](./autonomous.md)
- [Chat](./chat.md)
- [Collective_evolution](./collective_evolution.md)
- [Compute_tier](./compute_tier.md)
- [Configuration](./configuration.md)
- [Consciousness](./consciousness.md)
- [Consensus](./consensus.md)
- [Core](./core.md)
- [Emergent_intelligence](./emergent_intelligence.md)
- [Evaluation](./evaluation.md)
- [Events](./events.md)
- [External_calls](./external_calls.md)
- [Health](./health.md)
- [Historian](./historian.md)
- [Info](./info.md)
- [Instances](./instances.md)
- [Jetstream](./jetstream.md)
- [Lifecycle](./lifecycle.md)
- [Litellm](./litellm.md)
- [Memories](./memories.md)
- [Memory](./memory.md)
- [Memory_versions](./memory_versions.md)
- [Metrics](./metrics.md)
- [Perceiver](./perceiver.md)
- [Plugins](./plugins.md)
- [Profiling](./profiling.md)
- [Prompt](./prompt.md)
- [Providers_config](./providers_config.md)
- [Provisioner](./provisioner.md)
- [Rag](./rag.md)
- [Rate_limiting](./rate_limiting.md)
- [Routing_control](./routing_control.md)
- [Routing_rules](./routing_rules.md)
- [Skills](./skills.md)
- [Stream](./stream.md)
- [Supervisor](./supervisor.md)
- [Swarm](./swarm.md)
- [Tools](./tools.md)
- [Traces](./traces.md)
- [Wizard](./wizard.md)
- [Workflows](./workflows.md)
- [Infra](./infra.md)
- [Ui](./ui.md)
- [Libraries](./libraries.md)

## Quick Stats

- Routes: **290**
- Models: **25**
- Components: **89**
- Env vars: **78** required, **43** with defaults

## How to Use

- **New session:** read `index.md` (this file) for orientation — WHERE things are
- **Architecture question:** read `overview.md` (~500 tokens)
- **Domain question:** read the relevant article, then **read those source files**
- **Database question:** read `database.md`, then read the actual schema files
- **Library question:** read `libraries.md`, then read the listed source files
- **Before implementing anything:** read the source files listed in the article
- **Full source context:** read `.codesight/CODESIGHT.md`

## What the Wiki Does Not Cover

These exist in your codebase but are **not** reflected in wiki articles:
- Routes registered dynamically at runtime (loops, plugin factories, `app.use(dynamicRouter)`)
- Internal routes from npm packages (e.g. Better Auth's built-in `/api/auth/*` endpoints)
- WebSocket and SSE handlers
- Raw SQL tables not declared through an ORM
- Computed or virtual fields absent from schema declarations
- TypeScript types that are not actual database columns
- Routes marked `[inferred]` were detected via regex and may have lower precision
- gRPC, tRPC, and GraphQL resolvers may be partially captured

When in doubt, search the source. The wiki is a starting point, not a complete inventory.

---
_Last compiled: 2026-05-30 · 50 articles · [codesight](https://github.com/Houseofmvps/codesight)_