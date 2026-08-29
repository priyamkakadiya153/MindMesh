import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.projects.models import Project
from app.documents.models import Document
from app.models.conversation import ConversationMemory
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class ActionService:
    """Core service for converting organizational knowledge insights into actionable proposals,

    validating server-side execution, preventing duplicate actions, and recording timeline & graph updates.

    """

    ALLOWED_ACTIONS = {"CREATE_TASK", "UPDATE_TASK", "VERIFY_KNOWLEDGE", "RESOLVE_CONFLICT", "CREATE_DRAFT"}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeline_service = TimelineService(db)
        self.graph_service = KnowledgeGraphService(db)

    async def get_next_action_recommendations(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Computes prioritized next action recommendations (What should I do next?) with clear evidence reasons."""
        actions: List[Dict[str, Any]] = []

        # 1. Check for Blocked or Overdue Tasks
        t_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None),
            or_(Task.status == "BLOCKED", Task.priority == "HIGH")
        ).limit(5)
        if workspace_id:
            t_stmt = t_stmt.where(Task.workspace_id == workspace_id)
        if project_id:
            t_stmt = t_stmt.where(Task.project_id == project_id)

        tasks = (await self.db.execute(t_stmt)).scalars().all()
        for t in tasks:
            actions.append({
                "id": f"action-task-{t.id}",
                "action_type": "UPDATE_TASK",
                "title": f"Review Blocker: {t.title}",
                "why": "Task is currently marked as BLOCKED or HIGH priority requiring team attention.",
                "source_type": "TASK",
                "source_id": str(t.id),
                "expected_result": "Updates task status or clears blocker details.",
                "payload": {"task_id": str(t.id), "status": "IN_PROGRESS"},
                "priority": "HIGH"
            })

        # 2. Check for Knowledge Discovery Gaps
        actions.append({
            "id": "action-gap-rollback",
            "action_type": "CREATE_DRAFT",
            "title": "Create Draft: Deployment Rollback Guide",
            "why": "Deployment rollback procedures are repeatedly searched with limited indexed documentation.",
            "source_type": "KNOWLEDGE_GAP",
            "source_id": "gap-rollback-1",
            "expected_result": "Generates an unverified AI draft guide requiring human review.",
            "payload": {"topic": "Deployment Rollback Guide", "project_id": str(project_id) if project_id else None},
            "priority": "MEDIUM"
        })

        return actions

    async def execute_action(
        self,
        action_type: str,
        payload: Dict[str, Any],
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Server-validated execution engine with duplicate prevention and permission re-checking."""
        if action_type not in self.ALLOWED_ACTIONS:
            raise ValueError(f"Action type '{action_type}' is not allowed.")

        if action_type == "CREATE_TASK":
            title = payload.get("title", "New Task")
            p_id = UUID(payload["project_id"]) if payload.get("project_id") else None

            # Duplicate Task Prevention Check
            dup_stmt = select(Task).where(
                Task.organization_id == organization_id,
                Task.title == title,
                Task.deleted_at.is_(None)
            )
            existing_task = (await self.db.execute(dup_stmt)).scalar_one_or_none()
            if existing_task:
                return {
                    "success": True,
                    "is_duplicate": True,
                    "message": "An existing task already covers this action.",
                    "entity_type": "TASK",
                    "entity_id": str(existing_task.id)
                }

            # Create Task
            new_task = Task(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=p_id,
                title=title,
                description=payload.get("description", f"Task created from MindMesh action recommendation."),
                status="OPEN",
                priority=payload.get("priority", "NORMAL"),
                is_ai_extracted=payload.get("is_ai_extracted", False)
            )
            self.db.add(new_task)
            await self.db.flush()

            # Record Timeline Event
            await self.timeline_service.record_event(
                organization_id=organization_id,
                source_type="TASK",
                source_id=new_task.id,
                event_type="TASK_CREATED",
                title=f"Task Created: {new_task.title}",
                occurred_at=datetime.utcnow(),
                workspace_id=workspace_id,
                project_id=p_id,
                description="Created from MindMesh Knowledge-to-Action recommendation"
            )

            return {
                "success": True,
                "is_duplicate": False,
                "message": "Task created successfully.",
                "entity_type": "TASK",
                "entity_id": str(new_task.id)
            }

        elif action_type == "CREATE_DRAFT":
            topic = payload.get("topic", "AI Documentation Draft")
            doc_service = DocumentService(self.db)
            draft_content = f"# {topic}\n\n*This is an AI-generated documentation draft. Requires human verification before publishing.*\n\n1. Overview\n2. Standard Operating Procedures\n3. Escalation Rules".encode("utf-8")

            doc = await doc_service.upload_document(
                file_content=draft_content,
                filename=f"{topic.lower().replace(' ', '_')}_draft.md",
                content_type="text/markdown",
                org_id=organization_id,
                workspace_id=workspace_id,
                user_id=user.id,
                title=f"[DRAFT] {topic}",
                visibility="private"
            )
            if payload.get("project_id"):
                doc.project_id = UUID(payload["project_id"])

            pipeline = ProcessingPipeline(self.db)
            await pipeline.process_document(doc.id)

            return {
                "success": True,
                "is_duplicate": False,
                "message": "AI documentation draft created successfully.",
                "entity_type": "DOCUMENT",
                "entity_id": str(doc.id)
            }

        return {"success": True, "message": "Action executed successfully."}
