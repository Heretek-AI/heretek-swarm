---
id: S03
milestone: M005
status: ready
---

# S03: Convert surviving flat actors to thin re-exports — Context

## Goal

Replace all surviving flat actor files with thin re-exports pointing to canonical subpackage implementations, and standardize the one outlier subpackage (arbiter) to match the majority convention.

## Why this Slice

After M001 collapsed the dual `actors/` directories, 12 subpackages were fully migrated (no flat file remnant), but 14 flat files still carry real implementation code — even though 4 of them (triad agents) already have canonical implementations in `triad/agent.py`, and 1 (explorer) has a full subpackage with the same code reorganized. This creates an inconsistent convention: new contributors can't tell whether an agent lives in a flat file or a subpackage directory. This slice finishes the M001 refactor, making every agent discoverable by its subpackage name.

## Scope

### In Scope

- **Triad agents** (alpha.py, beta.py, charlie.py, steward.py): Replace with re-exports to `heretek_swarm.actors.triad.agent` (canonical `TriadAgent`-based MRO)
- **Explorer** (explorer.py): Replace with re-export to `heretek_swarm.actors.explorer` (subpackage is canonical — verified by diff: same 9 types, same 28 handler methods, plus legacy aliases)
- **6 new subpackages with split pattern** (types.py + agent.py):
  - `actors/historian/` — LRUCache → types.py, HistorianAgent → agent.py
  - `actors/echo/` — 4 enums/dataclasses → types.py, EchoAgent (renamed) → agent.py
  - `actors/coder/` — 6 enums/dataclasses → types.py, CoderAgent → agent.py
  - `actors/catalyst/` — 5 enums/dataclasses → types.py, CatalystAgent → agent.py
  - `actors/perceiver/` — ModalityType → types.py, PerceiverAgent → agent.py
  - `actors/handoff/` — HandoffContext + HandoffResult → types.py (deduplicated), HandoffOrchestrator + strategies → orchestrator.py, handlers → handlers.py
- **2 new subpackages with simple pattern** (agent.py only, no helper types):
  - `actors/metis/` — MetisAgent → agent.py
  - `actors/empath/` — EmpathAgent → agent.py
- **EchoActor → EchoAgent rename**: Update all 5 sites:
  - `actors/echo.py` → `actors/echo/agent.py` (class definition)
  - `actors/echo/__init__.py` (re-export)
  - `actors/__init__.py` (public API surface)
  - `api/main.py` (import + dispatch table)
  - `runtime/main_loop.py` (import + dispatch table)
  - `tests/test_actor_lifecycle.py` (test reference)
  - `docs/actors/README.md` (3 references)
- **Arbiter standardization**: Rename `arbiter/core.py` → `arbiter/agent.py`; switch `arbiter/__init__.py` from relative to absolute imports
- **Flat file re-exports** preserve all public names including private constants (`_HISTORIAN_FILE`) for test compatibility

### Out of Scope

- Writing new code beyond re-exports, `__init__.py` files, and the EchoActor→EchoAgent rename
- Adding new agent types or modifying agent behavior
- Renaming agent classes other than EchoActor→EchoAgent
- Modifying the `actors/__init__.py` re-export surface beyond the EchoActor rename
- Writing integration or E2E tests
- Updating any docs beyond `docs/actors/README.md` (the 3 EchoActor references)
- Handoff classes remain internal — NOT added to `actors/__init__.py` public API

## Constraints

- All 658 existing tests must pass after changes
- No circular imports — verified: zero flat files import from other flat files; base/mixins never import from flat files; re-export pattern adds no new edges
- `actors/__init__.py` public API surface must not change except EchoActor→EchoAgent rename
- Subpackage `__init__.py` files must use absolute imports (majority convention), not relative imports
- `configure_logging()` from S02 must continue to work — unrelated to S03 changes
- `HandoffOrchestrator` does NOT extend `AgentActor` — it's infrastructure code; treat accordingly

## Integration Points

### Consumes

- `heretek_swarm/actors/base/` — AgentActor, ActorMessage, mixins (unchanged imports in subpackage agent.py files)
- `heretek_swarm/actors/mixins/` — all mixin classes (unchanged)
- `heretek_swarm/actors/__init__.py` — public re-export surface (minimal change: EchoActor→EchoAgent)
- `heretek_swarm/actors/triad/agent.py` — canonical TriadAgent, StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
- `heretek_swarm/actors/explorer/` — canonical ExplorerAgent + types + pathfinding mixins
- `heretek_swarm/api/main.py` — lazy per-agent imports + dispatch table
- `heretek_swarm/runtime/main_loop.py` — lazy per-agent imports + dispatch table
- `tests/test_actor_lifecycle.py` — EchoActor test reference
- `tests/test_historian_jsonl.py`, `tests/test_historian_pg.py` — _HISTORIAN_FILE imports
- `docs/actors/README.md` — echo.py / EchoActor references

### Produces

- 8 new subpackage directories each with proper `__init__.py` re-exports
- 10 flat files converted to thin re-export stubs (alpha, beta, charlie, steward, explorer, historian, metis, empath, echo, coder, catalyst, perceiver, handoff, handoff_handlers)
- 1 standardized subpackage (arbiter: core.py→agent.py + absolute imports)
- 1 renamed public symbol (EchoActor→EchoAgent) with all call sites updated

## Open Questions

- None — all 9 architectural decisions resolved during context interview. Verified: import chains (no circular risk), explorer canonicality (diff confirmed), handoff deduplication strategy, extraction granularity per file.

## Subpackage Map (Final)

| Flat file | Lines | Target subpackage | Strategy |
|-----------|-------|-------------------|----------|
| alpha.py | 282 | actors/triad/ | re-export only |
| beta.py | 299 | actors/triad/ | re-export only |
| charlie.py | 393 | actors/triad/ | re-export only |
| steward.py | 840 | actors/triad/ | re-export only |
| explorer.py | 1317 | actors/explorer/ | re-export only |
| historian.py | 1353 | actors/historian/ (new) | types.py + agent.py |
| metis.py | 1110 | actors/metis/ (new) | agent.py only |
| empath.py | 1085 | actors/empath/ (new) | agent.py only |
| echo.py | 749 | actors/echo/ (new) | types.py + agent.py (rename EchoActor→EchoAgent) |
| coder.py | 979 | actors/coder/ (new) | types.py + agent.py |
| catalyst.py | 1135 | actors/catalyst/ (new) | types.py + agent.py |
| perceiver.py | 911 | actors/perceiver/ (new) | types.py + agent.py |
| handoff.py | 599 | actors/handoff/ (new) | orchestrator.py |
| handoff_handlers.py | 243 | actors/handoff/ (new) | handlers.py |
| arbiter/core.py | — | arbiter/agent.py | rename (standardization) |
