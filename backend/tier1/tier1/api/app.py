"""FastAPI app factory with full dependency wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from tier1.api.routes import deliberations, health, ws
from tier1.config import Settings, get_settings
from tier1.events.nats_client import NatsClient
from tier1.llm.garage import ModelGarage
from tier1.persistence.postgres import PostgresPool
from tier1.persistence.redis import RedisCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    pg = PostgresPool(settings.postgres_dsn)
    redis = RedisCache(settings.redis_url, settings.redis_ttl_s)
    nats = NatsClient(settings.nats_url)
    garage = ModelGarage(settings)

    # Connect in order; if any later connect fails, close the ones that
    # succeeded so we don't leak resources.
    connected: list[tuple[str, object]] = []
    try:
        await pg.connect()
        connected.append(("pg", pg))
        await redis.connect()
        connected.append(("redis", redis))
        await nats.connect()
        connected.append(("nats", nats))
    except Exception:
        for name, client in reversed(connected):
            try:
                await client.close()
            except Exception:  # noqa: BLE001
                pass
        raise

    app.state.pg = pg
    app.state.redis = redis
    app.state.nats = nats
    app.state.garage = garage

    try:
        yield
    finally:
        await nats.close()
        await redis.close()
        await pg.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Tier 1 Core Triad", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(deliberations.router)
    app.include_router(ws.router)
    return app
