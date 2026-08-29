import time
import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ...similarity import rank_results, normalize_scores

logger = logging.getLogger(__name__)

async def search_pgvector(
    db: AsyncSession,
    query_vector: list[float],
    limit: int = 5,
    metric: str = "COSINE",
    filters: dict = None
) -> list[dict]:
    """Performs similarity search using pgvector native queries with SQLite fallback."""
    start_time = time.time()
    dialect_name = db.bind.dialect.name if db.bind else "sqlite"
    metric = metric.upper()
    
    # 1. SQLite Fallback (In-memory search)
    if dialect_name != "postgresql":
        logger.info("Non-Postgres database detected. Using in-memory cosine similarity fallback.")
        # Load all active chunks and embeddings
        # Filters are applied in SQL to limit memory footprint
        sql_base = """
            SELECT c.id, c.document_id, c.content, c.metadata_json, e.embedding
            FROM document_chunks c
            JOIN document_embeddings e ON c.id = e.chunk_id
            WHERE c.is_active = :is_active
        """
        params = {"is_active": True}
        
        # Apply organizational and project isolation filters
        if filters:
            for key, val in filters.items():
                if key == "tag":
                    sql_base += " AND json_extract(c.metadata_json, '$.tags') LIKE :tag_like"
                    params["tag_like"] = f'%"{val}"%'
                else:
                    sql_base += f" AND json_extract(c.metadata_json, '$.{key}') = :{key}"
                    params[key] = str(val)

                
        res = await db.execute(text(sql_base), params)
        rows = res.all()
        
        candidates = []
        for r in rows:
            import json
            # Handle JSON loading if raw string is returned
            emb_val = r[4]
            if isinstance(emb_val, str):
                emb_val = json.loads(emb_val)
            meta_val = r[3]
            if isinstance(meta_val, str):
                meta_val = json.loads(meta_val)
                
            candidates.append({
                "chunk_id": UUID(r[0]) if isinstance(r[0], str) else r[0],
                "document_id": UUID(r[1]) if isinstance(r[1], str) else r[1],
                "content": r[2],
                "metadata": meta_val,
                "embedding": emb_val
            })

            
        ranked = rank_results(candidates, query_vector, metric)
        normalized = normalize_scores(ranked, metric)
        return normalized[:limit]

    # 2. Native PostgreSQL + pgvector Search
    # Map metric to postgres distance operator
    # Note: <#> in pgvector returns negative inner product, so to sort correctly we order by distance ASC.
    if metric == "COSINE":
        op = "<=>" # Cosine distance
    elif metric == "INNER_PRODUCT":
        op = "<#>" # Negated inner product
    elif metric == "EUCLIDEAN":
        op = "<->" # L2 distance
    else:
        op = "<=>"
        
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"
    
    sql_pg = f"""
        SELECT c.id, c.document_id, c.content, c.metadata_json, e.embedding,
               ((e.embedding::text)::vector) {op} :query_vector::vector as distance
        FROM document_chunks c
        JOIN document_embeddings e ON c.id = e.chunk_id
        WHERE c.is_active = true
    """
    
    params = {"query_vector": vector_str}
    
    # Enforce multi-tenant filters
    if filters:
        for key, val in filters.items():
            if key == "tag":
                sql_pg += " AND c.metadata_json->'tags' ? :tag"
                params["tag"] = str(val)
            else:
                sql_pg += f" AND c.metadata_json->>'{key}' = :{key}"
                params[key] = str(val)

            
    sql_pg += f" ORDER BY distance ASC LIMIT {limit}"
    
    try:
        res = await db.execute(text(sql_pg), params)
        rows = res.all()
        
        candidates = []
        for r in rows:
            import json
            emb_val = r[4]
            if isinstance(emb_val, str):
                emb_val = json.loads(emb_val)
            meta_val = r[3]
            if isinstance(meta_val, str):
                meta_val = json.loads(meta_val)
                
            distance = float(r[5])
            
            # Map distance back to score
            if metric == "COSINE":
                score = 1.0 - distance
            elif metric == "INNER_PRODUCT":
                score = -distance
            else: # EUCLIDEAN
                score = distance
                
            candidates.append({
                "chunk_id": r[0],
                "document_id": r[1],
                "content": r[2],
                "metadata": meta_val,
                "embedding": emb_val,
                "score": score
            })
            
        # Rerank is not needed as it's sorted by DB, but normalize scores
        normalized = normalize_scores(candidates, metric)
        return normalized
        
    except Exception as e:
        logger.exception(f"Native pgvector search failed: {e}. Falling back to in-memory processing.")
        # Fallback to python calculation in case pgvector extension error
        # (e.g. pgvector not loaded on DB or cast error)
        sql_fallback = """
            SELECT c.id, c.document_id, c.content, c.metadata_json, e.embedding
            FROM document_chunks c
            JOIN document_embeddings e ON c.id = e.chunk_id
            WHERE c.is_active = true
        """
        params_fb = {}
        if filters:
            for key, val in filters.items():
                sql_fallback += f" AND c.metadata_json->>'{key}' = :{key}"
                params_fb[key] = str(val)
                
        res = await db.execute(text(sql_fallback), params_fb)
        rows = res.all()
        
        candidates = []
        for r in rows:
            import json
            emb_val = r[4]
            if isinstance(emb_val, str):
                emb_val = json.loads(emb_val)
            meta_val = r[3]
            if isinstance(meta_val, str):
                meta_val = json.loads(meta_val)
                
            candidates.append({
                "chunk_id": r[0],
                "document_id": r[1],
                "content": r[2],
                "metadata": meta_val,
                "embedding": emb_val
            })
            
        ranked = rank_results(candidates, query_vector, metric)
        normalized = normalize_scores(ranked, metric)
        return normalized[:limit]
