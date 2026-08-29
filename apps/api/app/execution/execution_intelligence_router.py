from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .execution_intelligence_service import ExecutionIntelligenceService

router = APIRouter(prefix="/execution-intelligence", tags=["Execution Intelligence, Workflow Orchestration & Closed-Loop Action"])

class CreateActionPlanRequest(BaseModel):
    decision_id: str
    project_id: str
    objective: str
    expected_outcome: str
    success_criteria: Optional[List[str]] = None

class RecordClosedLoopOutcomeRequest(BaseModel):
    expected_outcome: str
    actual_outcome: str

@router.post("/action-plans", status_code=status.HTTP_200_OK)
async def create_action_plan(
    req: CreateActionPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Convert finalized decision into Action Plan."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ExecutionIntelligenceService(db)
    return await service.create_action_plan(
        decision_id=req.decision_id,
        project_id=p_uuid,
        objective=req.objective,
        expected_outcome=req.expected_outcome,
        success_criteria=req.success_criteria,
        user=current_user
    )

@router.get("/action-plans/{plan_id}", status_code=status.HTTP_200_OK)
async def get_action_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve Action Plan details."""
    service = ExecutionIntelligenceService(db)
    return await service.get_action_plan(plan_id=plan_id, user=current_user)

@router.post("/action-plans/{plan_id}/tasks/suggest", status_code=status.HTTP_200_OK)
async def suggest_tasks(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate suggested tasks with SUGGESTED status."""
    service = ExecutionIntelligenceService(db)
    return await service.suggest_tasks(plan_id=plan_id, user=current_user)

@router.post("/action-plans/{plan_id}/tasks/confirm", status_code=status.HTTP_200_OK)
async def confirm_task(
    plan_id: str,
    suggested_task_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Confirm suggested task into active task."""
    service = ExecutionIntelligenceService(db)
    return await service.confirm_task(suggested_task_id=suggested_task_id, user=current_user)

@router.get("/blockers", status_code=status.HTTP_200_OK)
async def detect_blockers(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Detect blockers and dependency issues."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ExecutionIntelligenceService(db)
    return await service.detect_blockers(project_id=p_uuid, user=current_user)

@router.get("/critical-path", status_code=status.HTTP_200_OK)
async def get_critical_path(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluate task dependencies and Critical Path."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ExecutionIntelligenceService(db)
    return await service.get_critical_path(project_id=p_uuid, user=current_user)

@router.post("/closed-loop/outcomes", status_code=status.HTTP_200_OK)
async def record_closed_loop_outcome(
    plan_id: str = Query(...),
    req: RecordClosedLoopOutcomeRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Record closed-loop outcome discrepancy."""
    if not req:
        raise HTTPException(status_code=400, detail="Request body required")
    service = ExecutionIntelligenceService(db)
    return await service.record_closed_loop_outcome(
        plan_id=plan_id,
        expected_outcome=req.expected_outcome,
        actual_outcome=req.actual_outcome,
        user=current_user
    )

@router.get("/pending-actions", status_code=status.HTTP_200_OK)
async def get_pending_actions(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get prepared actions awaiting human confirmation."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ExecutionIntelligenceService(db)
    return await service.get_pending_actions(project_id=p_uuid, user=current_user)
