"""
Tests for AI Providers and Model Routing API endpoint.
Verifies provider discovery, local Ollama models (llama3.2, qwen2.5:1.5b),
and unconfigured cloud status handling.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_providers_status_endpoint():
    """
    Test GET /api/v1/providers/status returns all configured and available providers.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/providers/status")
        assert response.status_code == 200

        data = response.json()
        assert "active_provider" in data
        assert data["active_provider"] == "ollama"
        assert data["default_model"] == "llama3.2"

        providers = {p["id"]: p for p in data["providers"]}
        assert "ollama" in providers
        assert "openai" in providers

        # Verify Ollama metadata
        ollama = providers["ollama"]
        assert ollama["provider_type"] == "local"
        assert ollama["requires_api_key"] is False
        model_ids = [m["id"] for m in ollama["models"]]
        assert "llama3.2" in model_ids
        assert "qwen2.5:1.5b" in model_ids

        # Verify OpenAI cloud provider configuration state
        openai_p = providers["openai"]
        assert openai_p["provider_type"] == "cloud"
        assert openai_p["requires_api_key"] is True
        openai_models = [m["id"] for m in openai_p["models"]]
        assert "gpt-4o" in openai_models
        assert "gpt-4o-mini" in openai_models

        assert "groq" in providers
        groq_p = providers["groq"]
        assert groq_p["provider_type"] == "cloud"
        assert groq_p["requires_api_key"] is True
        groq_models = [m["id"] for m in groq_p["models"]]
        assert "openai/gpt-oss-20b" in groq_models

        if not settings.OPENAI_API_KEY:
            assert openai_p["is_configured"] is False
            assert "Unconfigured" in openai_p["status_message"]

        any_cloud = bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY or settings.GROQ_API_KEY)
        expected_status = "active" if any_cloud else "pending"
        assert data["cloud_testing_status"] == expected_status
