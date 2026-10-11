"""
Integration tests for Sessions API endpoints backed by PostgreSQL.
"""

from fastapi import status
from starlette.testclient import TestClient

from app.core.config import settings


def test_sessions_crud_lifecycle(client: TestClient) -> None:
    """Verify session creation, retrieval, listing, and deletion."""
    # 1. Create session
    create_res = client.post(
        f"{settings.API_V1_PREFIX}/sessions",
        json={"title": "Strategy Session", "model_provider": "ollama", "model_name": "llama3.2"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Strategy Session"
    assert session_data["model_provider"] == "ollama"

    # 2. Get session by ID
    get_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == session_id

    # 3. List sessions
    list_res = client.get(f"{settings.API_V1_PREFIX}/sessions")
    assert list_res.status_code == status.HTTP_200_OK
    list_data = list_res.json()
    assert list_data["total"] > 0
    assert any(s["id"] == session_id for s in list_data["sessions"])

    # 4. Rename session (PATCH)
    rename_res = client.patch(
        f"{settings.API_V1_PREFIX}/sessions/{session_id}",
        json={"title": "Renamed Strategy Session"},
    )
    assert rename_res.status_code == status.HTTP_200_OK
    assert rename_res.json()["title"] == "Renamed Strategy Session"

    # 5. Get history (empty initially)
    hist_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}/history")
    assert hist_res.status_code == status.HTTP_200_OK
    assert hist_res.json()["session_id"] == session_id
    assert len(hist_res.json()["messages"]) == 0

    # 6. Get session citations and artifacts
    citations_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}/citations")
    assert citations_res.status_code == status.HTTP_200_OK
    assert isinstance(citations_res.json(), list)

    artifacts_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}/artifacts")
    assert artifacts_res.status_code == status.HTTP_200_OK
    assert isinstance(artifacts_res.json(), list)

    # 7. Delete session
    del_res = client.delete(f"{settings.API_V1_PREFIX}/sessions/{session_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 8. Verify 404 after deletion
    not_found_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}")
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
