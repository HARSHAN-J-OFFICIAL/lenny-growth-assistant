"""
Tests for structured JSON error format and exception handling.
"""

from fastapi import status
from starlette.testclient import TestClient

from app.core.config import settings


def test_404_not_found_structured_format(client: TestClient) -> None:
    """
    Ensure non-existent routes return standardized JSON error contract with code NOT_FOUND.
    """
    response = client.get(f"{settings.API_V1_PREFIX}/non-existent-route")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "timestamp" in data["error"]
    assert data["error"]["message"] is not None


def test_405_method_not_allowed_format(client: TestClient) -> None:
    """
    Ensure invalid HTTP methods return standardized JSON error contract with code METHOD_NOT_ALLOWED.
    """
    response = client.post(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "timestamp" in data["error"]
