---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Run and fix full pytest suite

Run pytest tests/ with verbose output. Fix all failures and errors found. Pay special attention to import errors from the restructure (M006-M008). Add regression tests for any untested bugs discovered.

## Inputs

- `tests/`

## Expected Output

- `pytest tests/ — all tests pass, 0 failures, 0 errors`

## Verification

cd backend && pytest tests/ -v --tb=short 2>&1 | tail -5
