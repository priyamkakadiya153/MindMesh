from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import TaskService

router = APIRouter(prefix="/tasks", tags=["Task Intelligence"])

class TaskCreateSchema(BaseModel):
    title: str
    description: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    task_type: Optional[str] = "TASK"

class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None
    blocked_reason: Optional[str] = None

class TaskCompleteSchema(BaseModel):
    completion_note: Optional[str] = None

class TaskResponseSchema(BaseModel):
    id: str
    title: str
    description: str
    status: str
    task_type: str
    priority: str
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    decision_id: Optional[str] = None
    is_ai_extracted: bool
    created_at: str

@router.get("", response_model=List[TaskResponseSchema], status_code=status.HTTP_200_OK)
async def list_tasks(
    workspace_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assignee: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve tasks with optional status, project, or assignee filtering."""
    ws_uuid = UUID(workspace_id) if workspace_id and workspace_id != "all" else None
    proj_uuid = UUID(project_id) if project_id and project_id != "all" else None

    service = TaskService(db)
    tasks = await service.list_tasks(
        user_id=current_user.id,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        status_filter=status,
        assignee_filter=assignee,
        limit=limit
    )

    return [
        {
            "id": str(t.id),
            "title": t.title or t.description[:60],
            "description": t.description,
            "status": t.status,
            "task_type": t.task_type,
            "priority": t.priority,
            "assignee_id": str(t.assignee_id) if t.assignee_id else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "organization_id": str(t.organization_id),
            "workspace_id": str(t.workspace_id) if t.workspace_id else None,
            "project_id": str(t.project_id) if t.project_id else None,
            "source_type": t.source_type,
            "source_id": str(t.source_id) if t.source_id else None,
            "decision_id": str(t.decision_id) if t.decision_id else None,
            "is_ai_extracted": t.is_ai_extracted,
            "created_at": t.created_at.isoformat() if t.created_at else ""
        }
        for t in tasks
    ]

@router.post("", response_model=TaskResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_manual_task(
    payload: TaskCreateSchema,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Manually create a user-created task."""
    ws_uuid = UUID(payload.workspace_id) if payload.workspace_id else None
    proj_uuid = UUID(payload.project_id) if payload.project_id else None
    a_uuid = UUID(payload.assignee_id) if payload.assignee_id else None
    due_dt = datetime.fromisoformat(payload.due_date) if payload.due_date else None

    service = TaskService(db)
    task = await service.create_task(
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        title=payload.title,
        description=payload.description,
        assignee_id=a_uuid,
        due_date=due_dt,
        priority=payload.priority or "MEDIUM",
        task_type=payload.task_type or "TASK",
        source_type="USER_CREATED",
        creator_id=current_user.id
    )

    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "task_type": task.task_type,
        "priority": task.priority,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "organization_id": str(task.organization_id),
        "workspace_id": str(task.workspace_id) if task.workspace_id else None,
        "project_id": str(task.project_id) if task.project_id else None,
        "source_type": task.source_type,
        "source_id": str(task.source_id) if task.source_id else None,
        "decision_id": str(task.decision_id) if task.decision_id else None,
        "is_ai_extracted": task.is_ai_extracted,
        "created_at": task.created_at.isoformat() if task.created_at else ""
    }

@router.get("/{task_id}/why", status_code=status.HTTP_200_OK)
async def get_task_why_provenance(
    task_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve grounded "Why do I have this task?" provenance explanation."""
    try:
        t_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task UUID format")

    service = TaskService(db)
    res = await service.get_task_provenance_explanation(t_uuid, org_id, current_user.id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/{task_id}/complete", response_model=TaskResponseSchema, status_code=status.HTTP_200_OK)
async def complete_task(
    task_id: str,
    payload: TaskCompleteSchema,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark task as COMPLETED with optional completion note."""
    try:
        t_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task UUID format")

    service = TaskService(db)
    task = await service.update_task_status(
        task_id=t_uuid,
        organization_id=org_id,
        new_status="COMPLETED",
        user_id=current_user.id,
        completion_note=payload.completion_note
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "task_type": task.task_type,
        "priority": task.priority,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "organization_id": str(task.organization_id),
        "workspace_id": str(task.workspace_id) if task.workspace_id else None,
        "project_id": str(task.project_id) if task.project_id else None,
        "source_type": task.source_type,
        "source_id": str(task.source_id) if task.source_id else None,
        "decision_id": str(task.decision_id) if task.decision_id else None,
        "is_ai_extracted": task.is_ai_extracted,
        "created_at": task.created_at.isoformat() if task.created_at else ""
    }
