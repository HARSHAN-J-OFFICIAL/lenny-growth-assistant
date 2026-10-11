"""
Reproducible database migration mechanism and schema version tracking.
Can be executed via CLI: python -m app.db.migrate
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import text

from app.db.session import engine
from app.models import Base

logger = logging.getLogger("lenny.migrate")

MIGRATIONS = [
    {
        "version": "001_initial_schema",
        "description": "Create sessions, messages, and artifacts tables with foreign keys and indexes",
    }
]


async def run_migrations() -> Dict[str, Any]:
    """
    Applies pending schema migrations and records applied versions.
    """
    applied_now: List[str] = []
    already_applied: List[str] = []

    async with engine.begin() as conn:
        # 1. Ensure migration tracking table exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE NOT NULL,
                description TEXT NOT NULL
            );
        """))

        # 2. Query already applied migration versions
        result = await conn.execute(text("SELECT version FROM schema_migrations;"))
        applied_versions = {row[0] for row in result.fetchall()}

        # 3. Apply pending migrations
        for mig in MIGRATIONS:
            v = mig["version"]
            if v in applied_versions:
                already_applied.append(v)
                continue

            logger.info(f"Applying migration: {v} - {mig['description']}...")

            # For 001_initial_schema: generate tables from SQLAlchemy declarative models
            if v == "001_initial_schema":
                await conn.run_sync(Base.metadata.create_all)

            # Record migration application
            await conn.execute(
                text("""
                    INSERT INTO schema_migrations (version, applied_at, description)
                    VALUES (:version, :applied_at, :description);
                """),
                {
                    "version": v,
                    "applied_at": datetime.now(timezone.utc),
                    "description": mig["description"],
                },
            )
            applied_now.append(v)
            logger.info(f"Migration {v} successfully applied.")

    return {
        "status": "success",
        "applied_now": applied_now,
        "already_applied": already_applied,
        "total_migrations": len(MIGRATIONS),
    }


def main() -> None:
    """CLI entrypoint for executing migrations."""
    print("=====================================================")
    print("  Lenny Growth Assistant — Database Migration Runner")
    print("=====================================================")
    result = asyncio.run(run_migrations())
    print(f"Status:          {result['status']}")
    print(f"Applied Now:     {result['applied_now']}")
    print(f"Already Applied: {result['already_applied']}")
    print("=====================================================\n")


if __name__ == "__main__":
    main()
