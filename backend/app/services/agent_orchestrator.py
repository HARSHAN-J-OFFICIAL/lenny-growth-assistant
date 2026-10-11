"""
Agent Orchestrator providing genuine agentic reasoning, multi-step tool execution,
and sandboxed domain tool invocation for Lenny Growth Assistant.
Supports Local Ollama (llama3.2 default, qwen2.5:1.5b lightweight) and Cloud OpenAI.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.agent_tools import (
    AGENT_TOOL_SCHEMAS,
    execute_agent_tool,
    verify_sandboxing,
    SecuritySandboxingViolation,
)
from app.services.artifact_extractor import extract_artifacts, ExtractedArtifact
from app.services.ship30_skill import is_ship30_requested, SHIP_30_SYSTEM_PROMPT

logger = logging.getLogger("lenny.agent.orchestrator")

AGENT_SYSTEM_PROMPT = """You are The Lenny Growth Assistant, a world-class AI advisor and product leadership coach grounded in Lenny's Podcast transcripts.

Your Capabilities & Tools:
1. `search_podcast_transcripts`: Use this tool to find verifiable quotes, guest tactics, and timestamps from 303 podcast episodes.
2. `get_topic_insights`: Use this tool to discover curated guests and episode counts for product topics.
3. `generate_sandboxed_artifact`: Use this tool to output structured PRDs, checklists, or frameworks.

Operational Rules:
- Grounding: Always base your advice and assertions on verifiable podcast evidence.
- Citations: Clearly attribute key frameworks to the interviewed guests (e.g., Brian Chesky, Elena Verna, Shreyas Doshi).
- Honesty: If search results contain no relevant evidence, state honestly that Lenny has not covered this topic.
- Sandboxing: Only domain tools are permitted. No host filesystem or shell operations exist.
"""


class AgentExecutionResult(BaseModel):
    """Encapsulates the end-to-end outcome of an agent reasoning turn."""
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[ExtractedArtifact] = Field(default_factory=list)
    tool_calls_trace: List[Dict[str, Any]] = Field(default_factory=list)
    provider: str
    model_name: str
    evidence_status: str = "sufficient"
    notice: Optional[str] = None


class AgentOrchestrator:
    """
    Coordinates multi-step agent execution with strictly sandboxed tools.
    """

    def __init__(self):
        # Guarantee sandboxing on initialization
        verify_sandboxing()
        self.tool_schemas = AGENT_TOOL_SCHEMAS

    async def run(
        self,
        message: str,
        session_history: Optional[List[Dict[str, str]]] = None,
        provider: str = "ollama",
        model_name: Optional[str] = None,
        skill: Optional[str] = None,
        max_turns: int = 4,
    ) -> AgentExecutionResult:
        """
        Execute an agent turn with tool calling and multi-step reasoning.
        """
        norm_provider = (provider or "ollama").lower()
        selected_model = model_name or settings.OLLAMA_DEFAULT_MODEL
        use_ship30 = is_ship30_requested(message, skill)
        system_prompt = SHIP_30_SYSTEM_PROMPT if use_ship30 else AGENT_SYSTEM_PROMPT

        # Route to appropriate provider execution
        if norm_provider in ["openai", "gpt"]:
            if settings.OPENAI_API_KEY:
                return await self._run_openai_agent(
                    message=message,
                    session_history=session_history or [],
                    system_prompt=system_prompt,
                    model_name=selected_model if "gpt" in selected_model else "gpt-4o",
                    max_turns=max_turns,
                )
            else:
                logger.info("OPENAI_API_KEY missing; falling back to local Ollama agent.")
                res = await self._run_ollama_agent(
                    message=message,
                    session_history=session_history or [],
                    system_prompt=system_prompt,
                    model_name=settings.OLLAMA_DEFAULT_MODEL,
                    max_turns=max_turns,
                )
                res.provider = "openai"
                res.notice = (
                    "OpenAI Cloud provider is unconfigured (OPENAI_API_KEY not set). "
                    f"Automatically routed to local Ollama ({settings.OLLAMA_DEFAULT_MODEL}). "
                    "Live cloud testing marked as pending."
                )
                res.content = f"[Notice: {res.notice}]\n\n{res.content}"
                return res

        if norm_provider in ["anthropic", "claude"]:
            from app.services.anthropic_agent import claude_agent_runner
            claude_res = await claude_agent_runner.run(
                message=message,
                session_history=session_history or [],
                model_name=selected_model if "claude" in selected_model else settings.ANTHROPIC_DEFAULT_MODEL,
                max_turns=max_turns,
            )
            return AgentExecutionResult(
                content=claude_res["content"],
                citations=claude_res["citations"],
                artifacts=claude_res["artifacts"],
                tool_calls_trace=claude_res["tool_calls_trace"],
                provider=claude_res["provider"],
                model_name=claude_res["model_name"],
                evidence_status=claude_res["evidence_status"],
                notice=claude_res.get("notice"),
            )

        if norm_provider in ["groq", "groq-cloud"]:
            target_model = selected_model if selected_model and selected_model not in [settings.OLLAMA_DEFAULT_MODEL, "groq"] else settings.GROQ_MODEL
            if target_model in ["groq", "gpt-oss", "default"]:
                target_model = settings.GROQ_MODEL

            if settings.GROQ_API_KEY:
                try:
                    return await self._run_groq_agent(
                        message=message,
                        session_history=session_history or [],
                        system_prompt=system_prompt,
                        model_name=target_model,
                        max_turns=max_turns,
                    )
                except Exception as exc:
                    logger.warning(f"Groq agent call failed ({exc}), falling back to local Ollama agent.")
                    res = await self._run_ollama_agent(
                        message=message,
                        session_history=session_history or [],
                        system_prompt=system_prompt,
                        model_name=settings.OLLAMA_DEFAULT_MODEL,
                        max_turns=max_turns,
                    )
                    res.provider = "groq"
                    res.notice = (
                        f"Groq Cloud call encountered an error ({exc}). "
                        f"Fell back to local Ollama ({settings.OLLAMA_DEFAULT_MODEL})."
                    )
                    res.content = f"[Notice: {res.notice}]\n\n{res.content}"
                    return res
            else:
                logger.info("GROQ_API_KEY missing; falling back to local Ollama agent.")
                res = await self._run_ollama_agent(
                    message=message,
                    session_history=session_history or [],
                    system_prompt=system_prompt,
                    model_name=settings.OLLAMA_DEFAULT_MODEL,
                    max_turns=max_turns,
                )
                res.provider = "groq"
                res.notice = (
                    "Groq Cloud provider is unconfigured (GROQ_API_KEY not set). "
                    f"Automatically routed to local Ollama ({settings.OLLAMA_DEFAULT_MODEL}). "
                    "Live cloud testing marked as pending."
                )
                res.content = f"[Notice: {res.notice}]\n\n{res.content}"
                return res

        # Default: Ollama (supports llama3.2 and qwen2.5:1.5b)
        return await self._run_ollama_agent(
            message=message,
            session_history=session_history or [],
            system_prompt=system_prompt,
            model_name=selected_model,
            max_turns=max_turns,
        )

    async def _run_ollama_agent(
        self,
        message: str,
        session_history: List[Dict[str, str]],
        system_prompt: str,
        model_name: str,
        max_turns: int = 4,
    ) -> AgentExecutionResult:
        """
        Execute agent loop using local Ollama daemon with native tool calling.
        """
        target_model = model_name
        if target_model not in ["llama3.2", "qwen2.5:1.5b", "llama3.2:latest"]:
            target_model = settings.OLLAMA_DEFAULT_MODEL

        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(session_history)
        messages.append({"role": "user", "content": message})

        citations: List[Dict[str, Any]] = []
        tool_trace: List[Dict[str, Any]] = []
        evidence_status = "sufficient"

        async with httpx.AsyncClient(timeout=120.0) as client:
            for turn in range(max_turns):
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "tools": self.tool_schemas,
                    "stream": False,
                    "options": {"temperature": 0.2},
                }

                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        logger.error(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
                        break
                    data = resp.json()
                    msg_obj = data.get("message", {})
                except Exception as exc:
                    logger.error(f"Error calling Ollama in agent loop: {exc}")
                    break

                # Append assistant message to thread
                messages.append(msg_obj)

                tool_calls = msg_obj.get("tool_calls", [])
                if not tool_calls:
                    raw_content = msg_obj.get("content", "").strip()

                    # Check if small model (e.g. qwen2.5:1.5b) emitted raw tool call JSON in content instead of tool_calls
                    if turn == 0 and ("search_podcast_transcripts" in raw_content or '"arguments"' in raw_content):
                        import re
                        m = re.search(r'"query"\s*:\s*"([^"]+)"', raw_content)
                        extracted_query = m.group(1) if m else message
                        tool_output = execute_agent_tool("search_podcast_transcripts", {"query": extracted_query})
                        passages = tool_output.get("passages", [])
                        tool_trace.append({"turn": 1, "tool": "search_podcast_transcripts", "arguments": {"query": extracted_query}})
                        if not passages or tool_output.get("evidence_status") == "insufficient":
                            return AgentExecutionResult(
                                content="Lenny's Podcast does not contain discussions or evidence regarding this topic. The podcast focuses on product management, growth, startup strategy, and leadership.",
                                citations=[],
                                artifacts=[],
                                tool_calls_trace=tool_trace,
                                provider="ollama",
                                model_name=target_model,
                                evidence_status="insufficient",
                            )
                        for p in passages:
                            citations.append({
                                "guest": p.get("guest"),
                                "speaker": p.get("speaker"),
                                "episode_title": p.get("episode_title"),
                                "episode_slug": p.get("episode_slug"),
                                "timestamp_url": p.get("timestamp_url"),
                                "start_timestamp": p.get("start_timestamp"),
                                "score": p.get("score"),
                            })
                        evidence_status = "sufficient"
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(tool_output),
                        })
                        continue

                    # If model previously ran retrieval and found nothing, ensure honest phrasing
                    if evidence_status == "insufficient" and (not raw_content or "{" in raw_content):
                        raw_content = "Lenny's Podcast does not contain discussions or evidence regarding this topic. The podcast focuses on product management, growth, startup strategy, and leadership."

                    cleaned_content, extracted_arts = extract_artifacts(raw_content)
                    return AgentExecutionResult(
                        content=cleaned_content,
                        citations=citations,
                        artifacts=extracted_arts,
                        tool_calls_trace=tool_trace,
                        provider="ollama",
                        model_name=target_model,
                        evidence_status=evidence_status,
                    )

                # Execute requested tools
                for tc in tool_calls:
                    fn_name = tc.get("function", {}).get("name", "")
                    fn_args = tc.get("function", {}).get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {}

                    tool_trace.append({"turn": turn + 1, "tool": fn_name, "arguments": fn_args})

                    try:
                        tool_output = execute_agent_tool(tool_name=fn_name, arguments=fn_args)
                        # Collect citations if search tool was called
                        if fn_name == "search_podcast_transcripts" and isinstance(tool_output, dict):
                            evidence_status = tool_output.get("evidence_status", "sufficient")
                            if evidence_status == "insufficient":
                                citations.clear()
                            else:
                                for p in tool_output.get("passages", []):
                                    citations.append({
                                        "guest": p.get("guest"),
                                        "speaker": p.get("speaker"),
                                        "episode_title": p.get("episode_title"),
                                        "episode_slug": p.get("episode_slug"),
                                        "timestamp_url": p.get("timestamp_url"),
                                        "start_timestamp": p.get("start_timestamp"),
                                        "score": p.get("score"),
                                    })
                    except Exception as err:
                        logger.error(f"Error executing agent tool {fn_name}: {err}")
                        tool_output = {"error": str(err)}

                    # Feed tool response back to model
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_output),
                    })

            # If loop finished without clean exit, take last assistant content
            last_content = ""
            for m in reversed(messages):
                if m.get("role") == "assistant" and m.get("content"):
                    last_content = m.get("content")
                    break

            cleaned_content, extracted_arts = extract_artifacts(last_content)

            # If evidence was insufficient, ensure the response honestly acknowledges lack of evidence
            if evidence_status == "insufficient":
                citations.clear()
                content_lower = cleaned_content.lower()
                if not any(k in content_lower for k in ["does not", "not contain", "not covered", "insufficient", "unfortunately"]):
                    cleaned_content = (
                        "Lenny's Podcast does not contain discussions or evidence regarding this topic. "
                        "The podcast focuses on product management, growth, startup scaling, and leadership."
                    )

            return AgentExecutionResult(
                content=cleaned_content,
                citations=citations,
                artifacts=extracted_arts,
                tool_calls_trace=tool_trace,
                provider="ollama",
                model_name=target_model,
                evidence_status=evidence_status,
            )

    async def _run_openai_agent(
        self,
        message: str,
        session_history: List[Dict[str, str]],
        system_prompt: str,
        model_name: str,
        max_turns: int = 4,
    ) -> AgentExecutionResult:
        """
        Execute agent loop using OpenAI Cloud API via AsyncOpenAI.
        """
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(session_history)
        messages.append({"role": "user", "content": message})

        citations: List[Dict[str, Any]] = []
        tool_trace: List[Dict[str, Any]] = []
        evidence_status = "sufficient"

        for turn in range(max_turns):
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=self.tool_schemas,
                    temperature=0.2,
                )
            except Exception as exc:
                logger.error(f"Error in OpenAI agent loop: {exc}")
                raise

            choice = response.choices[0]
            msg = choice.message

            # Convert message to dict format for appending
            msg_dict: Dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(msg_dict)

            if not msg.tool_calls:
                # Agent completed turn
                cleaned_content, extracted_arts = extract_artifacts(msg.content or "")
                return AgentExecutionResult(
                    content=cleaned_content,
                    citations=citations,
                    artifacts=extracted_arts,
                    tool_calls_trace=tool_trace,
                    provider="openai",
                    model_name=model_name,
                    evidence_status=evidence_status,
                )

            # Execute tool calls
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                tool_trace.append({"turn": turn + 1, "tool": fn_name, "arguments": fn_args})

                try:
                    tool_output = execute_agent_tool(tool_name=fn_name, arguments=fn_args)
                    if fn_name == "search_podcast_transcripts" and isinstance(tool_output, dict):
                        for p in tool_output.get("passages", []):
                            citations.append({
                                "guest": p.get("guest"),
                                "speaker": p.get("speaker"),
                                "episode_title": p.get("episode_title"),
                                "episode_slug": p.get("episode_slug"),
                                "timestamp_url": p.get("timestamp_url"),
                                "start_timestamp": p.get("start_timestamp"),
                                "score": p.get("score"),
                            })
                        evidence_status = tool_output.get("evidence_status", "sufficient")
                except Exception as err:
                    logger.error(f"Error executing agent tool {fn_name}: {err}")
                    tool_output = {"error": str(err)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_output),
                })

        # Fallback if turns exhausted
        last_content = messages[-1].get("content", "")
        cleaned_content, extracted_arts = extract_artifacts(last_content)
        return AgentExecutionResult(
            content=cleaned_content,
            citations=citations,
            artifacts=extracted_arts,
            tool_calls_trace=tool_trace,
            provider="openai",
            model_name=model_name,
            evidence_status=evidence_status,
        )

    async def _run_groq_agent(
        self,
        message: str,
        session_history: List[Dict[str, str]],
        system_prompt: str,
        model_name: str,
        max_turns: int = 4,
    ) -> AgentExecutionResult:
        """
        Execute agent loop using Groq Cloud API via OpenAI-compatible AsyncOpenAI.
        """
        client = AsyncOpenAI(
            base_url=settings.GROQ_BASE_URL,
            api_key=settings.GROQ_API_KEY,
            timeout=60.0,
        )
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(session_history)
        messages.append({"role": "user", "content": message})

        citations: List[Dict[str, Any]] = []
        tool_trace: List[Dict[str, Any]] = []
        evidence_status = "sufficient"

        for turn in range(max_turns):
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=self.tool_schemas,
                    temperature=0.2,
                )
            except Exception as exc:
                logger.error(f"Error in Groq agent loop: {exc}")
                raise

            choice = response.choices[0]
            msg = choice.message

            # Convert message to dict format for appending
            msg_dict: Dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(msg_dict)

            if not msg.tool_calls:
                # Agent completed turn
                cleaned_content, extracted_arts = extract_artifacts(msg.content or "")
                return AgentExecutionResult(
                    content=cleaned_content,
                    citations=citations,
                    artifacts=extracted_arts,
                    tool_calls_trace=tool_trace,
                    provider="groq",
                    model_name=model_name,
                    evidence_status=evidence_status,
                )

            # Execute tool calls
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                tool_trace.append({"turn": turn + 1, "tool": fn_name, "arguments": fn_args})

                try:
                    tool_output = execute_agent_tool(tool_name=fn_name, arguments=fn_args)
                    if fn_name == "search_podcast_transcripts" and isinstance(tool_output, dict):
                        for p in tool_output.get("passages", []):
                            citations.append({
                                "guest": p.get("guest"),
                                "speaker": p.get("speaker"),
                                "episode_title": p.get("episode_title"),
                                "episode_slug": p.get("episode_slug"),
                                "timestamp_url": p.get("timestamp_url"),
                                "start_timestamp": p.get("start_timestamp"),
                                "score": p.get("score"),
                            })
                        evidence_status = tool_output.get("evidence_status", "sufficient")
                except Exception as err:
                    logger.error(f"Error executing agent tool {fn_name}: {err}")
                    tool_output = {"error": str(err)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_output),
                })

        # Fallback if turns exhausted
        last_content = messages[-1].get("content", "")
        cleaned_content, extracted_arts = extract_artifacts(last_content)
        return AgentExecutionResult(
            content=cleaned_content,
            citations=citations,
            artifacts=extracted_arts,
            tool_calls_trace=tool_trace,
            provider="groq",
            model_name=model_name,
            evidence_status=evidence_status,
        )


# Singleton agent orchestrator instance
agent_orchestrator = AgentOrchestrator()
