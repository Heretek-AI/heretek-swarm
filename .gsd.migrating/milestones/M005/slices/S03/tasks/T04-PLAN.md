---
estimated_steps: 7
estimated_files: 8
skills_used: []
---

# T04: Create echo subpackage with EchoActor→EchoAgent rename

**Create `actors/echo/types.py`:** Extract `CommunicationChannel(Enum)`, `MessagePriority(Enum)`, `CommunicationStyle`, `TranslationRule` from `actors/echo.py`.

**Create `actors/echo/agent.py`:** Copy the `EchoActor` class from `actors/echo.py` but **rename the class to `EchoAgent`**. Keep all mixins, methods, and imports identical. Import types from `.types`.

**Create `actors/echo/__init__.py`:** Absolute re-exports of CommunicationChannel, MessagePriority, CommunicationStyle, TranslationRule from `.types`, and `EchoAgent` from `.agent`.

**Update `actors/__init__.py`:** Change `from heretek_swarm.actors.echo import EchoActor` → `from heretek_swarm.actors.echo import EchoAgent`. Update `__all__` list: `"EchoActor"` → `"EchoAgent"`.

**Update `api/main.py`:** Change `from heretek_swarm.actors.echo import EchoActor` → `from heretek_swarm.actors.echo import EchoAgent` (line 213). Change `(EchoActor, "echo")` → `(EchoAgent, "echo")` (line 247).

**Update `runtime/main_loop.py`:** Change `from heretek_swarm.actors.echo import EchoActor` → `from heretek_swarm.actors.echo import EchoAgent` (line 742). Change `(EchoActor, "echo", [...])` → `(EchoAgent, "echo", [...])` (line 778).

**Update `docs/actors/README.md`:** Line 20: `echo.py` → `echo/agent.py`, `EchoActor` → `EchoAgent`. Line 344: `echo.py` → `echo/`, `EchoActor` → `EchoAgent`.

## Inputs

- `heretek-swarm/heretek_swarm/actors/echo.py`
- `heretek-swarm/heretek_swarm/actors/__init__.py`
- `heretek-swarm/heretek_swarm/api/main.py`
- `heretek-swarm/heretek_swarm/runtime/main_loop.py`
- `heretek-swarm/docs/actors/README.md`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/echo/__init__.py`
- `heretek-swarm/heretek_swarm/actors/echo/types.py`
- `heretek-swarm/heretek_swarm/actors/echo/agent.py`
- `heretek-swarm/heretek_swarm/actors/__init__.py`
- `heretek-swarm/heretek_swarm/api/main.py`
- `heretek-swarm/heretek_swarm/runtime/main_loop.py`
- `heretek-swarm/docs/actors/README.md`

## Verification

python -c "from heretek_swarm.actors import EchoAgent; print('EchoAgent import OK')" && ! python -c "from heretek_swarm.actors import EchoActor" 2>/dev/null && echo 'EchoActor removed from public API OK'
