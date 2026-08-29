from ..core.database import engine, AsyncSessionLocal
from ..models.base import BaseEntity
import app.models  # Ensure all SQLAlchemy models are registered in metadata
from sqlalchemy import text

async def verify_connection():
    # 1. Verify database connectivity
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))

    # 2. Schema synchronization & self-healing for obsolete tables
    async with engine.begin() as conn:
        # Create all tables defined in metadata if missing
        await conn.run_sync(BaseEntity.metadata.create_all)

        # Self-healing check: if otp_codes table exists but lacks user_id column, drop and recreate it
        try:
            await conn.execute(text("""
                DO $$ 
                BEGIN 
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name='otp_codes'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='otp_codes' AND column_name='user_id'
                    ) THEN
                        DROP TABLE otp_codes CASCADE;
                    END IF;
                END $$;
            """))
            # Re-run create_all to generate fresh otp_codes table
            await conn.run_sync(BaseEntity.metadata.create_all)
        except Exception as e:
            # Fallback for non-PostgreSQL dialects (e.g. SQLite in unit tests)
            pass
