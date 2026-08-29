from typing import List, Dict, Any
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.models import RetrievalRequest, RetrievalPlan, EvidenceItem, SourceType
from app.ai.retrieval.adapters.base import BaseRetrievalAdapter
from app.models.message import Message
from app.models.conversation import ConversationSummary

class ConversationSearchAdapter(BaseRetrievalAdapter):
    """Retrieves conversation history, messages, and conversation summaries."""

    async def search(self, request: RetrievalRequest, plan: RetrievalPlan) -> List[EvidenceItem]:
        results: List[EvidenceItem] = []
        if SourceType.CONVERSATION not in plan.sources and SourceType.MESSAGE not in plan.sources:
            return results

        queries = plan.queries or [request.original_query]

        # 1. Search Direct & Group Chat Messages
        from app.models.conversations import DirectMessage, Conversation
        dm_stmt = select(DirectMessage, Conversation).join(
            Conversation, DirectMessage.conversation_id == Conversation.id
        ).where(
            DirectMessage.organization_id == request.organization_id,
            DirectMessage.deleted.is_(False),
            Conversation.deleted_at.is_(None)
        ).order_by(desc(DirectMessage.created_at)).limit(20)

        if request.workspace_id:
            dm_stmt = dm_stmt.where(
                or_(DirectMessage.workspace_id == request.workspace_id, Conversation.workspace_id == request.workspace_id)
            )

        dm_res = await self.db.execute(dm_stmt)
        for dm, conv in dm_res.all():
            content = dm.content or ""
            matches = any(q.lower() in content.lower() for q in queries)
            if matches or "yesterday" in request.original_query.lower() or "discuss" in request.original_query.lower():
                results.append(EvidenceItem(
                    source_id=str(dm.id),
                    source_type=SourceType.MESSAGE,
                    title=f"Discussion: {conv.name or 'Team Discussion'}",
                    content=content,
                    score=0.80,
                    authority_score=0.70,
                    recency_score=0.85,
                    location={"conversation_id": str(conv.id), "message_id": str(dm.id)},
                    metadata={"sender_id": str(dm.sender_id) if dm.sender_id else None},
                    retrieval_methods=["conversation_search"]
                ))

        # 2. Search Summaries
        sum_stmt = select(ConversationSummary).where(
            ConversationSummary.organization_id == request.organization_id,
            ConversationSummary.deleted_at.is_(None)
        ).limit(5)

        if request.workspace_id:
            sum_stmt = sum_stmt.where(ConversationSummary.workspace_id == request.workspace_id)

        sum_res = await self.db.execute(sum_stmt)
        summaries = sum_res.scalars().all()

        for s in summaries:
            s_text = s.summary or ""
            results.append(EvidenceItem(
                source_id=str(s.id),
                source_type=SourceType.CONVERSATION,
                title="Conversation Summary",
                content=s_text,
                score=0.75,
                authority_score=0.75,
                recency_score=0.80,
                location={"conversation_id": str(s.conversation_id)},
                metadata={"message_range": [s.message_range_start, s.message_range_end]},
                retrieval_methods=["summary_search"]
            ))

        return results
