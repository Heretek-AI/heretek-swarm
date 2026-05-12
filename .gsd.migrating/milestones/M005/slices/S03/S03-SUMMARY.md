---
id: S03
parent: M005
milestone: M005
provides:
  - Uniform subpackage convention for all 24 agents — every agent discoverable by subpackage name
  - 8 new subpackages with proper __init__.py re-exports following absolute-import convention
  - 14 flat-file re-export stubs preserving backward compatibility for all existing import paths
  - EchoAgent as canonical public name (EchoActor fully removed)
  - Arbiter subpackage standardized to agent.py (matches 23/23 other subpackages)
requires:
  []
affects:
  []
key_files:
  - heretek_swarm/actors/arbiter/agent.py
  - heretek_swarm/actors/metis/agent.py
  - heretek_swarm/actors/empath/agent.py
  - heretek_swarm/actors/historian/agent.py
  - heretek_swarm/actors/coder/agent.py
  - heretek_swarm/actors/catalyst/agent.py
  - heretek_swarm/actors/perceiver/agent.py
  - heretek_swarm/actors/handoff/orchestrator.py
  - heretek_swarm/actors/echo/agent.py
  - heretek_swarm/actors/__init__.py
key_decisions:
  - Handoff subpackage: HandoffContext and HandoffResult deduplicated into single types.py — both handoff.py and handoff_handlers.py had identical definitions
  - Arbiter standardization: core.py→agent.py rename to match 24/24 subpackage convention, with all 3 internal imports updated
  - EchoActor→EchoAgent rename across exactly 6 sites: echo/agent.py, echo/__init__.py, actors/__init__.py, api/main.py, runtime/main_loop.py, docs/actors/README.md
  - Subpackage pattern: complex actors (with helper types) use split pattern (types.py + agent.py); simple actors use agent.py only
  - All subpackage __init__.py files use absolute imports (from heretek_swarm.actors.X import Y) — majority convention per M001
patterns_established:
  - Split subpackage pattern: types.py for enums/dataclasses + agent.py for AgentActor subclass + __init__.py with absolute re-exports
  - Simple subpackage pattern: agent.py only + __init__.py with absolute re-exports
  - Flat-file re-export stub pattern: import all names from subpackage, use __all__ for explicit surface, preserve private constants for test compatibility
  - Agent rename procedure: Update class definition → subpackage __init__.py → actors/__init__.py public API → api/main.py dispatch → runtime/main_loop.py dispatch → tests → docs
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-12T01:13:15.739Z
blocker_discovered: false
---

# S03: Convert surviving flat actors to thin re-exports

**Converted all 14 surviving flat actor .py files to thin re-export stubs, created 8 new subpackages following the uniform split/simple convention, standardized arbiter (core.py→agent.py), renamed EchoActor→EchoAgent across 6 call sites, and verified all 370 tests pass.**

## What Happened

## What Happened

S03 completed the M001 refactor by converting all 14 remaining flat actor `.py` files that still carried class definitions into thin re-export stubs. After this work, every one of the 24 agents follows the subpackage convention and no flat `.py` file contains implementation code.

### T01: Arbiter standardization + metis/empath subpackages (45min)

Renamed `arbiter/core.py` → `arbiter/agent.py` to match the majority convention. Updated all 3 internal imports: `arbiter/__init__.py`, `strategies.py`, and `handlers.py` now import from `.agent` instead of `.core`. Created `metis/` and `empath/` subpackages with the simple pattern (`agent.py` only, no helper types to extract). Both subpackages use absolute imports in their `__init__.py` files.

### T02: Split subpackages — historian, coder, catalyst, perceiver (1h)

For each of the 4 agents with helper types, extracted enums/dataclasses into a `types.py` and the AgentActor subclass into `agent.py`. Key extractions included:
- **historian**: `LRUCache` dataclass → `types.py`, `HistorianAgent` → `agent.py`
- **coder**: 6 enums/dataclasses (`CodeStrategy`, `CodeContext`, `CodeResult`, `RefactorMode`, `CodePriority`, `CodeReview`) → `types.py`, `CoderAgent` → `agent.py`
- **catalyst**: 5 enums/dataclasses (`CatalystRole`, `CreativeMode`, `BrainstormSession`, `IdeaEvaluation`, `CreativeInsight`) → `types.py`, `CatalystAgent` → `agent.py`
- **perceiver**: `ModalityType`, `ModalityResult`, `ModalityConfidence` → `types.py`, `PerceiverAgent` → `agent.py`

All `__init__.py` files use absolute imports from `heretek_swarm.actors.X` as per the majority convention. The `_HISTORIAN_FILE` constant is preserved in `types.py` and re-exported through both the subpackage and flat-file stub for test compatibility.

### T03: Handoff subpackage with deduplication (45min)

`HandoffContext` and `HandoffResult` were defined identically in both `handoff.py` and `handoff_handlers.py`. Created a single `handoff/types.py` with the deduplicated definitions. Extracted `HandoffOrchestrator` + strategy methods to `orchestrator.py`, and handler classes to `handlers.py`. Both flat files (`handoff.py`, `handoff_handlers.py`) are now thin re-export stubs. Handoff classes remain internal — NOT added to `actors/__init__.py` public API.

### T04: Echo subpackage with EchoActor→EchoAgent rename (30min)

Created `echo/types.py` with 4 extracted types (`CommunicationChannel`, `MessagePriority`, `CommunicationStyle`, `TranslationRule`). Moved `EchoActor` → `echo/agent.py` renamed to `EchoAgent`. Updated all 6 call sites: `echo/__init__.py`, `actors/__init__.py` (public API), `api/main.py` (import + dispatch table), `runtime/main_loop.py` (import + dispatch table), `tests/test_actor_lifecycle.py` (test reference), and `docs/actors/README.md` (3 references). The old `EchoActor` name is fully removed from the public API surface.

### T05: Convert all 14 flat files to thin re-export stubs (30min)

Replaced each flat `.py` file with a thin re-export stub that imports all previously-defined names from the corresponding subpackage. The stubs preserve backward compatibility — `from heretek_swarm.actors.xxx import YYY` continues to work. Verified via `grep -q "^class "` that zero flat files contain class definitions.

### T06: Final verification (15min)

Ran comprehensive verification: all 26 public symbols import from `actors.__init__.py`, all 370 existing tests pass (55s duration), `_HISTORIAN_FILE` constant preserved, `arbiter/core.py` confirmed deleted, `EchoActor` confirmed removed from public API, all 8 new subpackages present with proper `__init__.py` files.

## Verification

## Verification Performed

1. **Full agent import chain (T06):** All 26 public symbols (24 agents + ActorSupervisor + ActorFactory) import successfully from `heretek_swarm.actors` — the flat-to-subpackage re-export chain resolves correctly.
2. **Test suite (T06):** `pytest tests/` — all 370 tests pass (exit code 0, ~55s duration on full run).
3. **Flat file audit (T05/T06):** All 14 flat `.py` files contain zero class definitions — confirmed via `grep -q "^class "` on each file.
4. **Arbiter standardization (T01):** `arbiter/core.py` deleted, `arbiter/agent.py` is the canonical source, all internal imports updated.
5. **EchoActor→EchoAgent rename (T04):** `EchoAgent` imports from public API, `EchoActor` returns ImportError.
6. **Handoff deduplication (T03):** `HandoffContext`/`HandoffResult` resolve from single `types.py`, both flat stubs functional.
7. **_HISTORIAN_FILE preservation (T02):** Constant importable from both flat stub and subpackage agent module.
8. **New subpackages (T01-T04):** All 8 new subpackages present with proper `__init__.py` re-exports.
9. **Import chain integrity:** No circular imports — verified: zero flat files import from other flat files; base/mixins never import from flat files; re-export pattern adds no new edges.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `heretek_swarm/actors/arbiter/core.py` — Deleted — renamed to agent.py
- `heretek_swarm/actors/arbiter/agent.py` — Created — canonical ArbiterAgent (moved from core.py)
- `heretek_swarm/actors/arbiter/__init__.py` — Updated import from .agent instead of .core
- `heretek_swarm/actors/arbiter/strategies.py` — Updated import from .agent instead of .core
- `heretek_swarm/actors/arbiter/handlers.py` — Updated import from .agent instead of .core
- `heretek_swarm/actors/metis/agent.py` — Created — canonical MetisAgent
- `heretek_swarm/actors/metis/__init__.py` — Created — absolute re-exports
- `heretek_swarm/actors/empath/agent.py` — Created — canonical EmpathAgent
- `heretek_swarm/actors/empath/__init__.py` — Created — absolute re-exports
- `heretek_swarm/actors/historian/types.py` — Created — LRUCache dataclass
- `heretek_swarm/actors/historian/agent.py` — Created — canonical HistorianAgent
- `heretek_swarm/actors/coder/types.py` — Created — 6 enums/dataclasses
- `heretek_swarm/actors/coder/agent.py` — Created — canonical CoderAgent
- `heretek_swarm/actors/catalyst/types.py` — Created — 5 enums/dataclasses
- `heretek_swarm/actors/catalyst/agent.py` — Created — canonical CatalystAgent
- `heretek_swarm/actors/perceiver/types.py` — Created — ModalityType/Result/Confidence
- `heretek_swarm/actors/perceiver/agent.py` — Created — canonical PerceiverAgent
- `heretek_swarm/actors/handoff/types.py` — Created — deduplicated HandoffContext + HandoffResult
- `heretek_swarm/actors/handoff/orchestrator.py` — Created — HandoffOrchestrator + strategies
- `heretek_swarm/actors/handoff/handlers.py` — Created — handler classes
- `heretek_swarm/actors/echo/types.py` — Created — 4 enums/dataclasses
- `heretek_swarm/actors/echo/agent.py` — Created — EchoAgent (renamed from EchoActor)
- `heretek_swarm/actors/echo/__init__.py` — Created — absolute re-exports (EchoAgent)
- `heretek_swarm/actors/__init__.py` — Updated — EchoActor→EchoAgent
- `heretek_swarm/api/main.py` — Updated — EchoActor→EchoAgent in import + dispatch
- `heretek_swarm/runtime/main_loop.py` — Updated — EchoActor→EchoAgent in import + dispatch
- `docs/actors/README.md` — Updated — 3 EchoActor→EchoAgent references
- `heretek_swarm/actors/alpha.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/beta.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/charlie.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/steward.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/explorer.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/historian.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/metis.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/empath.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/echo.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/coder.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/catalyst.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/perceiver.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/handoff.py` — Replaced with thin re-export stub
- `heretek_swarm/actors/handoff_handlers.py` — Replaced with thin re-export stub
