---
estimated_steps: 6
estimated_files: 7
skills_used: []
---

# T01: Delete stale artifacts from pre-rename state

Delete four groups of stale directories/files left behind by the git mv:

1. `src/` — contains `cli.py` (537-line partial/older copy of canonical `heretek_swarm/cli.py`), `__init__.py`, and `agent_workspace/error.txt`. The canonical CLI lives in `backend/heretek_swarm/cli.py` (1831 lines).
2. `backend/docs/` — contains only `actors/README.md`. The canonical `docs/` at repo root (~20 files) is the complete documentation.
3. `backend/agent_workspace/` — contains 6 agent `MEMORY.md` files. The canonical `agent_workspace/` at repo root has 9 agents.
4. `backend/.claude/` — contains `tdd-guard/data/test.json`, a stale Claude project config from the old location.

Use `git rm -r` for git-tracked items, then `rm -rf` for untracked items. Do NOT delete `backend/heretek_swarm/agent_workspace/` — that's the real runtime agent workspace inside the package.

## Inputs

- None specified.

## Expected Output

- `src/cli.py`
- `src/__init__.py`
- `src/agent_workspace/error.txt`
- `backend/docs/actors/README.md`
- `backend/agent_workspace/agents/*/MEMORY.md`
- `backend/agent_workspace/error.txt`
- `backend/.claude/tdd-guard/data/test.json`

## Verification

test ! -d src && test ! -d backend/docs && test ! -d backend/agent_workspace && test ! -d backend/.claude
