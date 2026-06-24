"""FastAPI app factory."""

from fastapi import FastAPI

from tier1.api.routes import health


def create_app() -> FastAPI:
    app = FastAPI(title="Tier 1 Core Triad", version="0.1.0")
    app.include_router(health.router)
    return app
