# Auth

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Auth subsystem handles **5 routes** and touches: auth, db, cache.

## Routes

- `POST` `/auth/token` [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/auth/revoke` [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/decision/{decision_id}/verify` params(decision_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/reset` → in: dict [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `POST` `/{plugin_id}/reset` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`

## Middleware

- **strategies** (auth) — `backend\heretek_swarm\actors\coordinator\strategies.py`
- **auth** (auth) — `backend\heretek_swarm\gateway\auth.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\consensus.py`
- `backend\heretek_swarm\api\memories.py`
- `backend\heretek_swarm\api\plugins.py`

---
_Back to [overview.md](./overview.md)_