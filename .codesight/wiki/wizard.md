# Wizard

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Wizard subsystem handles **13 routes** and touches: auth, db, cache, ai.

## Routes

- `GET` `/providers` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `GET` `/providers/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `PUT` `/providers/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `DELETE` `/providers/{provider_id}` params(provider_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `GET` `/tiers` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `GET` `/tiers/{tier_id}` params(tier_id) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `POST` `/validate` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `GET` `/infrastructure` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `POST` `/infrastructure` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `GET` `/infrastructure/{service}` params(service) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `POST` `/infrastructure/{service}/health-check` params(service) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `POST` `/infrastructure/health-check-all` [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`
- `DELETE` `/infrastructure/{service}` params(service) [auth, db, cache, ai]
  `backend\heretek_swarm\api\wizard.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\wizard.py`

---
_Back to [overview.md](./overview.md)_