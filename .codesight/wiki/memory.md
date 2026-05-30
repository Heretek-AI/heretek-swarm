# Memory

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Memory subsystem handles **1 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/api/memory` → out: PromptResponse [auth, db, cache, ai]
  `backend\heretek_swarm\api\main.py`

## Related Models

- **memory_access_logs** (5 fields) → [database.md](./database.md)
- **memory_tier_state** (5 fields) → [database.md](./database.md)
- **agent_memory_config** (16 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\main.py`

---
_Back to [overview.md](./overview.md)_