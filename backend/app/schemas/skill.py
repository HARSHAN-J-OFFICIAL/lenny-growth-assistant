"""
Pydantic schemas for Specialized Writing Skills (Ship 30 for 30).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Ship30Request(BaseModel):
    """Request payload for dedicated Ship 30 for 30 essay generation."""
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Core topic or theme for the Ship 30 essay (e.g. 'Founder Mode', 'Product-Led Growth')",
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Target audience for tailored messaging (e.g. 'Product Managers & Early Founders')",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional active session UUID for persistent artifact storage",
    )
    model_provider: Optional[str] = Field(
        default="ollama",
        description="LLM provider: 'ollama', 'groq', 'openai', or 'anthropic'",
    )
    model_name: Optional[str] = Field(
        default="llama3.2",
        description="Target model identifier (e.g. 'llama3.2', 'qwen2.5:1.5b', 'openai/gpt-oss-20b')",
    )


class Ship30Response(BaseModel):
    """Response containing generated Ship 30 essay, citations, and artifacts."""
    session_id: Optional[str] = None
    artifact_id: Optional[str] = None
    topic: str
    content: str
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    provider: str
    model_name: str
    evidence_status: str
    word_count: Optional[int] = None
    headline: Optional[str] = None
    guest_references: Optional[List[str]] = Field(default_factory=list)
