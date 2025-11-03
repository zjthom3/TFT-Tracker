from contextlib import asynccontextmanager
import asyncio

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import get_settings
from app.db.session import init_database
from app.jobs.scheduler import poll_market_data
from app.routers import assets, auth, health, ingest, phase, snapshots, watchlist


def create_app(init_db: bool = True) -> FastAPI:
    settings = get_settings()

    if settings.sentry_dsn and not sentry_sdk.Hub.current.client:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.2,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        background_task: asyncio.Task | None = None
        if init_db:
            init_database()
        if settings.ingest_interval_minutes > 0:
            background_task = asyncio.create_task(poll_market_data())
        yield
        if background_task:
            background_task.cancel()

    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, tags=["health"])
    application.include_router(auth.router, tags=["auth"])
    application.include_router(assets.router, prefix="/assets", tags=["assets"])
    application.include_router(watchlist.router, tags=["watchlist"])
    application.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
    application.include_router(phase.router, tags=["phase"])
    application.include_router(snapshots.router, tags=["snapshots"])

    return application


app = create_app()
