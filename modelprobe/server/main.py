"""ModelProbe FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import modelprobe
from modelprobe.server.routes import health, runs, suites


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fully wired application instance.  Does not start a server —
    pass the result to uvicorn.run() or use it in tests via TestClient.

    Usage::

        from modelprobe.server.main import create_app
        app = create_app()
    """
    from modelprobe.config import settings

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        from modelprobe.server.db.database import init_db
        await init_db()
        yield

    app = FastAPI(
        title="ModelProbe",
        version=modelprobe.__version__,
        description="AI evaluation and regression testing platform",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(suites.router, prefix="/api")

    static_dir = Path(__file__).parent / "static" / "dist"
    if static_dir.exists() and any(static_dir.iterdir()):
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
