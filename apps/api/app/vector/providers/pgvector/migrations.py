import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def verify_pgvector_extension(db: AsyncSession) -> bool:
    """Checks if pgvector extension is active or can be enabled in Postgres."""
    try:
        # Verify active database dialect is PostgreSQL
        dialect_name = db.bind.dialect.name if db.bind else "sqlite"
        if dialect_name != "postgresql":
            logger.warning(f"Active database dialect is '{dialect_name}', not postgresql. Skipping pgvector check.")
            return False
            
        # Verify pgvector extension
        res = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        if res.scalar():
            return True
            
        # Try enabling the extension
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to verify or enable pgvector extension: {e}")
        return False
