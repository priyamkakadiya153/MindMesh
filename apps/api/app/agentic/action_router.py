from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .action_service import AgenticActionOrchestratorService

router = APIRouter(prefix="/agentic", tags=["Agentic Action & Controlled Execution"])

class ProposePlanRequest(BaseModel):
    goal: str
    project_id: Optional[str] = None

class ApproveActionRequest(BaseModel):
    plan_id: str
    action_id: str

@router.post("/propose-plan", status_code=status.HTTP_200_OK)
async def propose_action_plan(
    req: ProposePlanRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Propose a multi-step action plan for a natural language goal."""
    if not req.goal.strip():
        raise HTTPException(status_code=400, detail="Goal string cannot be empty")

    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = AgenticActionOrchestratorService(db)
    return await service.propose_action_plan(user=current_user, organization_id=org_id, goal=req.goal, project_id=p_uuid)

@router.get("/pending-approvals", status_code=status.HTTP_200_OK)
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve actions currently awaiting human approval."""
    service = AgenticActionOrchestratorService(db)
    return await service.get_pending_approvals(user=current_user, organization_id=org_id)

@router.post("/approve-action", status_code=status.HTTP_200_OK)
async def approve_action(
    req: ApproveActionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve and execute a specific action."""
    service = AgenticActionOrchestratorService(db)
    return await service.approve_action(user=current_user, organization_id=org_id, plan_id=req.plan_id, action_id=req.action_id)

@router.post("/reject-action", status_code=status.HTTP_200_OK)
async def reject_action(
    req: ApproveActionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Reject a proposed action."""
    service = AgenticActionOrchestratorService(db)
    return await service.reject_action(user=current_user, organization_id=org_id, plan_id=req.plan_id, action_id=req.action_id)

@router.get("/action-log", status_code=status.HTTP_200_OK)
async def get_action_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve action execution history."""
    service = AgenticActionOrchestratorService(db)
    return await service.get_action_log(user=current_user)
