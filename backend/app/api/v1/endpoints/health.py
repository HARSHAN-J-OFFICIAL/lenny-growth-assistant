"""
Health check diagnostic endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, status

from app.core.config import settings
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Probe",
    description="Liveness check returning application operational status, version, and database status.",
)
async def get_health(detailed: bool = False) -> HealthResponse:
    """
    Return liveness metadata and database connectivity check.
    """
    db_check = await check_database_connection()
    db_status = db_check.get("status", "disconnected")

    checks = None
    if detailed:
        checks = {
            "database": db_check,
        }

    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        database=db_status,
        checks=checks,
    )
