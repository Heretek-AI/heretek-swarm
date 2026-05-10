# S03: Wire actors/__init__.py as the single re-export surface — UAT

**Milestone:** M001
**Written:** 2026-05-07T12:40:11.971Z

# UAT: S03 — heretek_swarm.actors re-export surface

## Scope
Verifying that `from heretek_swarm.agents import *` resolves all public agent classes from the canonical heretek_swarm/agents/__init__.py surface.

## Preconditions
- heretek-swarm package is installed in the active Python environment
- `src/heretek_swarm/agents/__init__.py` exists

## Test Cases

### TC01: Core agents re-export from canonical surface
**Steps:**
1. Open a Python shell with heretek-swarm installed
2. Run: `from heretek_swarm.agents import AlphaAgent, ArbiterAgent, ExplorerAgent; print('OK')`
**Expected:** Exit code 0, prints `OK`, no ImportError

### TC02: Subpackage agents are also importable via canonical surface
**Steps:**
1. Run: `from heretek_swarm.agents import TemporalAgent, MemoryAgent, ToolExecutor; print('OK')`
**Expected:** Exit code 0, prints `OK`, no ImportError

### TC03: Full agents list is accessible
**Steps:**
1. Run: `from heretek_swarm.agents import agents; print(len(agents))`
**Expected:** Prints a positive integer > 0

### TC04: No flat-file references in canonical __init__
**Steps:**
1. Grep for `from .*(arbiter|base|triad|explorer|temporal)\.py` in `src/heretek_swarm/agents/__init__.py`
**Expected:** No matches

### TC05: pytest passes with no ImportError
**Steps:**
1. Run: `pytest tests/ -x -q`
**Expected:** All tests pass with exit code 0

## Not Proven by This UAT
- Import behavior of agents not listed in __init__.py __all__ (subpackages with import errors are silently skipped via try/except)
- Runtime behavior of individual agents after import
- Performance under concurrent import scenarios
- Integration with agents that have optional dependencies (LLM, memory backends)

