"""
PostgreSQL integration tests validating connection, schema, session persistence,
message cascades, and container restart persistence.
"""

import subprocess
import time
import uuid
import pytest
from sqlalchemy import select

from app.db.session import check_database_connection, engine, AsyncSessionLocal
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.artifact import ArtifactModel


@pytest.mark.asyncio
async def test_postgres_connection_health() -> None:
    """Verify live PostgreSQL connectivity through asyncpg."""
    res = await check_database_connection()
    assert res["status"] == "connected"
    assert res["database"] == "postgresql"
    assert "PostgreSQL" in res.get("version", "")
    assert res["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_session_message_artifact_persistence() -> None:
    """Verify full CRUD lifecycle and cascade deletion on PostgreSQL."""
    session_id = uuid.uuid4()
    message_id = uuid.uuid4()
    artifact_id = uuid.uuid4()

    # 1. Insert Session, Message, and Artifact in a transaction
    async with AsyncSessionLocal() as db:
        new_session = SessionModel(
            id=session_id,
            title="Growth Tactics with Lenny",
            model_provider="ollama",
            model_name="llama3.2",
        )
        db.add(new_session)
        await db.flush()

        new_message = MessageModel(
            id=message_id,
            session_id=session_id,
            role="assistant",
            content="Here are the key takeaways on product-led growth.",
            citations=[{
                "guest": "Elena Verna",
                "episode": "The ultimate guide to product-led sales",
                "timestamp_url": "https://www.youtube.com/watch?v=test&t=10s",
            }],
            metadata_payload={"model": "llama3.2", "tokens": 42},
        )
        db.add(new_message)
        await db.flush()

        new_artifact = ArtifactModel(
            id=artifact_id,
            session_id=session_id,
            message_id=message_id,
            title="PLG Checklist",
            artifact_type="markdown",
            content="# PLG Checklist\n- [ ] Viral loop\n- [ ] Self-serve pricing",
            version=1,
        )
        db.add(new_artifact)
        await db.commit()

    # 2. Query and verify persistence
    async with AsyncSessionLocal() as db:
        sess_query = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
        persisted_sess = sess_query.scalar_one_or_none()
        assert persisted_sess is not None
        assert persisted_sess.title == "Growth Tactics with Lenny"

        msg_query = await db.execute(select(MessageModel).where(MessageModel.id == message_id))
        persisted_msg = msg_query.scalar_one_or_none()
        assert persisted_msg is not None
        assert persisted_msg.role == "assistant"
        assert len(persisted_msg.citations) == 1
        assert persisted_msg.citations[0]["guest"] == "Elena Verna"
        assert persisted_msg.metadata_payload.get("tokens") == 42

        art_query = await db.execute(select(ArtifactModel).where(ArtifactModel.id == artifact_id))
        persisted_art = art_query.scalar_one_or_none()
        assert persisted_art is not None
        assert persisted_art.title == "PLG Checklist"

    # 3. Clean up / cascade deletion
    async with AsyncSessionLocal() as db:
        sess_to_del = await db.get(SessionModel, session_id)
        if sess_to_del:
            await db.delete(sess_to_del)
            await db.commit()

        # Verify cascades
        msg_check = await db.execute(select(MessageModel).where(MessageModel.session_id == session_id))
        assert msg_check.scalar_one_or_none() is None

        art_check = await db.execute(select(ArtifactModel).where(ArtifactModel.session_id == session_id))
        assert art_check.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_database_survives_container_restart() -> None:
    """Verify data persisted in named volume survives container restarts."""
    test_session_id = uuid.uuid4()

    # 1. Write marker session
    async with AsyncSessionLocal() as db:
        marker = SessionModel(
            id=test_session_id,
            title="Restart Persistence Verification Session",
            model_provider="ollama",
            model_name="llama3.2",
        )
        db.add(marker)
        await db.commit()

    # 2. Restart container via docker command
    docker_exe = r"C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
    subprocess.run([docker_exe, "restart", "lenny_postgres"], check=True, capture_output=True)

    # 3. Wait for PostgreSQL to become healthy again
    healthy = False
    for _ in range(30):
        time.sleep(1)
        res = subprocess.run(
            [docker_exe, "inspect", "--format={{json .State.Health.Status}}", "lenny_postgres"],
            capture_output=True,
            text=True,
        )
        if '"healthy"' in res.stdout:
            healthy = True
            break

    assert healthy, "PostgreSQL container failed to become healthy after restart"

    # 4. Dispose engine connections and verify marker session is still intact
    await engine.dispose()
    async with AsyncSessionLocal() as db:
        recovered = await db.get(SessionModel, test_session_id)
        assert recovered is not None
        assert recovered.title == "Restart Persistence Verification Session"

        # Cleanup test marker
        await db.delete(recovered)
        await db.commit()
