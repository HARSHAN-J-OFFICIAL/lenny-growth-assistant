"""
Asynchronous database engine and session management using SQLAlchemy and asyncpg.
"""

import logging
import time
from typing import Any, AsyncGenerator, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.pool import NullPool
from app.core.config import settings

logger = logging.getLogger("lenny.database")

# Build async engine with NullPool to guarantee clean event loop isolation
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    poolclass=NullPool,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing a transactional async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> Dict[str, Any]:
    """
    Execute a probe query to verify active PostgreSQL connectivity and latency.
    """
    start_time = time.perf_counter()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version_str = result.scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "connected",
                "database": "postgresql",
                "version": version_str,
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Database health check failed: {exc}")
        return {
            "status": "disconnected",
            "database": "postgresql",
            "error": str(exc),
            "latency_ms": latency_ms,
        }
