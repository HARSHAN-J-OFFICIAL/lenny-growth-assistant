import asyncio
from fastapi import APIRouter, status
from app.schemas.retrieval import SearchRequest, SearchResponse
from app.services.ingestion_manager import ingestion_manager

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid Transcript Search",
    description=(
        "Executes hybrid retrieval across Lenny's Podcast transcripts combining dense vector "
        "embeddings, BM25 lexical search, and curated topic indexes with Reciprocal Rank Fusion."
    ),
)
async def search_transcripts(request: SearchRequest) -> SearchResponse:
    """
    Search transcripts for grounded evidence passages.
    Offloaded to worker thread via asyncio.to_thread to prevent event loop starvation.
    """
    return await asyncio.to_thread(
        ingestion_manager.retriever.search,
        query=request.query,
        top_k=request.top_k,
        topic_filter=request.topic_filter,
        guest_filter=request.guest_filter,
    )
