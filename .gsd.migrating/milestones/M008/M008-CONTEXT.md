# M008: Post-Restructure Cleanup & Hardening — Context

## Summary

M008 completes the repository restructure (M006/M007) by cleaning up what was deferred. The work is purely cleanup — no functional code changes, no new features.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Slice ordering | Garbage → root files → docs → code → validation | Risk-first: medium-risk root file resolution (S02) happens early so findings inform downstream work |
| Validation basis | Project conventions + CI green status | No REQUIREMENTS.md exists; cleanup success criteria are self-evident |
| S02 approach | Code comparison before deletion | triage_classifier.py and audit/cli.py may contain unique logic; must cross-reference with backend/ equivalents before git rm |

## Reference Paths

- **Canonical audit module**: `backend/heretek_swarm/audit/` (has cli.py, report.py, severity.py, stub_patterns.py)
- **Stale root audit**: `audit/cli.py` — references `heretek-swarm/heretek_swarm/` in sys.path and defaults
- **Stale root classifier**: `triage_classifier.py` — references `ROOT / "heretek-swarm" / "heretek_swarm"` path
- **Garbage files**: 13 `=*.0` and `0` files at repo root
- **Key doc with stale refs**: `docs/ARCHITECTURE.md` (57 heretek-swarm/ directory refs), `README.md` (package diagram + CLI refs), `CLAUDE.md` (src/ refs)

## Verification Commands

```bash
# After each cleanup commit:
pytest tests/ --tb=short -q          # All tests must pass
ruff check backend/heretek_swarm/    # No linting regressions
grep -rn "heretek-swarm/" docs/      # Only CLI/PyPI refs remain, no directory refs
grep -rn "src/" --include="*.py" backend/heretek_swarm/  # Zero stale path refs
```

## Proof Strategy

- S02 resolves the uncertainty about unique logic in stale root files
- S03 + S04 use grep-based verification for stale refs
- S05 is the integration gate — full static validation
- Runtime verification (pytest, ruff, docker compose) deferred to CI push or dev environment

## Constraints

- Sandbox cannot run pip install, pytest, ruff, or docker compose
- git rm is required — rm alone leaves files tracked in the index
