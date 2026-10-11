import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.artifact import ArtifactModel
from app.schemas.skill import Ship30Request, Ship30Response
from app.services.ship30_skill import ship30_service

logger = logging.getLogger("lenny.skills.endpoint")
router = APIRouter()


@router.post(
    "/ship30",
    response_model=Ship30Response,
    status_code=status.HTTP_200_OK,
    summary="Generate Ship 30 for 30 Atomic Essay",
)
async def generate_ship30_essay(
    payload: Ship30Request,
    db: AsyncSession = Depends(get_db),
) -> Ship30Response:
    """
    Generate an executive-ready, ~1,250-word atomic essay following
    Dickie Bush & Nicolas Cole's Ship 30 for 30 digital writing architecture,
    grounded in Lenny's Podcast transcripts. Automatically persists the generated
    Markdown artifact to PostgreSQL when an active session_id is provided.
    """
    result = await ship30_service.generate_essay(
        topic=payload.topic,
        provider=payload.model_provider or "ollama",
        model_name=payload.model_name or "llama3.2",
    )

    created_artifact_id: Optional[str] = None
    persisted_session_id: Optional[str] = payload.session_id

    # If an active session UUID is provided, persist the artifact and assistant message
    if payload.session_id:
        try:
            sess_uuid = uuid.UUID(payload.session_id)
            session_obj = await db.get(SessionModel, sess_uuid)
            if session_obj:
                headline = result.get("headline", payload.topic)
                full_essay = result.get("content", "")

                # 1. Create assistant message documenting essay synthesis
                guest_list = result.get('guest_references', [])
                guests_str = ', '.join(guest_list) if guest_list else "Lenny's Guests"
                summary_content = (
                    f"### 🚀 Ship 30 for 30 Essay Generated: \"{headline}\"\n\n"
                    f"Word Count: **{result.get('word_count', 0)} words** | "
                    f"Grounded in: **{guests_str}**\n\n"
                    f"The full structured essay has been saved as a Markdown artifact and is now accessible in the Artifact Viewer."
                )
                assistant_msg = MessageModel(
                    session_id=sess_uuid,
                    role="assistant",
                    content=summary_content,
                    citations=result.get("citations", []),
                    metadata_payload={
                        "skill": "ship30",
                        "topic": payload.topic,
                        "model_name": payload.model_name or "llama3.2",
                        "provider": payload.model_provider or "ollama",
                    },
                )
                db.add(assistant_msg)
                await db.flush()

                # 2. Persist artifact record
                art_title = f"Ship 30 Essay: {headline}"
                artifact_obj = ArtifactModel(
                    session_id=sess_uuid,
                    message_id=assistant_msg.id,
                    title=art_title,
                    artifact_type="markdown",
                    content=full_essay,
                    version=1,
                )
                db.add(artifact_obj)
                await db.commit()
                await db.refresh(artifact_obj)

                created_artifact_id = str(artifact_obj.id)
                persisted_session_id = str(sess_uuid)
                logger.info(f"Persisted Ship 30 essay artifact {created_artifact_id} for session {persisted_session_id}")
            else:
                logger.warning(f"Session {payload.session_id} not found in database; skipping persistence.")
        except Exception as exc:
            logger.warning(f"Failed to persist Ship 30 essay to PostgreSQL: {exc}")
            await db.rollback()

    result["session_id"] = persisted_session_id
    result["artifact_id"] = created_artifact_id

    return Ship30Response(**result)
