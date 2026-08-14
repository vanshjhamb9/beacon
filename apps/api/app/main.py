from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.tracing import RequestTracingMiddleware
from app.db.redis import close_redis, create_redis_client
from app.db.session import close_database
from runtime_ops.redis.validator import RedisStreamsValidator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    redis = create_redis_client()
    try:
        result = await RedisStreamsValidator().validate_async(redis)
        app.state.redis_validation = result
        if not result.ok:
            logger.error(
                "Redis Streams validation failed",
                extra={"extra": {"errors": result.errors, "version": result.version}},
            )
            if settings.environment == "production":
                raise RuntimeError(
                    "Production startup blocked: Redis Streams unsupported or unavailable. "
                    f"errors={result.errors}"
                )
        else:
            logger.info(
                "Redis Streams validated",
                extra={"extra": {"version": result.version, "latency_ms": result.latency_ms}},
            )
    finally:
        await redis.aclose()

    yield
    await close_database()
    await close_redis()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestTracingMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
