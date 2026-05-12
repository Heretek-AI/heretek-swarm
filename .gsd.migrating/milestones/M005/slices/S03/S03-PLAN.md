# S03: Convert surviving flat actors to thin re-exports

**Goal:** Convert 14 surviving flat actor files to thin re-exports pointing to canonical subpackage implementations, standardize the arbiter subpackage (core.py→agent.py), and rename EchoActor→EchoAgent across all call sites. After this slice, all 24 agent files follow the same subpackage convention and no flat .py file contains class definitions.
**Demo:** actors/alpha.py contains only re-exports, no implementation

## Must-Haves

- After this slice: (1) All 14 flat .py files are thin re-exports with zero class definitions. (2) All 24 agents import correctly from actors.__init__.py. (3) EchoActor→EchoAgent rename is complete across all 6 call sites. (4) Arbiter subpackage uses agent.py (not core.py). (5) 8 new subpackages exist with proper __init__.py files. (6) All 658 existing tests pass. (7) _HISTORIAN_FILE, _SYSTEM_RECOVERY_TOPIC, _PARADIGM_NOT_INITIALIZED constants are preserved in their flat-file re-export stubs.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice completes the M001 refactor by making every agent discoverable by its subpackage name. After this, 24/24 agents follow the subpackage convention. The actors/__init__.py surface is updated (EchoActor→EchoAgent). api/main.py and runtime/main_loop.py import paths are updated. docs/actors/README.md references are updated.

## Verification

- None — pure refactor with no runtime behavioral changes. All public API surfaces preserved (names unchanged except EchoActor→EchoAgent).

## Tasks

- [x] **T01: Standardize arbiter subpackage + create simple subpackages (metis, empath)** `est:45m`
  **Arbiter:** Rename `arbiter/core.py` → `arbiter/agent.py`. Update `arbiter/__init__.py` to use `from .agent import` (relative import stays). Update `arbiter/strategies.py` to import from `.agent` instead of `.core`. handlers.py and constants.py don't import from core — no changes needed.
  - Files: `heretek-swarm/heretek_swarm/actors/arbiter/core.py`, `heretek-swarm/heretek_swarm/actors/arbiter/agent.py`, `heretek-swarm/heretek_swarm/actors/arbiter/__init__.py`, `heretek-swarm/heretek_swarm/actors/arbiter/strategies.py`, `heretek-swarm/heretek_swarm/actors/metis.py`, `heretek-swarm/heretek_swarm/actors/metis/__init__.py`, `heretek-swarm/heretek_swarm/actors/metis/agent.py`, `heretek-swarm/heretek_swarm/actors/empath.py`, `heretek-swarm/heretek_swarm/actors/empath/__init__.py`, `heretek-swarm/heretek_swarm/actors/empath/agent.py`
  - Verify: python -c "from heretek_swarm.actors import ArbiterAgent, MetisAgent, EmpathAgent; print('Arbiter, Metis, Empath OK')" && test ! -f heretek-swarm/heretek_swarm/actors/arbiter/core.py

- [x] **T02: Create split subpackages (historian, coder, catalyst, perceiver)** `est:1h`
  For each of historian, coder, catalyst, perceiver: extract types/enums into a `types.py` and the agent class into `agent.py`, then create `__init__.py` with absolute re-exports.
  - Files: `heretek-swarm/heretek_swarm/actors/historian.py`, `heretek-swarm/heretek_swarm/actors/historian/__init__.py`, `heretek-swarm/heretek_swarm/actors/historian/types.py`, `heretek-swarm/heretek_swarm/actors/historian/agent.py`, `heretek-swarm/heretek_swarm/actors/coder.py`, `heretek-swarm/heretek_swarm/actors/coder/__init__.py`, `heretek-swarm/heretek_swarm/actors/coder/types.py`, `heretek-swarm/heretek_swarm/actors/coder/agent.py`, `heretek-swarm/heretek_swarm/actors/catalyst.py`, `heretek-swarm/heretek_swarm/actors/catalyst/__init__.py`, `heretek-swarm/heretek_swarm/actors/catalyst/types.py`, `heretek-swarm/heretek_swarm/actors/catalyst/agent.py`, `heretek-swarm/heretek_swarm/actors/perceiver.py`, `heretek-swarm/heretek_swarm/actors/perceiver/__init__.py`, `heretek-swarm/heretek_swarm/actors/perceiver/types.py`, `heretek-swarm/heretek_swarm/actors/perceiver/agent.py`
  - Verify: python -c "from heretek_swarm.actors import HistorianAgent, CoderAgent, CatalystAgent, PerceiverAgent; print('Split subpackages OK')" && python -c "from heretek_swarm.actors.historian import _HISTORIAN_FILE; print(f'_HISTORIAN_FILE={_HISTORIAN_FILE}')"

- [x] **T03: Create handoff subpackage with deduplication** `est:45m`
  **Key challenge:** HandoffContext and HandoffResult are defined identically in both `handoff.py` and `handoff_handlers.py`. Create a single `handoff/types.py` with the deduplicated definitions.
  - Files: `heretek-swarm/heretek_swarm/actors/handoff.py`, `heretek-swarm/heretek_swarm/actors/handoff_handlers.py`, `heretek-swarm/heretek_swarm/actors/handoff/__init__.py`, `heretek-swarm/heretek_swarm/actors/handoff/types.py`, `heretek-swarm/heretek_swarm/actors/handoff/orchestrator.py`, `heretek-swarm/heretek_swarm/actors/handoff/handlers.py`
  - Verify: python -c "from heretek_swarm.actors.handoff import HandoffContext, HandoffResult, HandoffOrchestrator; print('Handoff subpackage OK')" && python -c "from heretek_swarm.actors.handoff.handlers import HandoffProcessor; print('Handoff handlers import OK')"

- [x] **T04: Create echo subpackage with EchoActor→EchoAgent rename** `est:30m`
  **Create `actors/echo/types.py`:** Extract `CommunicationChannel(Enum)`, `MessagePriority(Enum)`, `CommunicationStyle`, `TranslationRule` from `actors/echo.py`.
  - Files: `heretek-swarm/heretek_swarm/actors/echo.py`, `heretek-swarm/heretek_swarm/actors/echo/__init__.py`, `heretek-swarm/heretek_swarm/actors/echo/types.py`, `heretek-swarm/heretek_swarm/actors/echo/agent.py`, `heretek-swarm/heretek_swarm/actors/__init__.py`, `heretek-swarm/heretek_swarm/api/main.py`, `heretek-swarm/heretek_swarm/runtime/main_loop.py`, `heretek-swarm/docs/actors/README.md`
  - Verify: python -c "from heretek_swarm.actors import EchoAgent; print('EchoAgent import OK')" && ! python -c "from heretek_swarm.actors import EchoActor" 2>/dev/null && echo 'EchoActor removed from public API OK'

- [x] **T05: Convert all 14 flat files to thin re-export stubs** `est:30m`
  Replace each flat .py file with a thin re-export stub that imports all previously-defined names from the corresponding subpackage. The stubs preserve backward compatibility — any `from heretek_swarm.actors.xxx import YYY` continues to work.
  - Files: `heretek-swarm/heretek_swarm/actors/alpha.py`, `heretek-swarm/heretek_swarm/actors/beta.py`, `heretek-swarm/heretek_swarm/actors/charlie.py`, `heretek-swarm/heretek_swarm/actors/steward.py`, `heretek-swarm/heretek_swarm/actors/explorer.py`, `heretek-swarm/heretek_swarm/actors/historian.py`, `heretek-swarm/heretek_swarm/actors/metis.py`, `heretek-swarm/heretek_swarm/actors/empath.py`, `heretek-swarm/heretek_swarm/actors/echo.py`, `heretek-swarm/heretek_swarm/actors/coder.py`, `heretek-swarm/heretek_swarm/actors/catalyst.py`, `heretek-swarm/heretek_swarm/actors/perceiver.py`, `heretek-swarm/heretek_swarm/actors/handoff.py`, `heretek-swarm/heretek_swarm/actors/handoff_handlers.py`
  - Verify: for f in alpha beta charlie steward explorer historian metis empath echo coder catalyst perceiver handoff handoff_handlers; do if grep -q "^class " "heretek-swarm/heretek_swarm/actors/${f}.py" 2>/dev/null; then echo "FAIL: ${f}.py still has class"; fi; done; echo 'All flat files verified as re-exports'

- [x] **T06: Final verification — full import check + test suite** `est:15m`
  Run comprehensive verification to confirm all changes work correctly and no regressions were introduced.
  - Verify: python -c "from heretek_swarm.actors import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent, ExplorerAgent, HistorianAgent, MetisAgent, EmpathAgent, EchoAgent, CoderAgent, CatalystAgent, PerceiverAgent, ArbiterAgent, ChronosAgent, CoordinatorAgent, DreamerAgent, ExaminerAgent, HabitForgeAgent, NexusAgent, PerceiverPlusAgent, PrismAgent, SentinelAgent, SentinelPrimeAgent, ActorSupervisor, ActorFactory, AgentActor; print(f'All {len([x for x in dir() if not x.startswith("_")])} agents import OK')" && cd heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/arbiter/core.py
- heretek-swarm/heretek_swarm/actors/arbiter/agent.py
- heretek-swarm/heretek_swarm/actors/arbiter/__init__.py
- heretek-swarm/heretek_swarm/actors/arbiter/strategies.py
- heretek-swarm/heretek_swarm/actors/metis.py
- heretek-swarm/heretek_swarm/actors/metis/__init__.py
- heretek-swarm/heretek_swarm/actors/metis/agent.py
- heretek-swarm/heretek_swarm/actors/empath.py
- heretek-swarm/heretek_swarm/actors/empath/__init__.py
- heretek-swarm/heretek_swarm/actors/empath/agent.py
- heretek-swarm/heretek_swarm/actors/historian.py
- heretek-swarm/heretek_swarm/actors/historian/__init__.py
- heretek-swarm/heretek_swarm/actors/historian/types.py
- heretek-swarm/heretek_swarm/actors/historian/agent.py
- heretek-swarm/heretek_swarm/actors/coder.py
- heretek-swarm/heretek_swarm/actors/coder/__init__.py
- heretek-swarm/heretek_swarm/actors/coder/types.py
- heretek-swarm/heretek_swarm/actors/coder/agent.py
- heretek-swarm/heretek_swarm/actors/catalyst.py
- heretek-swarm/heretek_swarm/actors/catalyst/__init__.py
- heretek-swarm/heretek_swarm/actors/catalyst/types.py
- heretek-swarm/heretek_swarm/actors/catalyst/agent.py
- heretek-swarm/heretek_swarm/actors/perceiver.py
- heretek-swarm/heretek_swarm/actors/perceiver/__init__.py
- heretek-swarm/heretek_swarm/actors/perceiver/types.py
- heretek-swarm/heretek_swarm/actors/perceiver/agent.py
- heretek-swarm/heretek_swarm/actors/handoff.py
- heretek-swarm/heretek_swarm/actors/handoff_handlers.py
- heretek-swarm/heretek_swarm/actors/handoff/__init__.py
- heretek-swarm/heretek_swarm/actors/handoff/types.py
- heretek-swarm/heretek_swarm/actors/handoff/orchestrator.py
- heretek-swarm/heretek_swarm/actors/handoff/handlers.py
- heretek-swarm/heretek_swarm/actors/echo.py
- heretek-swarm/heretek_swarm/actors/echo/__init__.py
- heretek-swarm/heretek_swarm/actors/echo/types.py
- heretek-swarm/heretek_swarm/actors/echo/agent.py
- heretek-swarm/heretek_swarm/actors/__init__.py
- heretek-swarm/heretek_swarm/api/main.py
- heretek-swarm/heretek_swarm/runtime/main_loop.py
- heretek-swarm/docs/actors/README.md
- heretek-swarm/heretek_swarm/actors/alpha.py
- heretek-swarm/heretek_swarm/actors/beta.py
- heretek-swarm/heretek_swarm/actors/charlie.py
- heretek-swarm/heretek_swarm/actors/steward.py
- heretek-swarm/heretek_swarm/actors/explorer.py
