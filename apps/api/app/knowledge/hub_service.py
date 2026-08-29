import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.documents.models import Document
from app.models.conversations import Conversation, DirectMessage, ConversationMember
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.models.timeline import TimelineEvent
from app.workspace.models import WorkspaceMember
from app.models.organization_member import OrganizationMember

logger = logging.getLogger(__name__)

class KnowledgeHubService:
    """Core aggregation service for the MindMesh Unified Knowledge Hub, providing

    real database counts, normalized knowledge items, project knowledge

    breakdowns, and strict RBAC permission filtering.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hub_overview(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """Returns real database counts, recent normalized knowledge items, and

        activity timeline events for the user's accessible workspace scope.

        """
        # 1. Organization Authorization Check
        org_member_stmt = select(OrganizationMember.id).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id
        )
        if not (await self.db.execute(org_member_stmt)).scalar_one_or_none():
            return {
                "counts": {"documents": 0, "decisions": 0, "tasks": 0, "conversations": 0, "projects": 0},
                "recent_knowledge": [],
                "recent_activity": []
            }

        user_ws_ids = await self._get_user_workspace_ids(user.id)
        if workspace_id and workspace_id not in user_ws_ids:
            user_ws_ids = [workspace_id]

        auth_chat_ids = set(str(cid) for cid in (await self._get_authorized_chat_ids(user.id)))

        # 2. Count Real Entities
        # Documents count
        doc_cnt_stmt = select(func.count(Document.id)).where(
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None)
        )
        if user_ws_ids:
            doc_cnt_stmt = doc_cnt_stmt.where(Document.workspace_id.in_(user_ws_ids))
        doc_count = (await self.db.execute(doc_cnt_stmt)).scalar() or 0

        # Decisions count
        dec_cnt_stmt = select(func.count(ConversationMemory.id)).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        )
        if user_ws_ids:
            dec_cnt_stmt = dec_cnt_stmt.where(ConversationMemory.workspace_id.in_(user_ws_ids))
        dec_count = (await self.db.execute(dec_cnt_stmt)).scalar() or 0

        # Tasks count
        task_cnt_stmt = select(func.count(Task.id)).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None)
        )
        task_count = (await self.db.execute(task_cnt_stmt)).scalar() or 0

        # Conversations count
        valid_chat_uuids = [UUID(cid) for cid in auth_chat_ids if self._is_valid_uuid(cid)]
        conv_cnt_stmt = select(func.count(Conversation.id)).where(
            Conversation.organization_id == organization_id,
            Conversation.deleted_at.is_(None)
        )
        if valid_chat_uuids:
            conv_cnt_stmt = conv_cnt_stmt.where(Conversation.id.in_(valid_chat_uuids))
        conv_count = (await self.db.execute(conv_cnt_stmt)).scalar() or 0

        # Projects count
        proj_cnt_stmt = select(func.count(Project.id)).where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None)
        )
        if user_ws_ids:
            proj_cnt_stmt = proj_cnt_stmt.where(Project.workspace_id.in_(user_ws_ids))
        proj_count = (await self.db.execute(proj_cnt_stmt)).scalar() or 0

        # 3. Fetch Recent Normalized Knowledge Items
        recent_items: List[Dict[str, Any]] = []

        # Decisions
        dec_stmt = select(ConversationMemory).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        ).order_by(ConversationMemory.created_at.desc()).limit(10)
        if user_ws_ids:
            dec_stmt = dec_stmt.where(ConversationMemory.workspace_id.in_(user_ws_ids))
        decs = (await self.db.execute(dec_stmt)).scalars().all()
        for d in decs:
            recent_items.append(self._format_decision_item(d))

        # Tasks
        t_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None)
        ).order_by(Task.created_at.desc()).limit(10)
        tasks = (await self.db.execute(t_stmt)).scalars().all()
        for t in tasks:
            recent_items.append(self._format_task_item(t))

        # Documents
        d_stmt = select(Document).where(
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None)
        ).order_by(Document.created_at.desc()).limit(10)
        if user_ws_ids:
            d_stmt = d_stmt.where(Document.workspace_id.in_(user_ws_ids))
        docs = (await self.db.execute(d_stmt)).scalars().all()
        for doc in docs:
            recent_items.append(self._format_document_item(doc))

        # Sort all items by timestamp
        recent_items.sort(key=lambda x: x["timestamp"], reverse=True)

        # 4. Fetch Timeline Activity
        tl_stmt = select(TimelineEvent).where(
            TimelineEvent.organization_id == organization_id,
            TimelineEvent.deleted_at.is_(None)
        ).order_by(TimelineEvent.occurred_at.desc()).limit(15)
        if user_ws_ids:
            tl_stmt = tl_stmt.where(TimelineEvent.workspace_id.in_(user_ws_ids))
        tl_events = (await self.db.execute(tl_stmt)).scalars().all()

        activity = [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else e.created_at.isoformat(),
                "source_type": e.source_type,
                "source_id": str(e.source_id)
            }
            for e in tl_events
        ]

        return {
            "counts": {
                "documents": doc_count,
                "decisions": dec_count,
                "tasks": task_count,
                "conversations": conv_count,
                "projects": proj_count
            },
            "recent_knowledge": recent_items[:limit],
            "recent_activity": activity
        }

    async def get_project_knowledge_overview(
        self,
        user: User,
        organization_id: UUID,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Returns connected knowledge overview for a specific project."""
        proj = (await self.db.execute(select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None)
        ))).scalar_one_or_none()

        if not proj:
            return {"error": "Project not found or access denied"}

        # Counts for project
        doc_count = (await self.db.execute(select(func.count(Document.id)).where(
            Document.project_id == project_id, Document.deleted_at.is_(None)
        ))).scalar() or 0

        conv_count = (await self.db.execute(select(func.count(Conversation.id)).where(
            Conversation.project_id == project_id, Conversation.deleted_at.is_(None)
        ))).scalar() or 0

        dec_count = (await self.db.execute(select(func.count(ConversationMemory.id)).where(
            ConversationMemory.project_id == project_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        ))).scalar() or 0

        task_count = (await self.db.execute(select(func.count(Task.id)).where(
            Task.project_id == project_id, Task.deleted_at.is_(None)
        ))).scalar() or 0

        tl_count = (await self.db.execute(select(func.count(TimelineEvent.id)).where(
            TimelineEvent.project_id == project_id, TimelineEvent.deleted_at.is_(None)
        ))).scalar() or 0

        # Fetch key decisions
        decs = (await self.db.execute(select(ConversationMemory).where(
            ConversationMemory.project_id == project_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        ).limit(5))).scalars().all()

        # Fetch open tasks
        tasks = (await self.db.execute(select(Task).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        ).limit(5))).scalars().all()

        return {
            "project_id": str(proj.id),
            "name": proj.name,
            "description": proj.description,
            "status": proj.status,
            "counts": {
                "documents": doc_count,
                "conversations": conv_count,
                "decisions": dec_count,
                "tasks": task_count,
                "timeline_events": tl_count
            },
            "key_decisions": [d.content for d in decs],
            "open_tasks": [t.description for t in tasks]
        }

    async def _get_user_workspace_ids(self, user_id: UUID) -> List[UUID]:
        stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        return [r[0] for r in res.all()]

    async def _get_authorized_chat_ids(self, user_id: UUID) -> List[UUID]:
        chat_ids = set()
        stmt1 = select(Chat.id).where(Chat.user_id == user_id, Chat.deleted_at.is_(None))
        res1 = await self.db.execute(stmt1)
        for r in res1.scalars().all():
            chat_ids.add(r)

        stmt2 = select(Conversation.id).where(
            or_(
                Conversation.participant_one == user_id,
                Conversation.participant_two == user_id,
                Conversation.id.in_(
                    select(ConversationMember.conversation_id).where(
                        ConversationMember.user_id == user_id,
                        ConversationMember.deleted_at.is_(None)
                    )
                )
            ),
            Conversation.deleted_at.is_(None)
        )
        res2 = await self.db.execute(stmt2)
        for r in res2.scalars().all():
            chat_ids.add(r)

        return list(chat_ids)

    def _is_valid_uuid(self, val: Any) -> bool:
        try:
            UUID(str(val))
            return True
        except ValueError:
            return False

    def _format_decision_item(self, d: ConversationMemory) -> Dict[str, Any]:
        return {
            "id": str(d.id),
            "type": "DECISION",
            "title": d.content[:80],
            "description": d.content,
            "source_type": "conversation",
            "source_id": str(d.chat_id or d.conversation_id or d.id),
            "timestamp": d.created_at.isoformat() if d.created_at else datetime.utcnow().isoformat(),
            "deep_link": f"/decisions/{d.id}",
            "workspace_id": str(d.workspace_id) if d.workspace_id else None,
            "project_id": str(d.project_id) if d.project_id else None
        }

    def _format_task_item(self, t: Task) -> Dict[str, Any]:
        return {
            "id": str(t.id),
            "type": "TASK",
            "title": f"Task: {t.description[:60]}",
            "description": t.description,
            "source_type": "task",
            "source_id": str(t.id),
            "timestamp": t.created_at.isoformat() if t.created_at else datetime.utcnow().isoformat(),
            "deep_link": f"/tasks/{t.id}",
            "project_id": str(t.project_id) if t.project_id else None
        }

    def _format_document_item(self, doc: Document) -> Dict[str, Any]:
        return {
            "id": str(doc.id),
            "type": "DOCUMENT",
            "title": doc.title,
            "description": f"Document: {doc.filename}",
            "source_type": "document",
            "source_id": str(doc.id),
            "timestamp": doc.created_at.isoformat() if doc.created_at else datetime.utcnow().isoformat(),
            "deep_link": f"/files?preview={doc.id}",
            "workspace_id": str(doc.workspace_id) if doc.workspace_id else None,
            "project_id": str(doc.project_id) if doc.project_id else None
        }
