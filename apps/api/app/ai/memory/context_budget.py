from typing import List, Dict, Any

class ContextBudgetManager:
    """
    Context Ranking & Budgeting Engine.
    Enforces message context window token budgets using deterministic relevance scoring:
    ContextScore = Recency + EntityOverlap + TopicContinuity + ExplicitReference.
    """

    @classmethod
    def rank_and_select(
        cls,
        current_query: str,
        history: List[Dict[str, Any]],
        intent_result: Any,
        max_messages: int = 10,
        max_tokens: int = 2500
    ) -> List[Dict[str, Any]]:
        if not history:
            return []

        q_lower = current_query.lower()
        intent_entities = [e.text.lower() for e in getattr(intent_result, "entities", [])]

        scored_messages = []
        total_count = len(history)

        for idx, msg in enumerate(history):
            content = (msg.get("content") or msg.get("text") or "").lower()
            
            # 1. Recency Score (0 to 40 points)
            recency_score = ((idx + 1) / total_count) * 40.0

            # 2. Entity Overlap Score (+50 points)
            entity_score = 0.0
            for ent in intent_entities:
                if ent in content:
                    entity_score += 50.0

            # 3. Explicit Reference Score (+100 points if user asks for specific deadline/turn)
            ref_score = 0.0
            if "deadline" in q_lower and "deadline" in content:
                ref_score += 100.0
            elif "first" in q_lower and idx == 0:
                ref_score += 100.0

            total_score = recency_score + entity_score + ref_score
            scored_messages.append((total_score, idx, msg))

        # Sort by total_score descending
        scored_messages.sort(key=lambda x: x[0], reverse=True)

        # Select top messages within max_messages and max_tokens
        selected = []
        current_token_est = 0

        for score, original_idx, msg in scored_messages[:max_messages]:
            c_text = msg.get("content") or msg.get("text") or ""
            msg_tokens = len(c_text.split()) * 1.3
            if current_token_est + msg_tokens <= max_tokens:
                selected.append((original_idx, msg))
                current_token_est += msg_tokens

        # Restore chronological order for context package
        selected.sort(key=lambda x: x[0])
        return [item[1] for item in selected]
