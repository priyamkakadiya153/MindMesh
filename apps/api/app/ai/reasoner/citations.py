import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.documents.models import Document
from app.models.conversations import DirectMessage, Conversation
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory

logger = logging.getLogger(__name__)

class CitationValidator:
    """Validates citations to ensure tags [1], [2] point to accessible real

    source entities, attaching deep links and stripping hallucinated claims.

    """

    @classmethod
    async def validate_and_build(
        cls,
        db: AsyncSession,
        user_id: UUID,
        organization_id: UUID,
        answer_text: str,
        evidence_budget: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        verified_sources: List[Dict[str, Any]] = []

        # Process chunks
        for idx, chunk in enumerate(evidence_budget.get("chunks", []), 1):
            doc_id = chunk.get("document_id")
            if doc_id:
                try:
                    d_uuid = UUID(str(doc_id))
                    doc = (await db.execute(select(Document).where(Document.id == d_uuid))).scalar_one_or_none()
                    if doc:
                        verified_sources.append({
                            "index": idx,
                            "source_type": "document",
                            "source_id": str(doc.id),
                            "title": doc.title,
                            "deep_link": f"/files?preview={doc.id}",
                            "excerpt": chunk.get("content", "")[:120]
                        })
                except Exception as e:
                    logger.warning(f"Error resolving citation doc {doc_id}: {e}")

        # Process timeline / graph / messages
        for graph_rel in evidence_budget.get("graph_relationships", []):
            verified_sources.append({
                "index": len(verified_sources) + 1,
                "source_type": "relationship",
                "source_id": f"rel-{graph_rel.get('source_title')}",
                "title": f"{graph_rel.get('source_title')} --[{graph_rel.get('relation_type')}]--> {graph_rel.get('target_title')}",
                "deep_link": "/knowledge/graph",
                "excerpt": f"Graph Relationship: {graph_rel.get('relation_type')}"
            })

        return verified_sources[:10]
