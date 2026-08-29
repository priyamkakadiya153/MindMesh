import re
import logging
from typing import Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

class MindMeshQueryProcessor:
    """
    Lightweight Query Understanding and Intent Processor for MindMesh AI.
    Analyzes raw user prompts to detect intent, scope, target entities, and whether vector retrieval is required,
    avoiding unnecessary LLM calls for trivial or casual messages.
    """
    CASUAL_PATTERNS = [
        re.compile(r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b", re.IGNORECASE),
        re.compile(r"^(thanks|thank you|cool|great|awesome|ok|okay)\b", re.IGNORECASE)
    ]

    DECISION_PATTERNS = [
        re.compile(r"\b(decision|decided|agreed|choice|chosen|resolution)\b", re.IGNORECASE)
    ]

    SUMMARY_PATTERNS = [
        re.compile(r"\b(summarize|summary|overview|tl;dr|recap|synopsis)\b", re.IGNORECASE)
    ]

    TASK_PATTERNS = [
        re.compile(r"\b(task|todo|action item|assignee|deadline|due date)\b", re.IGNORECASE)
    ]

    PROJECT_PATTERNS = [
        re.compile(r"\b(project|roadmap|milestone|sprint|epic)\b", re.IGNORECASE)
    ]

    @classmethod
    def process_query(
        self,
        query: str,
        workspace_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        clean_query = query.strip()
        
        # 1. Check for Casual/Greeting Intent
        for pattern in self.CASUAL_PATTERNS:
            if pattern.search(clean_query) and len(clean_query.split()) <= 4:
                return {
                    "query": clean_query,
                    "intent": "CASUAL",
                    "requires_retrieval": False,
                    "scope": "NONE",
                    "target_sources": []
                }

        # 2. Document Summary Intent
        if document_id or any(p.search(clean_query) for p in self.SUMMARY_PATTERNS):
            return {
                "query": clean_query,
                "intent": "DOCUMENT_SUMMARY",
                "requires_retrieval": True,
                "scope": "SELECTED_DOCUMENT" if document_id else "WORKSPACE",
                "target_sources": ["document"]
            }

        # 3. Decision Lookup Intent
        if any(p.search(clean_query) for p in self.DECISION_PATTERNS):
            return {
                "query": clean_query,
                "intent": "DECISION_LOOKUP",
                "requires_retrieval": True,
                "scope": "WORKSPACE",
                "target_sources": ["document", "conversation", "task"]
            }

        # 4. Task Lookup Intent
        if any(p.search(clean_query) for p in self.TASK_PATTERNS):
            return {
                "query": clean_query,
                "intent": "TASK_LOOKUP",
                "requires_retrieval": True,
                "scope": "WORKSPACE",
                "target_sources": ["task", "conversation"]
            }

        # 5. Project Status Intent
        if any(p.search(clean_query) for p in self.PROJECT_PATTERNS):
            return {
                "query": clean_query,
                "intent": "PROJECT_STATUS",
                "requires_retrieval": True,
                "scope": "WORKSPACE",
                "target_sources": ["project", "document"]
            }

        # 6. Default Workspace Fact Lookup
        return {
            "query": clean_query,
            "intent": "FACT_LOOKUP",
            "requires_retrieval": True,
            "scope": "WORKSPACE",
            "target_sources": ["document", "conversation", "task", "project"]
        }
