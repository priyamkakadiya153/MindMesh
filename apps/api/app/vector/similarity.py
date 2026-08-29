import math

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def inner_product(v1: list[float], v2: list[float]) -> float:
    """Calculates dot product (inner product) between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))

def euclidean_distance(v1: list[float], v2: list[float]) -> float:
    """Calculates Euclidean distance between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

def rank_results(candidates: list[dict], query_vector: list[float], metric: str = "COSINE") -> list[dict]:
    """Scores and ranks candidate search hits by a similarity metric."""
    metric = metric.upper()
    ranked = []
    
    for cand in candidates:
        v = cand.get("embedding")
        if not v:
            continue
        
        if metric == "COSINE":
            score = cosine_similarity(query_vector, v)
        elif metric == "INNER_PRODUCT":
            score = inner_product(query_vector, v)
        elif metric == "EUCLIDEAN":
            score = euclidean_distance(query_vector, v)
        else:
            score = cosine_similarity(query_vector, v)
            
        cand_copy = dict(cand)
        cand_copy["score"] = score
        ranked.append(cand_copy)
        
    # Sort candidates
    if metric == "EUCLIDEAN":
        # For Euclidean distance, lower is more similar
        ranked.sort(key=lambda x: x["score"])
    else:
        # Cosine and Inner Product: higher is more similar
        ranked.sort(key=lambda x: x["score"], reverse=True)
        
    return ranked

def normalize_scores(candidates: list[dict], metric: str = "COSINE") -> list[dict]:
    """Normalizes scores to a range of 0.0 to 1.0."""
    if not candidates:
        return []
        
    metric = metric.upper()
    normalized = []
    
    scores = [c["score"] for c in candidates if "score" in c]
    if not scores:
        return candidates
        
    min_score = min(scores)
    max_score = max(scores)
    range_score = max_score - min_score
    
    for cand in candidates:
        cand_copy = dict(cand)
        score = cand_copy.get("score", 0.0)
        
        if metric == "COSINE":
            # Cosine similarity is already between -1 and 1. Normalize to 0 to 1
            cand_copy["normalized_score"] = (score + 1.0) / 2.0
        elif metric == "EUCLIDEAN":
            # Map distance to similarity: 1 / (1 + distance)
            cand_copy["normalized_score"] = 1.0 / (1.0 + score)
        else:
            # Min-Max normalization fallback
            if range_score == 0.0:
                cand_copy["normalized_score"] = 1.0
            else:
                cand_copy["normalized_score"] = (score - min_score) / range_score
                
        normalized.append(cand_copy)
        
    return normalized
