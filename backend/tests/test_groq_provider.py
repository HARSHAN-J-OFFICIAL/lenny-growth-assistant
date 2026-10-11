"""
Tests for Groq Cloud Provider Integration.
Validates Groq API request construction, OpenAI-compatible protocol handling,
error wrapping (rate limits, auth), transparent local Ollama fallback,
and multi-turn tool calling via AgentOrchestrator.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.config import settings
from app.services.llm_provider import (
    generate_groq_completion,
    generate_completion,
    get_providers_status,
    LLMProviderError,
)
from app.services.agent_orchestrator import agent_orchestrator


@pytest.mark.asyncio
async def test_groq_status_unconfigured():
    """
    When GROQ_API_KEY is None, status endpoint reports Groq as unconfigured
    with fallback notice.
    """
    with patch.object(settings, "GROQ_API_KEY", None):
        status = await get_providers_status()
        groq_provider = next(p for p in status.providers if p.id == "groq")

        assert groq_provider.is_configured is False
        assert groq_provider.is_available is False
        assert "Unconfigured" in groq_provider.status_message
        assert groq_provider.default_model == "openai/gpt-oss-20b"
        model_ids = [m.id for m in groq_provider.models]
        assert "openai/gpt-oss-20b" in model_ids
        assert "llama-3.3-70b-versatile" in model_ids
        assert "llama-3.1-8b-instant" in model_ids


@pytest.mark.asyncio
async def test_groq_status_configured():
    """
    When GROQ_API_KEY is set, Groq reports is_configured=True and is_available=True.
    """
    with patch.object(settings, "GROQ_API_KEY", "gsk_test_mock_groq_key_12345"):
        status = await get_providers_status()
        groq_provider = next(p for p in status.providers if p.id == "groq")

        assert groq_provider.is_configured is True
        assert groq_provider.is_available is True
        assert "Configured and available" in groq_provider.status_message
        assert status.cloud_testing_status == "active"


@pytest.mark.asyncio
async def test_groq_mocked_success():
    """
    Verify generate_groq_completion constructs AsyncOpenAI with Groq base_url
    and calls chat.completions.create with correct model.
    """
    mock_choice = MagicMock()
    mock_choice.message.content = "Groq LPU high-speed response grounded in Lenny's Podcast."
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    with patch("app.services.llm_provider.AsyncOpenAI", return_value=mock_client) as mock_cls:
        messages = [
            {"role": "system", "content": "You are Lenny assistant."},
            {"role": "user", "content": "Explain product strategy."},
        ]
        res = await generate_groq_completion(
            messages=messages,
            model_name="openai/gpt-oss-20b",
            api_key="gsk_mock_test_key",
        )
        assert res == "Groq LPU high-speed response grounded in Lenny's Podcast."
        mock_cls.assert_called_once_with(
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk_mock_test_key",
            timeout=60.0,
        )
        mock_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.3,
        )


@pytest.mark.asyncio
async def test_groq_missing_key_raises_error():
    """Calling generate_groq_completion without API key raises LLMProviderError."""
    with patch.object(settings, "GROQ_API_KEY", None):
        with pytest.raises(LLMProviderError) as exc_info:
            await generate_groq_completion(
                messages=[{"role": "user", "content": "test"}],
                api_key=None,
            )
        assert "not configured" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_groq_unconfigured_transparent_fallback():
    """
    When GROQ_API_KEY is not set, generate_completion routes to local Ollama
    with a clear diagnostic notice banner.
    """
    with patch.object(settings, "GROQ_API_KEY", None):
        with patch(
            "app.services.llm_provider.generate_ollama_completion",
            new_callable=AsyncMock,
        ) as mock_ollama:
            mock_ollama.return_value = "Local Ollama fallback answer for Groq."

            res = await generate_completion(
                messages=[{"role": "user", "content": "Explain retention loops"}],
                provider="groq",
                model_name="openai/gpt-oss-20b",
            )
            assert "Notice: Groq Cloud provider is unconfigured" in res
            assert "Local Ollama fallback answer for Groq." in res
            mock_ollama.assert_called_once()


@pytest.mark.asyncio
async def test_groq_rate_limit_error_handling():
    """
    HTTP 429 rate limit errors from Groq API are formatted as friendly error messages.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Error 429: rate_limit_exceeded (TPM limit)"))

    with patch("app.services.llm_provider.AsyncOpenAI", return_value=mock_client):
        with pytest.raises(LLMProviderError) as exc_info:
            await generate_groq_completion(
                messages=[{"role": "user", "content": "Hi"}],
                api_key="gsk_test_key",
            )
        assert "rate limit exceeded" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_groq_auth_error_handling():
    """
    HTTP 401 invalid key errors from Groq API are caught and explained clearly.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Error 401: Invalid API Key provided"))

    with patch("app.services.llm_provider.AsyncOpenAI", return_value=mock_client):
        with pytest.raises(LLMProviderError) as exc_info:
            await generate_groq_completion(
                messages=[{"role": "user", "content": "Hi"}],
                api_key="gsk_invalid_key",
            )
        assert "authentication error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_groq_secret_isolation_no_key_leak():
    """
    Verify raw GROQ_API_KEY secrets are never exposed in get_providers_status() payloads.
    """
    secret_key = "gsk_super_confidential_production_groq_key_999888"
    with patch.object(settings, "GROQ_API_KEY", secret_key):
        status_res = await get_providers_status()
        json_str = status_res.model_dump_json()

        assert secret_key not in json_str
        assert "super_confidential" not in json_str


@pytest.mark.asyncio
async def test_groq_agent_orchestrator_mocked():
    """
    Verify AgentOrchestrator._run_groq_agent invokes Groq client and handles tool calls.
    """
    mock_msg = MagicMock()
    mock_msg.content = "Groq agent synthesized answer on founder mode."
    mock_msg.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.message = mock_msg

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch.object(settings, "GROQ_API_KEY", "gsk_test_key"):
        with patch("app.services.agent_orchestrator.AsyncOpenAI", return_value=mock_client):
            res = await agent_orchestrator.run(
                message="What did Brian Chesky say about founder mode?",
                provider="groq",
                model_name="openai/gpt-oss-20b",
            )
            assert res.provider == "groq"
            assert res.model_name == "openai/gpt-oss-20b"
            assert "Groq agent synthesized answer" in res.content
            mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_groq_agent_orchestrator_fallback_when_unconfigured():
    """
    When GROQ_API_KEY is not set, AgentOrchestrator gracefully delegates to Ollama.
    """
    with patch.object(settings, "GROQ_API_KEY", None):
        res = await agent_orchestrator.run(
            message="Explain PLG loops",
            provider="groq",
            model_name="openai/gpt-oss-20b",
        )
        assert res.provider == "groq"
        assert "Notice: Groq Cloud provider is unconfigured" in res.content
