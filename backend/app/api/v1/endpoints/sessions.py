"""
Sessions API endpoints for managing conversation sessions and history.
"""

from datetime import datetime, timezone
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.schemas.session import SessionCreate, SessionUpdate, SessionListResponse, SessionResponse
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse
from app.schemas.artifact import ArtifactResponse

router = APIRouter()


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Conversation Session",
)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Create a new session in PostgreSQL."""
    new_session = SessionModel(
        title=payload.title or "New Conversation",
        model_provider=payload.model_provider or "ollama",
        model_name=payload.model_name or "llama3.2",
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return SessionResponse.model_validate(new_session)


@router.get(
    "",
    response_model=SessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Conversation Sessions",
)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List stored sessions ordered by most recently updated."""
    query = (
        select(SessionModel)
        .order_by(desc(SessionModel.updated_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Session by ID",
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Retrieve session metadata by UUID."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    return SessionResponse.model_validate(session_obj)


@router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename/Update Session",
)
@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename/Update Session (PUT alias)",
)
async def update_session(
    session_id: uuid.UUID,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Update session title or attributes."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    session_obj.title = payload.title.strip()
    session_obj.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session_obj)
    return SessionResponse.model_validate(session_obj)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete session and cascade delete its messages and artifacts."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    await db.delete(session_obj)
    await db.commit()


@router.get(
    "/{session_id}/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Session Message History",
)
async def get_session_history(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """Retrieve chronological message history for a session."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Fetch messages with their artifacts
    query = (
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # Query artifacts for this session to map to messages
    from app.models.artifact import ArtifactModel
    art_query = select(ArtifactModel).where(ArtifactModel.session_id == session_id)
    art_result = await db.execute(art_query)
    artifacts = art_result.scalars().all()

    art_by_msg = {}
    for a in artifacts:
        if a.message_id:
            art_by_msg.setdefault(a.message_id, []).append(ArtifactResponse.model_validate(a))

    message_responses = [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            metadata_payload=m.metadata_payload or {},
            artifacts=art_by_msg.get(m.id, []),
            created_at=m.created_at,
        )
        for m in messages
    ]

    return ChatHistoryResponse(
        session_id=session_id,
        title=session_obj.title,
        messages=message_responses,
    )


@router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename / Update Session",
)
async def rename_session(
    session_id: uuid.UUID,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Rename a conversation session."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    session_obj.title = payload.title.strip()
    session_obj.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session_obj)
    return SessionResponse.model_validate(session_obj)


@router.get(
    "/{session_id}/citations",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get All Citations for Session",
)
async def get_session_citations(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Retrieve all verified citations associated with answers in this session."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    query = (
        select(MessageModel)
        .where(MessageModel.session_id == session_id, MessageModel.role == "assistant")
        .order_by(MessageModel.created_at)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    all_citations = []
    seen_urls = set()
    for m in messages:
        if m.citations:
            for c in m.citations:
                url = c.get("timestamp_url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_citations.append(c)
                elif not url:
                    all_citations.append(c)

    return all_citations


@router.get(
    "/{session_id}/artifacts",
    response_model=List[ArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Artifacts for Session",
)
async def get_session_artifacts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ArtifactResponse]:
    """Retrieve all artifacts generated within a session."""
    session_obj = await db.get(SessionModel, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    from app.models.artifact import ArtifactModel
    query = (
        select(ArtifactModel)
        .where(ArtifactModel.session_id == session_id)
        .order_by(ArtifactModel.created_at)
    )
    result = await db.execute(query)
    artifacts = result.scalars().all()
    return [ArtifactResponse.model_validate(a) for a in artifacts]
