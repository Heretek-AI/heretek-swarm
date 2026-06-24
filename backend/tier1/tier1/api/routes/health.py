"""GET /health — reports component status."""

from fastapi import APIRouter, Depends

from tier1.api.schemas import HealthComponent, HealthResponse
from tier1.config import Settings, get_settings
from tier1.events.nats_client import NatsClient
from tier1.persistence.postgres import PostgresPool
from tier1.persistence.redis import RedisCache

router = APIRouter()


def _pg() -> PostgresPool:  # placeholder — real wiring in Task 8
    raise NotImplementedError("PG dependency wired in Task 8")


def _redis() -> RedisCache:
    raise NotImplementedError("Redis dependency wired in Task 8")


def _nats() -> NatsClient:
    raise NotImplementedError("NATS dependency wired in Task 8")


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: Settings = Depends(get_settings),
    pg: PostgresPool = Depends(_pg),
    redis: RedisCache = Depends(_redis),
    nats: NatsClient = Depends(_nats),
) -> HealthResponse:
    components: dict[str, HealthComponent] = {"api": HealthComponent(status="ok")}
    try:
        async with pg.pool.acquire() as conn:  # type: ignore[union-attr]
            await conn.execute("SELECT 1")
        components["postgres"] = HealthComponent(status="ok")
    except Exception as exc:
        components["postgres"] = HealthComponent(status="down", detail=str(exc))
    try:
        await redis.client.ping()  # type: ignore[union-attr]
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
