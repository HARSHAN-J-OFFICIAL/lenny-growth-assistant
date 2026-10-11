"""
Pydantic API request and response data contracts.
"""

from .common import ErrorDetail, ErrorResponse
from .health import HealthResponse
from .knowledge import KnowledgeStatusResponse
from .retrieval import EvidenceStatus, RetrievedPassage, SearchRequest, SearchResponse
from .session import SessionCreate, SessionResponse, SessionListResponse
from .artifact import ArtifactResponse
from .chat import ChatRequest, ChatMessageResponse, ChatHistoryResponse

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "EvidenceStatus",
    "HealthResponse",
    "KnowledgeStatusResponse",
    "RetrievedPassage",
    "SearchRequest",
    "SearchResponse",
    "SessionCreate",
    "SessionResponse",
    "SessionListResponse",
    "ArtifactResponse",
    "ChatRequest",
    "ChatMessageResponse",
    "ChatHistoryResponse",
]
