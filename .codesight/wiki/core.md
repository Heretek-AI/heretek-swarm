# Core

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Core subsystem handles **4 routes** and touches: auth, db.

## Routes

- `GET` `/available` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\core.py`
- `GET` `/types/{agent_type}` params(agent_type) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\core.py`
- `POST` `/deploy` → in: DeployAgentRequest [auth, db]
  `backend\heretek_swarm\api\agents\core.py`
- `DELETE` `/{instance_id}` params(instance_id) [auth, db]
  `backend\heretek_swarm\api\agents\core.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\core.py`

---
_Back to [overview.md](./overview.md)_