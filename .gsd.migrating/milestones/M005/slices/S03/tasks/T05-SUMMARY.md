---
id: T05
parent: S03
milestone: M005
key_files:
  - heretek_swarm/actors/alpha.py
  - heretek_swarm/actors/beta.py
  - heretek_swarm/actors/charlie.py
  - heretek_swarm/actors/steward.py
  - heretek_swarm/actors/explorer.py
  - heretek_swarm/actors/historian.py
  - heretek_swarm/actors/metis.py
  - heretek_swarm/actors/empath.py
  - heretek_swarm/actors/echo.py
  - heretek_swarm/actors/coder.py
  - heretek_swarm/actors/catalyst.py
  - heretek_swarm/actors/perceiver.py
  - heretek_swarm/actors/handoff.py
  - heretek_swarm/actors/handoff_handlers.py
  - heretek_swarm/actors/triad/agent.py
key_decisions:
  - All 14 flat actor files converted to thin re-export stubs; no class definitions remain in any flat .py file
  - route_to_agent restored to StewardAgent in triad/agent.py (was missing from earlier migration)
  - _SYSTEM_RECOVERY_TOPIC preserved directly in steward.py stub since it's steward-specific and not in triad subpackage
duration: 
verification_result: passed
completed_at: 2026-05-12T00:49:39.601Z
blocker_discovered: false
---

# T05: Converted all 14 flat actor files to thin re-export stubs; fixed pre-existing migration gap by adding route_to_agent to StewardAgent in triad/agent.py

**Converted all 14 flat actor files to thin re-export stubs; fixed pre-existing migration gap by adding route_to_agent to StewardAgent in triad/agent.py**

## What Happened

Replaced each of the 14 flat .py files (alpha, beta, charlie, steward, explorer, historian, metis, empath, echo, coder, catalyst, perceiver, handoff, handoff_handlers) with thin re-export stubs that import all names from their canonical subpackages. Files mapping to the triad subpackage (alpha, beta, charlie, steward) use `from heretek_swarm.actors.triad import *`. Files with name collisions with existing subpackages (explorer, historian, metis, empath, echo, coder, catalyst, perceiver, handoff) use analogous re-exports — these are technically dead code since Python resolves packages before same-named modules, but they exist for consistency. handoff_handlers.py (no directory collision) re-exports from the handoff subpackage. Three module-level constants are preserved: _SYSTEM_RECOVERY_TOPIC in steward.py, _HISTORIAN_FILE in historian.py (re-exported via subpackage __init__), and _PARADIGM_NOT_INITIALIZED in catalyst.py (re-exported via subpackage __init__).

During verification, discovered that the old flat steward.py had a `route_to_agent` method that was never migrated to triad/agent.py's StewardAgent class. This caused test_end_to_end_s03::test_full_entrypoint_dispatch to fail. Fixed by adding `route_to_agent` (and the `import uuid` it needs) to triad/agent.py, restoring full backward compatibility.

## Verification

1. Grep confirmed zero `^class ` definitions in any of the 14 flat .py files
2. All 14 imports resolved correctly through re-export chain to subpackage classes
3. Three preserved constants verified: _SYSTEM_RECOVERY_TOPIC='system.recovery', _HISTORIAN_FILE=Path('.gsd/historian.jsonl'), _PARADIGM_NOT_INITIALIZED='ParadigmDetector not initialized'
4. StewardAgent.route_to_agent present after fix
5. EchoActor correctly not importable from actors package
6. Full test suite: 91 passed (test_actor_lifecycle, test_actor_routing, test_agent_factory, test_triad_analysis, test_mixin_guards, test_mixin_integration_s03, test_end_to_end_s03)

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -q "^class " heretek_swarm/actors/${f}.py for all 14 files` | 0 | ✅ pass | 50ms |
| 2 | `python -c "from heretek_swarm.actors.alpha import AlphaAgent; ... from heretek_swarm.actors.handoff_handlers import HandoffTransferHandler"` | 0 | ✅ pass | 2000ms |
| 3 | `python -c "assert hasattr(StewardAgent, 'route_to_agent')"` | 0 | ✅ pass | 1500ms |
| 4 | `python -c "from heretek_swarm.actors import EchoActor" 2>&1 (expected ImportError)` | 0 | ✅ pass | 1500ms |
| 5 | `pytest tests/test_actor_lifecycle.py tests/test_actor_routing.py tests/test_agent_factory.py tests/test_triad_analysis.py tests/test_mixin_guards.py tests/test_mixin_integration_s03.py tests/test_end_to_end_s03.py` | 0 | ✅ pass | 2940ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `heretek_swarm/actors/alpha.py`
- `heretek_swarm/actors/beta.py`
- `heretek_swarm/actors/charlie.py`
- `heretek_swarm/actors/steward.py`
- `heretek_swarm/actors/explorer.py`
- `heretek_swarm/actors/historian.py`
- `heretek_swarm/actors/metis.py`
- `heretek_swarm/actors/empath.py`
- `heretek_swarm/actors/echo.py`
- `heretek_swarm/actors/coder.py`
- `heretek_swarm/actors/catalyst.py`
- `heretek_swarm/actors/perceiver.py`
- `heretek_swarm/actors/handoff.py`
- `heretek_swarm/actors/handoff_handlers.py`
- `heretek_swarm/actors/triad/agent.py`
