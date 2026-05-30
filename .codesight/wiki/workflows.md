# Workflows

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Workflows subsystem handles **9 routes** and touches: auth, db, cache.

## Routes

- `GET` `/{workflow_id}` params(workflow_id) → in: Annotated [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `POST` `/{workflow_id}/execute` params(workflow_id) → in: dict [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `PUT` `/{workflow_id}` params(workflow_id) [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `DELETE` `/{workflow_id}` params(workflow_id) [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `GET` `/{workflow_id}/status` params(workflow_id) → in: Annotated [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `POST` `/{workflow_id}/cancel` params(workflow_id) → in: dict [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `POST` `/{workflow_id}/validate` params(workflow_id) → in: dict [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `GET` `/events` → in: Annotated [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`
- `GET` `/{workflow_id}/events` params(workflow_id) → in: Annotated [auth, db, cache]
  `backend\heretek_swarm\api\workflows.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\workflows.py`

---
_Back to [overview.md](./overview.md)_