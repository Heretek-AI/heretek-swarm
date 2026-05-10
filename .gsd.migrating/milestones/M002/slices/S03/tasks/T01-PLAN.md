---
estimated_steps: 14
estimated_files: 2
skills_used: []
---

# T01: Move IMMUTABLE_RULES and BASELINE_CONFIG into ValidationMixin

The ValidationMixin in actors/mixins/validation.py handles runtime behavioral baseline tracking but the IMMUTABLE_RULES constant (8 security patterns) and BASELINE_CONFIG dict live as module-level globals in actors/validation.py — a conceptual duplicate of what the mixin already owns at runtime.

**Steps:**
1. Add IMMUTABLE_RULES as a ValidationMixin class-level attribute (copy the 8-rule list from actors/validation.py)
2. Add BASELINE_CONFIG as a ValidationMixin class-level attribute
3. Add get_immutable_rules() as a @classmethod that returns a copy of IMMUTABLE_RULES
4. Add get_baseline_config() as a @classmethod that returns a copy of BASELINE_CONFIG
5. In actors/validation.py:
   - Add import: `from heretek_swarm.actors.mixins.validation import ValidationMixin`
   - Replace `IMMUTABLE_RULES = [...]` with `IMMUTABLE_RULES = ValidationMixin.IMMUTABLE_RULES`
   - Replace `BASELINE_CONFIG = {...}` with `BASELINE_CONFIG = ValidationMixin.BASELINE_CONFIG`
   - Replace `def get_immutable_rules()` with `get_immutable_rules = ValidationMixin.get_immutable_rules.__func__`
   - Replace `def get_baseline_config()` with `get_baseline_config = ValidationMixin.get_baseline_config.__func__`
6. Add a deprecation comment docstring at the top of the actors/validation.py module noting these constants now live in the mixin
7. Verify backward compat: both import paths work identically

## Inputs

- None specified.

## Expected Output

- `heretek-swarm/heretek_swarm/actors/mixins/validation.py`
- `heretek-swarm/heretek_swarm/actors/validation.py`

## Verification

cd C:/Users/Derek/Desktop/heretek-swarm && python -c "from heretek_swarm.actors.mixins.validation import ValidationMixin; rules = ValidationMixin.get_immutable_rules(); assert len(rules) > 0; print(f'OK: {len(rules)} rules in mixin')" && python -c "from heretek_swarm.actors.validation import get_immutable_rules; rules = get_immutable_rules(); assert len(rules) > 0; print(f'OK: backward-compat returns {len(rules)} rules')"
