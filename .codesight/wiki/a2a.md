# A2a

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The A2a subsystem handles **2 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/api/a2a/messages` → out: PromptResponse [auth, db, cache, ai]
  `backend\heretek_swarm\api\main.py`
- `GET` `/api/a2a/messages/{from_agent}/{to_agent}` params(from_agent, to_agent) → out: PromptResponse [auth, db, cache, ai]
  `backend\heretek_swarm\api\main.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\main.py`

---
_Back to [overview.md](./overview.md)_