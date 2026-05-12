---
estimated_steps: 4
estimated_files: 10
skills_used: []
---

# T01: Standardize arbiter subpackage + create simple subpackages (metis, empath)

**Arbiter:** Rename `arbiter/core.py` → `arbiter/agent.py`. Update `arbiter/__init__.py` to use `from .agent import` (relative import stays). Update `arbiter/strategies.py` to import from `.agent` instead of `.core`. handlers.py and constants.py don't import from core — no changes needed.

**Metis:** Create `actors/metis/__init__.py` with absolute re-export from `heretek_swarm.actors.metis.agent`. Create `actors/metis/agent.py` — copy the MetisAgent class definition from `actors/metis.py` verbatim. Preserve all imports and mixin usage.

**Empath:** Same pattern as metis — create `actors/empath/__init__.py` + `actors/empath/agent.py` with EmpathAgent class from `actors/empath.py`.

**Constraints:** Subpackage __init__.py must use absolute imports (majority convention). Copy the full class file, don't refactor behavior. Preserve ALL imports and method signatures exactly.

## Inputs

- `heretek-swarm/heretek_swarm/actors/metis.py`
- `heretek-swarm/heretek_swarm/actors/empath.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/__init__.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/core.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/strategies.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/arbiter/agent.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/__init__.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/strategies.py`
- `heretek-swarm/heretek_swarm/actors/metis/__init__.py`
- `heretek-swarm/heretek_swarm/actors/metis/agent.py`
- `heretek-swarm/heretek_swarm/actors/empath/__init__.py`
- `heretek-swarm/heretek_swarm/actors/empath/agent.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/core.py`

## Verification

python -c "from heretek_swarm.actors import ArbiterAgent, MetisAgent, EmpathAgent; print('Arbiter, Metis, Empath OK')" && test ! -f heretek-swarm/heretek_swarm/actors/arbiter/core.py
