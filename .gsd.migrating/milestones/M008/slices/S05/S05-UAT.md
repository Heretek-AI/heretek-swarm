# S05: Final validation pass — UAT

**Milestone:** M008
**Written:** 2026-05-12T23:54:17.450Z

# S05: Final validation pass — UAT

**Milestone:** M008
**Written:** 2026-05-12

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S05 is a pure verification slice — all checks are static grep/git-ls-files/file-content reviews. No runtime code exists to exercise.

## Preconditions

- Working directory is the repository root
- Git repository with M008 S01-S04 changes committed or staged
- Bash shell available (Windows git-bash or WSL)

## Smoke Test

```bash
test -f .gsd/milestones/M008/M008-SUMMARY.md && echo "SMOKE PASS" || echo "SMOKE FAIL"
```

## Test Cases

### 1. Stale `src/` refs absent from Python code

1. Run: `grep -rn 'src/' --include='*.py' backend/heretek_swarm/`
2. **Expected:** Exit code 1 (no matches). Zero lines returned.

### 2. Docs `heretek-swarm/` references are all legitimate

1. Run: `grep -rn 'heretek-swarm/' docs/`
2. **Expected:** Exit code 0. All returned lines must be one of: GitHub repo URLs (`github.com/HeretekAI/heretek-swarm`), CLI config paths (`~/.heretek-swarm/`), SSM parameter paths (`/heretek-swarm/dev/`), or log paths (`/var/log/heretek-swarm/`). Zero stale directory references.

### 3. CLAUDE.md has no `src/` references

1. Run: `grep -n 'src/' CLAUDE.md`
2. **Expected:** Exit code 1 (no matches).

### 4. CI workflows have no stale path references

1. Run: `grep -rn 'heretek-swarm/\|src/' .github/workflows/`
2. **Expected:** Exit code 1 (no matches).

### 5. pyproject.toml uses `backend/` paths

1. Run: `grep 'backend/' pyproject.toml`
2. **Expected:** At least 1 match. Zero `src/` directory references (only legitimate GitHub project URLs allowed).

### 6. Dockerfile uses `backend/` paths

1. Run: `grep -n 'src/' backend/Dockerfile`
2. **Expected:** Exit code 1 (no matches). Dockerfile uses `COPY backend ./backend` and `backend/` paths throughout.

### 7. Zero tracked garbage files (S01 closure)

1. Run: `git ls-files '=*.0' '=0' '0'`
2. **Expected:** Exit code 0 with empty output.

### 8. Zero stale root files (S02 closure)

1. Run: `git ls-files 'triage_classifier.py' 'audit/cli.py' 'audit-report.md' 'triage_data.json'`
2. **Expected:** Exit code 0 with empty output.

### 9. M008-SUMMARY.md content verification

1. Run: `grep -c 'S05\|verification\|pytest\|ruff' .gsd/milestones/M008/M008-SUMMARY.md`
2. **Expected:** Returns a number >= 1 (file contains milestone summary content).

## Edge Cases

### BusyBox grep on Windows

1. Use `grep -rn` (not `grep -r` alone) or use `git grep` as fallback
2. **Expected:** grep commands return correct exit codes. If BusyBox `grep` behaves unexpectedly, use `git grep` which is consistent across platforms.

## Failure Signals

- Any non-zero exit code from checks 3, 4, 6 would indicate stale refs remain
- Any grep result containing `src/` as a directory path (not as a legitimate word like "source") in checks 1-6 would be a failure
- Missing M008-SUMMARY.md indicates T02 was not completed

## Not Proven By This UAT

- pytest unit tests pass — requires dev environment with `pip install -e ".[dev]"`
- ruff check clean — requires dev environment
- These are deliberately deferred; M008 is structural-only cleanup with zero functional changes

## Notes for Tester

- The 14 remaining `heretek-swarm/` references in docs/ are intentional and legitimate — do not flag them as failures
- If BusyBox grep returns unexpected exit codes, substitute with `git grep` for equivalent checks
- pytest/ruff are deferred to actual dev environment — this UAT does not attempt to run them
