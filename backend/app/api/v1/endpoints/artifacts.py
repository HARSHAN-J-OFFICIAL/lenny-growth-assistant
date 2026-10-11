"""
Artifacts API endpoints for retrieving rendered and structured documents.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.artifact import ArtifactModel
from app.schemas.artifact import ArtifactResponse

router = APIRouter()


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Artifact by ID",
)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """Retrieve artifact entity for display in the dual-pane viewer."""
    artifact = await db.get(ArtifactModel, artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )
    return ArtifactResponse.model_validate(artifact)


@router.get(
    "/session/{session_id}",
    response_model=List[ArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="List Artifacts for Session",
)
async def list_session_artifacts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ArtifactResponse]:
    """Retrieve all artifacts associated with a conversation session."""
    query = (
        select(ArtifactModel)
        .where(ArtifactModel.session_id == session_id)
        .order_by(ArtifactModel.created_at)
    )
    result = await db.execute(query)
    artifacts = result.scalars().all()
    return [ArtifactResponse.model_validate(a) for a in artifacts]
