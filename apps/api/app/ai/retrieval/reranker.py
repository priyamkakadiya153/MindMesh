from typing import List, Dict, Any
from app.ai.retrieval.models import EvidenceItem, RetrievalPlan

class RetrievalReranker:
    """
    Multi-source Deduplicator & Reranker.
    Fuses evidence candidates from semantic, keyword, structured, and conversation sources.
    Calculates unified score:
    FinalScore = 0.40 * Score + 0.30 * AuthorityScore + 0.20 * RecencyScore + 0.10 * EntityMatch.
    """

    @classmethod
    def rerank(
        cls,
        candidates: List[EvidenceItem],
        plan: RetrievalPlan,
        intent_entities: List[str]
    ) -> List[EvidenceItem]:
        if not candidates:
            return []

        # 1. Deduplicate by source_id or content hash
        deduped_map: Dict[str, EvidenceItem] = {}

        for item in candidates:
            key = f"{item.source_type.value}:{item.source_id}"
            if key in deduped_map:
                existing = deduped_map[key]
                # Combine methods
                for m in item.retrieval_methods:
                    if m not in existing.retrieval_methods:
                        existing.retrieval_methods.append(m)
                # Take highest base score
                existing.score = max(existing.score, item.score)
            else:
                deduped_map[key] = item

        deduped = list(deduped_map.values())

        # 2. Rescore and Rank
        for item in deduped:
            content_lower = item.content.lower()
            entity_match_score = 0.0
            for ent in intent_entities:
                if ent.lower() in content_lower:
                    entity_match_score += 0.5
            entity_match_score = min(1.0, entity_match_score)

            final_score = (
                (0.40 * item.score) +
                (0.30 * item.authority_score) +
                (0.20 * item.recency_score) +
                (0.10 * entity_match_score)
            )

            item.score = round(min(1.0, final_score), 4)

        # 3. Sort descending by score
        deduped.sort(key=lambda x: x.score, reverse=True)
        return deduped[:plan.max_results]
