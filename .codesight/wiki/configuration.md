# Configuration

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Configuration subsystem handles **28 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/{key}` params(key) [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `PUT` `/{key}` params(key) [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/llm/types` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/llm/providers` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/llm/providers/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/llm/providers` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `DELETE` `/llm/providers/{provider_id}` params(provider_id) → in: UUID [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/llm/providers/{provider_id}/test` params(provider_id) → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/embedding/types` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/embedding/providers` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/embedding/providers/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/embedding/providers` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `DELETE` `/embedding/providers/{provider_id}` params(provider_id) → in: UUID [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/embedding/providers/{provider_id}/test` params(provider_id) → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/agent/configs` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/agent/configs/{config_id}` params(config_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/agent/configs` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `DELETE` `/agent/configs/{config_id}` params(config_id) → in: UUID [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/audit-log` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/export` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/import` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/migrate-from-env` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/seed-from-env` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/reload` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `GET` `/export/bundle` [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`
- `POST` `/import/bundle` → in: UserConfigurationCreate [auth, db, cache, ai]
  `backend\heretek_swarm\api\configuration.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\configuration.py`

---
_Back to [overview.md](./overview.md)_