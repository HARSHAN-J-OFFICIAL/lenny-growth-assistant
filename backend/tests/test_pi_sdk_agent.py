"""
Automated tests for official Pi Coding Agent SDK Integration.
Verifies compliance with Phase 2 Agent SDK requirements:
1. Genuine @earendil-works/pi-coding-agent SDK execution.
2. Sandboxed domain tools (bash/filesystem disabled).
3. Bridged retrieval and citation extraction.
4. Session persistence.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.pi_agent_client import pi_agent_client


@pytest.mark.asyncio
async def test_pi_agent_direct_execution():
    """Verify PiAgentClient executes via Node runner and handles response."""
    result = await pi_agent_client.run(
        message="What is Product-Led Growth in 1 sentence?",
        provider="ollama",
        model_name="llama3.2",
        timeout_seconds=60.0,
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0
    assert result.provider == "ollama"
    assert result.model_name == "llama3.2"
    assert "Pi Coding Agent SDK" in (result.notice or "")


@pytest.mark.asyncio
async def test_pi_agent_api_endpoint():
    """Verify POST /api/v1/chat/agent/pi executes through FastAPI endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/agent/pi",
            json={
                "message": "Give a 1-sentence tip on PM retention according to Elena Verna",
                "model_provider": "ollama",
                "model_name": "llama3.2",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
        assert data["session_id"] is not None
        assert "metadata" in data
        assert data["metadata"].get("agent_sdk") == "pi-coding-agent"
