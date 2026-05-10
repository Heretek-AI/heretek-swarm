# S03: Consolidate ValidationMixin and deprecate duplicates — UAT

**Milestone:** M002
**Written:** 2026-05-07T16:11:57.235Z

# S03: Consolidate ValidationMixin — UAT

**Milestone:** M002
**Written:** 2026-05-07

## UAT Type

- UAT mode: **artifact-driven**
- Why this mode is sufficient: This slice was a pure structural refactoring — no runtime behavior changes. All verification is done via static analysis of the code structure and the existing test suite.

## Preconditions

None — no runtime services required. Verification is structural and test-based.

## Smoke Test

```python
from heretek_swarm.actors.mixins.validation import ValidationMixin
rules = ValidationMixin.get_immutable_rules()
assert len(rules) == 8
```

## Test Cases

### 1. ValidationMixin is the single canonical source

1. Search the entire `heretek_swarm/` tree for `class ValidationMixin`.
2. **Expected:** Exactly one definition found, at `actors/mixins/validation.py`.

### 2. IMMUTABLE_RULES is a ValidationMixin class attribute

1. Inspect `ValidationMixin.IMMUTABLE_RULES`.
2. **Expected:** A list of 8 dicts, each with keys `pattern`, `severity`, `description`, `action`.

### 3. BASELINE_CONFIG is a ValidationMixin class attribute

1. Inspect `ValidationMixin.BASELINE_CONFIG`.
2. **Expected:** A dict with 9 keys: `initialization_mode`, `learning_period`, `anomaly_threshold`, `min_baseline_samples`, `baseline_decay_factor`, `max_baseline_age_hours`, `enable_immutable_rules`, `enable_behavioral_learning`, `flag_anomalies_until_baseline`.

### 4. get_immutable_rules() and get_baseline_config() return correct data

1. Call `ValidationMixin.get_immutable_rules()`.
2. **Expected:** Returns a deep copy of the 8-element IMMUTABLE_RULES list.
3. Call `ValidationMixin.get_baseline_config()`.
4. **Expected:** Returns a deep copy of the 9-key BASELINE_CONFIG dict.

### 5. Backward-compat shims in actors/validation.py work

1. `from heretek_swarm.actors.validation import IMMUTABLE_RULES` — resolves.
2. `from heretek_swarm.actors.validation import BASELINE_CONFIG` — resolves.
3. `from heretek_swarm.actors.validation import get_immutable_rules` — resolves, returns 8 rules.
4. `from heretek_swarm.actors.validation import get_baseline_config` — resolves, returns 9 keys.
5. **Expected:** All four imports resolve and return data identical to the mixin.

### 6. Full test suite passes

1. Run `pytest tests/ -x -q --tb=short`.
2. **Expected:** All tests pass (659 passed), zero failures.

## Edge Cases

### Import chain: base/core.py delegates validation to actors/validation.py only

1. Inspect `base/core.py` for validation imports.
2. **Expected:** It imports `validate_message` from `actors/validation` — does NOT directly import from `actors/mixins/validation` for message validation.

## Failure Signals

- `ImportError` when resolving any backward-compat import path.
- Test count decreases from 659.
- More than one `class ValidationMixin` definition found.

## Not Proven By This UAT

- Runtime behavioral correctness of validation logic — covered by the existing test suite (all 659 tests pass).
- Integration with external infrastructure (requires HERETEK_RUN_INTEGRATION=1) — 1 skipped test.
- Performance characteristics of the refactored imports.

## Notes for Tester

This UAT is structural. All assertions can be verified via Python one-liners and grep. No runtime services needed.
