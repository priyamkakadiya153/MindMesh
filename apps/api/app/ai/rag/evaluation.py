from typing import List, Dict, Any

class RAGEvaluator:
    @staticmethod
    def evaluate_groundedness(answer: str, chunks: List[Dict[str, Any]], query: Optional[str] = None) -> Dict[str, Any]:
        """Calculates a heuristic groundedness/faithfulness score between 0.0 and 1.0."""
        if not chunks:
            return {"score": 0.0, "reason": "No context provided to ground response"}
        if not answer:
            return {"score": 0.0, "reason": "Empty AI response"}

        # Heuristics based on matching key vocabulary words in sentences
        # Count overlapping keywords between answer and chunk contents
        answer_words = set(w.strip(".,;:!?()[]\"'").lower() for w in answer.split() if len(w.strip(".,;:!?()[]\"'")) > 3)
        if not answer_words:
            return {"score": 0.5, "reason": "Response text too brief to analyze overlaps"}

        chunk_words = set()
        for c in chunks:
            chunk_content = c.get("content", "")
            for w in chunk_content.split():
                clean_w = w.strip(".,;:!?()[]\"'").lower()
                if len(clean_w) > 3:
                    chunk_words.add(clean_w)

        overlap = answer_words.intersection(chunk_words)
        answer_ratio = len(overlap) / len(answer_words) if answer_words else 0.0
        chunk_ratio = len(overlap) / len(chunk_words) if chunk_words else 0.0
        ratio = max(answer_ratio, chunk_ratio)
        
        score = round(min(ratio * 1.0, 1.0), 2)

        # Target relevance check: If query asks specific entities ("mongodb", "approved", "budget") absent in chunks
        if query:
            q_lower = query.lower()
            chunk_all_text = " ".join(c.get("content", "").lower() for c in chunks)
            
            q_words = [w.strip(".,;:!?()[]\"'").lower() for w in query.split() if len(w.strip(".,;:!?()[]\"'")) >= 5]
            stop_words = {"decide", "decision", "decided", "agree", "agreed", "agreement", "team", "would", "about", "could", "should", "what", "which", "where", "there", "their", "created", "action", "item", "policy", "strategy", "specify", "specified", "specifies", "describe", "describes", "contain", "contains", "explain", "explains", "mention", "mentioned"}
            q_entities = [w for w in q_words if w not in stop_words]

            for ent in q_entities:
                if ent not in chunk_all_text:
                    score = 0.1
                    break

            if "approved" in q_lower or "who approved" in q_lower:
                if not any(w in chunk_all_text for w in ["approved", "approval", "signed", "author", "owner", "by"]):
                    score = 0.1

            if "budget" in q_lower or "cost" in q_lower:
                if not any(w in chunk_all_text for w in ["budget", "cost", "$", "usd", "price"]):
                    score = 0.1

            if "migration strategy" in q_lower or "database migration" in q_lower:
                if not any(w in chunk_all_text for w in ["migration", "postgres", "mongo", "database"]):
                    score = 0.1

        return {
            "score": score,
            "overlapping_keywords": list(overlap)[:10],
            "reason": f"Response matches {len(overlap)} critical context keywords" if score > 0.7 else "Low keyword overlap with source text"
        }
