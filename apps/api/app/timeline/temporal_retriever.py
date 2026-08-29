import re
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .service import TimelineService
from ..models.user import User

logger = logging.getLogger(__name__)

class TimelineRetriever:
    """Retrieves timeline events and temporal context for MindMesh AI

    Orchestrator, providing chronological grounding for temporal user queries

    (e.g., 'What was our JWT expiry in July?' vs 'What is the current JWT

    expiry?').

    """

    TEMPORAL_KEYWORDS = [
        "july", "august", "september", "october", "november", "december",
        "january", "february", "march", "april", "may", "june",
        "month", "year", "week", "today", "yesterday", "before", "after",
        "history", "historical", "evolve", "evolved", "changed", "change",
        "timeline", "when", "previously", "former", "initial", "first",
        "current", "currently", "latest", "now", "present", "recent", "status"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = TimelineService(db)

    def detect_temporal_intent(self, query_text: str) -> Dict[str, Any]:
        if not query_text:
            return {"has_temporal_intent": False, "target_month": None, "target_year": None}

        q_lower = query_text.lower()
        has_intent = any(kw in q_lower for kw in self.TEMPORAL_KEYWORDS)

        target_month = None
        months = [
            ("january", 1), ("february", 2), ("march", 3), ("april", 4),
            ("may", 5), ("june", 6), ("july", 7), ("august", 8),
            ("september", 9), ("october", 10), ("november", 11), ("december", 12)
        ]
        for m_name, m_num in months:
            if m_name in q_lower:
                target_month = m_num
                break

        year_match = re.search(r'\b(202\d)\b', q_lower)
        target_year = int(year_match.group(1)) if year_match else None

        return {
            "has_temporal_intent": has_intent,
            "target_month": target_month,
            "target_year": target_year,
            "query_lower": q_lower
        }

    async def get_temporal_context(
        self,
        user: User,
        organization_id: UUID,
        query_text: str,
        workspace_id: Optional[UUID] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        intent = self.detect_temporal_intent(query_text)

        date_from = None
        date_to = None

        if intent["target_month"]:
            yr = intent["target_year"] or datetime.utcnow().year
            m = intent["target_month"]
            date_from = datetime(yr, m, 1, 0, 0, 0)
            if m == 12:
                date_to = datetime(yr + 1, 1, 1, 0, 0, 0)
            else:
                date_to = datetime(yr, m + 1, 1, 0, 0, 0)

        # Extract primary topic keyword using QueryProcessor STOP_WORDS
        from ..search.query_processor import QueryProcessor
        stop_words = QueryProcessor.STOP_WORDS
        tokens = [t.strip(".,;:!?()").lower() for t in query_text.split() if len(t.strip(".,;:!?()")) >= 2]
        meaningful_tokens = [t for t in tokens if t not in stop_words and t not in self.TEMPORAL_KEYWORDS]
        
        search_kw = meaningful_tokens[0] if meaningful_tokens else None

        timeline_data = await self.service.get_timeline_events(
            user=user,
            organization_id=organization_id,
            workspace_id=workspace_id,
            search_query=search_kw,
            date_from=date_from,
            date_to=date_to,
            limit=top_k
        )

        return timeline_data.get("events", [])
