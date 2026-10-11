"""
End-to-end tests for Chat endpoint model routing and agent orchestration.
Verifies:
- Ollama llama3.2 routing
- Ollama qwen2.5:1.5b lightweight alternative routing
- OpenAI cloud routing with unconfigured fallback
- Agentic multi-turn tool-calling execution
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_chat_routing_ollama_llama32():
    """
    Test chat completion with default Ollama llama3.2 model.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "What did Brian Chesky say about founder mode in one short sentence?",
            "model_provider": "ollama",
            "model_name": "llama3.2",
            "agentic": False,
        }
        res = await client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
        assert data["metadata"]["model_provider"] == "ollama"
        assert data["metadata"]["model_name"] == "llama3.2"
        assert len(data["citations"]) > 0


@pytest.mark.asyncio
async def test_chat_routing_ollama_qwen_lightweight():
    """
    Test chat completion routed to lightweight qwen2.5:1.5b model.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Summarize what Elena Verna says about PLG in 10 words.",
            "model_provider": "ollama",
            "model_name": "qwen2.5:1.5b",
            "agentic": False,
        }
        res = await client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
        assert data["metadata"]["model_provider"] == "ollama"
        assert data["metadata"]["model_name"] == "qwen2.5:1.5b"


@pytest.mark.asyncio
async def test_chat_routing_openai_unconfigured_fallback():
    """
    Test chat completion with openai provider when OPENAI_API_KEY is not configured.
    Must gracefully return response routed to local Ollama with diagnostic notice.
    """
    original_key = settings.OPENAI_API_KEY
    try:
        settings.OPENAI_API_KEY = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "message": "What is the best way to hire product managers?",
                "model_provider": "openai",
                "model_name": "gpt-4o",
                "agentic": False,
            }
            res = await client.post("/api/v1/chat", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["role"] == "assistant"
            assert "Notice" in data["content"] or "unconfigured" in data["content"].lower()
            # If evidence is sufficient, genuine citations must be attached; if insufficient, citations must remain empty
            if data.get("metadata", {}).get("evidence_status") in ("sufficient", "relevant_evidence_found"):
                assert len(data["citations"]) > 0
                for c in data["citations"]:
                    assert "guest" in c and "episode_title" in c
            else:
                assert len(data["citations"]) == 0
    finally:
        settings.OPENAI_API_KEY = original_key


@pytest.mark.asyncio
async def test_chat_agentic_orchestration_mode():
    """
    Test chat completion with agentic=True invoking AgentOrchestrator.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Search podcast transcripts for Shreyas Doshi on high agency and give 1 takeaway.",
            "model_provider": "ollama",
            "model_name": "llama3.2",
            "agentic": True,
        }
        res = await client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
        assert data["metadata"]["agentic"] is True
        assert "tool_calls_trace" in data["metadata"]
