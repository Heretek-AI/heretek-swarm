# Historian

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Historian subsystem handles **1 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/api/historian/events` → out: PromptResponse [auth, db, cache, ai]
  `backend\heretek_swarm\api\main.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\main.py`

---
_Back to [overview.md](./overview.md)_