"""
Tests for system health check and liveness diagnostics.
"""

from datetime import datetime
from fastapi import status
from starlette.testclient import TestClient

from app.core.config import settings


def test_health_endpoint_success(client: TestClient) -> None:
    """
    Ensure GET /api/v1/health returns HTTP 200 with valid metadata.
    """
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.VERSION
    assert data["environment"] == settings.ENVIRONMENT

    # Verify timestamp parses into an ISO UTC datetime
    parsed_time = datetime.fromisoformat(data["timestamp"])
    assert parsed_time is not None


def test_root_ping_endpoint(client: TestClient) -> None:
    """
    Ensure root GET / returns HTTP 200 with service metadata and documentation links.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["project"] == settings.PROJECT_NAME
    assert data["status"] == "online"
    assert data["docs"] == "/docs"
    assert data["health"] == f"{settings.API_V1_PREFIX}/health"
