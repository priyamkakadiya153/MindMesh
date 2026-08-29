import math
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

def calculate_bm25(tf: int, doc_len: int, avg_doc_len: float, df: int, total_docs: int, k1: float = 1.5, b: float = 0.75) -> float:
    """Computes BM25 score for a single term matching a document."""
    # Compute IDF
    idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
    # Compute TF component
    numerator = tf * (k1 + 1.0)
    denominator = tf + k1 * (1.0 - b + b * (doc_len / (avg_doc_len or 1.0)))
    return idf * (numerator / denominator)

async def search_bm25(
    db: AsyncSession,
    query_text: str,
    limit: int = 50,
    filters: dict = None
) -> list[dict]:
    """Performs lexical search using Postgres native FTS, falling back to a python BM25 scorer for SQLite."""
    dialect_name = db.bind.dialect.name if db.bind else "sqlite"
    
    # Clean/normalize query tokens
    query_terms = [t.lower().strip() for t in query_text.split() if t.strip()]
    if not query_terms:
        return []

    # 1. SQLite Fallback (In-memory BM25 index)
    if dialect_name != "postgresql":
        logger.info("SQLite database detected. Running Python-based BM25 lexical ranker.")
        
        # Load candidate document chunks matching filters
        sql = "SELECT id, document_id, content, metadata_json FROM document_chunks WHERE is_active = :is_active"
        params = {"is_active": True}
        
        if filters:
            for key, val in filters.items():
                if key == "tag":
                    sql += " AND json_extract(metadata_json, '$.tags') LIKE :tag_like"
                    params["tag_like"] = f'%"{val}"%'
                else:
                    sql += f" AND json_extract(metadata_json, '$.{key}') = :{key}"
                    params[key] = str(val)

                
        res = await db.execute(text(sql), params)
        rows = res.all()
        if not rows:
            return []
            
        # Build tokenized docs map
        documents = []
        total_len = 0
        
        # Calculate term frequencies and document lengths
        from uuid import UUID
        for r in rows:
            import json
            chunk_id, doc_id, content, meta_raw = r
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
            
            words = [w.lower() for w in content.split() if w.strip()]
            doc_len = len(words)
            total_len += doc_len
            
            documents.append({
                "chunk_id": UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id,
                "document_id": UUID(doc_id) if isinstance(doc_id, str) else doc_id,

                "content": content,
                "metadata": meta,
                "words": words,
                "doc_len": doc_len
            })
            
        total_docs = len(documents)
        avg_doc_len = total_len / total_docs
        
        # Calculate document frequency (DF) for each query term
        df_map = {}
        for term in query_terms:
            df_map[term] = sum(1 for doc in documents if term in doc["words"])
            
        # Score each document chunk
        scored = []
        for doc in documents:
            score = 0.0
            for term in query_terms:
                df = df_map.get(term, 0)
                if df == 0:
                    continue
                tf = doc["words"].count(term)
                if tf > 0:
                    score += calculate_bm25(tf, doc["doc_len"], avg_doc_len, df, total_docs)
                    
            if score > 0.0:
                scored.append({
                    "chunk_id": doc["chunk_id"],
                    "document_id": doc["document_id"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": score
                })
                
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    # 2. Postgres Native Full-Text Search (using tsvector and ts_rank_cd)
    # Join queries with logical AND operator '&'
    ts_query = " & ".join(f"{t}:*" for t in query_terms)
    
    sql_pg = """
        SELECT c.id, c.document_id, c.content, c.metadata_json,
               ts_rank_cd(to_tsvector('english', c.content), to_tsquery('english', :ts_query)) as rank
        FROM document_chunks c
        WHERE c.is_active = true
        AND to_tsvector('english', c.content) @@ to_tsquery('english', :ts_query)
    """
    params_pg = {"ts_query": ts_query}
    
    if filters:
        for key, val in filters.items():
            sql_pg += f" AND c.metadata_json->>'{key}' = :{key}"
            params_pg[key] = str(val)
            
    sql_pg += f" ORDER BY rank DESC LIMIT {limit}"
    
    try:
        res = await db.execute(text(sql_pg), params_pg)
        rows = res.all()
        
        results = []
        for r in rows:
            import json
            meta_raw = r[3]
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
            
            results.append({
                "chunk_id": r[0],
                "document_id": r[1],
                "content": r[2],
                "metadata": meta,
                "score": float(r[4])
            })
        return results
    except Exception as e:
        logger.exception(f"Postgres Full-Text Search failed: {e}. Falling back to basic LIKE query match.")
        
        # Simple LIKE fallback search in case of syntax or configuration issues
        sql_like = """
            SELECT c.id, c.document_id, c.content, c.metadata_json
            FROM document_chunks c
            WHERE c.is_active = true
        """
        params_like = {}
        if filters:
            for key, val in filters.items():
                sql_like += f" AND c.metadata_json->>'{key}' = :{key}"
                params_like[key] = str(val)
                
        res = await db.execute(text(sql_like), params_like)
        all_rows = res.all()
        
        matches = []
        for r in all_rows:
            import json
            chunk_content = r[2].lower()
            matches_count = sum(1 for term in query_terms if term in chunk_content)
            if matches_count > 0:
                meta = json.loads(r[3]) if isinstance(r[3], str) else r[3]
                matches.append({
                    "chunk_id": r[0],
                    "document_id": r[1],
                    "content": r[2],
                    "metadata": meta,
                    "score": float(matches_count)
                })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]
