"""FastAPI application entrypoint for OceanGuard AI."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import (
    analytics_router,
    auth_router,
    detections_router,
    hotspots_router,
    missions_router,
    reports_router,
    reviews_router,
    scans_router,
    system_router,
)
from app.ml.inference import get_inference_engine
from app.models.database import init_db
from app.utils.config import get_settings
from app.utils.logging import configure_logging
from app.utils.middleware import RequestIDMiddleware
from app.utils.ratelimit import RateLimitMiddleware


logger = logging.getLogger("oceanguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    logger.info("Starting OceanGuard AI %s (env=%s)", __version__, settings.app_env)
    init_db()
    # Eagerly initialize the inference engine so the first request is snappy.
    get_inference_engine()
    yield
    logger.info("Shutting down OceanGuard AI")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="OceanGuard AI API",
        description=(
            "AI-Powered Underwater Marine Debris & Anomaly Detection System "
            "using Side-Scan Sonar Imagery. SIH 2026 — PS SIH26057."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Order matters: request-id wraps everything else so every log entry has it.
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception [request_id=%s]: %s", rid, exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "error": str(exc),
                "path": str(request.url.path),
                "request_id": rid,
            },
        )

    @app.get("/health", tags=["system"])
    def health():
        """Detailed health check for orchestrators."""
        from app.ml.inference import get_inference_engine
        engine = get_inference_engine()
        return {
            "status": "ok",
            "version": __version__,
            "service": settings.app_name,
            "model": {
                "name": engine.bundle.name,
                "version": engine.bundle.version,
                "type": engine.bundle.model_type,
                "demo_mode": engine.is_demo,
            },
            "uptime": time.time(),
        }

    @app.get("/", tags=["system"])
    def root():
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
        }

    app.include_router(auth_router)
    app.include_router(scans_router)
    app.include_router(detections_router)
    app.include_router(missions_router)
    app.include_router(analytics_router)
    app.include_router(hotspots_router)
    app.include_router(reports_router)
    app.include_router(reviews_router)
    app.include_router(system_router)

    return app


app = create_app()