import time
import math
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from app.ai.embeddings.providers import EmbeddingProviderFactory
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.documents.models import Document

logger = logging.getLogger(__name__)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return (dot / (norm1 * norm2)) if (norm1 > 0 and norm2 > 0) else 0.0

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def vector_search(
        self,
        query_text: str,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        provider_name: str = "gemini",
        top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """Performs vector similarity search against document_embeddings."""
        provider = EmbeddingProviderFactory.get_provider(provider_name)
        query_vec = await provider.embed_query(query_text)

        stmt = select(DocumentEmbedding, DocumentChunk, Document).join(
            DocumentChunk, DocumentEmbedding.chunk_id == DocumentChunk.id
        ).join(
            Document, DocumentEmbedding.document_id == Document.id
        ).where(
            DocumentEmbedding.organization_id == organization_id,
            Document.deleted_at.is_(None),
            DocumentChunk.deleted_at.is_(None)
        )

        if workspace_id:
            stmt = stmt.where(DocumentEmbedding.workspace_id == workspace_id)

        res = await self.db.execute(stmt)
        rows = res.all()

        candidates = []
        for emb_obj, chunk_obj, doc_obj in rows:
            sim = cosine_similarity(query_vec, emb_obj.embedding)
            if sim > 0.0:
                candidates.append({
                    "chunk_id": chunk_obj.id,
                    "document_id": doc_obj.id,
                    "title": doc_obj.title or doc_obj.original_filename or "Untitled Document",
                    "section_title": chunk_obj.section_title,
                    "page_number": chunk_obj.page_number,
                    "content": chunk_obj.content,
                    "token_count": chunk_obj.token_count,
                    "created_at": doc_obj.created_at,
                    "file_type": doc_obj.extension,
                    "vector_score": round(sim, 4),
                    "match_type": "vector"
                })

        candidates.sort(key=lambda x: x["vector_score"], reverse=True)
        return candidates[:top_n]

    async def keyword_search(
        self,
        query_text: str,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """Performs PostgreSQL keyword & text search across content and titles."""
        words = [w.strip() for w in query_text.split() if len(w.strip()) > 2]
        if not words:
            words = [query_text.strip()]

        conditions = []
        for word in words:
            pattern = f"%{word}%"
            conditions.append(DocumentChunk.content.ilike(pattern))
            conditions.append(DocumentChunk.section_title.ilike(pattern))
            conditions.append(Document.title.ilike(pattern))
            conditions.append(Document.original_filename.ilike(pattern))

        stmt = select(DocumentChunk, Document).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.organization_id == organization_id,
            Document.deleted_at.is_(None),
            DocumentChunk.deleted_at.is_(None),
            or_(*conditions)
        )

        if workspace_id:
            stmt = stmt.where(DocumentChunk.workspace_id == workspace_id)

        res = await self.db.execute(stmt)
        rows = res.all()

        candidates = []
        q_lower = query_text.lower()

        for chunk_obj, doc_obj in rows:
            # Simple keyword frequency & title match scoring
            content_lower = chunk_obj.content.lower()
            section_lower = (chunk_obj.section_title or "").lower()
            title_lower = (doc_obj.title or doc_obj.original_filename or "").lower()

            match_count = sum(content_lower.count(w.lower()) for w in words)
            title_match = sum(1 for w in words if w.lower() in title_lower or w.lower() in section_lower)

            kw_score = min(1.0, (match_count * 0.15) + (title_match * 0.35) + (0.2 if q_lower in content_lower else 0.0))

            candidates.append({
                "chunk_id": chunk_obj.id,
                "document_id": doc_obj.id,
                "title": doc_obj.title or doc_obj.original_filename or "Untitled Document",
                "section_title": chunk_obj.section_title,
                "page_number": chunk_obj.page_number,
                "content": chunk_obj.content,
                "token_count": chunk_obj.token_count,
                "created_at": doc_obj.created_at,
                "file_type": doc_obj.extension,
                "keyword_score": round(kw_score, 4),
                "match_type": "keyword"
            })

        candidates.sort(key=lambda x: x["keyword_score"], reverse=True)
        return candidates[:top_n]

    async def hybrid_search(
        self,
        query_text: str,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        top_k: int = 10,
        provider_name: str = "gemini",
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Combines Vector and Keyword search results using Reciprocal Rank Fusion (RRF)."""
        start_time = time.time()

        # Run vector search and keyword search
        vec_results = await self.vector_search(query_text, organization_id, workspace_id, provider_name, top_n=50)
        kw_results = await self.keyword_search(query_text, organization_id, workspace_id, top_n=50)

        # Build rank dictionaries for Reciprocal Rank Fusion (RRF)
        vec_ranks = {item["chunk_id"]: idx + 1 for idx, item in enumerate(vec_results)}
        kw_ranks = {item["chunk_id"]: idx + 1 for idx, item in enumerate(kw_results)}

        # Merge candidate records by chunk_id
        chunk_map: Dict[UUID, Dict[str, Any]] = {}

        for item in vec_results:
            chunk_map[item["chunk_id"]] = item.copy()

        for item in kw_results:
            cid = item["chunk_id"]
            if cid in chunk_map:
                chunk_map[cid]["keyword_score"] = item["keyword_score"]
                chunk_map[cid]["match_type"] = "hybrid"
            else:
                chunk_map[cid] = item.copy()
                chunk_map[cid]["vector_score"] = 0.0

        # Calculate combined Reciprocal Rank Fusion (RRF) score
        rrf_constant = 60
        q_lower = query_text.lower()
        now = datetime.utcnow()

        scored_list = []
        for cid, item in chunk_map.items():
            vec_rank = vec_ranks.get(cid)
            kw_rank = kw_ranks.get(cid)

            rrf_vec = (0.6 / (rrf_constant + vec_rank)) if vec_rank else 0.0
            rrf_kw = (0.4 / (rrf_constant + kw_rank)) if kw_rank else 0.0

            hybrid_score = rrf_vec + rrf_kw

            # Metadata Title/Heading boost
            section_str = (item.get("section_title") or "").lower()
            title_str = (item.get("title") or "").lower()
            if any(word in title_str or word in section_str for word in q_lower.split() if len(word) > 3):
                hybrid_score += 0.005

            # Filter by file_type if specified
            if file_type and item.get("file_type") != file_type:
                continue

            # Convert raw RRF into normalized 0-1 percentage score
            norm_score = min(0.99, round(hybrid_score * 70, 4))
            item["score"] = norm_score
            scored_list.append(item)

        scored_list.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = scored_list[:top_k]

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query_text,
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "top_k": top_k,
            "latency_ms": elapsed_ms,
            "total_candidates_found": len(scored_list),
            "chunks": top_chunks
        }
