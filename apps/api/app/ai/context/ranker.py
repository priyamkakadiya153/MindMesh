import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextRanker:
    """
    Context Ranking & Diversity Control Engine for MindMesh AI.
    Ranks retrieved chunks using hybrid semantic, keyword, recency, and source authority metrics,
    filtering out redundant duplicate sections and detecting conflicting organizational claims.
    """
    @classmethod
    def rank_and_deduplicate_chunks(
        cls,
        chunks: List[Dict[str, Any]],
        query: str,
        top_k: int = 8
    ) -> Dict[str, Any]:
        if not chunks:
            return {
                "ranked_chunks": [],
                "conflicts_detected": False,
                "conflict_details": []
            }

        words = [w.lower().strip() for w in query.split() if len(w.strip()) > 3]

        scored_chunks = []
        for idx, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            content_lower = content.lower()

            # 1. Base Semantic / Score
            base_score = chunk.get("score", 0.5)

            # 2. Keyword Match Boost
            match_count = sum(content_lower.count(w) for w in words) if words else 0
            keyword_score = min(0.3, match_count * 0.05)

            # 3. Source Authority Score
            source_type = chunk.get("source_type", "document")
            source_weight = 0.2 if source_type == "decision" else (0.15 if source_type == "document" else 0.1)

            # 4. Final Combined Rank Score
            final_score = base_score + keyword_score + source_weight
            
            scored_chunk = dict(chunk)
            scored_chunk["final_rank_score"] = round(final_score, 4)
            scored_chunks.append(scored_chunk)

        # Sort by final_rank_score descending
        scored_chunks.sort(key=lambda x: x["final_rank_score"], reverse=True)

        # Diversity Control: Deduplicate chunks with identical section_title or overlapping content prefix
        seen_sections = set()
        seen_prefixes = set()
        diverse_chunks = []

        for item in scored_chunks:
            sec = item.get("section_title")
            prefix = item.get("content", "")[:60].lower().strip()

            if sec and sec in seen_sections:
                continue
            if prefix and prefix in seen_prefixes:
                continue

            if sec:
                seen_sections.add(sec)
            if prefix:
                seen_prefixes.add(prefix)

            diverse_chunks.append(item)
            if len(diverse_chunks) >= top_k:
                break

        # If diversity filter removed too many, fallback to top scored
        if len(diverse_chunks) < min(3, len(scored_chunks)):
            diverse_chunks = scored_chunks[:top_k]

        # Detect potential conflicting claims (e.g. differing numbers/dates for same topic)
        conflicts = cls._detect_conflicts(diverse_chunks)

        return {
            "ranked_chunks": diverse_chunks,
            "conflicts_detected": len(conflicts) > 0,
            "conflict_details": conflicts
        }

    @classmethod
    def _detect_conflicts(cls, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifies conflicting numerical or policy statements across distinct documents."""
        conflicts = []
        if len(chunks) < 2:
            return conflicts

        import re
        unit_pattern = re.compile(r"(\d+)\s*([a-zA-Z%]+)", re.IGNORECASE)

        seen_units: Dict[str, Dict[str, Any]] = {}
        for c in chunks:
            content = c.get("content", "")
            matches = unit_pattern.findall(content)
            doc_name = c.get("title", "Document")
            for num, unit in matches:
                u_clean = unit.lower().strip()
                if u_clean in ["minutes", "hours", "days", "percent", "%", "usd"]:
                    if u_clean in seen_units:
                        prev = seen_units[u_clean]
                        if prev["val"] != num and prev["doc"] != doc_name:
                            conflicts.append({
                                "claim": f"{u_clean} ({prev['val']} vs {num})",
                                "source_a": prev["doc"],
                                "source_b": doc_name
                            })
                    else:
                        seen_units[u_clean] = {"val": num, "doc": doc_name}

        return conflicts
