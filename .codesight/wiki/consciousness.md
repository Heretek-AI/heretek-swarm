# Consciousness

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Consciousness subsystem handles **27 routes** and touches: auth.

## Routes

- `GET` `/api/observability/agency/swarm` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/swarm/compliance` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/evolution` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/distribution` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `POST` `/api/observability/agency/record` → in: dict [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `POST` `/api/observability/agency/generate-sample` → in: dict [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/all` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/{agent_id}` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agency/{agent_id}/compliance` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/statistics` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agents/{agent_id}` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agents/{agent_id}/iit` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/agents/{agent_id}/fep` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/connectivity` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/states` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/history` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `POST` `/api/observability/record-interaction` → in: dict [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `POST` `/api/observability/record-prediction` → in: dict [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `POST` `/api/observability/record-outcome` → in: dict [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/metrics/{agent_id}` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/visualization/network` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/visualization/timeseries` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/deliberation/{deliberation_id}` params(deliberation_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/thinking-stream/{agent_id}` params(agent_id) → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/api/observability/thinking-stream/all` → in: Annotated [auth]
  `backend\heretek_swarm\api\consciousness.py`
- `GET` `/consciousness`
  `backend\heretek_swarm\api\observability\consciousness.py`
- `GET` `/consciousness/agent/{agent_id}` params(agent_id)
  `backend\heretek_swarm\api\observability\consciousness.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\consciousness.py`
- `backend\heretek_swarm\api\observability\consciousness.py`

---
_Back to [overview.md](./overview.md)_