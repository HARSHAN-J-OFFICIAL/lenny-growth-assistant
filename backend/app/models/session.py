"""
Session ORM model for multi-session conversation persistence.
"""

import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.message import MessageModel
    from app.models.artifact import ArtifactModel


class SessionModel(Base):
    """Stores conversation session metadata and settings."""
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
    )
    model_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ollama",
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="llama3.2",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at",
    )
    artifacts: Mapped[List["ArtifactModel"]] = relationship(
        "ArtifactModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ArtifactModel.created_at",
    )
