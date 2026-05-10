---
estimated_steps: 6
estimated_files: 4
skills_used: []
---

# T01: Create schemas/actors.py with consolidated Pydantic models

Read actors/validation.py and validation/agent_messages.py to identify all Pydantic model classes and enums. Create schemas/actors.py that:
1. Imports and re-exports MessageType, MessagePriority from validation/agent_messages.py
2. Imports and re-exports all request/response models from actors/validation.py (MessageContent, DeliberationRequest, MemoryStoreRequest, AnalysisRequest, ValidationRequest, QueryRequest, LineageRequest, HealthCheckRequest, SuspendResumeRequest, TerminateRequest, CollectiveTaskRequest, TaskRequest, DependencyRequest, CoordinationRequest, IMMUTABLE_RULES, BASELINE_CONFIG, get_immutable_rules, get_baseline_config)
3. Imports and re-exports all agent message models from validation/agent_messages.py (AgentMessageBase, ActorMessage, StateUpdate, ToolRequest, ToolResponse, CoordinationRequest, ConsensusProposal, ConsensusVote, ErrorMessage, TaskMessage, CodeExecutionRequest, MESSAGE_TYPES, validate_message, create_actor_message, create_state_update, create_tool_request, create_tool_response)
4. Adds a DEPRECATED module-level __getattr__ that emits a DeprecationWarning and returns the class for backward compatibility with old import paths (heretek_swarm.actors.base.core.ActorMessage -> heretek_swarm.schemas.actors.ActorMessage)
5. Does NOT import the dataclass ActorMessage from actors/base/core.py — that stays there for internal use

## Inputs

- None specified.

## Expected Output

- `heretek-swarm/heretek_swarm/schemas/actors.py`

## Verification

cd heretek-swarm && python -c "from heretek_swarm.schemas.actors import ActorMessage, MessageType, MESSAGE_TYPES; print('OK:', ActorMessage, MessageType)"
