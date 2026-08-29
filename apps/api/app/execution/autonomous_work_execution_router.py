from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .autonomous_work_execution_service import AutonomousWorkExecutionService

router = APIRouter(prefix="/autonomous-work", tags=["Autonomous Knowledge Operations & Intelligent Work Execution"])

class CreatePlanRequest(BaseModel):
    raw_user_prompt: str
    project_id: Optional[str] = None

class DryRunRequest(BaseModel):
    plan_id: str

class ApprovalActionRequest(BaseModel):
    plan_id: str
    action: str

class ExecuteStepRequest(BaseModel):
    plan_id: str
    step_number: int

class EmergencyStopRequest(BaseModel):
    scope: str

@router.post("/plans", status_code=status.HTTP_200_OK)
async def parse_intent_and_create_plan(
    req: CreatePlanRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Converts raw prompt into structured execution plan with steps and risk levels."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = AutonomousWorkExecutionService(db)
    return await service.parse_intent_and_create_plan(raw_user_prompt=req.raw_user_prompt, project_id=proj_uuid, organization_id=org_id, user=current_user)

@router.post("/dry-run", status_code=status.HTTP_200_OK)
async def execute_dry_run(
    req: DryRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulates plan steps without mutating production state."""
    service = AutonomousWorkExecutionService(db)
    return await service.execute_dry_run(plan_id=req.plan_id, user=current_user)

@router.post("/approval-action", status_code=status.HTTP_200_OK)
async def manage_approval_request(
    req: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Handles explicit human approval gates."""
    service = AutonomousWorkExecutionService(db)
    return await service.manage_approval_request(plan_id=req.plan_id, action=req.action, user=current_user)

@router.post("/execute-step", status_code=status.HTTP_200_OK)
async def execute_plan_step(
    req: ExecuteStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes step via Tool Registry with loop detection."""
    service = AutonomousWorkExecutionService(db)
    return await service.execute_plan_step(plan_id=req.plan_id, step_number=req.step_number, user=current_user)

@router.post("/emergency-stop", status_code=status.HTTP_200_OK)
async def emergency_stop_autonomy(
    req: EmergencyStopRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Triggers immediate global or project-level kill switch for autonomous execution."""
    service = AutonomousWorkExecutionService(db)
    return await service.emergency_stop_autonomy(scope=req.scope, user=current_user)

@router.get("/execution-journal", status_code=status.HTTP_200_OK)
async def get_execution_journal(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns traceable audit execution history."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AutonomousWorkExecutionService(db)
    return await service.get_execution_journal(organization_id=org_id, user=current_user)
