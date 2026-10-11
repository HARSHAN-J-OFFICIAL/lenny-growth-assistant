"""
Pydantic data contracts for knowledge base status and ingestion reporting.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class KnowledgeStatusResponse(BaseModel):
    """
    Diagnostic status of the persistent transcript knowledge base.
    """

    ingestion_state: str = Field(description="Operational state: 'ready', 'indexing', 'unindexed', or 'error'")
    indexed_episodes_count: int = Field(default=0, description="Total distinct podcast episodes indexed")
    indexed_chunks_count: int = Field(default=0, description="Total searchable conversational chunks")
    indexed_topics_count: int = Field(default=0, description="Total curated topical taxonomies loaded")
    last_indexed_at: Optional[datetime] = Field(default=None, description="Timestamp of last successful indexing run")
    embedding_model: str = Field(description="Identifier of active embedding model")
    vector_dim: int = Field(default=384, description="Embedding vector dimension")
    index_storage_bytes: int = Field(default=0, description="Total disk size of persistent index files in bytes")
    warnings: List[str] = Field(default_factory=list, description="Diagnostic warnings or operational notices")
