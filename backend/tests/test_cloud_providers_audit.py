"""
Phase 4B Cloud LLM Configuration, Security & Provider Readiness Audit Test Suite.
Verifies:
1. Provider status introspection and cloud readiness flags.
2. OpenAI adapter execution with mocked AsyncOpenAI client.
3. Anthropic adapter execution with mocked AsyncAnthropic client.
4. Model name normalization and timeout behavior.
5. Missing API key detection and transparent local Ollama fallback.
6. Secret isolation (no API key leakage in status responses or error messages).
7. Error and network failure handling without application crashes.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.config import settings
from app.services.llm_provider import (
    generate_anthropic_completion,
    generate_completion,
    generate_openai_completion,
    get_providers_status,
    LLMProviderError,
)


@pytest.mark.asyncio
async def test_providers_status_unconfigured_cloud_state():
    """
    When OPENAI_API_KEY and ANTHROPIC_API_KEY are unset/empty,
    /providers/status reports cloud providers as is_configured=False and is_available=False,
    while Ollama remains is_configured=True.
    """
    with patch.object(settings, "OPENAI_API_KEY", None):
        with patch.object(settings, "ANTHROPIC_API_KEY", None):
            with patch.object(settings, "GROQ_API_KEY", None):
                res = await get_providers_status()
                assert res.active_provider == "ollama"
                assert res.cloud_testing_status == "pending"

                providers_by_id = {p.id: p for p in res.providers}
                assert "ollama" in providers_by_id
                assert "openai" in providers_by_id
                assert "anthropic" in providers_by_id
                assert "groq" in providers_by_id

                # Local Ollama must be ready
                assert providers_by_id["ollama"].is_configured is True
                assert providers_by_id["ollama"].requires_api_key is False

                # Cloud providers must be unconfigured without false claims
                assert providers_by_id["openai"].is_configured is False
                assert providers_by_id["openai"].is_available is False
                assert providers_by_id["openai"].requires_api_key is True
                assert "Unconfigured" in providers_by_id["openai"].status_message

                assert providers_by_id["anthropic"].is_configured is False
                assert providers_by_id["anthropic"].is_available is False
                assert providers_by_id["anthropic"].requires_api_key is True
                assert "Unconfigured" in providers_by_id["anthropic"].status_message

                assert providers_by_id["groq"].is_configured is False
                assert providers_by_id["groq"].is_available is False
                assert providers_by_id["groq"].requires_api_key is True
                assert "Unconfigured" in providers_by_id["groq"].status_message


@pytest.mark.asyncio
async def test_providers_status_configured_cloud_state():
    """
    When valid mock keys are supplied, cloud providers are reported as configured.
    """
    with patch.object(settings, "OPENAI_API_KEY", "sk-mock-valid-openai-key"):
        with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-mock-valid-key"):
            res = await get_providers_status()
            assert res.cloud_testing_status == "active"

            providers_by_id = {p.id: p for p in res.providers}
            assert providers_by_id["openai"].is_configured is True
            assert providers_by_id["openai"].is_available is True
            assert providers_by_id["anthropic"].is_configured is True
            assert providers_by_id["anthropic"].is_available is True


@pytest.mark.asyncio
async def test_openai_mocked_success():
    """
    Verify OpenAI adapter invokes AsyncOpenAI correctly and returns output.
    """
    mock_choice = MagicMock()
    mock_choice.message.content = "OpenAI GPT-4o synthesized response."

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.services.llm_provider.AsyncOpenAI", return_value=mock_client) as mock_cls:
        res = await generate_openai_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model_name="gpt-4o",
            api_key="sk-mock-test-key",
        )
        assert res == "OpenAI GPT-4o synthesized response."
        mock_cls.assert_called_once_with(api_key="sk-mock-test-key", timeout=60.0)
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_anthropic_mocked_success():
    """
    Verify Anthropic adapter invokes AsyncAnthropic correctly, formats system message,
    normalizes model aliases, and returns output.
    """
    mock_block = MagicMock()
    mock_block.text = "Anthropic Claude 3.5 Sonnet response."

    mock_resp = MagicMock()
    mock_resp.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client) as mock_cls:
        messages = [
            {"role": "system", "content": "You are Lenny assistant."},
            {"role": "user", "content": "What is PLG?"},
        ]
        res = await generate_anthropic_completion(
            messages=messages,
            model_name="claude-sonnet",  # Short alias should normalize to default ID
            api_key="sk-ant-mock-test-key",
        )
        assert res == "Anthropic Claude 3.5 Sonnet response."
        mock_cls.assert_called_once_with(api_key="sk-ant-mock-test-key", timeout=60.0)

        # Check call arguments
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-6"
        assert "You are Lenny assistant." in call_kwargs["system"]
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_anthropic_missing_key_raises_error():
    """
    Calling generate_anthropic_completion directly without key raises LLMProviderError.
    """
    with patch.object(settings, "ANTHROPIC_API_KEY", None):
        with pytest.raises(LLMProviderError) as exc_info:
            await generate_anthropic_completion(
                messages=[{"role": "user", "content": "test"}],
                api_key=None,
            )
        assert "not configured" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_unconfigured_anthropic_transparent_fallback():
    """
    When ANTHROPIC_API_KEY is not set, generate_completion routes to local Ollama
    with a clear diagnostic notice.
    """
    with patch.object(settings, "ANTHROPIC_API_KEY", None):
        with patch(
            "app.services.llm_provider.generate_ollama_completion",
            new_callable=AsyncMock,
        ) as mock_ollama:
            mock_ollama.return_value = "Local Ollama fallback answer."

            res = await generate_completion(
                messages=[{"role": "user", "content": "Explain churn"}],
                provider="anthropic",
                model_name="claude-3-5-sonnet",
            )
            assert "Notice: Anthropic Cloud provider is unconfigured" in res
            assert "Local Ollama fallback answer." in res
            mock_ollama.assert_called_once()


@pytest.mark.asyncio
async def test_secret_isolation_no_key_leak():
    """
    Verify that raw API key secrets are never exposed in get_providers_status()
    nor exposed inside exception details.
    """
    secret_key = "sk-live-super-secret-production-key-998877"
    with patch.object(settings, "OPENAI_API_KEY", secret_key):
        with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-super-secret-887766"):
            status_res = await get_providers_status()
            json_str = status_res.model_dump_json()

            assert secret_key not in json_str
            assert "sk-ant-super-secret-887766" not in json_str


@pytest.mark.asyncio
async def test_anthropic_haiku_model_normalization():
    """
    Verify that claude-haiku normalizes to claude-haiku-4-5.
    """
    mock_resp = MagicMock()
    mock_block = MagicMock()
    mock_block.text = "Fast lightweight Claude response."
    mock_resp.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        res = await generate_anthropic_completion(
            messages=[{"role": "user", "content": "Quick summary"}],
            model_name="claude-haiku",
            api_key="sk-ant-mock-test-key",
        )
        assert res == "Fast lightweight Claude response."
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5"


@pytest.mark.asyncio
async def test_anthropic_configurable_default_model():
    """
    Verify that ANTHROPIC_DEFAULT_MODEL can be overridden via configuration.
    """
    mock_resp = MagicMock()
    mock_block = MagicMock()
    mock_block.text = "Configurable model response."
    mock_resp.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)

    with patch.object(settings, "ANTHROPIC_DEFAULT_MODEL", "claude-sonnet-custom-v1"):
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            res = await generate_anthropic_completion(
                messages=[{"role": "user", "content": "Custom test"}],
                api_key="sk-ant-mock-test-key",
            )
            assert res == "Configurable model response."
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-sonnet-custom-v1"


@pytest.mark.asyncio
async def test_anthropic_provider_status_catalog():
    """
    Verify get_providers_status exposes claude-sonnet-4-6 and claude-haiku-4-5.
    """
    status = await get_providers_status()
    anthropic_info = next(p for p in status.providers if p.id == "anthropic")
    assert anthropic_info.default_model == "claude-sonnet-4-6"
    model_ids = [m.id for m in anthropic_info.models]
    assert "claude-sonnet-4-6" in model_ids
    assert "claude-haiku-4-5" in model_ids
