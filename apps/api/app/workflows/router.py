from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import WorkflowOrchestratorService

router = APIRouter(prefix="/workflows", tags=["Agentic Workflows"])

class CreateWorkflowPlanRequest(BaseModel):
    goal: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None

class ApproveWorkflowRequest(BaseModel):
    approved_step_ids: Optional[List[str]] = None

@router.post("/plan", status_code=status.HTTP_200_OK)
async def create_workflow_plan(
    req: CreateWorkflowPlanRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Understand a goal, gather context, and generate a draft multi-step workflow plan."""
    ws_uuid = UUID(req.workspace_id) if req.workspace_id else None
    p_uuid = UUID(req.project_id) if req.project_id else None

    service = WorkflowOrchestratorService(db)
    return await service.understand_goal_and_plan(
        goal=req.goal,
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=p_uuid
    )

@router.get("/{workflow_id}", status_code=status.HTTP_200_OK)
async def get_workflow_details(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch current status, progress, and step details for an Agentic Workflow."""
    try:
        wf_uuid = UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow UUID format")

    service = WorkflowOrchestratorService(db)
    try:
        return await service.get_workflow_details(workflow_id=wf_uuid, user=current_user, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{workflow_id}/approve", status_code=status.HTTP_200_OK)
async def approve_workflow(
    workflow_id: str,
    req: ApproveWorkflowRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve steps and initiate workflow execution."""
    try:
        wf_uuid = UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow UUID format")

    appr_uuids = [UUID(sid) for sid in req.approved_step_ids] if req.approved_step_ids else None
    service = WorkflowOrchestratorService(db)
    try:
        return await service.approve_and_start_workflow(
            workflow_id=wf_uuid,
            approved_step_ids=appr_uuids,
            user=current_user,
            organization_id=org_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{workflow_id}/pause", status_code=status.HTTP_200_OK)
async def pause_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Pause a running workflow."""
    try:
        wf_uuid = UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow UUID format")

    service = WorkflowOrchestratorService(db)
    return await service.pause_workflow(workflow_id=wf_uuid, user=current_user, organization_id=org_id)

@router.post("/{workflow_id}/resume", status_code=status.HTTP_200_OK)
async def resume_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Resume a paused workflow."""
    try:
        wf_uuid = UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow UUID format")

    service = WorkflowOrchestratorService(db)
    return await service.resume_workflow(workflow_id=wf_uuid, user=current_user, organization_id=org_id)
