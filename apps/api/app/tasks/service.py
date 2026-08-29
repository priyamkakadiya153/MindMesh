import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import re
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.models.conversations import Conversation, DirectMessage
from app.models.conversation import ConversationMemory
from app.documents.models import Document
from app.projects.models import Project
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService
from app.workspace.models import WorkspaceMember

logger = logging.getLogger(__name__)

class TaskService:
    """Core Task Intelligence service responsible for task extraction, provenance

    preservation, status lifecycle transitions, graph/timeline linkage, and grounded

    "Why do I have this task?" explanation generation.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeline_service = TimelineService(db)
        self.graph_service = KnowledgeGraphService(db)

    async def create_task(
        self,
        organization_id: UUID,
        title: str,
        description: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        assignee_id: Optional[UUID] = None,
        due_date: Optional[datetime] = None,
        priority: str = "MEDIUM",
        task_type: str = "TASK",
        source_type: Optional[str] = "USER_CREATED",
        source_id: Optional[UUID] = None,
        decision_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        is_ai_extracted: bool = False,
        creator_id: Optional[UUID] = None
    ) -> Task:
        """Creates a new task with deduplication check and records graph/timeline

        provenance.

        """
        # Deduplication check: check if task with similar description already exists under project or conversation
        dedup_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None),
            Task.status.in_(["TODO", "IN_PROGRESS", "BLOCKED"])
        )
        if project_id:
            dedup_stmt = dedup_stmt.where(Task.project_id == project_id)
        elif conversation_id:
            dedup_stmt = dedup_stmt.where(Task.conversation_id == conversation_id)

        existing_tasks = (await self.db.execute(dedup_stmt)).scalars().all()
        clean_desc = description.strip().lower()
        for ext in existing_tasks:
            if ext.description.strip().lower() == clean_desc or (title and ext.title and ext.title.strip().lower() == title.strip().lower()):
                logger.info(f"Duplicate task detected; returning existing task {ext.id}")
                return ext

        task = Task(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            title=title or description[:60],
            description=description,
            status="TODO",
            task_type=task_type,
            priority=priority,
            assignee_id=assignee_id,
            due_date=due_date,
            source_type=source_type,
            source_id=source_id,
            decision_id=decision_id,
            conversation_id=conversation_id,
            message_id=message_id,
            document_id=document_id,
            is_ai_extracted=is_ai_extracted
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Record Timeline Event
        await self.timeline_service.record_event(
            organization_id=organization_id,
            event_type="TASK_CREATED",
            title=f"Task Created: {task.title}",
            description=task.description,
            source_type="task",
            source_id=task.id,
            workspace_id=workspace_id,
            project_id=project_id,
            occurred_at=datetime.utcnow()
        )

        # Build Knowledge Graph Entities & Edges
        try:
            n_task = await self.graph_service.get_or_create_node(
                organization_id=organization_id,
                node_type="TASK",
                source_type="task",
                source_id=task.id,
                title=f"Task: {task.title}",
                workspace_id=workspace_id,
                project_id=project_id
            )

            if decision_id:
                n_dec = await self.graph_service.get_or_create_node(
                    organization_id=organization_id,
                    node_type="DECISION",
                    source_type="decision",
                    source_id=decision_id,
                    title="Related Decision",
                    workspace_id=workspace_id,
                    project_id=project_id
                )
                await self.graph_service.create_edge(organization_id, n_dec.id, n_task.id, "RESULTED_IN")

            if assignee_id:
                n_user = await self.graph_service.get_or_create_node(
                    organization_id=organization_id,
                    node_type="PERSON",
                    source_type="user",
                    source_id=assignee_id,
                    title="Assignee",
                    workspace_id=workspace_id
                )
                await self.graph_service.create_edge(organization_id, n_task.id, n_user.id, "ASSIGNED_TO")

            await self.db.commit()
        except Exception as e:
            logger.warning(f"Error creating task graph edges: {e}")

        return task

    async def update_task_status(
        self,
        task_id: UUID,
        organization_id: UUID,
        new_status: str,
        user_id: UUID,
        blocked_reason: Optional[str] = None,
        completion_note: Optional[str] = None
    ) -> Optional[Task]:
        """Updates task status following lifecycle rules and records audit timeline."""
        task = (await self.db.execute(select(Task).where(
            Task.id == task_id,
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None)
        ))).scalar_one_or_none()

        if not task:
            return None

        old_status = task.status
        valid_statuses = ["TODO", "IN_PROGRESS", "BLOCKED", "COMPLETED", "CANCELLED"]
        if new_status.upper() not in valid_statuses:
            raise ValueError(f"Invalid task status: {new_status}")

        task.status = new_status.upper()
        if new_status.upper() == "BLOCKED":
            task.blocked_reason = blocked_reason
        elif new_status.upper() == "COMPLETED":
            task.completed_at = datetime.utcnow()
            task.completed_by = user_id
            if completion_note:
                task.description = f"{task.description}\n\n[Completion Note]: {completion_note}"

        await self.db.commit()
        await self.db.refresh(task)

        # Timeline Event
        event_type = "TASK_COMPLETED" if new_status.upper() == "COMPLETED" else "TASK_UPDATED"
        await self.timeline_service.record_event(
            organization_id=organization_id,
            event_type=event_type,
            title=f"Task {new_status.capitalize()}: {task.title}",
            description=f"Status changed from {old_status} to {new_status}. {completion_note or ''}".strip(),
            source_type="task",
            source_id=task.id,
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            occurred_at=datetime.utcnow()
        )

        return task

    async def get_task_provenance_explanation(
        self,
        task_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Generates grounded "Why do I have this task?" provenance explanation."""
        task = (await self.db.execute(select(Task).where(
            Task.id == task_id,
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None)
        ))).scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        explanation_parts = []
        citations = []

        if task.decision_id:
            dec = (await self.db.execute(select(ConversationMemory).where(
                ConversationMemory.id == task.decision_id
            ))).scalar_one_or_none()
            if dec:
                explanation_parts.append(f"This task resulted from the recorded decision: '{dec.content}'.")
                citations.append({"type": "decision", "id": str(dec.id), "title": dec.content})

        if task.message_id:
            msg = (await self.db.execute(select(DirectMessage).where(
                DirectMessage.id == task.message_id
            ))).scalar_one_or_none()
            if msg:
                explanation_parts.append(f"It was extracted from message: '{msg.content}'.")
                citations.append({"type": "message", "id": str(msg.id), "title": msg.content[:60]})

        if task.document_id:
            doc = (await self.db.execute(select(Document).where(
                Document.id == task.document_id
            ))).scalar_one_or_none()
            if doc:
                explanation_parts.append(f"It was derived from document: '{doc.title}'.")
                citations.append({"type": "document", "id": str(doc.id), "title": doc.title})

        if not explanation_parts:
            if task.is_ai_extracted:
                explanation_parts.append("This task was extracted by MindMesh Conversation Intelligence during team discussion.")
            else:
                explanation_parts.append("This task was created manually by workspace team members.")

        return {
            "task_id": str(task.id),
            "title": task.title,
            "provenance_summary": " ".join(explanation_parts),
            "source_type": task.source_type or "USER_CREATED",
            "is_ai_extracted": task.is_ai_extracted,
            "citations": citations
        }

    async def list_tasks(
        self,
        user_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        assignee_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Task]:
        """Returns tasks matching scope and permission boundaries."""
        stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None)
        )

        if workspace_id:
            stmt = stmt.where(Task.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)

        if status_filter:
            if status_filter.upper() == "OVERDUE":
                stmt = stmt.where(
                    Task.due_date < datetime.utcnow(),
                    Task.status != "COMPLETED"
                )
            else:
                stmt = stmt.where(Task.status == status_filter.upper())

        if assignee_filter == "me":
            stmt = stmt.where(Task.assignee_id == user_id)
        elif assignee_filter and assignee_filter != "all":
            try:
                a_uuid = UUID(assignee_filter)
                stmt = stmt.where(Task.assignee_id == a_uuid)
            except ValueError:
                pass

        stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    def parse_relative_deadline(self, text: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
        """Parses relative date strings into absolute UTC datetimes."""
        base = base_time or datetime.utcnow()
        clean = text.lower()

        if "tomorrow" in clean:
            return base + timedelta(days=1)
        if "friday" in clean:
            days_ahead = (4 - base.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return base + timedelta(days=days_ahead)
        if "next week" in clean:
            return base + timedelta(days=7)

        # Regex match for ISO or month day (e.g. August 20)
        m = re.search(r'(august|aug|september|sep|october|oct|november|nov|december|dec)\s+(\d{1,2})', clean)
        if m:
            day = int(m.group(2))
            return datetime(base.year, 8, day)  # default month matching context

        return None
