import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.projects.models import Project, ProjectMember
from app.documents.models import Document
from app.models.conversation import ConversationMemory
from app.models.timeline import TimelineEvent
from app.activity.models import ActivityLog
from app.intelligence.service import ProactiveIntelligenceService

logger = logging.getLogger(__name__)

class UserContextService:
    """Core service for building personal context ('My Work'), tracking explicit knowledge

    interactions, computing 'Catch Me Up' updates, and enforcing strict permission-first

    workspace isolation.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_context(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Returns comprehensive personal context ('My Work') for the authenticated user."""

        # 1. My Tasks (Assigned or Created by User in Workspace)
        t_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None),
            or_(Task.assignee_id == user.id, Task.created_by == str(user.id))
        )
        if workspace_id:
            t_stmt = t_stmt.where(Task.workspace_id == workspace_id)

        user_tasks = (await self.db.execute(t_stmt)).scalars().all()

        now = datetime.utcnow()
        overdue_my_tasks = [t for t in user_tasks if t.due_date and t.due_date < now and t.status != "COMPLETED"]
        blocked_my_tasks = [t for t in user_tasks if t.status == "BLOCKED"]
        open_my_tasks = [t for t in user_tasks if t.status in ["TODO", "IN_PROGRESS", "BLOCKED"]]

        # Sort tasks: Overdue -> Blocked -> In Progress -> TODO -> Completed
        def task_sort_key(t: Task):
            if t.due_date and t.due_date < now and t.status != "COMPLETED":
                return 0
            if t.status == "BLOCKED":
                return 1
            if t.status == "IN_PROGRESS":
                return 2
            if t.status == "TODO":
                return 3
            return 4

        sorted_tasks = sorted(user_tasks, key=task_sort_key)

        # 2. My Projects (Projects where user is member or has assigned tasks)
        proj_stmt = select(Project).where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None)
        )
        if workspace_id:
            proj_stmt = proj_stmt.where(Project.workspace_id == workspace_id)

        all_projs = (await self.db.execute(proj_stmt)).scalars().all()
        user_proj_ids = set(t.project_id for t in user_tasks if t.project_id)

        my_projects = [p for p in all_projs if p.id in user_proj_ids or p.owner_id == user.id]

        # 3. Recent Knowledge (Recently viewed/interacted documents and decisions)
        act_stmt = select(ActivityLog).where(
            ActivityLog.organization_id == organization_id,
            ActivityLog.user_id == user.id,
            ActivityLog.is_active.is_(True)
        ).order_by(desc(ActivityLog.created_at)).limit(10)

        if workspace_id:
            act_stmt = act_stmt.where(ActivityLog.workspace_id == workspace_id)

        user_activities = (await self.db.execute(act_stmt)).scalars().all()

        doc_stmt = select(Document).where(
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None)
        ).order_by(desc(Document.created_at)).limit(5)
        if workspace_id:
            doc_stmt = doc_stmt.where(Document.workspace_id == workspace_id)

        recent_docs = (await self.db.execute(doc_stmt)).scalars().all()

        # 4. Proactive Signals for User
        intel_service = ProactiveIntelligenceService(self.db)
        user_signals = await intel_service.get_important_signals_for_user(
            user=user,
            organization_id=organization_id,
            workspace_id=workspace_id,
            limit=5
        )

        return {
            "user_id": str(user.id),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "needs_attention": {
                "overdue_count": len(overdue_my_tasks),
                "blocked_count": len(blocked_my_tasks),
                "items": [
                    {
                        "id": str(t.id),
                        "title": t.title or "Task",
                        "status": t.status,
                        "reason": t.blocked_reason if t.status == "BLOCKED" else "Due date passed"
                    }
                    for t in (overdue_my_tasks + blocked_my_tasks)[:5]
                ]
            },
            "my_tasks": [
                {
                    "id": str(t.id),
                    "title": t.title or "Task",
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "project_id": str(t.project_id) if t.project_id else None
                }
                for t in sorted_tasks[:15]
            ],
            "my_projects": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "description": p.description
                }
                for p in my_projects[:10]
            ],
            "recent_knowledge": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "filename": d.filename,
                    "updated_at": d.updated_at.isoformat() if d.updated_at else ""
                }
                for d in recent_docs
            ],
            "recent_activity": [
                {
                    "id": str(a.id),
                    "event_type": a.event_type,
                    "entity_type": a.entity_type,
                    "created_at": a.created_at.isoformat() if a.created_at else ""
                }
                for a in user_activities
            ],
            "important_updates": user_signals
        }

    async def get_catch_up_summary(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Computes timeline changes, new decisions, and task updates since the user's last interaction."""

        # Determine last user activity timestamp
        last_act_stmt = select(ActivityLog).where(
            ActivityLog.organization_id == organization_id,
            ActivityLog.user_id == user.id
        ).order_by(desc(ActivityLog.created_at)).limit(1)

        last_act = (await self.db.execute(last_act_stmt)).scalar_one_or_none()
        since_time = last_act.created_at if last_act else (datetime.utcnow() - timedelta(days=7))

        # 1. New Decisions
        d_stmt = select(ConversationMemory).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.created_at >= since_time,
            ConversationMemory.deleted_at.is_(None)
        )
        if project_id:
            d_stmt = d_stmt.where(ConversationMemory.project_id == project_id)
        elif workspace_id:
            d_stmt = d_stmt.where(ConversationMemory.workspace_id == workspace_id)

        new_decisions = (await self.db.execute(d_stmt)).scalars().all()

        # 2. Timeline Events
        tl_stmt = select(TimelineEvent).where(
            TimelineEvent.organization_id == organization_id,
            TimelineEvent.occurred_at >= since_time,
            TimelineEvent.deleted_at.is_(None)
        )
        if project_id:
            tl_stmt = tl_stmt.where(TimelineEvent.project_id == project_id)
        elif workspace_id:
            tl_stmt = tl_stmt.where(TimelineEvent.workspace_id == workspace_id)

        tl_events = (await self.db.execute(tl_stmt)).scalars().all()

        # 3. New Documents
        doc_stmt = select(Document).where(
            Document.organization_id == organization_id,
            Document.created_at >= since_time,
            Document.deleted_at.is_(None)
        )
        if project_id:
            doc_stmt = doc_stmt.where(Document.project_id == project_id)
        elif workspace_id:
            doc_stmt = doc_stmt.where(Document.workspace_id == workspace_id)

        new_docs = (await self.db.execute(doc_stmt)).scalars().all()

        has_history = last_act is not None
        summary_text = (
            f"Since your last activity on {since_time.strftime('%Y-%m-%d')}, {len(new_decisions)} decision(s) were recorded, "
            f"{len(new_docs)} document(s) were added, and {len(tl_events)} project change(s) occurred."
            if has_history else
            "Showing recent knowledge changes from the past 7 days."
        )

        return {
            "has_activity_history": has_history,
            "since_timestamp": since_time.isoformat(),
            "summary": summary_text,
            "new_decisions": [
                {"id": str(d.id), "content": d.content, "created_at": d.created_at.isoformat()}
                for d in new_decisions
            ],
            "timeline_events": [
                {"id": str(e.id), "title": e.title, "event_type": e.event_type, "occurred_at": e.occurred_at.isoformat()}
                for e in tl_events
            ],
            "new_documents": [
                {"id": str(doc.id), "title": doc.title, "filename": doc.filename}
                for doc in new_docs
            ]
        }

    async def record_user_activity(
        self,
        user: User,
        organization_id: UUID,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Records a lightweight user knowledge interaction log."""
        log = ActivityLog(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user.id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_metadata=action_metadata or {}
        )
        self.db.add(log)
        await self.db.flush()
        return log
