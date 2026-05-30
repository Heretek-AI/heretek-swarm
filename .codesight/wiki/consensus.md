# Consensus

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Consensus subsystem handles **28 routes** and touches: auth, db, cache.

## Routes

- `GET` `/history` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/{consensus_id}` params(consensus_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/{consensus_id}/vote` params(consensus_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/{consensus_id}/aggregate` params(consensus_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/{consensus_id}/results` params(consensus_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `DELETE` `/{consensus_id}` params(consensus_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/config` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/start` [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/{deliberation_id}/submit_position` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/{deliberation_id}/submit_argument` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/{deliberation_id}/submit_evidence` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/{deliberation_id}/run_round` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/deliberation/{deliberation_id}/state` params(deliberation_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/deliberation/{deliberation_id}/history` params(deliberation_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/deliberation/{deliberation_id}/finalize` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `DELETE` `/deliberation/{deliberation_id}` params(deliberation_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/decision/{decision_id}` params(decision_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/decision/{decision_id}/export` params(decision_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/statistics` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/failed` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/successful` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/audit/deliberation/{consensus_id}/history` params(consensus_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/tribunal/cases` [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/tribunal/cases/{case_id}` params(case_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/tribunal/cases/{case_id}/evidence` params(case_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `POST` `/tribunal/cases/{case_id}/rule` params(case_id) [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/tribunal/precedents` → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`
- `GET` `/tribunal/cases/{case_id}/precedents` params(case_id) → in: st [auth, db, cache]
  `backend\heretek_swarm\api\consensus.py`

## Related Models

- **consensus_proposals** (13 fields) → [database.md](./database.md)
- **consensus_votes** (3 fields) → [database.md](./database.md)
- **consensus_audit_trail** (8 fields) → [database.md](./database.md)
- **agent_consensus_config** (18 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\consensus.py`

---
_Back to [overview.md](./overview.md)_