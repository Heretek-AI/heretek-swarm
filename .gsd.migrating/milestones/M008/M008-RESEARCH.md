# M008 — Research

**Date:** 2026-05-12

## Summary

M008 was auto-queued after M007 (repository restructure) completed, but **no explicit vision, brief, or requirements were defined**. The M008 ROADMAP.md is empty, the CONTEXT.md is a recovery-failure placeholder, and no REQUIREMENTS.md exists at the project level. This research therefore takes a **survey-first approach**: catalog the project's current state, surface the most impactful next directions, and recommend a path that the planner can slice meaningfully.

The project has recently completed a major repository restructure (M007: renaming `heretek-swarm/` to `backend/` via git mv across 463 files). With 411 Python files across ~40 subpackages and 62 test files, the codebase is mature but carries cleanup debt from the restructure. The most valuable next milestone would be a **Post-Restructure Cleanup & Hardening** pass — resolving known issues, fixing stale path references, removing tracked garbage files, and updating documentation to match the new layout — before embarking on new feature work.

## Recommendation

**Recommended direction: Post-Restructure Cleanup & Hardening (Phase 2 of the restructure pipeline).**

M006 planned the restructure. M007 executed the rename. M008 should **complete the restructure** by cleaning up what M007 deferred and hardening the result. This is the most cost-effective use of effort because:

1. **Low risk, high confidence** — cleanup work has clear success criteria and few unknowns
2. **Unblocks everything else** — stale references and garbage files create noise for every subsequent change
3. **Immediate impact** — the 12 garbage files and stale root files are visible to every developer/user

The alternative directions (new features, observability, testing expansion) are all valid but should wait until the restructure debt is fully paid.

## Implementation Landscape

### Key Files

| File/Dir | Status | What Needs To Change |
|----------|--------|---------------------|
| `=0.2.0`, `=0.23.0`, `=1.1.0`, `=1.8.0`, `=2.3.0`, `=24.0.0`, `=3.12.0`, `=3.5.0`, `=4.0.0`, `=4.1.0`, `=6.98.0`, `=8.0.0` | 12 garbage files at repo root | `git rm` — these were created during package build/version resolution and are tracked in git |
| `0` | ASCII text file at root | `git rm` — orphaned artifact |
| `triage_classifier.py` | Stale root-level script with pre-restructure path references | Move to `backend/` or remove; update internal path references |
| `audit/cli.py` | Stale directory with pre-restructure references | Move to `backend/heretek_swarm/audit/` or remove |
| `backend/heretek_swarm/audit/` | Canonical audit module co-existing with stale root `audit/` | Verify no import overlap; remove the stale root copy |
| `backend/pyproject.toml` | Build configuration | Verify all paths are correct post-restructure |
| `.github/workflows/ci.yml` | CI pipeline | Verify path references point to `backend/` (M007 updated some, verify no stale remain) |
| `.github/workflows/ci-cd.yml` | CI/CD pipeline | Same as above |
| `docs/ARCHITECTURE.md` | Architecture documentation | Update any references to old `heretek-swarm/` directory paths |
| `README.md` | Project root readme | Package structure diagram shows `heretek-swarm/` — update to `backend/` |
| `CLAUDE.md` | AI agent guidance | References `src/` which no longer exists — update to `backend/heretek_swarm/` |

### Build Order

1. **Clean tracked garbage files first** — `git rm` the 13 root-level orphan files (`=*.0` and `0`). These have zero dependencies and can be done in a single commit. Quickest win.
2. **Resolve stale root files** — `audit/cli.py` and `triage_classifier.py` contain pre-restructure path references. Either `git mv` to canonical locations or remove if they're superseded by `backend/` equivalents.
3. **Update stale path references in docs** — `README.md`, `CLAUDE.md`, and `docs/` files may reference old paths. Audit and fix.
4. **Verify CI/config path correctness** — Check `pyproject.toml`, `docker-compose.yml`, and workflow files for any remaining stale paths.
5. **Final validation** — Ensure `pytest`, `ruff`, and `mypy` pass with the cleaned structure.

### Verification Approach

```bash
# After each cleanup commit:
pytest tests/ --tb=short -q          # All tests must pass
ruff check backend/heretek_swarm/    # No linting regressions
grep -r "heretek-swarm" backend/     # Verify no stale path references remain
grep -r "src/" --include="*.py"      # Verify no stale src/ references
```

The sandbox cannot run these commands (no pip/pytest/ruff), so verification is deferred to the dev environment or CI push.

## Constraints

- **Sandbox limitations**: Full runtime verification (pip install, pytest, ruff, mypy, docker compose) cannot execute in the auto-mode sandbox. All verification relies on CI push or manual dev environment runs.
- **Git discipline**: Garbage file removal requires `git rm` to fully delete from tracking — `rm` alone leaves the files in git history and creates divergence.
- **No REQUIREMENTS.md**: There is no requirements document to validate against. All work in M008 should be validated against project conventions and CI green status.

## Common Pitfalls

- **Garbage files are tracked in git** — Running `rm` instead of `git rm` will leave the files in the index. Always use `git rm` and commit.
- **Pre-restructure path references in string literals** — Path references in docstrings, comments, and error messages are easy to miss. Use `grep` for `heretek-swarm/` and `src/` patterns broadly, not just in import statements.
- **`audit/` ambiguity** — There are two `audit/` directories: root `audit/` (stale) and `backend/heretek_swarm/audit/` (canonical). The stale one needs careful removal to avoid import breakage if something imports from it.

## Open Risks

- **M008 has no defined brief** — This research is projecting a cleanup direction in the absence of user-defined requirements. The planner should confirm this direction before proceeding, or provide an alternative brief.
- **The stale root files may contain unique logic** — `triage_classifier.py` and `audit/cli.py` may implement functionality not present in `backend/` equivalents. A code comparison is needed before deleting.

## Skills Discovered

No new skills were discovered or installed — the core technologies (Python, FastAPI, React, GitHub Actions) are already covered by existing installed skills in the ecosystem.

## Sources

- **PROJECT.md (inlined context)**: Known issues section explicitly documents 12 tracked `=X.Y.Z` garbage files, stale `audit/cli.py` and `triage_classifier.py`, and deferred cleanup.
- **M007 completion state**: git log confirms `heretek-swarm/ → backend/` rename via git mv completed, with path reference updates in CI/config files.
- **Filesystem survey**: 12 `=*.0` garbage files confirmed present at repo root via `ls`; `triage_classifier.py` and `audit/cli.py` confirmed present with pre-restructure path references.
