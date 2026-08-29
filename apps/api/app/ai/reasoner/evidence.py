import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EvidenceRanker:
    """Ranks, deduplicates, and structures evidence across documents, direct

    messages, decision memories, tasks, timeline events, and graph triples for

    the MindMesh Reasoner.

    """

    @classmethod
    def assemble_and_rank(
        cls,
        retrieved_chunks: List[Dict[str, Any]],
        timeline_events: List[Dict[str, Any]],
        graph_context: Dict[str, Any],
        intent_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        seen_texts = set()
        deduped_chunks = []

        # 1. Deduplicate Chunks
        for c in retrieved_chunks:
            text_snippet = c.get("content", "").strip().lower()[:100]
            if text_snippet and text_snippet not in seen_texts:
                seen_texts.add(text_snippet)
                deduped_chunks.append(c)

        # 2. Prioritize Direct Source Evidence & Explicit Decisions
        primary_intent = intent_info.get("primary_intent", "FACT_LOOKUP")

        def score_item(item: Dict[str, Any]) -> float:
            base = float(item.get("score", 0.5))
            stype = item.get("source_type", "").lower()
            if primary_intent == "DECISION_LOOKUP" and "decision" in stype:
                base += 0.3
            elif primary_intent == "TASK_LOOKUP" and "task" in stype:
                base += 0.3
            elif primary_intent == "DOCUMENT_LOOKUP" and "document" in stype:
                base += 0.2
            elif primary_intent == "WHO_QUERY" and ("message" in stype or "user" in stype):
                base += 0.25
            return base

        deduped_chunks.sort(key=score_item, reverse=True)

        return {
            "chunks": deduped_chunks[:8],
            "timeline_events": timeline_events[:8],
            "graph_relationships": graph_context.get("relationships", [])[:15],
            "graph_entities": graph_context.get("entities", [])[:10],
            "total_evidence_items": len(deduped_chunks) + len(timeline_events) + len(graph_context.get("relationships", []))
        }
