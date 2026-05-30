# Memories

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Memories subsystem handles **9 routes** and touches: auth, db.

## Routes

- `POST` `/configure` → in: dict [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `POST` `/memories` → in: dict [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `GET` `/memories` [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `GET` `/memories/{memory_id}` params(memory_id) [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `PUT` `/memories/{memory_id}` params(memory_id) [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `DELETE` `/memories/{memory_id}` params(memory_id) [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `GET` `/memories/{memory_id}/history` params(memory_id) [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `DELETE` `/memories` [auth, db]
  `backend\heretek_swarm\api\memories.py`
- `POST` `/search` → in: dict [auth, db]
  `backend\heretek_swarm\api\memories.py`

## Related Models

- **swarm_memories** (4 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\memories.py`

---
_Back to [overview.md](./overview.md)_