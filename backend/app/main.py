"""
Main FastAPI application entrypoint for The Lenny Growth Assistant.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.services.ingestion_manager import ingestion_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager: non-blocking initialization of persistent knowledge indices.
    """
    # Load persistent indices if already computed; do NOT block startup with full re-indexing
    ingestion_manager.initialize()
    yield


def create_application() -> FastAPI:
    """
    Application factory initializing FastAPI, middleware, routes, and error handlers.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Enterprise-grade conversational RAG assistant grounded in Lenny's Podcast transcripts, "
            "with interactive sandboxed Claude-style artifact generation and dynamic model routing."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # 1. Environment-driven CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Centralized structured error handling
    register_exception_handlers(app)

    # 3. Mount Versioned API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # 4. Root Welcome Route
    @app.get(
        "/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
    )
    async def root_ping() -> JSONResponse:
        return JSONResponse(
            content={
                "project": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": "online",
                "docs": "/docs",
                "health": f"{settings.API_V1_PREFIX}/health",
                "knowledge_status": f"{settings.API_V1_PREFIX}/knowledge/status",
            }
        )

    return app


app = create_application()
