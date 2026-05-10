# M006: Audit and plan repository restructure

**Restructure repo: nested heretek-swarm/ → flat backend/**

## What Happened

M006 planned the repository restructure. Produced three audit scripts and their output manifests.

## Cross-Slice Verification

M006 does not execute — it only plans. Verification is the audit scripts producing complete output.

## Requirement Changes

No requirements were modified — this is purely an infrastructure/planning milestone.

## Forward Intelligence

### What the next milestone should know
- Use `git mv heretek-swarm/ backend/` from repo root to preserve history
- Python imports inside `backend/` can stay as `from heretek_swarm.` if PYTHONPATH is set correctly
- CI workflows OUTSIDE `backend/` must use `backend/` prefix
- Docker compose and Dockerfile reference paths from repo root, not from inside the package

### What's fragile
- `swarm-dashboard/` may import the Python package via subprocess or file path — check before assuming it's unaffected

### What assumptions changed
- Assumed frontend was nested — it was already correctly placed at `swarm-dashboard/`
- The only real rename is `heretek-swarm/` → `backend/`

## Files Created/Modified

- `scripts/audit_files.py` — file inventory script
- `scripts/audit_imports.py` — import dependency map script
- `scripts/audit_workflows.py` — CI/workflow impact list script
- `PLAN.md` — consolidated audit results

---
id: M006
provides:
  - Complete file manifest with current→target paths
  - Import rewrite manifest
  - CI/workflow change manifest
key_decisions:
  - swarm-dashboard/ stays in place — already correctly placed
  - docs/, agent_workspace/, root files stay in place
  - Using `git mv` to preserve history
patterns_established: []
observability_surfaces: []
requirement_outcomes: []
duration: pending
verification_result: pending
completed_at: pending
