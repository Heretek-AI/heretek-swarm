# Lifecycle

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Lifecycle subsystem handles **5 routes** and touches: auth.

## Routes

- `POST` `/{instance_id}/start` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\lifecycle.py`
- `POST` `/{instance_id}/stop` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\lifecycle.py`
- `POST` `/{instance_id}/suspend` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\lifecycle.py`
- `POST` `/{instance_id}/resume` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\lifecycle.py`
- `PUT` `/{instance_id}/config` params(instance_id) [auth]
  `backend\heretek_swarm\api\agents\lifecycle.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\lifecycle.py`

---
_Back to [overview.md](./overview.md)_