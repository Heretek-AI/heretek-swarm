---
id: S02
milestone: M008
status: ready
---

# S02: Resolve stale root files — Context

## Goal

Delete both stale root files (`triage_classifier.py`, `audit/cli.py`) and their tightly-coupled data artifacts (`audit-report.md`, `triage_data.json`) after confirming all logic is superseded by `backend/` equivalents or was a one-off tool with no ongoing value.

## Why this Slice

S02 is the highest-risk slice in M008 — it resolves the uncertainty about whether stale root files contain unique logic. Completing it unblocks the mechanical documentation updates in S03 and code-string updates in S04, which both assume a clean root. A developer encountering `triage_classifier.py` or `audit/cli.py` at the repo root would reasonably assume they are active tools; their stale `heretek-swarm/` path references make them actively misleading.

## Scope

### In Scope

- **`git rm audit/cli.py`** — Stale root audit CLI. ~90% identical to `backend/heretek_swarm/audit/cli.py`. The canonical version has functional improvements: imports `group_by_severity` from `report.py` and `DEFAULT_EXTENSIONS` from `stub_patterns.py`. The stale version hardcodes extensions and lacks `group_by_severity`. Zero code in `backend/` imports from this file. Clear deletion.
- **`git rm triage_classifier.py`** — 330-line standalone AST-based audit classifier. One-off tool built for a completed audit run. References `ROOT / "heretek-swarm" / "heretek_swarm"` (broken path). No backend equivalent exists, and no code references it. The capability is not needed going forward.
- **`git rm audit-report.md`** — 71KB input to `triage_classifier.py`. Stale audit report from a prior run. No code reads it.
- **`git rm triage_data.json`** — 173KB output of `triage_classifier.py`. Classified findings JSON. No code reads it.
- **Remove empty `audit/` directory** — The root `audit/` directory contains only `cli.py`; after deletion it should be cleaned up.

### Out of Scope

- Any changes to `backend/heretek_swarm/audit/` — the canonical audit module is untouched
- Path reference fixes in remaining code (S03, S04)
- `.gitignore` rules (S01 already added `=*`)
- Verification commands beyond static checks (pytest/ruff deferred to dev environment)
- Any new code or functionality

## Constraints

- **`git rm` is required** — `rm` alone leaves files tracked in the index. All four files are confirmed tracked in git (`git ls-files` verifies each).
- **Must not break `backend/heretek_swarm/audit/`** — The canonical audit module (`__init__.py`, `cli.py`, `report.py`, `severity.py`, `stub_patterns.py`) must remain fully functional. No imports or re-exports reference the stale files.
- **Sandbox cannot run pytest/ruff** — Verification is static only (git status, file existence checks, grep for stale references).

## Integration Points

### Consumes

- `audit/cli.py` — Stale root file to be deleted
- `triage_classifier.py` — Stale root file to be deleted
- `audit-report.md` — Coupled data artifact to be deleted
- `triage_data.json` — Coupled data artifact to be deleted

### Produces

- A clean repo root with zero stale Python files or audit artifacts
- A root `audit/` directory that no longer exists (canonical audit lives at `backend/heretek_swarm/audit/`)
- No new files

## Open Questions

None. All decisions resolved:
- `triage_classifier.py` → Delete (was one-off tool, no backend equivalent, broken paths)
- `audit/cli.py` → Delete (superseded by canonical `backend/heretek_swarm/audit/cli.py`)
- `audit-report.md` + `triage_data.json` → Bundle-delete with the classifier (tightly coupled, zero references)
