from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .adaptive_workflow_engine_service import AdaptiveWorkflowEngineService

router = APIRouter(prefix="/adaptive-workflows", tags=["Adaptive Workflows & Intelligent Work Execution"])

class CreateObjectiveRequest(BaseModel):
    goal: str
    scope: str
    priority: str = "HIGH"
    deadline: Optional[str] = None
    project_id: Optional[str] = None

class GeneratePlanRequest(BaseModel):
    objective_id: str
    user_intent: str
    project_id: Optional[str] = None

class ExecuteStepRequest(BaseModel):
    plan_id: str
    step_id: str
    action: str = "START" # START, COMPLETE, APPROVE, REJECT, PAUSE

class HandleExceptionRequest(BaseModel):
    plan_id: str
    step_id: str
    error_message: str

class PlanIdRequest(BaseModel):
    plan_id: str

@router.post("/objectives", status_code=status.HTTP_200_OK)
async def create_work_objective(
    req: CreateObjectiveRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates WorkObjective with goal, scope, constraints, and risk classification."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = AdaptiveWorkflowEngineService(db)
    return await service.create_work_objective(
        goal=req.goal,
        scope=req.scope,
        priority=req.priority,
        deadline=req.deadline,
        project_id=proj_uuid,
        organization_id=org_id,
        user=current_user
    )

@router.post("/plans/generate", status_code=status.HTTP_200_OK)
async def generate_work_plan(
    req: GeneratePlanRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates WorkPlan from user intent, playbooks, graph, and proactive signals."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = AdaptiveWorkflowEngineService(db)
    return await service.generate_work_plan(
        objective_id=req.objective_id,
        user_intent=req.user_intent,
        project_id=proj_uuid,
        organization_id=org_id,
        user=current_user
    )

@router.post("/plans/preview", status_code=status.HTTP_200_OK)
async def validate_and_preview_plan(
    req: PlanIdRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Validates permissions, dependencies, inputs, and approvals; returns plan preview."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdaptiveWorkflowEngineService(db)
    return await service.validate_and_preview_plan(plan_id=req.plan_id, organization_id=org_id, user=current_user)

@router.post("/execute-step", status_code=status.HTTP_200_OK)
async def execute_workflow_step(
    req: ExecuteStepRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Advances workflow and step lifecycle states with output validation and audit tracing."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdaptiveWorkflowEngineService(db)
    return await service.execute_workflow_step(
        plan_id=req.plan_id,
        step_id=req.step_id,
        action=req.action,
        organization_id=org_id,
        user=current_user
    )

@router.post("/exceptions/handle", status_code=status.HTTP_200_OK)
async def handle_workflow_exception(
    req: HandleExceptionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Manages WorkflowException classification, recovery actions, and compensating actions."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdaptiveWorkflowEngineService(db)
    return await service.handle_workflow_exception(
        plan_id=req.plan_id,
        step_id=req.step_id,
        error_message=req.error_message,
        organization_id=org_id,
        user=current_user
    )

@router.post("/dry-run", status_code=status.HTTP_200_OK)
async def dry_run_workflow(
    req: PlanIdRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulates workflow execution trace without production mutation."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdaptiveWorkflowEngineService(db)
    return await service.dry_run_workflow(plan_id=req.plan_id, organization_id=org_id, user=current_user)

@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_plan_vs_actual(
    req: PlanIdRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compares planned vs actual execution, deviation analysis, and outcome evidence."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdaptiveWorkflowEngineService(db)
    return await service.evaluate_plan_vs_actual(plan_id=req.plan_id, organization_id=org_id, user=current_user)
