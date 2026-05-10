# S01: Audit file inventory and plan

**Goal:** Scan the entire repo tree. Document each file's purpose and destination in the new structure. Identify all import rewrites and CI/workflow changes needed.
**Demo:** After this: a written plan with exact file moves, import rewrites, and CI fixes ready to execute.

## Must-Haves

- Every tracked file catalogued with current path and target path
- All cross-package import statements enumerated
- All GitHub workflow files inventoried
- No file left unmapped

## Proof Level

- This slice proves: audit-output
- Real runtime required: no
- Human/UAT required: no

## Verification

```bash
# Every file in the repo is catalogued
python scripts/audit_files.py  # lists all tracked files with current/target paths

# Import graph is complete
python scripts/audit_imports.py  # lists all Python import rewrites needed

# CI impact is documented
python scripts/audit_workflows.py  # lists all workflow files needing updates
```

If audit scripts don't exist, fall back to:
```bash
git ls-files | wc -l  # total tracked files
git ls-files heretek-swarm/ | wc -l  # files in the inner directory
```

## Tasks

- [ ] **T01: File inventory** `est:30m`
  - Why: Need a complete list of all tracked files before any moves
  - Files: `scripts/audit_files.py`
  - Do: Write `scripts/audit_files.py` that runs `git ls-files` and categorizes each file by destination: `backend/` (heretek-swarm/ contents), `swarm-dashboard/`, `docs/`, `.github/`, `agent_workspace/`, root
  - Verify: `python scripts/audit_files.py` outputs a complete list with current→target paths for all files
  - Done when: Every tracked file appears in the output with a destination path

- [ ] **T02: Import dependency map** `est:30m`
  - Why: Need to know every Python import that must change when heretek-swarm/ is renamed
  - Files: `scripts/audit_imports.py`
  - Do: Write `scripts/audit_imports.py` that greps all `.py` files for `from heretek_swarm.` and `import heretek_swarm.` patterns, outputs unique import statements with file:line
  - Verify: `python scripts/audit_imports.py` lists every import reference that needs updating
  - Done when: Every Python import referencing the package is enumerated

- [ ] **T03: CI/workflow impact list** `est:15m`
  - Why: CI workflows and Docker files reference paths that will change
  - Files: `scripts/audit_workflows.py`
  - Do: Write `scripts/audit_workflows.py` that greps `.github/workflows/*.yml`, `docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `setup.py`, `setup.cfg` for references to `heretek-swarm/` or `heretek_swarm/` paths
  - Verify: `python scripts/audit_workflows.py` lists every file that references old paths
  - Done when: Every CI file, Dockerfile, and config referencing old paths is enumerated

## Files Likely Touched

- `scripts/audit_files.py` (new)
- `scripts/audit_imports.py` (new)
- `scripts/audit_workflows.py` (new)
- `PLAN.md` (this file, updated with audit results)

## Integration Closure

N/A — documentation only

---
id: M006-S01
provides:
  - Complete file inventory with current→target paths
  - Import rewrite manifest
  - CI/workflow change manifest
key_decisions:
  - swarm-dashboard/ stays in place — already correctly placed outside heretek-swarm/
  - docs/, agent_workspace/ stay in place — already correctly placed
  - Root-level markdown files (PATH_TO_EMERGENCE.md, RALPH.md, etc.) stay in place
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: ~1.5h
verification_result: pending
completed_at: pending
