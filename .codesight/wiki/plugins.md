# Plugins

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Plugins subsystem handles **7 routes** and touches: auth, db.

## Routes

- `GET` `/{plugin_id}` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `POST` `/{plugin_id}/enable` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `POST` `/{plugin_id}/disable` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `GET` `/{plugin_id}/config` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `PUT` `/{plugin_id}/config` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `GET` `/{plugin_id}/metrics` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`
- `GET` `/{plugin_id}/status` params(plugin_id) [auth, db]
  `backend\heretek_swarm\api\plugins.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\plugins.py`

---
_Back to [overview.md](./overview.md)_