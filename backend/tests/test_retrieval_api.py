"""
Integration tests for Retrieval and Knowledge FastAPI endpoints.
"""

from fastapi import status
from starlette.testclient import TestClient
from app.core.config import settings


def test_knowledge_status_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/knowledge/status returns valid diagnostic schema."""
    response = client.get(f"{settings.API_V1_PREFIX}/knowledge/status")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "ingestion_state" in data
    assert "embedding_model" in data
    assert "indexed_episodes_count" in data
    assert "indexed_chunks_count" in data
    assert data["embedding_model"] == settings.EMBEDDING_MODEL_NAME


def test_retrieval_search_validation(client: TestClient) -> None:
    """Verify POST /api/v1/retrieval/search handles validation correctly."""
    # 1. Invalid empty query
    response = client.post(
        f"{settings.API_V1_PREFIX}/retrieval/search",
        json={"query": ""},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Invalid top_k (< 1)
    response = client.post(
        f"{settings.API_V1_PREFIX}/retrieval/search",
        json={"query": "test query", "top_k": 0},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_retrieval_search_successful_contract(client: TestClient) -> None:
    """Verify POST /api/v1/retrieval/search returns standard schema."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/retrieval/search",
        json={"query": "product strategy", "top_k": 3},
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["query"] == "product strategy"
    assert "evidence_status" in data
    assert "passages" in data
    assert "total_candidates" in data
    assert "latency_ms" in data
    assert "diagnostics" in data
