import re
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import ConversationMemory
from app.models.search import SearchIndex
from app.ai.knowledge.models import KnowledgeItem

logger = logging.getLogger(__name__)

class ConversationIntelligenceProcessor:
    """
    Asynchronous Conversation Intelligence Engine for MindMesh.
    Analyzes conversation turns, extracts structured Decisions, Tasks, Action Items, Facts,
    and Questions, and indexes them into vector storage with strict RBAC source traceability.
    """
    NOISE_PATTERNS = [
        re.compile(r"^(hi|hello|hey|greetings|ok|okay|cool|thanks|thank you|yes|no|great|awesome)\b", re.IGNORECASE),
        re.compile(r"^[\s\W\d]*$", re.IGNORECASE)  # Emojis or whitespace only
    ]

    DECISION_PATTERNS = [
        re.compile(r"(?:we|team)\s+(?:decided|agreed)\s+(?:to|that)\s+(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"decision:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"agreed\s+upon:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"production\s+database\s+is\s+(.*?)(?:\.|\n|$)", re.IGNORECASE)
    ]

    TASK_PATTERNS = [
        re.compile(r"(.*?)\s+(?:will|shall|must|should|needs to|is to)\s+(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"action\s+item:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE),
        re.compile(r"todo:\s*(.*?)(?:\.|\n|$)", re.IGNORECASE)
    ]

    FACT_PATTERNS = [
        re.compile(r"(?:production|server|api|service|database)\s+(?:uses|runs|requires|is)\s+(.*?)(?:\.|\n|$)", re.IGNORECASE)
    ]

    @classmethod
    def is_noise(cls, text: str) -> bool:
        clean = text.strip()
        if len(clean) < 3:
            return True
        for p in cls.NOISE_PATTERNS:
            if p.search(clean) and len(clean.split()) <= 3:
                return True
        return False

    @classmethod
    async def process_conversation_messages(
        cls,
        db: AsyncSession,
        chat_id: UUID,
        organization_id: UUID,
        workspace_id: UUID,
        messages: List[Dict[str, Any]],
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Extracts structured intelligence (Decisions, Tasks, Facts) from a conversation message window.
        Stores extracted items into ConversationMemory and SearchIndex.
        """
        extracted_insights = []
        
        # 1. Filter out chat noise
        meaningful_messages = [m for m in messages if not cls.is_noise(m.get("content", ""))]

        if not meaningful_messages:
            return {"status": "SKIPPED_NOISE", "extracted_count": 0}

        # 2. Scan message turns for Decisions, Tasks, and Facts
        for msg in meaningful_messages:
            content = msg.get("content", "").strip()
            sender = msg.get("sender_name", msg.get("sender_id", "Unknown"))
            msg_id = str(msg.get("id", ""))
            ts = msg.get("timestamp", datetime.utcnow().isoformat())

            # Check Decisions
            for p in cls.DECISION_PATTERNS:
                matches = p.findall(content)
                for m in matches:
                    d_text = m.strip() if isinstance(m, str) else m[0].strip()
                    if len(d_text) > 4:
                        extracted_insights.append({
                            "type": "DECISION",
                            "content": f"Decision: {d_text}",
                            "source_message_ids": [msg_id],
                            "sender": sender,
                            "timestamp": ts
                        })

            # Check Tasks
            for p in cls.TASK_PATTERNS:
                matches = p.findall(content)
                for m in matches:
                    if isinstance(m, tuple):
                        assignee = m[0].strip()
                        action = m[1].strip()
                    else:
                        assignee = sender
                        action = m.strip()

                    if len(action) > 4:
                        extracted_insights.append({
                            "type": "TASK",
                            "content": f"Task ({assignee}): {action}",
                            "assignee": assignee,
                            "action": action,
                            "source_message_ids": [msg_id],
                            "sender": sender,
                            "timestamp": ts
                        })

            # Check Facts
            for p in cls.FACT_PATTERNS:
                matches = p.findall(content)
                for m in matches:
                    f_text = m.strip() if isinstance(m, str) else m[0].strip()
                    if len(f_text) > 4:
                        extracted_insights.append({
                            "type": "IMPORTANT_FACT",
                            "content": f"Fact: {content}",
                            "source_message_ids": [msg_id],
                            "sender": sender,
                            "timestamp": ts
                        })

        # 3. Persist and Index Extracted Insights
        saved_count = 0
        for insight in extracted_insights:
            # Check idempotency / deduplication
            stmt = select(ConversationMemory).where(
                ConversationMemory.conversation_id == chat_id,
                ConversationMemory.memory_type == insight["type"],
                ConversationMemory.content == insight["content"]
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if not existing:
                memory = ConversationMemory(
                    conversation_id=chat_id,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    memory_type=insight["type"],
                    importance=4 if insight["type"] == "DECISION" else 3,
                    content=insight["content"],
                    metadata_json={
                        "source_message_ids": insight.get("source_message_ids", []),
                        "sender": insight.get("sender"),
                        "timestamp": insight.get("timestamp"),
                        "assignee": insight.get("assignee")
                    }
                )
                db.add(memory)
                await db.flush()

                # Add to SearchIndex for semantic retrieval
                si = SearchIndex(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    entity_type=insight["type"].lower(),
                    entity_id=memory.id,
                    title=f"{insight['type'].title()} from Conversation",
                    content=insight["content"]
                )
                db.add(si)
                saved_count += 1

        await db.commit()

        return {
            "status": "PROCESSED",
            "extracted_count": saved_count,
            "insights": extracted_insights
        }
