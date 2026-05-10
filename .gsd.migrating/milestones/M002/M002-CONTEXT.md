# M002: Unify validation into a single entry point

**Gathered:** 2026-01-19
**Status:** Ready for planning

---

## Project Description

Consolidate all Pydantic message models and ValidationMixin into a single canonical location. Currently:
- `actors/mixins/validation.py` — contains `ValidationMixin` with Zero-Trust validation logic (behavioral baselines, anomaly detection, circular validation prevention)
- `actors/validation.py` — contains `validate_message()` used by `actors/base/core.py`
- `actors/base/core.py` — contains `ActorMessage` Pydantic model and calls both

## Why This Milestone

Three validation locations with subtle behavioral differences create maintenance burden and risk of inconsistency. When an actor receives a message, it may validate against different rules depending on which path is taken. There is no single place to reason about what "valid" means.

## User-Visible Outcome

### When this milestone is complete, the user can:

- `from heretek_swarm.schemas.actors import ActorMessage` — all Pydantic models in one importable module
- `from heretek_swarm.actors.mixins.validation import ValidationMixin` — the single canonical validator
- `pytest tests/` passes with no validation-related import or assertion errors
- Only one `ValidationMixin` exists; the duplicate in `actors/validation.py` and any in `actors/base/core.py` are deprecated/removed

### Entry point / environment

- Entry point: `pytest tests/` (Python test runner)
- Environment: local dev / CI
- Live dependencies: none (in-process only)

## Completion Class

- **Contract complete** means: all Pydantic models import from `heretek_swarm.schemas.actors`; `ValidationMixin` is the only mixin class found by grep; no duplicate `validate_message` functions exist
- **Integration complete** means: `pytest tests/` passes end-to-end; actor message passing still works with the refactored code
- **Operational complete** means: same as integration — no runtime lifecycle involved

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `from heretek_swarm.schemas.actors import ActorMessage` imports cleanly with no duplicate-model import errors
- `from heretek_swarm.actors.mixins.validation import ValidationMixin` is the only `ValidationMixin` in the codebase (verified by grep)
- `pytest tests/` passes with exit code 0
- A new unit test file `tests/test_validation_consolidation.py` covers the canonical validator with happy-path and failure-path cases

## Architectural Decisions

### Canonical ValidationMixin

**Decision:** `actors/mixins/validation.py` is the single source of truth for `ValidationMixin`. All actor message validation flows through it. The `validate_message` function in `actors/validation.py` is deprecated (stub left behind that re-exports from the mixin module for backward compatibility). `actors/base/core.py` loses its own copy.

**Rationale:** The `ValidationMixin` in `actors/mixins/` already has the richer behavior — Zero-Trust hooks, behavioral baselines, anomaly detection. The other locations are subsets of this logic. Making it canonical means one place to maintain validation policy.

**Alternatives Considered:**
- `actors/base/core.py` as canonical — rejected, because base class should be thin and delegate to mixins
- `actors/validation.py` as canonical — rejected, because it lacks the Zero-Trust behavioral tracking features

### Canonical Pydantic models location

**Decision:** All actor message Pydantic models (currently in `actors/base/core.py` and `validation/agent_messages.py`) are moved to `schemas/actors.py`. A `schemas/__init__.py` re-exports them as a public API surface.

**Rationale:** `schemas/` is the intended canonical location for all Pydantic models in the codebase (already contains `schemas/external_call_log.py`). Actors should not be the home of message models — models belong in schemas.

**Alternatives Considered:**
- Keep models in `actors/validation.py` — rejected, conflates validation logic with model definitions
- Keep models in `actors/base/core.py` — rejected, base class should not own data-transfer models

### Validation behavior

**Decision:** The canonical validator raises `ValidationError` (Pydantic-native) on failure rather than returning a tuple or monad.

**Rationale:** Consistent with Pydantic v2 idioms; callers already handle `pydantic.ValidationError`; avoids an extra branch on every validation call site.

**Alternatives Considered:**
- Return `(bool, str)` tuple — rejected, callers must always check bool; more error-prone
- Return `Result[T, E]` monad — rejected, adds a third-party or custom monad dependency for what Pydantic already does natively

## Error Handling Strategy

- `ValidationError` raised by Pydantic propagates to callers — no silent swallowed validation failures
- Timeout-protected validation (already in `ValidationMixin`) — 10ms timeout per validation step; fails open on timeout (logs anomaly, allows through)
- Deprecated stubs in `actors/validation.py` emit a `DeprecationWarning` when imported, pointing to the canonical path

## Risks and Unknowns

- Breaking existing callers of `actors/validation.py` or `actors/base/core.py` directly — mitigated by leaving deprecated stubs that re-export from canonical location
- Behavioral differences between the three locations are described as "subtle" but were not enumerated in the roadmap — S01 (the audit slice) is designed to surface them before refactoring begins

## Existing Codebase / Prior Art

- `heretek_swarm/actors/mixins/validation.py` — source of truth for `ValidationMixin`; has Zero-Trust features not present elsewhere
- `heretek_swarm/actors/validation.py` — partial `validate_message()`; will become a deprecated stub
- `heretek_swarm/actors/base/core.py` — has `ActorMessage` Pydantic model; will be refactored to import from `schemas/actors.py`
- `heretek_swarm/schemas/__init__.py` — already exists; will grow actor model exports
- `heretek_swarm/validation/agent_messages.py` — has full `ActorMessage` Pydantic model with `MessageType` enum; this module may be subsumed by `schemas/actors.py`

## Relevant Requirements

- No existing GSD requirements directly reference M002; this is a pure codebase hygiene milestone

## Scope

### In Scope

- Audit all three validation locations and document behavioral differences (S01)
- Move `ActorMessage` and related Pydantic models to `schemas/actors.py` (S02)
- Refactor `actors/base/core.py` to import from `schemas/actors.py` and delegate to `ValidationMixin` only (S02)
- Ensure backward-compat stubs exist for any removed/deprecated paths (S02, S03)
- Deprecate `actors/validation.py` as a standalone module (S03)
- Write `tests/test_validation_consolidation.py` with unit coverage (S03)

### Out of Scope / Non-Goals

- Adding new validation features (the Zero-Trust behavior already exists)
- Changing how actors are initialized or run
- Any changes to `validation/llm_output.py` (separate module, not actor-specific)
- Changing `actors/base/core.py` beyond moving models and delegation

## Technical Constraints

- Pydantic v2 — all models use `pydantic.BaseModel` with `model_config` and `model_validate`
- `pytest` — existing test runner; new tests must use pytest
- No new external dependencies beyond what is already installed

## Integration Points

- `pytest tests/` — the only integration surface; must pass without changes to test code itself
- Python import paths — any change to where `ActorMessage` lives must be reflected in all callers

## Testing Requirements

- **Unit tests** for the canonical `ValidationMixin`: happy-path validation, invalid input raises `ValidationError`, timeout behavior, circular validation prevention
- **Import tests**: `from heretek_swarm.schemas.actors import ActorMessage` works; no import errors for the deprecated stubs
- **Regression tests**: existing `pytest tests/` suite passes without modification (deprecation warnings are acceptable)

## Acceptance Criteria

- S01: A markdown document mapping each validation function to its canonical home
- S02: `from heretek_swarm.schemas.actors import ActorMessage` works
- S02: `actors/base/core.py` imports models from `schemas/actors.py` (no duplicate model definitions)
- S03: Only one `ValidationMixin` in the codebase
- S03: `tests/test_validation_consolidation.py` exists and covers the canonical path
- All slices: `pytest tests/` passes with exit code 0

## Open Questions

- Should `validation/agent_messages.py` be kept as-is, renamed, or subsumed entirely into `schemas/actors.py`? — current thinking: subsume into `schemas/actors.py` and leave a re-export stub for backward compat
