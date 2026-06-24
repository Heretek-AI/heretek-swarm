"""GET /health — reports component status."""

from fastapi import APIRouter

from tier1.api.deps import NatsDep, PgDep, RedisDep
from tier1.api.schemas import HealthComponent, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    pg: PgDep,
    redis: RedisDep,
    nats: NatsDep,
) -> HealthResponse:
    components: dict[str, HealthComponent] = {"api": HealthComponent(status="ok")}
    try:
        async with pg.pool.acquire() as conn:
            await conn.execute("SELECT 1")
        components["postgres"] = HealthComponent(status="ok")
    except Exception as exc:
        components["postgres"] = HealthComponent(status="down", detail=str(exc))
    try:
        await redis.client.ping()
        components["redis"] = HealthComponent(status="ok")
    except Exception as exc:
        components["redis"] = HealthComponent(status="down", detail=str(exc))
    try:
        if await nats.health():
            components["nats"] = HealthComponent(status="ok")
        else:
            components["nats"] = HealthComponent(status="down")
    except Exception as exc:
        components["nats"] = HealthComponent(status="down", detail=str(exc))
    overall = "ok" if all(c.status == "ok" for c in components.values()) else "degraded"
    return HealthResponse(status=overall, components=components)
