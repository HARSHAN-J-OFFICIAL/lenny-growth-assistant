"""
Main FastAPI application entrypoint for The Lenny Growth Assistant.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.services.ingestion_manager import ingestion_manager

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lenny.http")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Structured HTTP request observability:
    - Generates or propagates X-Request-ID correlation tokens
    - Measures and logs exact route processing latencies
    - Emits structured diagnostic logs on endpoint failures
    - Returns X-Request-ID in HTTP response headers
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} FAILED after {duration_ms}ms: {exc}",
                exc_info=True,
            )
            raise


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

    # 1. Observability: Request correlation & latency logging
    app.add_middleware(RequestCorrelationMiddleware)

    # 2. Environment-driven CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Centralized structured error handling
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
