from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .workflow_orchestration_service import WorkflowOrchestrationService

router = APIRouter(prefix="/workflow-orchestration", tags=["Intelligent Workflow Orchestration & Controlled Autonomous Action"])

class CreatePlanRequest(BaseModel):
    project_id: str
    goal: str

class ApproveWorkflowRequest(BaseModel):
    workflow_id: str

class ExecuteStepRequest(BaseModel):
    workflow_id: str
    step_id: str

class RetryStepRequest(BaseModel):
    workflow_id: str
    step_id: str

class PostmortemRequest(BaseModel):
    workflow_id: str

@router.get("/center", status_code=status.HTTP_200_OK)
async def get_workflow_center(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active workflows categorized by execution state."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = WorkflowOrchestrationService(db)
    return await service.get_workflow_center(organization_id=org_id, user=current_user)

@router.post("/create-plan", status_code=status.HTTP_200_OK)
async def create_workflow_plan(
    req: CreatePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Construct multi-step executable DAG plan."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = WorkflowOrchestrationService(db)
    return await service.create_workflow_plan(project_id=p_uuid, goal=req.goal, user=current_user)

@router.post("/approve", status_code=status.HTTP_200_OK)
async def approve_workflow(
    req: ApproveWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve workflow via human approval gate."""
    service = WorkflowOrchestrationService(db)
    return await service.approve_workflow(workflow_id=req.workflow_id, approver=current_user)

@router.post("/execute-step", status_code=status.HTTP_200_OK)
async def execute_workflow_step(
    req: ExecuteStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute workflow step with idempotency and verification."""
    service = WorkflowOrchestrationService(db)
    return await service.execute_workflow_step(workflow_id=req.workflow_id, step_id=req.step_id, user=current_user)

@router.post("/retry", status_code=status.HTTP_200_OK)
async def handle_step_failure_and_retry(
    req: RetryStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retry failed workflow step with circuit breaker evaluation."""
    service = WorkflowOrchestrationService(db)
    return await service.handle_step_failure_and_retry(workflow_id=req.workflow_id, step_id=req.step_id, user=current_user)

@router.post("/postmortem", status_code=status.HTTP_200_OK)
async def generate_workflow_postmortem(
    req: PostmortemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate evidence-backed workflow postmortem."""
    service = WorkflowOrchestrationService(db)
    return await service.generate_workflow_postmortem(workflow_id=req.workflow_id, user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_workflow_digest(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve workflow summary digest metrics."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = WorkflowOrchestrationService(db)
    return await service.get_workflow_digest(organization_id=org_id, user=current_user)
