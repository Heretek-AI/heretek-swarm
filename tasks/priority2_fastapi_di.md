# Priority 2: HIGH - FastAPI Dependency Injection

## Objective
Update deprecated FastAPI dependency injection syntax to use `Annotated` type hints.

## Files to Fix
- src/heretek_swarm/api/consciousness.py - 20 issues
- src/heretek_swarm/api/emergent_intelligence.py - 15 issues
- src/heretek_swarm/api/rag.py - 2 issues

## Pattern Change
Before:
```python
from fastapi import Depends

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    pass
```

After:
```python
from typing import Annotated
from fastapi import Depends

@app.get("/items")
def get_items(db: Annotated[Session, Depends(get_db)]):
    pass
```

## Affected Lines in consciousness.py
Lines: 77, 116, 149, 186, 205-213, 236, 257, 337, 374, 403, 425, 452, 482-483, 515, 536, 565-567, 599, 626, 653, 679, 701, 744-746

## Verification
1. All endpoints use Annotated syntax
2. API still functions correctly
3. OpenAPI docs reflect the changes