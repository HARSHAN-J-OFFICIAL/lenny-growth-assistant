"""
Provider and Model Status API Endpoint.
Reports configured and available LLM providers, model catalogs, and cloud readiness.
"""

from fastapi import APIRouter, status
from app.schemas.provider import ProvidersStatusResponse
from app.services.llm_provider import get_providers_status

router = APIRouter()


@router.get(
    "",
    response_model=ProvidersStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Providers & Models Status",
)
@router.get(
    "/status",
    response_model=ProvidersStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Providers & Models Status",
)
async def get_providers() -> ProvidersStatusResponse:
    """
    Introspect active and available inference providers:
    - Ollama: Local engine (llama3.2 default, qwen2.5:1.5b lightweight)
    - OpenAI: Optional cloud engine (configured via OPENAI_API_KEY)
    - Anthropic: Optional cloud engine (configured via ANTHROPIC_API_KEY)
    """
    return await get_providers_status()
