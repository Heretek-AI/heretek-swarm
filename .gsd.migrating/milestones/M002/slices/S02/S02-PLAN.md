# S02: Move Pydantic models to schemas/ and refactor base/core.py

**Goal:** Create schemas/actors.py consolidating all Pydantic models for actors, refactor actors/base/core.py to import from it, and update all callers so that from heretek_swarm.schemas.actors import ActorMessage works cleanly.
**Demo:** from heretek_swarm.schemas.actors import ActorMessage works

## Must-Haves

- `from heretek_swarm.schemas.actors import ActorMessage` imports cleanly\n- `actors/base/core.py` imports ActorMessage Pydantic model from schemas.actors\n- `actors/base/core.py` still has its own internal dataclass ActorMessage (distinct from Pydantic)\n- pytest tests/ passes with no validation-related import errors\n- No Pydantic models are duplicated between actors/validation.py and validation/agent_messages.py (consolidated in schemas/actors.py)", "proofLevel">contract

## Integration Closure

schemas/actors.py is the single canonical home for all actor Pydantic models. actors/validation.py and validation/agent_messages.py re-export from schemas/actors.py for backward compatibility. actors/base/core.py uses schemas.actors for its Pydantic import. No other wiring changes required for this slice.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Create schemas/actors.py with consolidated Pydantic models** `est:45m`
  Read actors/validation.py and validation/agent_messages.py to identify all Pydantic model classes and enums. Create schemas/actors.py that:
  1. Imports and re-exports MessageType, MessagePriority from validation/agent_messages.py
  2. Imports and re-exports all request/response models from actors/validation.py (MessageContent, DeliberationRequest, MemoryStoreRequest, AnalysisRequest, ValidationRequest, QueryRequest, LineageRequest, HealthCheckRequest, SuspendResumeRequest, TerminateRequest, CollectiveTaskRequest, TaskRequest, DependencyRequest, CoordinationRequest, IMMUTABLE_RULES, BASELINE_CONFIG, get_immutable_rules, get_baseline_config)
  3. Imports and re-exports all agent message models from validation/agent_messages.py (AgentMessageBase, ActorMessage, StateUpdate, ToolRequest, ToolResponse, CoordinationRequest, ConsensusProposal, ConsensusVote, ErrorMessage, TaskMessage, CodeExecutionRequest, MESSAGE_TYPES, validate_message, create_actor_message, create_state_update, create_tool_request, create_tool_response)
  4. Adds a DEPRECATED module-level __getattr__ that emits a DeprecationWarning and returns the class for backward compatibility with old import paths (heretek_swarm.actors.base.core.ActorMessage -> heretek_swarm.schemas.actors.ActorMessage)
  5. Does NOT import the dataclass ActorMessage from actors/base/core.py — that stays there for internal use
  - Files: `heretek-swarm/heretek_swarm/actors/validation.py`, `heretek-swarm/heretek_swarm/validation/agent_messages.py`, `heretek-swarm/heretek_swarm/schemas/__init__.py`, `heretek-swarm/heretek_swarm/schemas/actors.py (new)`
  - Verify: cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage, MessageType, MESSAGE_TYPES; print('OK:', ActorMessage, MessageType)"

- [x] **T02: Update actors/base/core.py to import Pydantic models from schemas.actors** `est:30m`
  Edit actors/base/core.py:
  1. Remove all Pydantic model definitions (dataclass ActorMessage stays — it's internal, not the Pydantic one)
  2. Keep ActorState and ActorStatus dataclasses
  3. Keep AgentActor class
  4. Add import: from heretek_swarm.schemas.actors import ActorMessage as PydanticActorMessage
  5. Add backward-compat alias at module bottom: ActorMessage = PydanticActorMessage (so existing code that imports ActorMessage from actors.base.core still works)
  6. Update _validate_message_content docstring to reference the schemas.actors import path
  - Files: `heretek-swarm/heretek_swarm/actors/base/core.py`, `heretek-swarm/heretek_swarm/schemas/actors.py`
  - Verify: cd heretek-swarm && python -c "from heretek_swarm.actors.base.core import ActorMessage as AM; print('dataclass OK:', type(AM).__name__)" && python -c "from heretek_swarm.schemas.actors import ActorMessage as PA; print('Pydantic OK:', type(PA).__name__, PA.__bases__)"

- [x] **T03: Find and update all callers importing ActorMessage from old paths** `est:30m`
  Use grep to find all files importing ActorMessage from actors.base.core or actors.validation or validation.agent_messages. For each file:
  1. Update the import to use heretek_swarm.schemas.actors
  2. If the file uses the dataclass ActorMessage (from actors.base.core), update the import name to avoid collision
  3. Add from heretek_swarm.schemas.actors import ActorMessage as PydanticActorMessage if the Pydantic version is needed
  Run grep: grep -r "from heretek_swarm.actors" --include="*.py" | grep -i "import.*ActorMessage\|import.*MessageType" | grep -v __pycache__
  - Files: `(grep results determine files)`
  - Verify: cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage; print('ActorMessage from schemas OK')" && python -c "from heretek_swarm.actors.base.core import AgentActor; print('AgentActor OK')" && python -c "from heretek_swarm.actors.validation import validate_message; print('validate_message OK')"

- [x] **T04: Run pytest to verify no import or validation errors** `est:20m`
  Run the full test suite to ensure the refactoring introduces no regressions:
  1. cd heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | head -50
  2. If there are import errors, fix them
  3. If there are ValidationError failures, ensure they existed before (regression check)
  4. Final verification: python -c "from heretek_swarm.schemas.actors import ActorMessage, MESSAGE_TYPES; print('ActorMessage fields:', list(ActorMessage.model_fields.keys()))"
  - Files: `heretek-swarm/heretek_swarm/schemas/actors.py`, `heretek-swarm/heretek_swarm/actors/base/core.py`
  - Verify: cd heretek-swarm && python -m pytest tests/ -x -q --tb=short; echo "EXIT:$?"

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/validation.py
- heretek-swarm/heretek_swarm/validation/agent_messages.py
- heretek-swarm/heretek_swarm/schemas/__init__.py
- heretek-swarm/heretek_swarm/schemas/actors.py (new)
- heretek-swarm/heretek_swarm/actors/base/core.py
- heretek-swarm/heretek_swarm/schemas/actors.py
- (grep results determine files)
