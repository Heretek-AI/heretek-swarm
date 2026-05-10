# S02: Move Pydantic models to schemas/ and refactor base/core.py — UAT

**Milestone:** M002
**Written:** 2026-05-07T13:46:47.869Z

## UAT: schemas.actors Unified Pydantic Entry Point

### UAT-1: Canonical import works
**Given** the schemas/actors.py module exists
**When** I run `from heretek_swarm.schemas.actors import ActorMessage, MESSAGE_TYPES`
**Then** it imports cleanly and `ActorMessage.model_fields` contains the expected Pydantic fields
**Result:** ✅ Verified — fields: `['message_id', 'message_type', 'sender_id', 'recipient_id', 'timestamp', 'priority', 'correlation_id', 'metadata', 'content']`

### UAT-2: Backward compatibility preserved
**Given** existing code imports `ActorMessage` from `heretek_swarm.actors.base.core`
**When** I run that import
**Then** it still resolves to the internal dataclass (distinct from Pydantic)
**Result:** ✅ Verified — both import paths work and resolve to different classes

### UAT-3: No test regressions
**Given** the refactoring is complete
**When** I run the full pytest suite
**Then** all tests pass with exit code 0
**Result:** ✅ Verified — 386 tests pass, exit 0
