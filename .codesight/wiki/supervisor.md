# Supervisor

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Supervisor subsystem handles **4 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/{agent_id}` params(agent_id) → in: st [auth]
  `backend\heretek_swarm\api\agents\supervisor.py`
- `GET` `/{agent_id}/metrics` params(agent_id) → in: st [auth]
  `backend\heretek_swarm\api\agents\supervisor.py`
- `POST` `/{agent_id}/terminate` params(agent_id) [auth]
  `backend\heretek_swarm\api\agents\supervisor.py`
- `GET` `/api/supervisor/status` → out: PromptResponse [auth, db, cache, ai]
  `backend\heretek_swarm\api\main.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\supervisor.py`
- `backend\heretek_swarm\api\main.py`

---
_Back to [overview.md](./overview.md)_