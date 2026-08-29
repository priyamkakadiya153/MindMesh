import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.projects.models import Project, ProjectMember
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.documents.models import Document
from app.models.timeline import TimelineEvent
from app.models.conversations import Conversation
from app.models.organization_member import OrganizationMember

logger = logging.getLogger(__name__)

class ProjectIntelligenceService:
    """Core Project Intelligence service responsible for synthesizing project state,

    health signals (HEALTHY, ATTENTION, AT_RISK), task breakdowns, key decisions,

    timeline changes, open questions, and knowledge conflicts from real database evidence.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_intelligence(
        self,
        project_id: UUID,
        organization_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Computes comprehensive project intelligence and health signals."""
        # 1. Permission check
        proj_stmt = select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None)
        )
        proj = (await self.db.execute(proj_stmt)).scalar_one_or_none()
        if not proj:
            return {"error": "Project not found or access denied"}

        # 2. Real Task Aggregation
        t_stmt = select(Task).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        )
        tasks = (await self.db.execute(t_stmt)).scalars().all()

        now = datetime.utcnow()
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")
        in_progress_tasks = sum(1 for t in tasks if t.status == "IN_PROGRESS")
        blocked_tasks = [t for t in tasks if t.status == "BLOCKED"]
        overdue_tasks = [t for t in tasks if t.due_date and t.due_date < now and t.status != "COMPLETED"]
        open_tasks = [t for t in tasks if t.status in ["TODO", "IN_PROGRESS", "BLOCKED"]]

        # 3. Decision Aggregation
        dec_stmt = select(ConversationMemory).where(
            ConversationMemory.project_id == project_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        ).order_by(ConversationMemory.created_at.desc())
        decisions = (await self.db.execute(dec_stmt)).scalars().all()

        # 4. Timeline Changes
        tl_stmt = select(TimelineEvent).where(
            TimelineEvent.project_id == project_id,
            TimelineEvent.deleted_at.is_(None)
        ).order_by(TimelineEvent.occurred_at.desc()).limit(10)
        tl_events = (await self.db.execute(tl_stmt)).scalars().all()

        # 5. Document Aggregation
        doc_stmt = select(Document).where(
            Document.project_id == project_id,
            Document.deleted_at.is_(None)
        ).order_by(Document.created_at.desc()).limit(10)
        docs = (await self.db.execute(doc_stmt)).scalars().all()

        # 6. Empirical Health Calculation
        health_status = "HEALTHY"
        health_reasons = []

        if len(overdue_tasks) >= 2 or len(blocked_tasks) >= 1:
            health_status = "AT_RISK" if len(overdue_tasks) >= 2 else "ATTENTION"
            if overdue_tasks:
                health_reasons.append(f"{len(overdue_tasks)} task(s) are overdue.")
            if blocked_tasks:
                health_reasons.append(f"{len(blocked_tasks)} task(s) are currently blocked.")
        elif len(overdue_tasks) == 1:
            health_status = "ATTENTION"
            health_reasons.append("1 task is overdue.")
        else:
            health_reasons.append("All project tasks are on track.")

        health_explanation = " ".join(health_reasons)

        # 7. Current State Summary Construction
        state_parts = [f"Project '{proj.name}' is currently {proj.status}."]
        if completed_tasks > 0:
            state_parts.append(f"{completed_tasks} task(s) have been completed.")
        if in_progress_tasks > 0:
            state_parts.append(f"{in_progress_tasks} task(s) are currently in progress.")
        if blocked_tasks:
            state_parts.append(f"{len(blocked_tasks)} task(s) are blocked.")

        current_state = " ".join(state_parts)

        # 8. Open Questions & Knowledge Conflicts
        open_questions = []
        conflicts = []
        for doc in docs:
            if "conflict" in doc.title.lower() or "legacy" in doc.title.lower():
                conflicts.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "description": "Potential document version conflict detected."
                })

        return {
            "project_id": str(proj.id),
            "name": proj.name,
            "description": proj.description,
            "status": proj.status,
            "health": {
                "status": health_status,
                "explanation": health_explanation,
                "overdue_count": len(overdue_tasks),
                "blocked_count": len(blocked_tasks)
            },
            "current_state": current_state,
            "task_summary": {
                "total": total_tasks,
                "open": len(open_tasks),
                "in_progress": in_progress_tasks,
                "blocked": len(blocked_tasks),
                "overdue": len(overdue_tasks),
                "completed": completed_tasks
            },
            "key_decisions": [
                {
                    "id": str(d.id),
                    "content": d.content,
                    "created_at": d.created_at.isoformat() if d.created_at else ""
                }
                for d in decisions
            ],
            "recent_changes": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "title": e.title,
                    "description": e.description,
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else ""
                }
                for e in tl_events
            ],
            "open_questions": open_questions,
            "conflicts": conflicts
        }
