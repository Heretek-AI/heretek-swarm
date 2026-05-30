# Rag

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Rag subsystem handles **12 routes** and touches: auth, db.

## Routes

- `POST` `/ingest` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/ingest/batch` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/query` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `GET` `/documents` [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `GET` `/documents/{document_id}` params(document_id) [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `DELETE` `/documents/{document_id}` params(document_id) [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/config` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/graph/query` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/graph/chunks` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `GET` `/graph/statistics` [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `GET` `/graph/document/{document_id}/headings` params(document_id) [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`
- `POST` `/graph/decompose` → in: UploadFile [auth, db, upload]
  `backend\heretek_swarm\api\rag.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend\heretek_swarm\api\rag.py`

---
_Back to [overview.md](./overview.md)_