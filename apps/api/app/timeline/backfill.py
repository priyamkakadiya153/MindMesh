import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .service import TimelineService
from ..documents.models import Document
from ..models.conversations import Conversation, DirectMessage
from ..models.chat import Chat
from ..projects.models import Project
from ..models.task import Task
from ..models.conversation import ConversationMemory

logger = logging.getLogger(__name__)

class TimelineBackfillService:
    """Safe, non-blocking, and idempotent historical data backfill engine for

    converting existing documents, messages, tasks, projects, and AI decisions

    into normalized timeline events.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = TimelineService(db)

    async def run_backfill(self, organization_id: Optional[UUID] = None, batch_size: int = 100) -> Dict[str, Any]:
        stats = {
            "documents_processed": 0,
            "messages_processed": 0,
            "projects_processed": 0,
            "tasks_processed": 0,
            "decisions_processed": 0,
            "events_created": 0
        }

        # 1. Backfill Documents
        doc_stmt = select(Document).where(Document.deleted_at.is_(None))
        if organization_id:
            doc_stmt = doc_stmt.where(Document.organization_id == organization_id)
        doc_res = await self.db.execute(doc_stmt.limit(batch_size))
        docs = doc_res.scalars().all()

        for doc in docs:
            await self.service.record_event(
                organization_id=doc.organization_id,
                workspace_id=doc.workspace_id,
                project_id=doc.project_id,
                source_type="document",
                source_id=doc.id,
                event_type="DOCUMENT_CREATED",
                importance="MEDIUM",
                title=f"Document Created: {doc.title}",
                description=f"File {doc.filename} ({doc.mime_type or 'document'}) was uploaded.",
                occurred_at=doc.created_at or datetime.utcnow(),
                metadata_json={
                    "filename": doc.filename,
                    "size": doc.size,
                    "mime_type": doc.mime_type,
                    "deep_link": f"/files?preview={doc.id}"
                }
            )
            stats["documents_processed"] += 1
            stats["events_created"] += 1

        # 2. Backfill Projects
        proj_stmt = select(Project).where(Project.deleted_at.is_(None))
        if organization_id:
            proj_stmt = proj_stmt.where(Project.organization_id == organization_id)
        proj_res = await self.db.execute(proj_stmt.limit(batch_size))
        projs = proj_res.scalars().all()

        for p in projs:
            await self.service.record_event(
                organization_id=p.organization_id,
                workspace_id=p.workspace_id,
                project_id=p.id,
                source_type="project",
                source_id=p.id,
                event_type="PROJECT_CREATED",
                importance="HIGH",
                title=f"Project Created: {p.name}",
                description=p.description or f"Project {p.name} initialized.",
                occurred_at=p.created_at or datetime.utcnow(),
                metadata_json={"project_name": p.name, "deep_link": f"/projects/{p.id}"}
            )
            stats["projects_processed"] += 1
            stats["events_created"] += 1

        # 3. Backfill Tasks
        task_stmt = select(Task).where(Task.deleted_at.is_(None))
        if organization_id:
            task_stmt = task_stmt.where(Task.organization_id == organization_id)
        task_res = await self.db.execute(task_stmt.limit(batch_size))
        tasks = task_res.scalars().all()

        for t in tasks:
            event_type = "TASK_COMPLETED" if t.status == "completed" else "TASK_CREATED"
            importance = "HIGH" if t.status == "completed" else "MEDIUM"
            await self.service.record_event(
                organization_id=t.organization_id,
                workspace_id=None,
                project_id=t.project_id,
                source_type="task",
                source_id=t.id,
                event_type=event_type,
                importance=importance,
                title=f"Task: {t.description[:60]}",
                description=t.description,
                occurred_at=t.updated_at if t.status == "completed" else (t.created_at or datetime.utcnow()),
                metadata_json={"status": t.status, "due_date": t.due_date.isoformat() if t.due_date else None}
            )
            stats["tasks_processed"] += 1
            stats["events_created"] += 1

        # 4. Backfill Conversation Memories / Decisions
        mem_stmt = select(ConversationMemory).where(ConversationMemory.deleted_at.is_(None))
        if organization_id:
            mem_stmt = mem_stmt.where(ConversationMemory.organization_id == organization_id)
        mem_res = await self.db.execute(mem_stmt.limit(batch_size))
        mems = mem_res.scalars().all()

        for m in mems:
            if m.memory_type == "decision":
                event_type = "DECISION_MADE"
                importance = "HIGH"
            elif m.memory_type == "action_item":
                event_type = "TASK_CREATED"
                importance = "MEDIUM"
            else:
                event_type = "IMPORTANT_FACT_DISCOVERED"
                importance = "MEDIUM"

            await self.service.record_event(
                organization_id=m.organization_id,
                workspace_id=m.workspace_id,
                project_id=m.project_id,
                source_type="decision" if m.memory_type == "decision" else "message",
                source_id=m.id,
                event_type=event_type,
                importance=importance,
                title=m.content[:80],
                description=m.content,
                occurred_at=m.created_at or datetime.utcnow(),
                metadata_json={
                    "chat_id": str(m.chat_id) if m.chat_id else None,
                    "conversation_id": str(m.conversation_id) if m.conversation_id else None,
                    "memory_type": m.memory_type
                }
            )
            stats["decisions_processed"] += 1
            stats["events_created"] += 1

        await self.db.flush()
        logger.info(f"Timeline historical backfill completed: {stats}")
        return stats
