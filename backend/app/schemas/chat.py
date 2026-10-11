"""
Pydantic schemas for Chat completion, history, and message responses.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.artifact import ArtifactResponse


class ChatRequest(BaseModel):
    """Request payload for /api/v1/chat endpoint."""
    session_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional session UUID. If omitted, a new session is created.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User question or prompt for the assistant",
    )
    model_provider: Optional[str] = Field(
        default="ollama",
        description="Model provider: 'ollama', 'anthropic', or 'openai'",
    )
    model_name: Optional[str] = Field(
        default="llama3.2",
        description="Target model identifier (e.g. 'llama3.2', 'qwen2.5:1.5b')",
    )
    skill: Optional[str] = Field(
        default=None,
        description="Optional specialized skill trigger (e.g. 'ship30')",
    )
    agentic: Optional[bool] = Field(
        default=False,
        description="Enable multi-step tool-calling agent orchestration",
    )
    agent_sdk: Optional[str] = Field(
        default=None,
        description="Official Agent SDK engine: 'pi' for Pi Coding Agent SDK, 'claude' for Claude Agent SDK, or None",
    )


class ChatMessageResponse(BaseModel):
    """Single message response representation."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    artifacts: List[ArtifactResponse] = Field(default_factory=list)
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Full session history containing all conversation turns."""
    session_id: uuid.UUID
    title: str
    messages: List[ChatMessageResponse]
