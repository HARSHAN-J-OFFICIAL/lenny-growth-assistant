"""
Pydantic schemas for generated Artifacts (PRDs, tables, interactive mockups).
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ArtifactResponse(BaseModel):
    """Schema representing an extracted artifact entity."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    title: str
    artifact_type: str
    content: str
    version: int
    created_at: datetime
