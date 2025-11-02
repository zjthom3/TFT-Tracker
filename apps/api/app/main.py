from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db.session import init_database
from app.routers import assets, health, ingest, snapshots


def create_app(init_db: bool = True) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if init_db:
            init_database()
        yield

    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.include_router(health.router, tags=["health"])
    application.include_router(assets.router, prefix="/assets", tags=["assets"])
    application.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
    application.include_router(snapshots.router, tags=["snapshots"])

    return application


app = create_app()
