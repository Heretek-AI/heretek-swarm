---
estimated_steps: 35
estimated_files: 14
skills_used: []
---

# T05: Convert all 14 flat files to thin re-export stubs

Replace each flat .py file with a thin re-export stub that imports all previously-defined names from the corresponding subpackage. The stubs preserve backward compatibility — any `from heretek_swarm.actors.xxx import YYY` continues to work.

For each flat file, the stub should:
1. Import ALL public names from the canonical subpackage (using absolute import)
2. Preserve module-level constants that tests patch (e.g., `_HISTORIAN_FILE`, `_SYSTEM_RECOVERY_TOPIC`, `_PARADIGM_NOT_INITIALIZED`)
3. Export via __all__ if the original had one (most don't)

**Mapping (14 files):**
| Flat file | Re-export from | Key constants to preserve |
|-----------|----------------|--------------------------|
| alpha.py | triad.agent | — |
| beta.py | triad.agent | — |
| charlie.py | triad.agent | — |
| steward.py | triad.agent | _SYSTEM_RECOVERY_TOPIC |
| explorer.py | explorer | — (subpackage __init__.py already re-exports) |
| historian.py | historian | _HISTORIAN_FILE |
| metis.py | metis | — |
| empath.py | empath | — |
| echo.py | echo | — (now EchoAgent) |
| coder.py | coder | — |
| catalyst.py | catalyst | _PARADIGM_NOT_INITIALIZED |
| perceiver.py | perceiver | — |
| handoff.py | handoff.orchestrator + handoff.types | — |
| handoff_handlers.py | handoff.handlers + handoff.types | — |

**IMPORTANT:** After this task, NO flat .py file should contain `^class ` definitions. Verify with grep.

**Pattern:**
```python
# flake8: noqa: F401,F403
from heretek_swarm.actors.subpkg import *
from heretek_swarm.actors.subpkg import SpecificName  # if __all__ is restricted

# Preserved constants
_SYSTEM_RECOVERY_TOPIC = "system.recovery"  # example
```

For explorer.py: the explorer/__init__.py already has __all__ with all names. Simple `from heretek_swarm.actors.explorer import *` works.

For handoff.py and handoff_handlers.py: These need more specific imports since the classes are split across orchestrator.py, handlers.py, and types.py:
- handoff.py stub: import from handoff (the __init__.py which re-exports everything)
- handoff_handlers.py stub: import from handoff the handler classes + context/result

## Inputs

- None specified.

## Expected Output

- `heretek-swarm/heretek_swarm/actors/alpha.py`
- `heretek-swarm/heretek_swarm/actors/beta.py`
- `heretek-swarm/heretek_swarm/actors/charlie.py`
- `heretek-swarm/heretek_swarm/actors/steward.py`
- `heretek-swarm/heretek_swarm/actors/explorer.py`
- `heretek-swarm/heretek_swarm/actors/historian.py`
- `heretek-swarm/heretek_swarm/actors/metis.py`
- `heretek-swarm/heretek_swarm/actors/empath.py`
- `heretek-swarm/heretek_swarm/actors/echo.py`
- `heretek-swarm/heretek_swarm/actors/coder.py`
- `heretek-swarm/heretek_swarm/actors/catalyst.py`
- `heretek-swarm/heretek_swarm/actors/perceiver.py`
- `heretek-swarm/heretek_swarm/actors/handoff.py`
- `heretek-swarm/heretek_swarm/actors/handoff_handlers.py`

## Verification

for f in alpha beta charlie steward explorer historian metis empath echo coder catalyst perceiver handoff handoff_handlers; do if grep -q "^class " "heretek-swarm/heretek_swarm/actors/${f}.py" 2>/dev/null; then echo "FAIL: ${f}.py still has class"; fi; done; echo 'All flat files verified as re-exports'
