import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def rebuild_pgvector_index(
    db: AsyncSession,
    index_name: str,
    index_type: str = "HNSW",
    similarity_metric: str = "COSINE",
    dimensions: int = 1536
) -> bool:
    """Builds or rebuilds a pgvector ANN index on the database."""
    dialect_name = db.bind.dialect.name if db.bind else "sqlite"
    if dialect_name != "postgresql":
        logger.warning(f"Database dialect '{dialect_name}' is not postgresql. Skipping index creation (mock success).")
        return True
        
    index_type = index_type.upper()
    metric = similarity_metric.upper()
    
    # Resolve operator classes
    if metric == "COSINE":
        op_class = "vector_cosine_ops"
    elif metric == "INNER_PRODUCT":
        op_class = "vector_ip_ops"
    elif metric == "EUCLIDEAN":
        op_class = "vector_l2_ops"
    else:
        op_class = "vector_cosine_ops"
        
    # Drop existing index first if any
    try:
        await db.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to drop old index {index_name}: {e}. Retrying...")
        
    # Build CREATE INDEX statement
    # Note: If embedding is JSON/JSONB, we must cast it to vector inside a functional index
    # (e.g. ((embedding::text)::vector) or similar) or if already vector type.
    # To be extremely safe, we cast the JSON data to a float array and then to vector:
    # OR we try standard casting if the column contains JSON.
    # Here is a generic functional index expression:
    # "CAST(embedding AS vector)" - wait, Postgres doesn't allow standard casting in functional indexes directly without parenthesis:
    # "((embedding::text)::vector)"
    
    target_expression = f"((embedding::text)::vector({dimensions}))"
    
    if index_type == "HNSW":
        sql = f"CREATE INDEX {index_name} ON document_embeddings USING hnsw ({target_expression} {op_class})"
    elif index_type == "IVFFLAT":
        # Calculate lists dynamically or set a default
        lists = 100
        sql = f"CREATE INDEX {index_name} ON document_embeddings USING ivfflat ({target_expression} {op_class}) WITH (lists = {lists})"
    else:
        # FLAT (no index / skip)
        logger.info(f"Skipping index creation for FLAT type index {index_name}")
        return True
        
    try:
        logger.info(f"Executing: {sql}")
        await db.execute(text(sql))
        await db.commit()
        logger.info(f"Successfully created pgvector ANN index: {index_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to build pgvector ANN index {index_name}: {e}")
        # Try fallback without casting, in case the database column has already been modified to a raw vector type
        try:
            sql_fallback = ""
            if index_type == "HNSW":
                sql_fallback = f"CREATE INDEX {index_name} ON document_embeddings USING hnsw (embedding {op_class})"
            elif index_type == "IVFFLAT":
                sql_fallback = f"CREATE INDEX {index_name} ON document_embeddings USING ivfflat (embedding {op_class}) WITH (lists = 100)"
            
            if sql_fallback:
                logger.info(f"Retrying fallback without cast: {sql_fallback}")
                await db.execute(text(sql_fallback))
                await db.commit()
                logger.info(f"Successfully created pgvector index using fallback: {index_name}")
                return True
        except Exception as e2:
            logger.error(f"Fallback index creation failed: {e2}")
            
        return False
