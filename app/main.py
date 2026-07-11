"""
main.py — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import get_logger
from api.v1.router import api_router

logger = get_logger("main")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AutoML Agent — Natural Language Driven Machine Learning Pipeline. "
            "Upload datasets, describe your ML problem in plain English, and get a "
            "trained, export-ready model automatically."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Root / Health ────────────────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok", "env": settings.APP_ENV}

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} started in {settings.APP_ENV} mode.")
    return app


app = create_app()