# Providers_config

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Providers_config subsystem handles **10 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/llm` [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `POST` `/llm` [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `PUT` `/llm/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `DELETE` `/llm/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `POST` `/llm/{provider_id}/test` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `GET` `/embedding` [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `POST` `/embedding` [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `PUT` `/embedding/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `DELETE` `/embedding/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`
- `POST` `/embedding/{provider_id}/test` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\providers_config.py`

## Related Models

- **agent_memory_config** (16 fields) → [database.md](./database.md)
- **agent_consensus_config** (18 fields) → [database.md](./database.md)
- **llm_providers** (14 fields) → [database.md](./database.md)
- **embedding_providers** (11 fields) → [database.md](./database.md)
- **config_audit_log** (5 fields) → [database.md](./database.md)
- **config_cache** (2 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\providers_config.py`

---
_Back to [overview.md](./overview.md)_