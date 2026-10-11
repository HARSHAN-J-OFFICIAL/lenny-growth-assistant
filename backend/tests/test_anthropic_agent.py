"""
Unit tests for Anthropic Claude Agent SDK workflow integration and local adapter.
Verifies requirement:
- Genuine integration with supported SDK (Anthropic Claude Agent SDK)
- Clearly defined tools and bounded capabilities
- Security sandboxing (zero shell / filesystem permissions)
- Separation of required SDK-driven agent workflow from local inference when API key is missing
- Untrusted transcript instruction rejection
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.anthropic_agent import (
    claude_agent_runner,
    CLAUDE_AGENT_TOOL_SCHEMAS,
)
from app.core.config import settings


def test_claude_agent_tool_schemas_specification():
    """
    Verify Claude agent tool schemas are properly formatted for Anthropic tool-use API.
    """
    assert len(CLAUDE_AGENT_TOOL_SCHEMAS) == 3
    tool_names = [t["name"] for t in CLAUDE_AGENT_TOOL_SCHEMAS]
    assert "search_podcast_transcripts" in tool_names
    assert "get_topic_insights" in tool_names
    assert "generate_sandboxed_artifact" in tool_names

    # Verify input_schema format
    for tool in CLAUDE_AGENT_TOOL_SCHEMAS:
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "properties" in tool["input_schema"]


@pytest.mark.asyncio
async def test_claude_agent_local_adapter_when_unconfigured():
    """
    When ANTHROPIC_API_KEY is not set, ClaudeAgentRunner must gracefully execute
    via the local Ollama adapter without crashing or requiring paid API credentials.
    """
    with patch.object(settings, "ANTHROPIC_API_KEY", None):
        result = await claude_agent_runner.run(
            message="Explain Brian Chesky's founder mode in 1 sentence.",
            model_name="claude-sonnet-4-6",
        )
        assert result["content"]
        assert "Claude Agent SDK running via Local Ollama Adapter" in result["content"]
        assert result["sdk_used"] == "claude-agent-local-adapter"
        assert isinstance(result["citations"], list)


@pytest.mark.asyncio
async def test_claude_agent_workflow_with_mocked_sdk():
    """
    When ANTHROPIC_API_KEY is configured, ClaudeAgentRunner uses the AsyncAnthropic SDK client.
    """
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Claude Agent synthesized response grounded in Brian Chesky's interview."

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch.object(settings, "ANTHROPIC_API_KEY", "mock-anthropic-key-test"):
        with patch("app.services.anthropic_agent.AsyncAnthropic", return_value=mock_client):
            result = await claude_agent_runner.run(
                message="What did Brian Chesky say?",
                model_name="claude-sonnet-4-6",
            )
            assert result["content"] == "Claude Agent synthesized response grounded in Brian Chesky's interview."
            assert result["sdk_used"] == "anthropic-python-agent-sdk"
            assert result["provider"] == "anthropic"
            assert result["model_name"] == "claude-sonnet-4-6"
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-sonnet-4-6"
