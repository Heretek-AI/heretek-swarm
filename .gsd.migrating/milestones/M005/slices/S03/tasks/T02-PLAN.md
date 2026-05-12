---
estimated_steps: 6
estimated_files: 16
skills_used: []
---

# T02: Create split subpackages (historian, coder, catalyst, perceiver)

For each of historian, coder, catalyst, perceiver: extract types/enums into a `types.py` and the agent class into `agent.py`, then create `__init__.py` with absolute re-exports.

**Historian:** `types.py` gets LRUCache; `agent.py` gets HistorianAgent class + `_HISTORIAN_FILE` constant. Both import as needed internally. __init__.py re-exports LRUCache, HistorianAgent, _HISTORIAN_FILE.

**Coder:** `types.py` gets `CodeLanguage(StrEnum)`, `CodeTask`, `ReviewSeverity`, `CodeSnippet`, `ReviewIssue`, `CodeReview`, `DebugSession`, `ImplementationTask`; `agent.py` gets CoderAgent class with all imports. __init__.py re-exports all.

**Catalyst:** `types.py` gets `ChangeStatus(Enum)`, `ChangeType(Enum)`, `ImpactLevel(Enum)`, `ChangeRequest`, `ChangeNotification`; `agent.py` gets CatalystAgent class + `_PARADIGM_NOT_INITIALIZED` constant. __init__.py re-exports all.

**Perceiver:** `types.py` gets `ModalityType(StrEnum)`; `agent.py` gets PerceiverAgent class. __init__.py re-exports all.

**Constraints:** All __init__.py must use absolute imports. Copy class/enum definitions verbatim — no behavior changes. Preserve all imports in agent.py files.

## Inputs

- `heretek-swarm/heretek_swarm/actors/historian.py`
- `heretek-swarm/heretek_swarm/actors/coder.py`
- `heretek-swarm/heretek_swarm/actors/catalyst.py`
- `heretek-swarm/heretek_swarm/actors/perceiver.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/historian/__init__.py`
- `heretek-swarm/heretek_swarm/actors/historian/types.py`
- `heretek-swarm/heretek_swarm/actors/historian/agent.py`
- `heretek-swarm/heretek_swarm/actors/coder/__init__.py`
- `heretek-swarm/heretek_swarm/actors/coder/types.py`
- `heretek-swarm/heretek_swarm/actors/coder/agent.py`
- `heretek-swarm/heretek_swarm/actors/catalyst/__init__.py`
- `heretek-swarm/heretek_swarm/actors/catalyst/types.py`
- `heretek-swarm/heretek_swarm/actors/catalyst/agent.py`
- `heretek-swarm/heretek_swarm/actors/perceiver/__init__.py`
- `heretek-swarm/heretek_swarm/actors/perceiver/types.py`
- `heretek-swarm/heretek_swarm/actors/perceiver/agent.py`

## Verification

python -c "from heretek_swarm.actors import HistorianAgent, CoderAgent, CatalystAgent, PerceiverAgent; print('Split subpackages OK')" && python -c "from heretek_swarm.actors.historian import _HISTORIAN_FILE; print(f'_HISTORIAN_FILE={_HISTORIAN_FILE}')"
