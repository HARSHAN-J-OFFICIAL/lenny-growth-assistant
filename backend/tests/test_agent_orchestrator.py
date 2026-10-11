"""
Unit and integration tests for Agent Orchestrator, Sandboxed Domain Tools,
and Pi Coding Agent compatibility bridge.
"""

import pytest
from app.services.agent_tools import (
    search_podcast_transcripts,
    get_topic_insights,
    generate_sandboxed_artifact,
    verify_sandboxing,
    execute_agent_tool,
    SecuritySandboxingViolation,
    TOOL_REGISTRY,
)
from app.services.agent_orchestrator import agent_orchestrator
from app.services.pi_agent_bridge import pi_agent_bridge
from app.core.config import settings


def test_sandboxing_enforcement_whitelisting():
    """
    Verify all registered tools adhere to security sandboxing.
    No filesystem, shell, or execution tools are permitted.
    """
    assert verify_sandboxing() is True
    # Verify exact set of safe domain tools
    registered = set(TOOL_REGISTRY.keys())
    assert registered == {
        "search_podcast_transcripts",
        "get_topic_insights",
        "generate_sandboxed_artifact",
    }


def test_sandboxing_violation_blocks_forbidden_tools():
    """
    Attempting to invoke unauthorized shell or filesystem operations raises SecuritySandboxingViolation.
    """
    forbidden_calls = [
        "bash_shell_exec",
        "read_file_content",
        "write_file_data",
        "delete_filesystem_path",
        "powershell_command",
        "python_eval_exec",
    ]
    for bad_tool in forbidden_calls:
        with pytest.raises(SecuritySandboxingViolation):
            execute_agent_tool(bad_tool, {})


def test_unknown_tool_rejection():
    """
    Invoking an unregistered arbitrary tool raises KeyError.
    """
    with pytest.raises(KeyError):
        execute_agent_tool("arbitrary_unknown_function", {})


def test_search_podcast_transcripts_tool():
    """
    Verify search_podcast_transcripts tool executes hybrid retrieval and formats results.
    """
    res = search_podcast_transcripts(query="Brian Chesky founder mode", top_k=2)
    assert res["query"] == "Brian Chesky founder mode"
    assert "passages" in res
    assert len(res["passages"]) <= 2
    if res["passages"]:
        first = res["passages"][0]
        assert "guest" in first
        assert "episode_title" in first
        assert "timestamp_url" in first
        assert "text" in first


def test_get_topic_insights_tool():
    """
    Verify get_topic_insights queries curated topic indices.
    """
    res = get_topic_insights(topic_name="PLG")
    assert res["queried_topic"] == "PLG"
    assert "topics" in res
    assert res["matched_topics_count"] >= 1


def test_generate_sandboxed_artifact_tool():
    """
    Verify generate_sandboxed_artifact wraps deliverables in structured format.
    """
    res = generate_sandboxed_artifact(
        title="Founder Mode PRD Checklist",
        artifact_type="markdown",
        content="# Actionable Items\n- Stay in the details\n- Verify metrics",
    )
    assert res["status"] == "created"
    assert res["title"] == "Founder Mode PRD Checklist"
    assert ":::artifact" in res["formatted_block"]
    assert "Stay in the details" in res["formatted_block"]


def test_pi_agent_bridge_definitions_and_rpc():
    """
    Verify PiAgentCompatibilityBridge exports compliant tool schemas and handles RPC dispatch.
    """
    schemas = pi_agent_bridge.get_tool_definitions()
    assert len(schemas) == 3
    tool_names = [s["function"]["name"] for s in schemas]
    assert "search_podcast_transcripts" in tool_names
    assert "generate_sandboxed_artifact" in tool_names

    # Safe RPC dispatch
    rpc_res = pi_agent_bridge.handle_rpc_tool_call(
        tool_name="get_topic_insights",
        parameters={"topic_name": "Pricing"},
    )
    assert rpc_res["status"] == "success"
    assert "result" in rpc_res

    # Disallowed RPC dispatch blocked
    blocked_res = pi_agent_bridge.handle_rpc_tool_call(
        tool_name="execute_shell_cmd",
        parameters={"cmd": "whoami"},
    )
    assert blocked_res["status"] == "security_violation"


@pytest.mark.asyncio
async def test_agent_orchestrator_ollama_execution():
    """
    Verify AgentOrchestrator runs an agent turn with local Ollama (llama3.2).
    """
    result = await agent_orchestrator.run(
        message="What does Brian Chesky advise about product leadership?",
        provider="ollama",
        model_name="llama3.2",
    )
    assert result.content
    assert result.provider == "ollama"
    assert result.model_name in ["llama3.2", "llama3.2:latest"]
    assert isinstance(result.citations, list)


@pytest.mark.asyncio
async def test_agent_orchestrator_qwen_lightweight_routing():
    """
    Verify AgentOrchestrator routes to lightweight qwen2.5:1.5b.
    """
    result = await agent_orchestrator.run(
        message="Explain retention in 2 sentences.",
        provider="ollama",
        model_name="qwen2.5:1.5b",
    )
    assert result.content
    assert result.provider == "ollama"
    assert result.model_name == "qwen2.5:1.5b"


@pytest.mark.asyncio
async def test_agent_orchestrator_unconfigured_openai_fallback():
    """
    Verify AgentOrchestrator gracefully handles unconfigured OpenAI without breaking.
    """
    # Force OPENAI_API_KEY to None to test unconfigured cloud handling
    original_key = settings.OPENAI_API_KEY
    try:
        settings.OPENAI_API_KEY = None
        result = await agent_orchestrator.run(
            message="What is product led growth?",
            provider="openai",
            model_name="gpt-4o",
        )
        assert result.content
        assert "Notice: OpenAI Cloud provider is unconfigured" in result.content
        assert "Live cloud testing marked as pending" in result.content
    finally:
        settings.OPENAI_API_KEY = original_key
