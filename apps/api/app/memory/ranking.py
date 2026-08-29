import logging
from typing import List
from datetime import datetime
from app.memory.models import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryRanker:
    @staticmethod
    def rank_memories(memories: List[LongTermMemory]) -> List[LongTermMemory]:
        """Ranks memories using a combined score of importance, confidence, and access recency."""
        now = datetime.utcnow()
        scored_memories = []

        for m in memories:
            # Recency calculation: exponential decay over hours since last access
            delta = now - m.last_accessed_at
            hours_elapsed = delta.total_seconds() / 3600.0
            # Decay factor of 0.95 per hour
            recency = (0.95 ** hours_elapsed)

            importance = m.importance_score
            confidence = m.confidence_score

            # Combined Score Formula
            score = (importance * 0.4) + (confidence * 0.4) + (recency * 0.2)
            scored_memories.append((score, m))

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_memories]
