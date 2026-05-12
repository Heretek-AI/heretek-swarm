# S03 Research: Convert surviving flat actors to thin re-exports

**Researched:** 2026-05-11
**Researcher:** Scout agent (research lane)

## Summary

This slice converts 14 flat actor files into thin re-exports pointing to canonical subpackage implementations, creates 8 new subpackages, standardizes the arbiter subpackage (core.py → agent.py), and renames EchoActor→EchoAgent across 6 call sites. The changes are purely mechanical — no behavior changes, no new code, no public API surface changes beyond the EchoActor rename.

## Findings

### 1. Current State: 14 flat files with implementation, 12 existing subpackages

**Flat files with existing canonical subpackages (re-export only):**
| Flat file | Lines | Target | Class(es) in flat |
|-----------|-------|--------|-------------------|
| alpha.py | 282 | triad/agent.py | `AlphaAgent` |
| beta.py | 299 | triad/agent.py | `BetaAgent` |
| charlie.py | 393 | triad/agent.py | `CharlieAgent` |
| steward.py | 840 | triad/agent.py | `StewardAgent` + `_SYSTEM_RECOVERY_TOPIC` |
| explorer.py | 1317 | explorer/agent.py | `ExplorerAgent` + 9 types (OpportunityType, ThreatLevel, AnomalyType, Opportunity, Anomaly, IntelligenceReport, ResearchState, ResearchProgress, Pattern) |

**Flat files needing new subpackages:**
| Flat file | Lines | New subpackage | Classes/enums in flat |
|-----------|-------|----------------|----------------------|
| historian.py | 1353 | historian/ | `LRUCache`, `HistorianAgent`, `_HISTORIAN_FILE` |
| metis.py | 1110 | metis/ | `MetisAgent` |
| empath.py | 1085 | empath/ | `EmpathAgent` |
| echo.py | 749 | echo/ | `CommunicationChannel`, `MessagePriority`, `CommunicationStyle`, `TranslationRule`, `EchoActor` → `EchoAgent` |
| coder.py | 979 | coder/ | `CodeLanguage`, `CodeTask`, `ReviewSeverity`, `CodeSnippet`, `ReviewIssue`, `CodeReview`, `DebugSession`, `ImplementationTask`, `CoderAgent` |
| catalyst.py | 1135 | catalyst/ | `ChangeStatus`, `ChangeType`, `ImpactLevel`, `ChangeRequest`, `ChangeNotification`, `CatalystAgent`, `_PARADIGM_NOT_INITIALIZED` |
| perceiver.py | 911 | perceiver/ | `ModalityType`, `PerceiverAgent` |
| handoff.py | 599 | handoff/ | `HandoffContext`, `HandoffResult`, `HandoffValidator`, `AgentHandoff`, `HandoffStrategy`, `TaskTypeStrategy`, `PerformanceStrategy`, `LoadBalancingStrategy`, `HandoffOrchestrator` |
| handoff_handlers.py | 243 | handoff/ | `HandoffContext` (dup), `HandoffResult` (dup), `HandoffValidationHandler`, `HandoffRateLimitHandler`, `HandoffTransferHandler`, `HandoffLoggingHandler`, `HandoffProcessor` |

**Already-migrated subpackages (no flat file):**
chronos, coordinator, dreamer, examiner, habit_forge, nexus, prism, sentinel, sentinel_prime

### 2. Critical Findings

#### 2a. `_HISTORIAN_FILE` patching pattern (highest risk)
The tests extensively use a module-mutation pattern:
```python
from heretek_swarm.actors.historian import _HISTORIAN_FILE as _orig_file
_h_mod._HISTORIAN_FILE = tmp_jsonl_path
```

This means the re-export stub for `historian.py` MUST re-export `_HISTORIAN_FILE` as a module-level global. The test code does `_h_mod._HISTORIAN_FILE = value` which sets an attribute on the flat module object. The re-export stub must have `_HISTORIAN_FILE = ...` at module level. The canonical definition in `historian/agent.py` or `historian/types.py` sets the value; the flat stub re-exports it so the patching target exists.

Files affected: `tests/test_historian_jsonl.py`, `tests/test_living_loop_integration.py` (many patching sites)

#### 2b. HandoffContext/HandoffResult deduplication
`HandoffContext` and `HandoffResult` are defined identically in both `handoff.py` and `handoff_handlers.py`. The plan is to define them once in `handoff/types.py` and import into both `handoff/orchestrator.py` and `handoff/handlers.py`. The flat `handoff.py` re-exports from `handoff/orchestrator.py` and the flat `handoff_handlers.py` re-exports from `handoff/handlers.py`.

#### 2c. EchoActor → EchoAgent rename (6 sites, moderate risk)
The rename touches these known locations:
1. `actors/echo/agent.py` — class definition (moved from flat echo.py)
2. `actors/echo/__init__.py` — re-export
3. `actors/__init__.py` — `from ... echo import EchoActor` → `EchoAgent` + `__all__`
4. `api/main.py` — import + dispatch table entry (2 references)
5. `runtime/main_loop.py` — import + dispatch table entry (2 references)
6. `tests/test_actor_lifecycle.py` — import + usage (2 references)
7. `docs/actors/README.md` — agent table entry (1 reference)

#### 2d. Arbiter standardization
`arbiter/core.py` contains the ArbiterAgent class. Need to:
1. `mv arbiter/core.py arbiter/agent.py`
2. Update `arbiter/__init__.py`: change `from .core import` → `from heretek_swarm.actors.arbiter.agent import` (absolute import)
3. Update `arbiter/handlers.py`: change `from .core import` → `from .agent import` (but this module uses relative imports which stay — the import path stays relative since it's internal to the subpackage)
4. Update `arbiter/strategies.py`: same as handlers.py

Wait — re-reading the constraint: "switch arbiter/__init__.py from relative to absolute imports". The handlers.py and strategies.py use relative imports within the subpackage, which is fine. Only `__init__.py` needs to switch.

#### 2e. Perceiver vs PerceiverPlus are DIFFERENT agents
`perceiver.py` exports `PerceiverAgent` and `ModalityType`. `perceiver_plus/agent.py` exports `PerceiverPlusAgent`. These are separate classes with different behavior. The plan to create a `perceiver/` subpackage (NOT re-export to perceiver_plus) is correct.

### 3. Import Verification

No circular import risk exists because:
- Subpackage `__init__.py` files import from subpackage-internal modules (absolute imports)
- Flat re-export stubs import from the subpackage
- Base/mixins never import from flat files
- No flat file imports from another flat file

After migration, this import chain holds:
```
actors/__init__.py ──→ actors/steward.py (flat stub) ──→ actors/triad/__init__.py ──→ actors/triad/agent.py
```
No cycle because each step imports a deeper path.

### 4. Test Verification Strategy

1. After each batch: `pytest tests/ -x -q` (fast-fail on first error)
2. Import check: `python -c "from heretek_swarm.actors import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent, ExplorerAgent, HistorianAgent, MetisAgent, EmpathAgent, EchoActor, CoderAgent, CatalystAgent, PerceiverAgent"`
3. After EchoActor→EchoAgent: update the above to `EchoAgent`
4. Flat file check: `grep -c "^class "` on each flat file should return 0
5. Verify `_HISTORIAN_FILE` patching still works

### 5. Skills Discovered

None — this is a pure local-refactor slice with familiar Python packaging patterns. No external libraries or services involved.

### 6. Natural Seams (independent work units)

The work breaks naturally into these execution tasks, ordered by dependency:

**T01: Arbiter standardization** (low risk, mechanical)
- Rename `arbiter/core.py` → `arbiter/agent.py`
- Fix 3 relative imports in `handlers.py`, `strategies.py`, `__init__.py`
- Switch `__init__.py` to absolute imports

**T02: EchoActor→EchoAgent rename** (moderate risk, 6 sites)
- Update class definition, subpackage __init__.py, actors __init__.py, api/main.py, runtime/main_loop.py, test file, docs

**T03: Simple subpackages (metis, empath)** (low risk, agent.py only)
- Create `actors/metis/agent.py` — copy `MetisAgent` class from flat
- Create `actors/metis/__init__.py` — absolute re-export
- Same for `actors/empath/`

**T04: Split subpackages (historian, echo, coder, catalyst, perceiver)** (medium risk, types.py + agent.py)
- For each: extract types/enums into `types.py`, agent class into `agent.py`, create `__init__.py`
- echo gets the rename (EchoActor→EchoAgent)
- historian must re-export `_HISTORIAN_FILE` in stub

**T05: Handoff subpackage** (medium risk, deduplication)
- Create `handoff/types.py` with deduplicated `HandoffContext`, `HandoffResult`
- Create `handoff/orchestrator.py` from `handoff.py` minus types
- Create `handoff/handlers.py` from `handoff_handlers.py` minus types
- Create `handoff/__init__.py`

**T06: Re-export stubs (14 flat files)** (low risk, mechanical)
- Replace each flat file with `from subpackage import ...` re-exports
- Preserve module-level constants (`_HISTORIAN_FILE`, `_SYSTEM_RECOVERY_TOPIC`, `_PARADIGM_NOT_INITIALIZED`)

**T07: Triad + Explorer re-exports** (lowest risk, already canonical)
- alpha.py, beta.py, charlie.py, steward.py: re-export from triad.agent
- explorer.py: re-export from explorer (already done in subpackage __init__.py)

### 7. First Proof (highest risk / biggest unblocker)

**Historian subpackage extraction** is the highest risk item because:
1. `_HISTORIAN_FILE` patching pattern is fragile — the flat re-export stub MUST have `_HISTORIAN_FILE` at module scope
2. The test suite heavily patches this module (20+ sites in 2 test files)
3. LRUCache must be extractable without breaking internal usage in HistorianAgent

Recommend starting with T01 (arbiter — lowest risk, quick win) to validate the toolchain works, then T03 (simple subpackages), then T04 starting with historian.

### 8. Verification

```bash
# Quick import check after each batch
python -c "
from heretek_swarm.actors import (
    AlphaAgent, BetaAgent, CharlieAgent, StewardAgent,
    ExplorerAgent, HistorianAgent, MetisAgent, EmpathAgent,
    EchoAgent, CoderAgent, CatalystAgent, PerceiverAgent,
    ArbiterAgent, ChronosAgent, CoordinatorAgent, DreamerAgent,
    ExaminerAgent, HabitForgeAgent, NexusAgent, PerceiverPlusAgent,
    PrismAgent, SentinelAgent, SentinelPrimeAgent,
    ActorSupervisor, ActorFactory, AgentActor,
)
print('All 23 agents import OK')
"

# Full test suite
pytest tests/ -x -q

# Verify no class definitions in flat files
for f in alpha beta charlie steward explorer historian metis empath echo coder catalyst perceiver handoff handoff_handlers; do
  if grep -q "^class " "heretek-swarm/heretek_swarm/actors/${f}.py" 2>/dev/null; then
    echo "FAIL: ${f}.py still has class definitions"
  fi
done

# Verify _HISTORIAN_FILE patching still works
python -c "
from heretek_swarm.actors.historian import _HISTORIAN_FILE
import pathlib
assert isinstance(_HISTORIAN_FILE, pathlib.Path), '_HISTORIAN_FILE must be a Path'
print('_HISTORIAN_FILE OK')
"
```
