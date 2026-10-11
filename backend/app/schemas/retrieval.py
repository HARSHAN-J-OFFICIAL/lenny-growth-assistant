"""
Pydantic data contracts for retrieval requests, citations, and search responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    """
    Explicit evidence confidence classifications for retrieval results.
    """

    RELEVANT_EVIDENCE_FOUND = "relevant_evidence_found"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    EMPTY_KNOWLEDGE_BASE = "empty_knowledge_base"
    INDEX_UNAVAILABLE = "index_unavailable"
    INVALID_QUERY = "invalid_query"
    RETRIEVAL_FAILURE = "retrieval_failure"


class RetrievedPassage(BaseModel):
    """
    A single verifiable transcript passage with full citation evidence.
    """

    chunk_id: str = Field(description="Deterministic chunk identifier")
    episode_slug: str = Field(description="Directory-level slug identifier")
    episode_title: str = Field(description="Official episode title")
    guest: str = Field(description="Featured guest name")
    speaker: str = Field(description="Speaker identity for this passage turn")
    text: str = Field(description="Verbatim transcript excerpt")
    start_timestamp: str = Field(description="Formatted start timestamp HH:MM:SS")
    start_seconds: int = Field(description="Start time in seconds")
    end_timestamp: str = Field(description="Formatted end timestamp HH:MM:SS")
    end_seconds: int = Field(description="End time in seconds")
    timestamp_url: Optional[str] = Field(default=None, description="Direct YouTube URL with timestamp parameter")
    source_file: str = Field(description="Relative path to source transcript")
    score: float = Field(description="Unified Reciprocal Rank Fusion relevance score")
    rrf_rank: int = Field(description="Rank position in merged search results")
    semantic_score: Optional[float] = Field(default=None, description="Cosine similarity score if matched in vector search")
    lexical_score: Optional[float] = Field(default=None, description="BM25 score if matched in keyword search")
    topic_tags: List[str] = Field(default_factory=list, description="Associated topic taxonomy tags from podcast indexes")


class SearchRequest(BaseModel):
    """
    Search request query schema.
    """

    query: str = Field(..., min_length=1, max_length=1000, description="Product/growth question or search keywords")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of passages to return")
    topic_filter: Optional[str] = Field(default=None, description="Optional topic filter slug (e.g. 'product-led-growth')")
    guest_filter: Optional[str] = Field(default=None, description="Optional guest name or slug filter")


class SearchResponse(BaseModel):
    """
    Search response wrapper containing evidence status, citations, and performance diagnostics.
    """

    query: str = Field(description="Original user query")
    evidence_status: EvidenceStatus = Field(description="Evidence validity classification")
    passages: List[RetrievedPassage] = Field(default_factory=list, description="Ranked transcript evidence passages")
    total_candidates: int = Field(description="Total candidate chunks evaluated")
    latency_ms: float = Field(description="Retrieval execution time in milliseconds")
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic retrieval metadata")
