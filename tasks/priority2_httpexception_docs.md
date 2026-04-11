# Priority 2: HIGH - Undocumented HTTPException Responses

## Objective
Document HTTPException status codes in OpenAPI `responses` parameter.

## Files to Fix
- src/heretek_swarm/api/consciousness.py
- src/heretek_swarm/api/emergent_intelligence.py
- src/heretek_swarm/api/plugins.py

## Rule
python:S8415

## Pattern
Before:
```python
@app.get("/items/{item_id}")
def get_item(item_id: str):
    if not found:
        raise HTTPException(status_code=404)
    return item
```

After:
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.get(
    "/items/{item_id}",
    responses={
        404: {"description": "Item not found", "model": ErrorModel}
    }
)
def get_item(item_id: str):
    if not found:
        raise HTTPException(status_code=404)
    return item
```

## Verification
1. All HTTPException raised have corresponding responses documented
2. OpenAPI docs show error responses
3. API documentation is complete