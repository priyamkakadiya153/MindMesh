class SearchRankWeights:
    """Configurable weights for blending different retrieval channels."""
    SEMANTIC_WEIGHT: float = 0.5
    BM25_WEIGHT: float = 0.5
    RERANK_LIMIT: int = 50
    DEFAULT_LIMIT: int = 10
