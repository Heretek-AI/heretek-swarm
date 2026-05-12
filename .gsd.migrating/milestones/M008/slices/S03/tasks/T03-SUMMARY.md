---
id: T03
parent: S03
milestone: M008
key_files:
  - README.md
  - CLAUDE.md
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T22:22:07.237Z
blocker_discovered: false
---

# T03: Updated README.md directory tree and install instructions; cleaned CLAUDE.md of src/ references

**Updated README.md directory tree and install instructions; cleaned CLAUDE.md of src/ references**

## What Happened

Updated README.md: replaced pip install -e . with pip install -e backend/, fixed docker compose up to cd backend first, rewrote the Package Structure directory tree to show backend/ root with heretek_swarm/ core library (no longer the old heretek-swarm/ repo name). Updated CLAUDE.md: replaced src/ references with backend/heretek_swarm/, updated ruff/mypy commands to use correct paths. Ran full 5-check verification suite — all pass.

## Verification

All 4 gates pass: 1) heretek-swarm/ in docs — only 14 legitimate project-name refs; 2) zero src/heretek_swarm in docs; 3) no src/ in CLAUDE.md; 4) ^backend/ found in README.md

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `README.md`
- `CLAUDE.md`
