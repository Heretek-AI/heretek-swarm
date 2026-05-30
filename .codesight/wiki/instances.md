# Instances

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Instances subsystem handles **10 routes** and touches: auth, db.

## Routes

- `GET` `/instances` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}/logs` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}/memory` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}/tools` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}/tasks` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/stats` → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `GET` `/{instance_id}/channels` params(instance_id) → in: Annotated [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `POST` `/{instance_id}/channels` params(instance_id) [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`
- `DELETE` `/{instance_id}/channels/{channel_name}` params(instance_id, channel_name) [auth, db]
  `backend\heretek_swarm\api\agents\instances.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\agents\instances.py`

---
_Back to [overview.md](./overview.md)_