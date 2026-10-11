"""
API Endpoints for knowledge base diagnostic status and ingestion management.
"""

from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Query, status
from app.schemas.knowledge import KnowledgeStatusResponse
from app.services.ingestion_manager import ingestion_manager

router = APIRouter()


@router.get(
    "/status",
    response_model=KnowledgeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Knowledge Base Status",
    description="Inspect ingestion state, indexed document counts, vector dimension, and index availability.",
)
async def get_knowledge_status() -> KnowledgeStatusResponse:
    """
    Return knowledge base operational status.
    """
    return ingestion_manager.get_status()


@router.post(
    "/index",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Transcript Ingestion",
    description="Trigger asynchronous or limited dataset indexing without blocking server requests.",
)
async def trigger_indexing(
    background_tasks: BackgroundTasks,
    max_episodes: Optional[int] = Query(default=None, description="Optional cap on episodes to index"),
):
    """
    Trigger transcript ingestion.
    """
    background_tasks.add_task(ingestion_manager.ingest_dataset, max_episodes=max_episodes)
    return {
        "status": "indexing_scheduled",
        "message": f"Ingestion queued in background (max_episodes={max_episodes})",
    }
