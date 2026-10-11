"""
Pydantic schemas for Conversation Sessions.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    """Schema for creating a new conversation session."""
    title: Optional[str] = Field(default="New Conversation", max_length=255)
    model_provider: Optional[str] = Field(default="ollama", max_length=50)
    model_name: Optional[str] = Field(default="llama3.2", max_length=100)


class SessionUpdate(BaseModel):
    """Schema for updating/renaming an existing conversation session."""
    title: str = Field(..., min_length=1, max_length=255, description="Updated session title")


class SessionResponse(BaseModel):
    """Schema representing a stored conversation session."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """Schema for listing multiple sessions."""
    sessions: List[SessionResponse]
    total: int
