import re
from typing import Dict, Any, List, Set

class QueryIntentDetector:
    """Classifies user query intent, extracts entities, and detects temporal

    markers for MindMesh Knowledge Reasoning.

    """

    TEMPORAL_KEYWORDS: List[str] = [
        "today", "yesterday", "this week", "last week", "last month", "recently",
        "before", "after", "since", "until", "july", "august", "september", "october",
        "november", "december", "january", "february", "march", "april", "may", "june",
        "current", "historical", "previously", "former", "evolve", "changed", "history"
    ]

    INTENT_PATTERNS: Dict[str, List[str]] = {
        "WHY_QUERY": [r"\bwhy\b", r"\breason\b", r"\brationale\b", r"\bmotivation\b"],
        "WHO_QUERY": [r"\bwho\b", r"\bauthor\b", r"\bcreated by\b", r"\bagreed\b", r"\bproposed\b"],
        "WHAT_CHANGED": [r"\bwhat changed\b", r"\bhow did\b.*\bevolve\b", r"\bchanges\b", r"\bdifference\b"],
        "TASK_LOOKUP": [r"\btask\b", r"\btasks\b", r"\baction item\b", r"\bresulted from\b", r"\bto do\b"],
        "DECISION_LOOKUP": [r"\bdecide\b", r"\bdecision\b", r"\bdecisions\b", r"\bagreed\b", r"\bchosen\b", r"\bselected\b"],
        "DOCUMENT_LOOKUP": [r"\bdocument\b", r"\bfile\b", r"\bpdf\b", r"\bspecification\b", r"\bsupports\b"],
        "CONVERSATION_LOOKUP": [r"\bconversation\b", r"\bchat\b", r"\bmessage\b", r"\bdiscussed\b", r"\bdiscussion\b"],
        "PROJECT_SUMMARY": [r"\bsummarize\b", r"\boverview\b", r"\bproject\b", r"\bstatus\b"],
        "RELATIONSHIP_QUERY": [r"\brelated to\b", r"\bconnected to\b", r"\brelationship\b"],
        "TIMELINE_QUERY": [r"\bwhen\b", r"\bdate\b", r"\btimeline\b", r"\bchronology\b"]
    }

    @classmethod
    def detect(cls, query: str) -> Dict[str, Any]:
        q_clean = query.strip().lower()

        # 1. Detect Intents
        detected_intents: List[str] = []
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for p in patterns:
                if re.search(p, q_clean):
                    detected_intents.append(intent)
                    break

        primary_intent = detected_intents[0] if detected_intents else "FACT_LOOKUP"

        # 2. Temporal Marker Detection
        found_temporal = [kw for kw in cls.TEMPORAL_KEYWORDS if kw in q_clean]

        # 3. Entity & Keyword Extraction
        words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", q_clean)
        stopwords = {
            "what", "when", "where", "which", "who", "why", "how", "did", "does", "done",
            "were", "was", "are", "is", "the", "that", "this", "from", "with", "about",
            "have", "has", "had", "used", "use", "using", "for", "our", "we", "you", "they"
        }
        entities = [w for w in words if w not in stopwords and w not in found_temporal]

        return {
            "primary_intent": primary_intent,
            "intents": detected_intents or ["FACT_LOOKUP"],
            "temporal_markers": found_temporal,
            "has_temporal": len(found_temporal) > 0,
            "entities": entities[:10],
            "query_text": query
        }
