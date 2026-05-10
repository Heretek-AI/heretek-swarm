# M004: Add integration test scaffold and CI surface

**Vision:** 413 files with minimal test surface — establish a coverage baseline and a CI gate that prevents regressions. After this milestone, every PR runs pytest + ruff automatically, there is a canonical smoke test for agent lifecycle, and the test directory has a clear structure with fixtures reusable across agents.

## Success Criteria

- pytest collects all tests without collection errors
- At least one actor lifecycle test exists per canonical agent
- GitHub Actions CI runs pytest and ruff on push/PR
- CI completes in under 2min on a standard runner
- Ruff reports fewer than 50 warnings on the codebase

## Slices

- [ ] **S01: S01** `risk:low` `depends:[]`
  > After this: pytest --co -q lists all existing tests

- [ ] **S02: Write actor lifecycle smoke tests** `risk:medium` `depends:[]`
  > After this: pytest tests/test_actor_lifecycle.py -x -q passes

- [ ] **S03: Add GitHub Actions CI for pytest and ruff** `risk:low` `depends:[S02]`
  > After this: CI runs on push/PR and reports pass/fail

## Boundary Map

Not provided.
