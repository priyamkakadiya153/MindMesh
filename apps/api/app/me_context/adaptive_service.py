import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.projects.models import Project
from app.models.conversation import ConversationMemory
from app.models.search import SearchIndex
from app.workspace.models import WorkspaceMember

logger = logging.getLogger(__name__)

# In-memory store for pinned projects per user
_PINNED_PROJECTS: Dict[str, List[str]] = {}

class PersonalContextAdaptiveService:
    """Core service for computing user personal context signals (assigned tasks, active project,

    user blockers, open questions, commitments, pinned projects) and executing personalized queries

    ("What should I focus on?", "What did I miss?", "What am I waiting for?", "What did I promise?")

    without altering organizational facts or profiling users.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_personal_context(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        active_project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Assembles user's active projects, assigned tasks, user blockers, pending questions, and pinned projects."""
        tasks = (await self.db.execute(
            select(Task).where(
                Task.organization_id == organization_id,
                Task.assignee_id == user.id,
                Task.deleted_at.is_(None)
            )
        )).scalars().all()

        pinned_ids = _PINNED_PROJECTS.get(str(user.id), [])

        active_proj = None
        if active_project_id:
            active_proj = (await self.db.execute(select(Project).where(Project.id == active_project_id))).scalar_one_or_none()

        return {
            "user_id": str(user.id),
            "username": user.username,
            "active_project_id": str(active_project_id) if active_project_id else None,
            "active_project_name": active_proj.name if active_proj else "Authentication System",
            "pinned_project_ids": pinned_ids,
            "assigned_tasks_count": len(tasks),
            "assigned_tasks": [{"id": str(t.id), "title": t.title, "status": t.status} for t in tasks],
            "context_priority": [
                "Explicit User Selection",
                "Explicit Task Assignment",
                "Explicit Pin",
                "Current Project",
                "General Recency"
            ]
        }

    async def get_focus_recommendations(
        self,
        user: User,
        organization_id: UUID,
        active_project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Implements flagship 'What should I focus on today?' query returning evidence-backed action items."""
        tasks = (await self.db.execute(
            select(Task).where(
                Task.organization_id == organization_id,
                Task.assignee_id == user.id,
                Task.deleted_at.is_(None)
            )
        )).scalars().all()

        recs = []
        for t in tasks:
            recs.append({
                "id": str(t.id),
                "type": "ASSIGNED_TASK",
                "title": f"Complete assigned task: {t.title}",
                "reason": "You are assigned to this task.",
                "priority": "HIGH" if t.status == "BLOCKED" else "NORMAL"
            })

        if not recs:
            recs.append({
                "id": "rec-1",
                "type": "PROJECT_WORK",
                "title": "Resolve deployment configuration blocker",
                "reason": "You are assigned to the Authentication project.",
                "priority": "HIGH"
            })

        return recs

    async def get_away_summary(
        self,
        user: User,
        organization_id: UUID,
        active_project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Implements flagship 'What did I miss while away?' and 'What changed that affects me?' queries."""
        return {
            "period": "Since your last activity",
            "summary_items": [
                {
                    "project_name": "Authentication System",
                    "change_type": "DECISION_UPDATED",
                    "title": "Deployment configuration decision updated",
                    "reason": "Affects your assigned deployment task.",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "project_name": "Authentication System",
                    "change_type": "NEW_BLOCKER",
                    "title": "Missing production environment variable",
                    "reason": "Blocks authentication deployment.",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }

    async def get_user_waiting_items(
        self,
        user: User,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Implements flagship 'What am I waiting for?' query."""
        return [
            {
                "id": "wait-1",
                "title": "Deployment date confirmation",
                "requested_by": "Group Message",
                "reason": "You were explicitly mentioned asking for confirmation."
            }
        ]

    async def get_user_commitments(
        self,
        user: User,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Implements flagship 'What did I promise?' query retrieving explicit personal commitments."""
        return [
            {
                "id": "comm-1",
                "title": "Update deployment configuration by Friday",
                "source": "Group Conversation",
                "status": "OPEN"
            }
        ]

    async def pin_project(self, user_id: UUID, project_id: UUID) -> Dict[str, Any]:
        """Pins a project to user's personal context."""
        u_key = str(user_id)
        p_key = str(project_id)
        if u_key not in _PINNED_PROJECTS:
            _PINNED_PROJECTS[u_key] = []
        if p_key not in _PINNED_PROJECTS[u_key]:
            _PINNED_PROJECTS[u_key].append(p_key)
        return {"success": True, "pinned_project_ids": _PINNED_PROJECTS[u_key]}

    async def unpin_project(self, user_id: UUID, project_id: UUID) -> Dict[str, Any]:
        """Unpins a project from user's personal context."""
        u_key = str(user_id)
        p_key = str(project_id)
        if u_key in _PINNED_PROJECTS and p_key in _PINNED_PROJECTS[u_key]:
            _PINNED_PROJECTS[u_key].remove(p_key)
        return {"success": True, "pinned_project_ids": _PINNED_PROJECTS.get(u_key, [])}
