from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .decision_intelligence_service import DecisionIntelligenceService

router = APIRouter(prefix="/decision-intelligence", tags=["Decision Intelligence, Organizational Reasoning & Actionable Knowledge"])

class CreateDecisionWorkspaceRequest(BaseModel):
    question: str
    project_id: str
    scope: Optional[str] = None
    constraints: Optional[List[str]] = None

class AddEvidenceRequest(BaseModel):
    source_entity_id: str
    source_entity_type: str
    title: str
    category: str = "CURRENT"
    governance_status: str = "APPROVED"
    content_snippet: str = ""

class AddAlternativeRequest(BaseModel):
    title: str
    security_score: str = "HIGH"
    cost: str = "LOW"
    complexity: str = "LOW"
    timeline: str = "1 Week"

class FinalizeDecisionRequest(BaseModel):
    selected_option_id: str
    selected_option_title: str
    rationale: str
    user_override_reason: Optional[str] = None

class CreateRetrospectiveRequest(BaseModel):
    expected_outcome: str
    actual_outcome: str
    outcome_status: str = "SUCCESSFUL"
    lessons_learned: Optional[List[str]] = None

@router.post("/workspaces", status_code=status.HTTP_200_OK)
async def create_decision_workspace(
    req: CreateDecisionWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Initialize a Decision Workspace."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = DecisionIntelligenceService(db)
    return await service.create_decision_workspace(
        question=req.question,
        project_id=p_uuid,
        scope=req.scope,
        constraints=req.constraints,
        user=current_user
    )

@router.get("/workspaces/{workspace_id}", status_code=status.HTTP_200_OK)
async def get_decision_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve decision workspace details."""
    service = DecisionIntelligenceService(db)
    return await service.get_decision_workspace(workspace_id=workspace_id, user=current_user)

@router.post("/workspaces/{workspace_id}/evidence", status_code=status.HTTP_200_OK)
async def add_evidence(
    workspace_id: str,
    req: AddEvidenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Attach authorized evidence to decision workspace."""
    service = DecisionIntelligenceService(db)
    return await service.add_evidence(
        workspace_id=workspace_id,
        source_entity_id=req.source_entity_id,
        source_entity_type=req.source_entity_type,
        title=req.title,
        category=req.category,
        governance_status=req.governance_status,
        content_snippet=req.content_snippet,
        user=current_user
    )

@router.post("/workspaces/{workspace_id}/alternatives", status_code=status.HTTP_200_OK)
async def add_alternative(
    workspace_id: str,
    req: AddAlternativeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Add decision alternative."""
    service = DecisionIntelligenceService(db)
    return await service.add_alternative(
        workspace_id=workspace_id,
        title=req.title,
        security_score=req.security_score,
        cost=req.cost,
        complexity=req.complexity,
        timeline=req.timeline,
        user=current_user
    )

@router.get("/workspaces/{workspace_id}/recommendation", status_code=status.HTTP_200_OK)
async def generate_recommendation(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluate evidence-grounded recommendation."""
    service = DecisionIntelligenceService(db)
    return await service.generate_recommendation(workspace_id=workspace_id, user=current_user)

@router.post("/workspaces/{workspace_id}/finalize", status_code=status.HTTP_200_OK)
async def finalize_decision(
    workspace_id: str,
    req: FinalizeDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Finalize and approve decision."""
    service = DecisionIntelligenceService(db)
    return await service.finalize_decision(
        workspace_id=workspace_id,
        selected_option_id=req.selected_option_id,
        selected_option_title=req.selected_option_title,
        rationale=req.rationale,
        user_override_reason=req.user_override_reason,
        user=current_user
    )

@router.post("/workspaces/{workspace_id}/retrospective", status_code=status.HTTP_200_OK)
async def create_retrospective(
    workspace_id: str,
    req: CreateRetrospectiveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Record decision retrospective."""
    service = DecisionIntelligenceService(db)
    return await service.create_retrospective(
        workspace_id=workspace_id,
        expected_outcome=req.expected_outcome,
        actual_outcome=req.actual_outcome,
        outcome_status=req.outcome_status,
        lessons_learned=req.lessons_learned,
        user=current_user
    )
