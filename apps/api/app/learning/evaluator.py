import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoryEvaluator:
    @staticmethod
    def evaluate_quality(key: str, value: Dict[str, Any]) -> float:
        """Determines memory confidence score (0.0 -> 1.0) based on payload structures."""
        if not value:
            return 0.0
        score = 0.5
        # Add score points for richness of metadata
        if len(value.keys()) > 2:
            score += 0.2
        if "history" in value and len(value["history"]) > 0:
            score += 0.2
        if "user_confirmed" in value and value["user_confirmed"] is True:
            score += 0.1
        return min(score, 1.0)
