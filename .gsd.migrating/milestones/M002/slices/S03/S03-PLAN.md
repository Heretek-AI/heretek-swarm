# S03: Consolidate ValidationMixin and deprecate duplicates

**Goal:** Consolidate IMMUTABLE_RULES and BASELINE_CONFIG from actors/validation.py into the ValidationMixin, making the mixin the single source of truth for behavioral baseline validation, with backward-compat shims left in place
**Demo:** Only one ValidationMixin exists in the codebase

## Must-Haves

- IMMUTABLE_RULES is a ValidationMixin class attribute, not a module-level global in actors/validation.py\n- ValidationMixin.get_immutable_rules() returns the 8 security rules\n- actors/validation.py re-exports IMMUTABLE_RULES from the mixin for backward compat\n- All existing callers of actors.validation.validate_message work unchanged\n- pytest tests/ passes

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Move IMMUTABLE_RULES and BASELINE_CONFIG into ValidationMixin** `est:25m`
  The ValidationMixin in actors/mixins/validation.py handles runtime behavioral baseline tracking but the IMMUTABLE_RULES constant (8 security patterns) and BASELINE_CONFIG dict live as module-level globals in actors/validation.py — a conceptual duplicate of what the mixin already owns at runtime.
  - Files: `heretek-swarm/heretek_swarm/actors/mixins/validation.py`, `heretek-swarm/heretek_swarm/actors/validation.py`
  - Verify: cd C:/Users/Derek/Desktop/heretek-swarm && python -c "from heretek_swarm.actors.mixins.validation import ValidationMixin; rules = ValidationMixin.get_immutable_rules(); assert len(rules) > 0; print(f'OK: {len(rules)} rules in mixin')" && python -c "from heretek_swarm.actors.validation import get_immutable_rules; rules = get_immutable_rules(); assert len(rules) > 0; print(f'OK: backward-compat returns {len(rules)} rules')"

- [x] **T02: Verify full test suite passes** `est:10m`
  After T01's refactoring, run the full pytest suite and confirm everything passes. Since backward-compat shims are in place, all ~40 existing callers work unchanged.
  - Files: `heretek-swarm/heretek_swarm/actors/mixins/validation.py`, `heretek-swarm/heretek_swarm/actors/validation.py`
  - Verify: cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20

- [x] **T03: Verify full test suite passes** `est:15m`
  After the changes above, run the full test suite. Fix any failures caused by import restructuring. Key things to check:
  - All import paths in the ~40 files that reference actors.validation still work
  - base/core.py's _validate_message_content() still works
  - supervisor.py, steward.py, explorer.py, sentinel/agent.py still import and use ValidationMixin correctly
  - Files: `heretek-swarm/heretek_swarm/actors/validation.py`, `heretek-swarm/heretek_swarm/actors/mixins/validation.py`
  - Verify: cd C:/Users/Derek/Desktop/heretek-swarm && python -m pytest tests/ -x -q --tb=short

## Files Likely Touched

- heretek-swarm/heretek_swarm/actors/mixins/validation.py
- heretek-swarm/heretek_swarm/actors/validation.py
