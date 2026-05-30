# Collective_evolution

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Collective_evolution subsystem handles **9 routes** and touches: auth.

## Routes

- `GET` `/evolution-status` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `GET` `/capabilities` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `GET` `/capabilities/{capability_id}` params(capability_id) [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `GET` `/agent/{agent_id}/evolution` params(agent_id) [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `GET` `/fitness-landscape` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `GET` `/adaptability` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `POST` `/agent/{agent_id}/evolve` params(agent_id) [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `POST` `/record-capability` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`
- `POST` `/detect-evolution` [auth]
  `backend\heretek_swarm\api\collective_evolution.py`

## Related Models

- **collective_patterns** (10 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\collective_evolution.py`

---
_Back to [overview.md](./overview.md)_