---
estimated_steps: 6
estimated_files: 6
skills_used: []
---

# T03: Create handoff subpackage with deduplication

**Key challenge:** HandoffContext and HandoffResult are defined identically in both `handoff.py` and `handoff_handlers.py`. Create a single `handoff/types.py` with the deduplicated definitions.

**Create `handoff/types.py`:** One copy of `HandoffContext` (dataclass) and `HandoffResult` (dataclass), `HandoffValidator`, `AgentHandoff`, from the original `handoff.py`. Preserve all field definitions exactly.

**Create `handoff/orchestrator.py`:** Copy from the original `actors/handoff.py` minus the type definitions (HandoffContext, HandoffResult, HandoffValidator, AgentHandoff) that now live in types.py. Import them from `.types`. Keep HandoffStrategy(ABC), TaskTypeStrategy, PerformanceStrategy, LoadBalancingStrategy, HandoffOrchestrator.

**Create `handoff/handlers.py`:** Copy from the original `actors/handoff_handlers.py` minus the duplicate HandoffContext, HandoffResult definitions. Import them from `.types`. Keep HandoffValidationHandler, HandoffRateLimitHandler, HandoffTransferHandler, HandoffLoggingHandler, HandoffProcessor.

**Create `handoff/__init__.py`:** Absolute re-exports importing all public classes from the subpackage modules: HandoffContext, HandoffResult from .types; HandoffStrategy, TaskTypeStrategy, PerformanceStrategy, LoadBalancingStrategy, HandoffOrchestrator from .orchestrator; HandoffValidationHandler, HandoffRateLimitHandler, HandoffTransferHandler, HandoffLoggingHandler, HandoffProcessor from .handlers.

**Constraint:** Do NOT add Handoff classes to `actors/__init__.py` — they remain internal.

## Inputs

- `heretek-swarm/heretek_swarm/actors/handoff.py`
- `heretek-swarm/heretek_swarm/actors/handoff_handlers.py`

## Expected Output

- `heretek-swarm/heretek_swarm/actors/handoff/__init__.py`
- `heretek-swarm/heretek_swarm/actors/handoff/types.py`
- `heretek-swarm/heretek_swarm/actors/handoff/orchestrator.py`
- `heretek-swarm/heretek_swarm/actors/handoff/handlers.py`

## Verification

python -c "from heretek_swarm.actors.handoff import HandoffContext, HandoffResult, HandoffOrchestrator; print('Handoff subpackage OK')" && python -c "from heretek_swarm.actors.handoff.handlers import HandoffProcessor; print('Handoff handlers import OK')"
