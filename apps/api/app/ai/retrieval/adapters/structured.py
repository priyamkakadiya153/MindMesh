from typing import List, Dict, Any
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.models import RetrievalRequest, RetrievalPlan, EvidenceItem, SourceType
from app.ai.retrieval.adapters.base import BaseRetrievalAdapter
class StructuredDataSearchAdapter(BaseRetrievalAdapter):
    """Retrieves structured application records (Projects, Tasks, Decisions)."""

    async def search(self, request: RetrievalRequest, plan: RetrievalPlan) -> List[EvidenceItem]:
        from app.models import Project, Task

        results: List[EvidenceItem] = []
        queries = plan.queries or [request.original_query]

        # 1. Search Projects
        if SourceType.PROJECT in plan.sources:
            proj_stmt = select(Project).where(
                Project.organization_id == request.organization_id,
                Project.deleted_at.is_(None)
            )
            if request.workspace_id:
                proj_stmt = proj_stmt.where(Project.workspace_id == request.workspace_id)

            proj_res = await self.db.execute(proj_stmt)
            projects = proj_res.scalars().all()

            for p in projects:
                p_name = p.name or "Untitled Project"
                p_desc = p.description or ""
                p_status = getattr(p, "status", "ACTIVE")

                # Match against queries or entity mentions
                matches = any(q.lower() in p_name.lower() or q.lower() in p_desc.lower() for q in queries)
                if matches or not queries or "active" in request.original_query.lower():
                    results.append(EvidenceItem(
                        source_id=str(p.id),
                        source_type=SourceType.PROJECT,
                        title=f"Project: {p_name}",
                        content=f"Project '{p_name}' (Status: {p_status}). Description: {p_desc}",
                        score=0.90,
                        authority_score=0.95,
                        recency_score=0.90,
                        location={"workspace_id": str(p.workspace_id), "project_id": str(p.id)},
                        metadata={"status": str(p_status), "key": getattr(p, "key", "")},
                        retrieval_methods=["structured_db"]
                    ))

        # 2. Search Tasks
        if SourceType.TASK in plan.sources:
            task_stmt = select(Task).where(
                Task.organization_id == request.organization_id,
                Task.deleted_at.is_(None)
            )
            if request.workspace_id:
                task_stmt = task_stmt.where(Task.workspace_id == request.workspace_id)

            task_res = await self.db.execute(task_stmt)
            tasks = task_res.scalars().all()

            for t in tasks:
                t_title = t.title or "Untitled Task"
                t_status = getattr(t, "status", "OPEN")
                t_priority = getattr(t, "priority", "MEDIUM")

                matches = any(q.lower() in t_title.lower() for q in queries)
                if matches or "overdue" in request.original_query.lower() or "task" in request.original_query.lower():
                    results.append(EvidenceItem(
                        source_id=str(t.id),
                        source_type=SourceType.TASK,
                        title=f"Task: {t_title}",
                        content=f"Task '{t_title}' (Status: {t_status}, Priority: {t_priority})",
                        score=0.85,
                        authority_score=0.95,
                        recency_score=0.85,
                        location={"workspace_id": str(t.workspace_id), "task_id": str(t.id)},
                        metadata={"status": str(t_status), "priority": str(t_priority)},
                        retrieval_methods=["structured_db"]
                    ))

        return results
