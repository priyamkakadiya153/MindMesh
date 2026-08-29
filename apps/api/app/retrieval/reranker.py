import logging

logger = logging.getLogger(__name__)

def rerank_candidates(
    candidates: list[dict],
    query_text: str,
    limit: int = 10
) -> list[dict]:
    """Re-scores and filters top retrieval results candidates using cross-encoder concepts."""
    if not candidates:
        return []
        
    query_terms = set(w.lower() for w in query_text.split() if len(w) > 2)
    if not query_terms:
        # Fallback if query has only short words
        query_terms = set(w.lower() for w in query_text.split() if w.strip())
        
    reranked = []
    # Rerank only the Top 50 candidates
    subset = candidates[:50]
    
    for item in subset:
        content_lower = item["content"].lower()
        
        # Calculate Jaccard similarity/term match coverage ratio
        match_count = sum(1 for term in query_terms if term in content_lower)
        coverage_ratio = match_count / len(query_terms) if query_terms else 0.0
        
        # Dynamic blending of semantic/RRF score and coverage ratio
        base_score = item.get("score", 0.0)
        final_score = (base_score * 0.5) + (coverage_ratio * 0.5)
        
        updated_item = dict(item)
        updated_item["score"] = final_score
        updated_item["rerank_score"] = coverage_ratio
        reranked.append(updated_item)
        
    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked[:limit]
