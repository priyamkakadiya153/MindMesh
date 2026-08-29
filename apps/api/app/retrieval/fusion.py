def reciprocal_rank_fusion(
    lexical_results: list[dict],
    vector_results: list[dict],
    k: int = 60,
    limit: int = 50
) -> list[dict]:
    """Combines lexical and vector search lists using Reciprocal Rank Fusion (RRF)."""
    rrf_scores = {}
    metadata_lookup = {}
    
    # Apply RRF to lexical keyword hits
    for rank, item in enumerate(lexical_results):
        chunk_id = item["chunk_id"]
        score = 1.0 / (k + (rank + 1))
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score
        metadata_lookup[chunk_id] = item
        
    # Apply RRF to vector semantic hits
    for rank, item in enumerate(vector_results):
        chunk_id = item["chunk_id"]
        score = 1.0 / (k + (rank + 1))
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score
        metadata_lookup[chunk_id] = item
        
    # Assemble and sort final ranks list
    fused = []
    for chunk_id, score in rrf_scores.items():
        merged_item = dict(metadata_lookup[chunk_id])
        merged_item["score"] = score
        fused.append(merged_item)
        
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused[:limit]
