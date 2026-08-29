import time
import math
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from app.ai.embeddings.providers import EmbeddingProviderFactory
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.documents.models import Document
from app.models.message import Message
from app.models.conversations import Conversation, DirectMessage
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.organization_member import OrganizationMember
from app.workspace.models import WorkspaceMember

logger = logging.getLogger(__name__)

class MultiDomainRetriever:
    """
    Multi-domain knowledge retrieval engine for MindMesh AI.
    Searches across Documents, Direct Messages, Group Chats, Projects, Tasks, and Decisions,
    enforcing strict workspace and organization security boundary checks.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_user_access(self, user_id: UUID, organization_id: UUID, workspace_id: Optional[UUID] = None) -> bool:
        """Enforces multi-tenant authorization security boundaries."""
        # 1. Organization Membership Check
        org_stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
        org_res = await self.db.execute(org_stmt)
        if not org_res.scalar_one_or_none():
            logger.warning(f"User {user_id} unauthorized for Organization {organization_id}")
            return False

        # 2. Workspace Membership Check (if workspace_id provided)
        if workspace_id:
            ws_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id
            )
            ws_res = await self.db.execute(ws_stmt)
            if not ws_res.scalar_one_or_none():
                logger.warning(f"User {user_id} unauthorized for Workspace {workspace_id}")
                return False

        return True

    async def search_all_domains(
        self,
        user_id: UUID,
        organization_id: UUID,
        query_text: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Queries all organizational knowledge sources in parallel/sequence and ranks results by hybrid relevance.
        """
        # Security Boundary Check
        has_access = await self.verify_user_access(user_id, organization_id, workspace_id)
        if not has_access:
            return []

        results: List[Dict[str, Any]] = []

        # 1. Search Documents
        doc_chunks = await self._search_documents(organization_id, workspace_id, query_text, limit=limit)
        results.extend(doc_chunks)

        # 2. Search Direct & Group Chat Messages
        chat_msgs = await self._search_messages(organization_id, workspace_id, query_text, limit=limit)
        results.extend(chat_msgs)

        # 3. Search Projects & Tasks
        project_items = await self._search_projects_and_tasks(organization_id, workspace_id, project_id, query_text, limit=limit)
        results.extend(project_items)

        # Sort all candidates by combined relevance score
        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results[:limit]

    STOP_WORDS = {
        "what", "are", "the", "main", "this", "that", "with", "from", "for", "about",
        "and", "in", "is", "it", "to", "of", "a", "an", "on", "how", "all", "our", "my",
        "was", "were", "will", "can", "could", "should", "would", "tell", "show", "give"
    }

    @classmethod
    def _extract_query_words(cls, query_text: str) -> List[str]:
        import re
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", query_text.lower())
        meaningful = [t for t in tokens if len(t) > 2 and t not in cls.STOP_WORDS]
        base_words = meaningful or [t for t in tokens if len(t) > 2] or [query_text.strip().lower()]

        expanded = []
        for w in base_words:
            expanded.append(w)
            if w.endswith("ural") and len(w) > 6:
                expanded.append(w[:-4])
            elif w.endswith("ure") and len(w) > 5:
                expanded.append(w[:-3])
            elif w.endswith("ions") and len(w) > 5:
                expanded.append(w[:-4])
            elif w.endswith("ion") and len(w) > 4:
                expanded.append(w[:-3])
            elif w.endswith("ies") and len(w) > 4:
                expanded.append(w[:-3])
            elif w.endswith("ize") and len(w) > 4:
                expanded.append(w[:-3])
            elif w.endswith("ise") and len(w) > 4:
                expanded.append(w[:-3])
            elif w.endswith("ing") and len(w) > 4:
                expanded.append(w[:-3])
            elif w.endswith("ed") and len(w) > 4:
                expanded.append(w[:-2])
            elif w.endswith("s") and len(w) > 3:
                expanded.append(w[:-1])

        seen = set()
        final_words = []
        for w in expanded:
            if len(w) >= 3 and w not in seen and w not in cls.STOP_WORDS:
                seen.add(w)
                final_words.append(w)
        return final_words

    async def _search_documents(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        words = self._extract_query_words(query_text)
        if not words:
            return []

        conditions = []
        for word in words:
            pattern = f"%{word}%"
            conditions.append(DocumentChunk.content.ilike(pattern))
            conditions.append(DocumentChunk.section_title.ilike(pattern))
            conditions.append(Document.title.ilike(pattern))

        stmt = select(DocumentChunk, Document).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.organization_id == organization_id,
            Document.deleted_at.is_(None),
            DocumentChunk.deleted_at.is_(None),
            or_(*conditions)
        )
        if workspace_id:
            stmt = stmt.where(DocumentChunk.workspace_id == workspace_id)

        stmt = stmt.limit(limit * 2)
        res = await self.db.execute(stmt)
        rows = res.all()

        hits = []
        for chunk_obj, doc_obj in rows:
            content_lower = chunk_obj.content.lower()
            doc_title_lower = (doc_obj.title or "").lower()
            match_count = sum(content_lower.count(w.lower()) + doc_title_lower.count(w.lower()) for w in words)
            if match_count > 0:
                score = min(0.95, 0.4 + (match_count * 0.1))

                hits.append({
                    "source_type": "document",
                    "document_id": doc_obj.id,
                    "chunk_id": chunk_obj.id,
                    "title": doc_obj.title or doc_obj.original_filename or "Document",
                    "section_title": chunk_obj.section_title,
                    "page": chunk_obj.page_number,
                    "content": chunk_obj.content,
                    "score": round(score, 4),
                    "created_at": doc_obj.created_at
                })

        # Also search FileIntelligence table for extracted facts, decisions, and summaries
        from app.documents.models import FileIntelligence
        intel_conds = []
        for word in words:
            pattern = f"%{word}%"
            intel_conds.append(FileIntelligence.summary.ilike(pattern))

        intel_stmt = select(FileIntelligence, Document).join(
            Document, FileIntelligence.document_id == Document.id
        ).where(
            FileIntelligence.organization_id == organization_id,
            Document.deleted_at.is_(None),
            or_(*intel_conds) if intel_conds else True
        )
        if workspace_id:
            intel_stmt = intel_stmt.where(FileIntelligence.workspace_id == workspace_id)

        intel_rows = (await self.db.execute(intel_stmt)).all()
        for intel_obj, doc_obj in intel_rows:
            summary_lower = (intel_obj.summary or "").lower()
            facts_str = " ".join([f.get("fact", "") for f in (intel_obj.facts or [])])
            decisions_str = " ".join([d.get("decision", "") for d in (intel_obj.decisions or [])])
            combined_intel_text = f"{summary_lower} {facts_str.lower()} {decisions_str.lower()}"

            match_count = sum(combined_intel_text.count(w.lower()) for w in words)
            if match_count > 0:
                score = min(0.95, 0.5 + (match_count * 0.1))
                content_text = intel_obj.summary or facts_str or decisions_str
                hits.append({
                    "source_type": "document",
                    "document_id": doc_obj.id,
                    "chunk_id": doc_obj.id,
                    "title": doc_obj.title or doc_obj.original_filename or "Document",
                    "section_title": f"File Intelligence ({intel_obj.document_type})",
                    "page": 1,
                    "content": content_text,
                    "score": round(score, 4),
                    "created_at": doc_obj.created_at
                })

        return hits

    async def _search_messages(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        words = self._extract_query_words(query_text)
        if not words:
            return []

        hits = []
        clean_q = query_text.strip().lower()
        
        # 1. Search Direct & Group Chat Messages (conversations table + direct_messages table)
        dm_conditions = [DirectMessage.content.ilike(f"%{w}%") for w in words]
        dm_stmt = select(DirectMessage, Conversation).join(
            Conversation, DirectMessage.conversation_id == Conversation.id
        ).where(
            DirectMessage.organization_id == organization_id,
            DirectMessage.deleted.is_(False),
            Conversation.deleted_at.is_(None),
            or_(*dm_conditions)
        )
        if workspace_id:
            dm_stmt = dm_stmt.where(
                or_(DirectMessage.workspace_id == workspace_id, Conversation.workspace_id == workspace_id)
            )

        dm_stmt = dm_stmt.order_by(desc(DirectMessage.created_at)).limit(limit * 2)
        dm_res = await self.db.execute(dm_stmt)
        for dm_obj, conv_obj in dm_res.all():
            if (dm_obj.content or "").strip().lower() == clean_q:
                continue
            msg_lower = (dm_obj.content or "").lower()
            match_count = sum(msg_lower.count(w.lower()) for w in words)
            if match_count > 0:
                score = min(0.95, 0.5 + (match_count * 0.1))
                hits.append({
                    "source_type": "conversation",
                    "document_id": conv_obj.id,
                    "chunk_id": dm_obj.id,
                    "title": f"Discussion: {conv_obj.name or 'Project Discussion'}",
                    "section_title": f"Message ({dm_obj.message_type})",
                    "page": 1,
                    "content": dm_obj.content,
                    "score": round(score, 4),
                    "created_at": dm_obj.created_at
                })

        return hits

    async def _search_projects_and_tasks(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        project_id: Optional[UUID],
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        words = self._extract_query_words(query_text)
        if not words:
            return []

        hits = []
        
        # 1. Search Tasks (title & description)
        task_conds = []
        for w in words:
            task_conds.append(Task.description.ilike(f"%{w}%"))
            task_conds.append(Task.title.ilike(f"%{w}%"))

        task_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None),
            or_(*task_conds)
        )
        if workspace_id:
            task_stmt = task_stmt.where(Task.workspace_id == workspace_id)
        if project_id:
            task_stmt = task_stmt.where(Task.project_id == project_id)

        task_res = await self.db.execute(task_stmt.limit(limit))
        tasks = task_res.scalars().all()

        for t in tasks:
            task_name = getattr(t, "title", None) or t.description[:40]
            hits.append({
                "source_type": "task",
                "document_id": t.id,
                "chunk_id": t.id,
                "title": f"Task: {task_name}",
                "section_title": f"Status: {t.status}",
                "page": 1,
                "content": f"Task: {task_name}\nDescription: {t.description}\nStatus: {t.status}",
                "score": 0.85,
                "created_at": t.created_at
            })

        # 2. Search Projects
        proj_conds = []
        for w in words:
            proj_conds.append(Project.name.ilike(f"%{w}%"))
            proj_conds.append(Project.description.ilike(f"%{w}%"))

        proj_stmt = select(Project).where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),
            or_(*proj_conds)
        )
        if workspace_id:
            proj_stmt = proj_stmt.where(Project.workspace_id == workspace_id)

        proj_res = await self.db.execute(proj_stmt.limit(limit))
        for p in proj_res.scalars().all():
            hits.append({
                "source_type": "project",
                "document_id": p.id,
                "chunk_id": p.id,
                "title": f"Project: {p.name}",
                "section_title": f"Project ({p.status})",
                "page": 1,
                "content": f"Project: {p.name}\nDescription: {p.description or ''}\nStatus: {p.status}",
                "score": 0.80,
                "created_at": p.created_at
            })

        # 3. Search ConversationMemory Insights & Decisions
        mem_hits = await self._search_conversation_memories(organization_id, workspace_id, query_text, limit=limit)
        hits.extend(mem_hits)

        return hits

    async def _search_conversation_memories(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        words = self._extract_query_words(query_text)
        if not words:
            return []

        from app.models.conversation import ConversationMemory
        mem_conds = [ConversationMemory.content.ilike(f"%{w}%") for w in words]
        stmt = select(ConversationMemory).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.deleted_at.is_(None),
            or_(*mem_conds)
        )
        if workspace_id:
            stmt = stmt.where(ConversationMemory.workspace_id == workspace_id)

        res = await self.db.execute(stmt.limit(limit))
        memories = res.scalars().all()

        hits = []
        for m in memories:
            hits.append({
                "source_type": "decision" if m.memory_type == "DECISION" else "conversation",
                "document_id": m.conversation_id or m.chat_id,
                "chunk_id": m.id,
                "title": f"Extracted {m.memory_type.title()} from Discussion",
                "section_title": f"Memory Type: {m.memory_type}",
                "page": 1,
                "content": m.content,
                "score": 0.90 if m.memory_type == "DECISION" else 0.82,
                "created_at": m.created_at
            })

        return hits
