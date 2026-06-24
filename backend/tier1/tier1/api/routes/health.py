"""GET /health — reports component status.

For Task 1 we report only the API process itself. NATS/Postgres/Redis/Qdrant/
cognee/mem0 components are wired in later tasks; their entries appear as
'ok' once their client initializes successfully, otherwise 'down'.
"""

from fastapi import APIRouter, Depends

from tier1.api.schemas import HealthComponent, HealthResponse
from tier1.config import Settings, get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    # Task 1: only the API process is checked. Other components are added
    # in Tasks 4 (NATS/Postgres/Redis) and the memory task (Qdrant/cognee/mem0).
    components: dict[str, HealthComponent] = {
        "api": HealthComponent(status="ok"),
    }
    return HealthResponse(status="ok", components=components)
