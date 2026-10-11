"""
Pytest configuration and shared test fixtures.
"""

from typing import Generator
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient fixture for integration testing FastAPI endpoints.
    """
    with TestClient(app) as test_client:
        yield test_client
