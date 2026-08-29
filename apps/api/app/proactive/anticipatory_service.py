import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.projects.models import Project
from app.workspace.models import WorkspaceMember

logger = logging.getLogger(__name__)

# In-memory storage for proactive insights and user notification preferences
_PROACTIVE_INSIGHTS: List[Dict[str, Any]] = []
_USER_PREFERENCES: Dict[str, Dict[str, bool]] = {}

class ProactiveAnticipatoryEngineService:
    """Centralized Proactive Intelligence engine that monitors meaningful application events

    (TASK_ASSIGNED, DECISION_UPDATED, BLOCKER_CREATED, QUESTION_MENTION, KNOWLEDGE_CONFLICT),

    evaluates personal relevance & importance, deduplicates events, and surfaces actionable,

    source-backed insights ("Why am I seeing this?") without notification spam.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def emit_proactive_event(
        self,
        event_type: str,
        organization_id: UUID,
        workspace_id: UUID,
        target_user_id: UUID,
        title: str,
        description: str,
        source_type: str,
        source_id: UUID,
        project_id: Optional[UUID] = None,
        project_name: Optional[str] = None,
        importance: str = "IMPORTANT",
        context_explanation: Optional[str] = None,
        action_payload: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Processes an application event, evaluates user preferences & deduplication, and creates an insight."""
        # Preference Check
        u_key = str(target_user_id)
        user_prefs = _USER_PREFERENCES.get(u_key, {})
        category_map = {
            "TASK_ASSIGNED": "tasks",
            "BLOCKER_CREATED": "blockers",
            "DECISION_UPDATED": "decisions",
            "QUESTION_MENTION": "mentions",
            "KNOWLEDGE_CONFLICT": "conflicts",
            "PROJECT_UPDATE": "project_updates"
        }
        pref_key = category_map.get(event_type, "tasks")
        if user_prefs.get(pref_key) is False:
            logger.info(f"Insight skipped due to user preference for {event_type}")
            return None

        # Deduplication Check
        for existing in _PROACTIVE_INSIGHTS:
            if (existing["target_user_id"] == u_key and
                existing["source_id"] == str(source_id) and
                existing["event_type"] == event_type and
                existing["status"] == "UNREAD"):
                logger.info(f"Duplicate proactive event suppressed for {source_id}")
                return existing

        insight_id = str(uuid4())
        insight = {
            "id": insight_id,
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "target_user_id": u_key,
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name or "Authentication System",
            "event_type": event_type,
            "importance": importance,
            "title": title,
            "description": description,
            "source_type": source_type,
            "source_id": str(source_id),
            "context_explanation": context_explanation or "Because this activity directly affects your assigned work.",
            "status": "UNREAD",
            "created_at": datetime.utcnow().isoformat(),
            "action_payload": action_payload or {
                "action_type": "OPEN_SOURCE",
                "label": "Review Source"
            }
        }
        _PROACTIVE_INSIGHTS.append(insight)
        return insight

    async def get_user_proactive_insights(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        filter_type: str = "ALL"
    ) -> Dict[str, Any]:
        """Retrieves active proactive insights for the current user with unread counters."""
        u_key = str(user.id)
        user_insights = [i for i in _PROACTIVE_INSIGHTS if i["target_user_id"] == u_key and i["organization_id"] == str(organization_id)]

        if filter_type != "ALL":
            user_insights = [i for i in user_insights if i["event_type"] == filter_type or i["importance"] == filter_type]

        unread_count = sum(1 for i in user_insights if i["status"] == "UNREAD")

        return {
            "total_insights": len(user_insights),
            "unread_count": unread_count,
            "insights": user_insights
        }

    async def mark_insights_read(self, user_id: UUID, insight_ids: List[str]) -> Dict[str, Any]:
        """Marks specified insights as read."""
        u_key = str(user_id)
        updated = 0
        for i in _PROACTIVE_INSIGHTS:
            if i["target_user_id"] == u_key and i["id"] in insight_ids:
                i["status"] = "READ"
                updated += 1
        return {"success": True, "updated_count": updated}

    async def dismiss_insight(self, user_id: UUID, insight_id: str) -> Dict[str, Any]:
        """Dismisses an insight non-destructively without deleting the source entity."""
        u_key = str(user_id)
        for i in _PROACTIVE_INSIGHTS:
            if i["target_user_id"] == u_key and i["id"] == insight_id:
                i["status"] = "DISMISSED"
                return {"success": True, "message": "Insight dismissed"}
        return {"success": False, "message": "Insight not found"}

    async def update_user_preferences(self, user_id: UUID, preferences: Dict[str, bool]) -> Dict[str, Any]:
        """Updates user proactive notification category preferences."""
        u_key = str(user_id)
        _USER_PREFERENCES[u_key] = preferences
        return {"success": True, "preferences": _USER_PREFERENCES[u_key]}
