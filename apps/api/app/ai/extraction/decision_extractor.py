import re
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class DecisionExtractor:
    """
    Automated decision extraction engine.
    Parses conversational text and documents for explicit decisions and converts them into structured entities.
    """
    DECISION_PATTERNS = [
        re.compile(r"we\s+decided\s+to\s+(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"decision:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"agreed\s+upon:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"it\s+was\s+decided\s+that\s+(.*?)(?:\.|\n|$)", re.IGNORECASE)
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def extract_decisions_from_text(self, text: str, source_type: str = "conversation") -> List[Dict[str, Any]]:
        """Scans raw text snippet for explicit decision patterns."""
        if not text:
            return []

        decisions = []
        for pattern in self.DECISION_PATTERNS:
            matches = pattern.findall(text)
            for m in matches:
                clean_decision = m.strip()
                if clean_decision and len(clean_decision) > 5:
                    decisions.append({
                        "decision": clean_decision,
                        "context": text[:150],
                        "source_type": source_type,
                        "timestamp": datetime.utcnow().isoformat()
                    })

        return decisions
