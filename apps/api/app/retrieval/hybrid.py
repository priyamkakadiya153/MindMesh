import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .bm25 import search_bm25
from .vector import retrieve_vectors
from .fusion import reciprocal_rank_fusion
from .reranker import rerank_candidates
from .scorer import compute_combined_score
from ..documents.models import Document, DocumentMetadata
from ..workspace.models import Workspace
from ..projects.models import Project

logger = logging.getLogger(__name__)

async def retrieve_hybrid(
    db: AsyncSession,
    query_text: str,
    limit: int = 10,
    metric: str = "COSINE",
    filters: dict = None
) -> list[dict]:
    """Coordinates BM25 and Vector search, fuses them via RRF, reranks, and scores final results."""
    # 1. Lexical retrieval
    lexical_hits = await search_bm25(db, query_text, limit=50, filters=filters)
    
    # 2. Vector retrieval
    vector_hits = await retrieve_vectors(db, query_text, limit=50, metric=metric, filters=filters)
    
    # 3. Reciprocal Rank Fusion (RRF)
    fused = reciprocal_rank_fusion(lexical_hits, vector_hits, limit=50)
    
    # 4. Rerank top candidates
    reranked = rerank_candidates(fused, query_text, limit=limit)


    
    # 5. Enrich with Document/Workspace/Project names & apply combined scoring
    final_results = []
    
    for item in reranked:
        doc_id = item["document_id"]
        
        # Load Document, Workspace, Project, and Metadata details
        stmt = select(Document).where(Document.id == doc_id)
        doc = (await db.execute(stmt)).scalar_one_or_none()
        
        if not doc:
            continue
            
        # Get Workspace and Project names
        stmt_ws = select(Workspace.name).where(Workspace.id == doc.workspace_id)
        ws_name = (await db.execute(stmt_ws)).scalar() or "Unknown Workspace"
        
        stmt_proj = select(Project.name).where(Project.id == doc.project_id)
        proj_name = (await db.execute(stmt_proj)).scalar() or "Unknown Project"
        
        # Get tags from document metadata if exists
        stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == doc.id)
        doc_meta = (await db.execute(stmt_meta)).scalar_one_or_none()
        
        tags = []
        if doc_meta and doc_meta.keywords:
            # Assuming keywords contain tags list
            tags = doc_meta.keywords.get("tags", []) if isinstance(doc_meta.keywords, dict) else []
            if not tags and isinstance(doc_meta.keywords, list):
                tags = doc_meta.keywords
                
        # Perform Combined Scoring with freshness decay
        # For popularity clicks, we can default to 0 (or look up if clicked log exists)
        clicks = 0
        final_score = compute_combined_score(
            base_score=item["score"],
            created_at=doc.created_at,
            popularity_clicks=clicks
        )
        
        # Determine snippet content and page
        snippet = item["content"]
        page = item["metadata"].get("page", 1)
        
        final_results.append({
            "document_id": str(doc.id),
            "title": doc.filename,
            "score": round(final_score, 4),
            "snippet": snippet,
            "page": page,
            "workspace": ws_name,
            "project": proj_name,
            "tags": tags,
            "matched_chunks": [
                {
                    "chunk_id": str(item["chunk_id"]),
                    "content": snippet,
                    "page": page
                }
            ]
        })
        
    # Sort final list by score descending
    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:limit]
