"""
Unit and integration tests for OpenAI Cloud Provider with mocked credentials and responses.
Verifies requirement:
- Complete the cloud integration code.
- Test it using mocked credentials and responses.
- Mark live cloud testing as pending.
- If OPENAI_API_KEY is missing, show cloud provider as unconfigured without breaking local mode.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.llm_provider import (
    generate_openai_completion,
    generate_completion,
    LLMProviderError,
)
from app.core.config import settings


@pytest.mark.asyncio
async def test_openai_completion_with_mocked_client():
    """
    Verify generate_openai_completion executes correctly with mocked AsyncOpenAI client.
    """
    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked GPT-4o advice for product leaders."

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.llm_provider.AsyncOpenAI", return_value=mock_client):
        messages = [{"role": "user", "content": "What is PM-market fit?"}]
        result = await generate_openai_completion(
            messages=messages,
            model_name="gpt-4o",
            api_key="mock-sk-1234567890",
        )

        assert result == "Mocked GPT-4o advice for product leaders."
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["messages"] == messages


@pytest.mark.asyncio
async def test_openai_completion_without_api_key_raises_error():
    """
    Calling generate_openai_completion directly without key raises LLMProviderError.
    """
    with patch.object(settings, "OPENAI_API_KEY", None):
        with pytest.raises(LLMProviderError) as exc_info:
            await generate_openai_completion(
                messages=[{"role": "user", "content": "test"}],
                api_key=None,
            )
        assert "not configured" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_generate_completion_unconfigured_openai_fallback():
    """
    When OPENAI_API_KEY is missing, generate_completion(provider='openai')
    must gracefully route to local Ollama and include diagnostic notice without crashing.
    """
    with patch.object(settings, "OPENAI_API_KEY", None):
        with patch(
            "app.services.llm_provider.generate_ollama_completion",
            new_callable=AsyncMock,
        ) as mock_ollama:
            mock_ollama.return_value = "Local Ollama response for growth questions."

            messages = [{"role": "user", "content": "How do you calculate retention?"}]
            result = await generate_completion(
                messages=messages,
                provider="openai",
                model_name="gpt-4o",
            )

            assert "Notice: OpenAI Cloud provider is unconfigured" in result
            assert "Live cloud testing marked as pending" in result
            assert "Local Ollama response for growth questions." in result
            mock_ollama.assert_called_once()


@pytest.mark.asyncio
async def test_generate_completion_configured_openai_routing():
    """
    When OPENAI_API_KEY is present, generate_completion(provider='openai')
    routes to generate_openai_completion and returns cloud response.
    """
    with patch.object(settings, "OPENAI_API_KEY", "mock-valid-sk-key"):
        with patch(
            "app.services.llm_provider.generate_openai_completion",
            new_callable=AsyncMock,
        ) as mock_openai:
            mock_openai.return_value = "Cloud GPT-4o response."

            messages = [{"role": "user", "content": "Explain virality loops."}]
            result = await generate_completion(
                messages=messages,
                provider="openai",
                model_name="gpt-4o",
            )

            assert result == "Cloud GPT-4o response."
            mock_openai.assert_called_once()
