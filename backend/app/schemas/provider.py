"""
Pydantic schemas for AI Providers, Model Routing, and Cloud Status.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Metadata for an individual LLM model."""
    id: str
    name: str
    description: str
    context_length: Optional[int] = None
    is_default: bool = False
    is_lightweight: bool = False


class ProviderInfo(BaseModel):
    """Metadata and runtime status for an LLM inference provider."""
    id: str
    name: str
    provider_type: str = Field(description="'local' or 'cloud'")
    is_configured: bool
    is_available: bool
    status_message: str
    default_model: str
    models: List[ModelInfo]
    requires_api_key: bool


class ProvidersStatusResponse(BaseModel):
    """Status report of all registered inference providers."""
    active_provider: str
    default_model: str
    providers: List[ProviderInfo]
    cloud_testing_status: str = Field(
        default="pending",
        description="Status of live cloud testing: 'pending' (credentials unconfigured) or 'active'",
    )
