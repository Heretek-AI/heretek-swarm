# Memory_versions

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Memory_versions subsystem handles **10 routes** and touches: auth.

## Routes

- `POST` `/snapshot` → in: Annotated [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/labels` → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/head` → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/{version_id}` params(version_id) → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/{version_id}/entries` params(version_id) → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/diff/{from_version}/{to_version}` params(from_version, to_version) → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `POST` `/{version_id}/restore` params(version_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `POST` `/{version_id}/label/{label}` params(version_id, label) → in: Annotated [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/label/{label}` params(label) → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`
- `GET` `/statistics` → in: dic [auth]
  `backend\heretek_swarm\api\memory_versions.py`

## Related Models

- **memory_access_logs** (5 fields) → [database.md](./database.md)
- **memory_tier_state** (5 fields) → [database.md](./database.md)
- **agent_memory_config** (16 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\memory_versions.py`

---
_Back to [overview.md](./overview.md)_