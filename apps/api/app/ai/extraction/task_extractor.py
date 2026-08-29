import re
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class TaskExtractor:
    """
    Automated task extraction engine.
    Extracts action items, assignees, and task descriptions from conversations and document context.
    """
    TASK_PATTERNS = [
        re.compile(r"([A-Z][a-z]+)\s+will\s+(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"todo:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"action\s+item:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"task:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE)
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def extract_tasks_from_text(self, text: str, source_type: str = "conversation") -> List[Dict[str, Any]]:
        """Scans raw text snippet for task assignments and action items."""
        if not text:
            return []

        tasks = []
        for pattern in self.TASK_PATTERNS:
            matches = pattern.findall(text)
            for m in matches:
                if isinstance(m, tuple):
                    assignee = m[0].strip()
                    action = m[1].strip()
                else:
                    assignee = None
                    action = m.strip()

                if action and len(action) > 4:
                    tasks.append({
                        "task": action,
                        "assignee": assignee,
                        "status": "pending",
                        "source_type": source_type,
                        "timestamp": datetime.utcnow().isoformat()
                    })

        return tasks
