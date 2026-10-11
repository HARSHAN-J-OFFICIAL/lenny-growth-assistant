"""
Multi-provider LLM abstraction layer supporting Local Ollama (llama3.2, qwen2.5:1.5b)
and Cloud Models (OpenAI, Anthropic) with graceful fallback and status introspection.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.provider import ModelInfo, ProviderInfo, ProvidersStatusResponse

logger = logging.getLogger("lenny.llm")


class LLMProviderError(Exception):
    """Raised when an LLM provider fails to generate a completion."""
    pass


async def generate_ollama_completion(
    messages: List[Dict[str, str]],
    model_name: str = "llama3.2",
    temperature: float = 0.3,
) -> str:
    """
    Call local Ollama daemon via /api/chat endpoint.
    Supports llama3.2 (default) and qwen2.5:1.5b (lightweight alternative).
    """
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise LLMProviderError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            message = data.get("message", {})
            return message.get("content", "").strip()
    except httpx.ConnectError:
        raise LLMProviderError(
            f"Could not connect to Ollama daemon at {settings.OLLAMA_BASE_URL}. Ensure Ollama is running."
        )
    except Exception as exc:
        if isinstance(exc, LLMProviderError):
            raise
        raise LLMProviderError(f"Ollama inference error: {exc}")


async def generate_openai_completion(
    messages: List[Dict[str, str]],
    model_name: str = "gpt-4o",
    temperature: float = 0.3,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate completion using OpenAI Cloud API via AsyncOpenAI client.
    Requires OPENAI_API_KEY environment variable.
    """
    resolved_key = api_key or settings.OPENAI_API_KEY
    if not resolved_key:
        raise LLMProviderError(
            "OpenAI Cloud API key is not configured. Set OPENAI_API_KEY in .env or environment variables."
        )

    try:
        client = AsyncOpenAI(api_key=resolved_key, timeout=60.0)
        # Format messages according to OpenAI API expectations
        formatted_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]
        completion = await client.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            temperature=temperature,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:
        raise LLMProviderError(f"OpenAI inference error: {exc}")


async def generate_anthropic_completion(
    messages: List[Dict[str, str]],
    model_name: Optional[str] = None,
    temperature: float = 0.3,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate completion using Anthropic Claude Cloud API via AsyncAnthropic client.
    Supports configurable default model (claude-sonnet-4-6) and lightweight alternative (claude-haiku-4-5).
    """
    resolved_key = api_key or settings.ANTHROPIC_API_KEY
    if not resolved_key:
        raise LLMProviderError(
            "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in .env or environment variables."
        )

    # Normalize short aliases and retired IDs to currently supported API model identifiers
    target_model = model_name or settings.ANTHROPIC_DEFAULT_MODEL
    if target_model in ["claude-sonnet", "claude-sonnet-4-6", "claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "claude"]:
        target_model = settings.ANTHROPIC_DEFAULT_MODEL
    elif target_model in ["claude-haiku", "claude-haiku-4-5", "claude-3-5-haiku", "claude-3-5-haiku-20241022"]:
        target_model = "claude-haiku-4-5"

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=resolved_key, timeout=60.0)
        system_msg = ""
        chat_turns = []
        for m in messages:
            if m["role"] == "system":
                system_msg += m["content"] + "\n\n"
            else:
                chat_turns.append(m)

        kwargs: Dict[str, Any] = {
            "model": target_model,
            "max_tokens": 4096,
            "messages": chat_turns,
            "temperature": temperature,
        }
        if system_msg.strip():
            kwargs["system"] = system_msg.strip()

        response = await client.messages.create(**kwargs)
        return response.content[0].text.strip()
    except Exception as exc:
        raise LLMProviderError(f"Anthropic inference error: {exc}")


async def generate_groq_completion(
    messages: List[Dict[str, str]],
    model_name: Optional[str] = None,
    temperature: float = 0.3,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Generate completion using Groq Cloud API via OpenAI-compatible AsyncOpenAI client.
    Requires GROQ_API_KEY environment variable. Free-tier high-speed LPU inference.
    """
    resolved_key = api_key or settings.GROQ_API_KEY
    if not resolved_key:
        raise LLMProviderError(
            "Groq Cloud API key is not configured. Set GROQ_API_KEY in .env or environment variables."
        )

    resolved_base_url = base_url or settings.GROQ_BASE_URL
    target_model = model_name or settings.GROQ_MODEL
    # Normalize common shorthand aliases
    if target_model in ["groq", "gpt-oss", "gpt-oss-20b", "default"]:
        target_model = settings.GROQ_MODEL

    try:
        client = AsyncOpenAI(
            base_url=resolved_base_url,
            api_key=resolved_key,
            timeout=60.0,
        )
        formatted_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]
        completion = await client.chat.completions.create(
            model=target_model,
            messages=formatted_messages,
            temperature=temperature,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:
        err_msg = str(exc)
        if "401" in err_msg or "invalid_api_key" in err_msg.lower():
            raise LLMProviderError(f"Groq authentication error: Invalid GROQ_API_KEY ({err_msg})")
        elif "429" in err_msg or "rate_limit" in err_msg.lower():
            raise LLMProviderError(f"Groq free-tier rate limit exceeded (HTTP 429). Please retry shortly: {err_msg}")
        raise LLMProviderError(f"Groq inference error: {exc}")


async def generate_completion(
    messages: List[Dict[str, str]],
    provider: str = "ollama",
    model_name: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Route completion request to selected provider (ollama, openai, anthropic)
    with automatic fallback to local Ollama if cloud credentials are not configured.
    Ensures provider toggle changes actual model routing.
    """
    norm_provider = (provider or "ollama").lower()
    selected_model = model_name or settings.OLLAMA_DEFAULT_MODEL

    # 1. Local Ollama Provider
    if norm_provider == "ollama":
        # Support both llama3.2 and qwen2.5:1.5b
        target_model = selected_model
        if target_model not in ["llama3.2", "qwen2.5:1.5b", "llama3.2:latest"]:
            target_model = settings.OLLAMA_DEFAULT_MODEL
        return await generate_ollama_completion(
            messages,
            model_name=target_model,
            temperature=temperature,
        )

    # 2. OpenAI Cloud Provider
    if norm_provider in ["openai", "gpt"]:
        target_model = selected_model if "gpt" in selected_model else "gpt-4o"
        if settings.OPENAI_API_KEY:
            try:
                return await generate_openai_completion(
                    messages=messages,
                    model_name=target_model,
                    temperature=temperature,
                )
            except Exception as exc:
                logger.warning(f"OpenAI call failed ({exc}), falling back to local Ollama.")
                res = await generate_ollama_completion(
                    messages,
                    model_name=settings.OLLAMA_DEFAULT_MODEL,
                    temperature=temperature,
                )
                return (
                    f"[Notice: OpenAI call encountered an error ({exc}). "
                    f"Fell back to local Ollama ({settings.OLLAMA_DEFAULT_MODEL})]\n\n"
                    + res
                )
        else:
            # Cloud API credentials unavailable: graceful fallback to local Ollama without breaking
            logger.info("OpenAI API key missing; gracefully falling back to local Ollama.")
            res = await generate_ollama_completion(
                messages,
                model_name=settings.OLLAMA_DEFAULT_MODEL,
                temperature=temperature,
            )
            return (
                f"[Notice: OpenAI Cloud provider is unconfigured (OPENAI_API_KEY not set). "
                f"Automatically routed to local Ollama ({settings.OLLAMA_DEFAULT_MODEL}). "
                f"Live cloud testing marked as pending.]\n\n"
                + res
            )

    # 3. Anthropic Claude Provider
    if norm_provider in ["anthropic", "claude"]:
        target_model = selected_model if "claude" in selected_model else settings.ANTHROPIC_DEFAULT_MODEL
        if target_model in ["claude", "claude-sonnet", "claude-sonnet-4-6", "claude-3-5-sonnet", "claude-3-5-sonnet-20241022"]:
            target_model = settings.ANTHROPIC_DEFAULT_MODEL
        elif target_model in ["claude-haiku", "claude-haiku-4-5", "claude-3-5-haiku", "claude-3-5-haiku-20241022"]:
            target_model = "claude-haiku-4-5"
        if settings.ANTHROPIC_API_KEY:
            try:
                return await generate_anthropic_completion(
                    messages=messages,
                    model_name=target_model,
                    temperature=temperature,
                )
            except Exception as exc:
                logger.warning(f"Anthropic call failed ({exc}), falling back to Ollama.")
                res = await generate_ollama_completion(
                    messages,
                    model_name=settings.OLLAMA_DEFAULT_MODEL,
                    temperature=temperature,
                )
                return (
                    f"[Notice: Anthropic call encountered an error ({exc}). "
                    f"Fell back to local Ollama ({settings.OLLAMA_DEFAULT_MODEL})]\n\n"
                    + res
                )
        else:
            logger.info("Anthropic API key missing; gracefully falling back to local Ollama.")
            res = await generate_ollama_completion(
                messages,
                model_name=settings.OLLAMA_DEFAULT_MODEL,
                temperature=temperature,
            )
            return (
                f"[Notice: Anthropic Cloud provider is unconfigured (ANTHROPIC_API_KEY not set). "
                f"Automatically routed to local Ollama ({settings.OLLAMA_DEFAULT_MODEL}). "
                f"Live cloud testing marked as pending.]\n\n"
                + res
            )

    # 4. Groq Cloud Provider (Free-Tier High-Speed Inference)
    if norm_provider in ["groq", "groq-cloud"]:
        target_model = selected_model if selected_model and selected_model not in [settings.OLLAMA_DEFAULT_MODEL, "groq"] else settings.GROQ_MODEL
        if target_model in ["groq", "gpt-oss", "default"]:
            target_model = settings.GROQ_MODEL

        if settings.GROQ_API_KEY:
            try:
                return await generate_groq_completion(
                    messages=messages,
                    model_name=target_model,
                    temperature=temperature,
                )
            except Exception as exc:
                logger.warning(f"Groq call failed ({exc}), falling back to local Ollama.")
                res = await generate_ollama_completion(
                    messages,
                    model_name=settings.OLLAMA_DEFAULT_MODEL,
                    temperature=temperature,
                )
                return (
                    f"[Notice: Groq Cloud call encountered an error ({exc}). "
                    f"Fell back to local Ollama ({settings.OLLAMA_DEFAULT_MODEL})]\n\n"
                    + res
                )
        else:
            logger.info("Groq API key missing; gracefully falling back to local Ollama.")
            res = await generate_ollama_completion(
                messages,
                model_name=settings.OLLAMA_DEFAULT_MODEL,
                temperature=temperature,
            )
            return (
                f"[Notice: Groq Cloud provider is unconfigured (GROQ_API_KEY not set). "
                f"Automatically routed to local Ollama ({settings.OLLAMA_DEFAULT_MODEL}). "
                f"Live cloud testing marked as pending.]\n\n"
                + res
            )

    # Default fallback to local Ollama
    return await generate_ollama_completion(
        messages,
        model_name=settings.OLLAMA_DEFAULT_MODEL,
        temperature=temperature,
    )


async def get_providers_status() -> ProvidersStatusResponse:
    """
    Introspect the status and models of all supported inference providers.
    Detects local Ollama models dynamically and reports cloud configuration status.
    """
    ollama_models = [
        ModelInfo(
            id="llama3.2",
            name="Llama 3.2 (3.2B)",
            description="Default high-quality local reasoning model",
            context_length=131072,
            is_default=True,
            is_lightweight=False,
        ),
        ModelInfo(
            id="qwen2.5:1.5b",
            name="Qwen 2.5 (1.5B)",
            description="Ultra-fast lightweight alternative for low memory footprint",
            context_length=32768,
            is_default=False,
            is_lightweight=True,
        ),
    ]

    # Verify Ollama connectivity
    ollama_available = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                ollama_available = True
    except Exception:
        ollama_available = False

    ollama_provider = ProviderInfo(
        id="ollama",
        name="Ollama (Local Engine)",
        provider_type="local",
        is_configured=True,
        is_available=ollama_available,
        status_message="Connected and ready for local inference" if ollama_available else "Ollama daemon not responding",
        default_model="llama3.2",
        models=ollama_models,
        requires_api_key=False,
    )

    # OpenAI Cloud Provider
    openai_configured = bool(settings.OPENAI_API_KEY)
    openai_provider = ProviderInfo(
        id="openai",
        name="OpenAI (Cloud Engine)",
        provider_type="cloud",
        is_configured=openai_configured,
        is_available=openai_configured,
        status_message=(
            "Configured and available via OPENAI_API_KEY"
            if openai_configured
            else "Unconfigured: OPENAI_API_KEY not set (will fallback gracefully to Ollama)"
        ),
        default_model="gpt-4o",
        models=[
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                description="High-intelligence flagship cloud model",
                context_length=128000,
                is_default=True,
                is_lightweight=False,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                description="Fast and affordable cloud model",
                context_length=128000,
                is_default=False,
                is_lightweight=True,
            ),
        ],
        requires_api_key=True,
    )

    # Anthropic Cloud Provider
    anthropic_configured = bool(settings.ANTHROPIC_API_KEY)
    anthropic_provider = ProviderInfo(
        id="anthropic",
        name="Anthropic Claude (Cloud Engine)",
        provider_type="cloud",
        is_configured=anthropic_configured,
        is_available=anthropic_configured,
        status_message=(
            "Configured and available via ANTHROPIC_API_KEY"
            if anthropic_configured
            else "Unconfigured: ANTHROPIC_API_KEY not set (will fallback gracefully to Ollama)"
        ),
        default_model=settings.ANTHROPIC_DEFAULT_MODEL,
        models=[
            ModelInfo(
                id=settings.ANTHROPIC_DEFAULT_MODEL,
                name="Claude Sonnet 4.6",
                description="Flagship hybrid reasoning and coding cloud model",
                context_length=200000,
                is_default=True,
                is_lightweight=False,
            ),
            ModelInfo(
                id="claude-haiku-4-5",
                name="Claude Haiku 4.5",
                description="Fast and cost-efficient intelligent cloud model",
                context_length=200000,
                is_default=False,
                is_lightweight=True,
            ),
        ],
        requires_api_key=True,
    )

    # Groq Cloud Provider (Free-Tier High-Speed Inference)
    groq_configured = bool(settings.GROQ_API_KEY)
    groq_provider = ProviderInfo(
        id="groq",
        name="Groq Cloud (Free Tier)",
        provider_type="cloud",
        is_configured=groq_configured,
        is_available=groq_configured,
        status_message=(
            "Configured and available via GROQ_API_KEY"
            if groq_configured
            else "Unconfigured: GROQ_API_KEY not set (will fallback gracefully to Ollama)"
        ),
        default_model=settings.GROQ_MODEL,
        models=[
            ModelInfo(
                id=settings.GROQ_MODEL,
                name="GPT-OSS 20B (Groq LPU)",
                description="High-speed open-weight MoE reasoning model on Groq LPU",
                context_length=131072,
                is_default=True,
                is_lightweight=False,
            ),
            ModelInfo(
                id="llama-3.3-70b-versatile",
                name="Llama 3.3 70B (Groq LPU)",
                description="High-intelligence versatile open model on Groq LPU",
                context_length=131072,
                is_default=False,
                is_lightweight=False,
            ),
            ModelInfo(
                id="llama-3.1-8b-instant",
                name="Llama 3.1 8B Instant (Groq LPU)",
                description="Ultra-fast low-latency model on Groq LPU",
                context_length=131072,
                is_default=False,
                is_lightweight=True,
            ),
        ],
        requires_api_key=True,
    )

    cloud_testing_status = "active" if openai_configured or anthropic_configured or groq_configured else "pending"

    return ProvidersStatusResponse(
        active_provider="ollama",
        default_model=settings.OLLAMA_DEFAULT_MODEL,
        providers=[ollama_provider, openai_provider, anthropic_provider, groq_provider],
        cloud_testing_status=cloud_testing_status,
    )
