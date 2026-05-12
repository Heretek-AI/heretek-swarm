# S03: Update documentation path references — UAT

**Milestone:** M008
**Written:** 2026-05-12T22:22:21.506Z

## S03 UAT: Documentation Path Reference Updates

### Verification Gates

| # | Check | Result |
|---|-------|--------|
| 1 | `grep -r 'heretek-swarm/' docs/` — only CLI/PyPI/project-name refs remain | ✅ PASS — 14 remaining refs are all legitimate (GitHub URLs, SSM params, CLI config, log paths) |
| 2 | `grep -rn 'src/heretek_swarm' docs/` — zero matches | ✅ PASS — all 20 doc files updated |
| 3 | `grep -q 'src/' CLAUDE.md` — exit 1 | ✅ PASS — no src/ references remain |
| 4 | `grep -q '^backend/' README.md` — exit 0 | ✅ PASS — backend/ is the root directory entry |

### Files Modified

- **docs/ARCHITECTURE.md** — 54 path replacements + directory tree root
- **20 doc files** — src/heretek_swarm → backend/heretek_swarm sweep
- **README.md** — directory tree, install instructions, docker compose path
- **CLAUDE.md** — removed src/ references, updated ruff/mypy commands

### Verdict

**✅ PASS** — All verification criteria met. No functional changes, docs-only cleanup.
