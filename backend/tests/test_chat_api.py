"""
Integration tests for Grounded Chat completion and Artifact creation endpoints.
"""

from unittest.mock import patch
from fastapi import status
from starlette.testclient import TestClient

from app.core.config import settings
from app.services.artifact_extractor import extract_artifacts


def test_artifact_extractor_parsing() -> None:
    """Verify structured artifact directives are cleanly parsed."""
    raw_response = (
        "Here is your product growth framework.\n\n"
        ":::artifact{title=\"Product-Led Checklist\" type=\"markdown\"}\n"
        "# Checklist\n"
        "- [x] Self-serve onboarding\n"
        "- [x] In-product viral invite loop\n"
        ":::\n\n"
        "Let me know if you want to expand any step."
    )
    cleaned_text, artifacts = extract_artifacts(raw_response)
    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.title == "Product-Led Checklist"
    assert art.artifact_type == "markdown"
    assert "Self-serve onboarding" in art.content
    assert "Artifact Generated" in cleaned_text


def test_chat_completion_grounded_response_and_persistence(client: TestClient) -> None:
    """Verify /api/v1/chat triggers RAG retrieval, LLM completion, and stores turn in PostgreSQL."""
    # 1. Create a session first
    sess_res = client.post(
        f"{settings.API_V1_PREFIX}/sessions",
        json={"title": "Leadership Talk", "model_provider": "ollama", "model_name": "llama3.2"},
    )
    assert sess_res.status_code == status.HTTP_201_CREATED
    session_id = sess_res.json()["id"]

    # 2. Post a chat message with mocked LLM generation to ensure lightning-fast deterministic test execution
    mock_llm_reply = (
        "Brian Chesky emphasizes that leaders must be deeply involved in the details rather than managing from afar.\n\n"
        ":::artifact{title=\"Founder Mode Leadership Playbook\" type=\"markdown\"}\n"
        "# Founder Mode Playbook\n"
        "1. Know the details\n"
        "2. Don't abdicate responsibility\n"
        ":::"
    )

    with patch("app.api.v1.endpoints.chat.generate_completion", return_value=mock_llm_reply):
        chat_res = client.post(
            f"{settings.API_V1_PREFIX}/chat",
            json={
                "session_id": session_id,
                "message": "What did Brian Chesky say about being in the details and micromanagement?",
                "model_provider": "ollama",
                "model_name": "llama3.2",
            },
        )
        assert chat_res.status_code == status.HTTP_200_OK
        data = chat_res.json()

        # Check response structure
        assert data["session_id"] == session_id
        assert data["role"] == "assistant"
        assert len(data["citations"]) > 0
        top_citation = data["citations"][0]
        assert "Brian Chesky" in top_citation.get("guest", "") or "Brian Chesky" in top_citation.get("speaker", "")
        assert "youtube.com" in top_citation.get("timestamp_url", "")

        # Check extracted artifacts
        assert len(data["artifacts"]) == 1
        art = data["artifacts"][0]
        assert art["title"] == "Founder Mode Leadership Playbook"
        assert art["artifact_type"] == "markdown"
        artifact_id = art["id"]

    # 3. Verify history in PostgreSQL
    hist_res = client.get(f"{settings.API_V1_PREFIX}/sessions/{session_id}/history")
    assert hist_res.status_code == status.HTTP_200_OK
    hist_data = hist_res.json()
    assert len(hist_data["messages"]) == 2  # 1 user + 1 assistant
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][1]["role"] == "assistant"
    assert len(hist_data["messages"][1]["artifacts"]) == 1

    # 4. Verify artifact endpoint by ID
    art_res = client.get(f"{settings.API_V1_PREFIX}/artifacts/{artifact_id}")
    assert art_res.status_code == status.HTTP_200_OK
    assert art_res.json()["title"] == "Founder Mode Leadership Playbook"

    # 5. Clean up session
    client.delete(f"{settings.API_V1_PREFIX}/sessions/{session_id}")
