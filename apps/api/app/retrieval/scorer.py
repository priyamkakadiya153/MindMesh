import math
from datetime import datetime
from typing import Optional

def calculate_freshness_decay(created_at: Optional[datetime], decay_factor: float = 0.005) -> float:
    """Calculates freshness score using exponential decay based on document age in days."""
    if not created_at:
        return 0.5
    now = datetime.utcnow()
    # Ensure timezone-naive comparison
    dt = created_at.replace(tzinfo=None) if created_at.tzinfo else created_at
    age_days = (now - dt).days
    age_days = max(0, age_days)
    return math.exp(-age_days * decay_factor)

def calculate_popularity_boost(clicks: int) -> float:
    """Calculates logarithmic boost based on document click counts."""
    return 1.0 + math.log1p(max(0, clicks))

def compute_combined_score(
    base_score: float,
    created_at: Optional[datetime] = None,
    popularity_clicks: int = 0,
    metadata_boost: float = 0.0
) -> float:
    """Combines baseline rank scores, freshness decay, click popularity boosts and metadata boosts."""
    freshness = calculate_freshness_decay(created_at)
    popularity = calculate_popularity_boost(popularity_clicks)
    
    # Combined rank score
    return (base_score * freshness * popularity) + metadata_boost
