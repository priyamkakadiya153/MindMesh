import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def get_pgvector_stats(db: AsyncSession) -> dict:
    """Collects Postgres/pgvector system stats (index sizes, active indices, counts)."""
    stats = {
        "provider": "pgvector",
        "vector_count": 0,
        "index_count": 0,
        "index_size_bytes": 0,
        "additional_info": {}
    }
    try:
        dialect_name = db.bind.dialect.name if db.bind else "sqlite"
        if dialect_name != "postgresql":
            return stats
            
        # 1. Count total vectors in table
        res_count = await db.execute(text("SELECT COUNT(*) FROM document_embeddings"))
        stats["vector_count"] = res_count.scalar() or 0
        
        # 2. Count active ANN indexes
        res_index = await db.execute(text("""
            SELECT count(*)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_am am ON am.oid = c.relam
            WHERE c.relkind = 'i' AND am.amname IN ('hnsw', 'ivfflat')
        """))
        stats["index_count"] = res_index.scalar() or 0
        
        # 3. Calculate index size on disk
        res_size = await db.execute(text("""
            SELECT pg_relation_size(c.oid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_am am ON am.oid = c.relam
            WHERE c.relkind = 'i' AND am.amname IN ('hnsw', 'ivfflat')
        """))
        stats["index_size_bytes"] = sum(row[0] for row in res_size.all())
        
    except Exception as e:
        logger.error(f"Failed to query pgvector statistics: {e}")
        
    return stats
