"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, settings
from .db import Database
from .routers import explore, model


def create_app(config: Settings | None = None) -> FastAPI:
    config = config or settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = config
        app.state.db = Database(config.parquet_path)
        try:
            yield
        finally:
            app.state.db.close()

    app = FastAPI(
        title="Colombianos detenidos en el exterior API",
        description=(
            "Live exploratory queries over the 2026 cleaned warehouse. "
            "CANTIDAD is a stock per publication cutoff; never sum it across cutoffs."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(explore.router)
    app.include_router(model.router)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "name": "Colombianos detenidos en el exterior",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


app = create_app()
