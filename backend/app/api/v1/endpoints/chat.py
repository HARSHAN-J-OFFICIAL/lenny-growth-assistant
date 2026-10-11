"""
Chat completion endpoint orchestrating Hybrid RAG, Multi-Provider LLMs, and Artifact Persistence.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.artifact import ArtifactModel
from app.schemas.chat import ChatRequest, ChatMessageResponse
from app.schemas.artifact import ArtifactResponse
from app.schemas.retrieval import EvidenceStatus
from app.services.ingestion_manager import ingestion_manager
from app.services.llm_provider import generate_completion, LLMProviderError
from app.services.agent_orchestrator import agent_orchestrator
from app.services.pi_agent_client import pi_agent_client
from app.services.artifact_extractor import extract_artifacts
from app.services.ship30_skill import is_ship30_requested, SHIP_30_SYSTEM_PROMPT

logger = logging.getLogger("lenny.chat")
router = APIRouter()

STANDARD_SYSTEM_PROMPT = """You are The Lenny Growth Assistant, a world-class conversational AI and product advisor grounded in Lenny's Podcast transcripts.

Operational Rules:
1. Grounding: Base your factual assertions, frameworks, and tactics on the provided Transcript Evidence.
2. Citation Attribution: Clearly attribute key insights to the specific interviewed guests (e.g., Brian Chesky, Elena Verna, Shreyas Doshi).
3. Verifiable Honesty: If the provided transcripts do not contain the answer or evidence is insufficient, explicitly state that Lenny has not covered this specific topic on the podcast.
4. Artifacts: When creating actionable checklists, PRDs, tables, or interactive mockups, wrap them in:
:::artifact{title="Descriptive Title" type="markdown|html|svg|code"}
<content>
:::
"""


@router.post(
    "",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Chat Completion",
)
async def chat_completion(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """
    Execute grounded RAG completion turn:
    1. Retrieve verifiable evidence from 303 episodes.
    2. Route to chosen model provider (Local Ollama / Cloud).
    3. Extract structured sandboxed artifacts.
    4. Persist turn and artifacts to PostgreSQL.
    """
    # 1. Resolve or create session
    session_id = payload.session_id
    if session_id:
        session_obj = await db.get(SessionModel, session_id)
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )
    else:
        # Create new session with automatic title snippet
        snippet = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        session_obj = SessionModel(
            title=f"Chat: {snippet}",
            model_provider=payload.model_provider or "ollama",
            model_name=payload.model_name or "llama3.2",
        )
        db.add(session_obj)
        await db.flush()
        session_id = session_obj.id

    # 2. Record User Message in PostgreSQL with client/user metadata
    user_msg_id = uuid.uuid4()
    user_meta = dict(payload.user_metadata or {})
    user_meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    user_meta.setdefault("model_provider", payload.model_provider or session_obj.model_provider)
    user_meta.setdefault("model_name", payload.model_name or session_obj.model_name)
    if payload.skill:
        user_meta.setdefault("skill", payload.skill)
    if payload.agent_sdk:
        user_meta.setdefault("agent_sdk", payload.agent_sdk)

    user_msg = MessageModel(
        id=user_msg_id,
        session_id=session_id,
        role="user",
        content=payload.message,
        citations=[],
        metadata_payload=user_meta,
    )
    db.add(user_msg)
    await db.flush()

    # 3. Execute Completion Turn (Pi Agent SDK, Agentic Orchestration, or Direct Grounded RAG)
    if payload.agent_sdk == "pi" or (payload.agentic and (payload.model_provider or "").lower() == "pi"):
        # Genuine @earendil-works/pi-coding-agent SDK Execution
        agent_res = await pi_agent_client.run(
            message=payload.message,
            provider=payload.model_provider or session_obj.model_provider,
            model_name=payload.model_name or session_obj.model_name,
            skill=payload.skill,
        )
        cleaned_content = agent_res.content
        citation_records = agent_res.citations
        extracted_artifacts = agent_res.artifacts
        evidence_status_val = agent_res.evidence_status

        # Grounding guarantee: If no citations gathered via tool call and evidence is sufficient, execute hybrid retrieval
        if not citation_records and evidence_status_val != "insufficient":
            retrieval_res = await asyncio.to_thread(ingestion_manager.retriever.search, payload.message, top_k=4)
            if retrieval_res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND:
                for p in retrieval_res.passages:
                    citation_records.append({
                        "guest": p.guest,
                        "speaker": p.speaker,
                        "episode_title": p.episode_title,
                        "episode_slug": p.episode_slug,
                        "timestamp_url": p.timestamp_url,
                        "start_timestamp": p.start_timestamp,
                        "score": p.score,
                    })
            else:
                evidence_status_val = "insufficient"

        meta_payload = {
            "evidence_status": evidence_status_val,
            "model_provider": agent_res.provider,
            "model_name": agent_res.model_name,
            "agentic": True,
            "agent_sdk": "pi-coding-agent",
            "tool_calls_trace": agent_res.tool_calls_trace,
            "notice": agent_res.notice,
            "skill": payload.skill,
        }
    elif payload.agentic:
        # Multi-Step Tool-Calling Agent Loop with strictly sandboxed tools
        agent_res = await agent_orchestrator.run(
            message=payload.message,
            session_history=[],
            provider=payload.model_provider or session_obj.model_provider,
            model_name=payload.model_name or session_obj.model_name,
            skill=payload.skill,
        )
        cleaned_content = agent_res.content
        citation_records = agent_res.citations
        extracted_artifacts = agent_res.artifacts
        evidence_status_val = agent_res.evidence_status

        # Grounding guarantee: If no citations gathered via tool call and evidence is sufficient, execute hybrid retrieval
        if not citation_records and evidence_status_val != "insufficient":
            retrieval_res = await asyncio.to_thread(ingestion_manager.retriever.search, payload.message, top_k=4)
            if retrieval_res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND:
                for p in retrieval_res.passages:
                    citation_records.append({
                        "guest": p.guest,
                        "speaker": p.speaker,
                        "episode_title": p.episode_title,
                        "episode_slug": p.episode_slug,
                        "timestamp_url": p.timestamp_url,
                        "start_timestamp": p.start_timestamp,
                        "score": p.score,
                    })
            else:
                evidence_status_val = "insufficient"

        meta_payload = {
            "evidence_status": evidence_status_val,
            "model_provider": agent_res.provider,
            "model_name": agent_res.model_name,
            "agentic": True,
            "tool_calls_trace": agent_res.tool_calls_trace,
            "notice": agent_res.notice,
            "skill": payload.skill,
        }
    else:
        # Direct Grounded Hybrid RAG Turn
        retrieval_res = await asyncio.to_thread(ingestion_manager.retriever.search, payload.message, top_k=4)
        evidence_status_val = retrieval_res.evidence_status.value

        citation_records = []
        evidence_blocks = []
        if retrieval_res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND:
            for p in retrieval_res.passages:
                citation_records.append({
                    "guest": p.guest,
                    "speaker": p.speaker,
                    "episode_title": p.episode_title,
                    "episode_slug": p.episode_slug,
                    "timestamp_url": p.timestamp_url,
                    "start_timestamp": p.start_timestamp,
                    "score": p.score,
                })
                evidence_blocks.append(
                    f"--- [Episode: {p.episode_title} | Guest: {p.guest} | Timestamp: {p.start_timestamp}]\n"
                    f"Source URL: {p.timestamp_url}\n"
                    f"{p.text}\n"
                )

        context_str = "\n".join(evidence_blocks) if evidence_blocks else "No relevant transcript passages found."
        use_ship30 = is_ship30_requested(payload.message, payload.skill)
        system_prompt = SHIP_30_SYSTEM_PROMPT if use_ship30 else STANDARD_SYSTEM_PROMPT

        llm_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"### Verifiable Transcript Evidence from Lenny's Podcast:\n{context_str}\n\n"
                    f"### User Question:\n{payload.message}"
                ),
            },
        ]

        try:
            raw_completion = await generate_completion(
                messages=llm_messages,
                provider=payload.model_provider or session_obj.model_provider,
                model_name=payload.model_name or session_obj.model_name,
            )
        except LLMProviderError as err:
            logger.error(f"Inference error: {err}")
            raw_completion = (
                f"⚠️ **Inference Notice**: Could not complete query via {payload.model_provider} ({err}).\n\n"
                f"However, the following verifiable podcast citations were retrieved:\n"
                + "\n".join([f"- **{c['guest']}** ({c['episode_title']}): {c.get('timestamp_url')}" for c in citation_records[:3]])
            )

        cleaned_content, extracted_artifacts = extract_artifacts(raw_completion)
        meta_payload = {
            "evidence_status": evidence_status_val,
            "model_provider": payload.model_provider or session_obj.model_provider,
            "model_name": payload.model_name or session_obj.model_name,
            "agentic": False,
            "skill": "ship30" if use_ship30 else None,
            "candidates_count": retrieval_res.total_candidates,
            "retrieval_latency_ms": retrieval_res.latency_ms,
        }

    # 4. Persist Assistant Message and Artifacts in PostgreSQL
    assistant_msg_id = uuid.uuid4()
    assistant_msg = MessageModel(
        id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=cleaned_content,
        citations=citation_records,
        metadata_payload=meta_payload,
    )
    db.add(assistant_msg)
    await db.flush()

    saved_artifacts: List[ArtifactResponse] = []
    for art in extracted_artifacts:
        art_entity = ArtifactModel(
            session_id=session_id,
            message_id=assistant_msg_id,
            title=art.title,
            artifact_type=art.artifact_type,
            content=art.content,
            version=1,
        )
        db.add(art_entity)
        await db.flush()
        saved_artifacts.append(ArtifactResponse.model_validate(art_entity))

    # Update session timestamp
    session_obj.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return ChatMessageResponse(
        id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=cleaned_content,
        citations=citation_records,
        metadata_payload=assistant_msg.metadata_payload,
        artifacts=saved_artifacts,
        created_at=assistant_msg.created_at,
    )


@router.post(
    "/agent/pi",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Completion via Genuine Pi Coding Agent SDK",
)
async def chat_pi_agent(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """
    Dedicated endpoint executing turns via genuine @earendil-works/pi-coding-agent SDK.
    """
    payload.agent_sdk = "pi"
    return await chat_completion(payload=payload, db=db)

