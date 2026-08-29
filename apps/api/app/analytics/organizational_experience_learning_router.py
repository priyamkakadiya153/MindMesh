from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_experience_learning_service import OrganizationalExperienceLearningService

router = APIRouter(prefix="/experience-learning", tags=["Organizational Memory, Experience Learning & Continuous Improvement"])

class CaptureExperienceRequest(BaseModel):
    title: str
    situation: str
    action: str
    outcome: str
    project_id: Optional[str] = None

class OutcomeAttributionRequest(BaseModel):
    project_id: Optional[str] = None
    expected_outcome: str
    actual_outcome: str

class ImprovementRequest(BaseModel):
    problem_description: str
    proposal: str

@router.post("/capture", status_code=status.HTTP_200_OK)
async def capture_experience_record(
    req: CaptureExperienceRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Preserves ExperienceRecord objects with explicit context and validation status."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = OrganizationalExperienceLearningService(db)
    return await service.capture_experience_record(
        title=req.title,
        situation=req.situation,
        action=req.action,
        outcome=req.outcome,
        project_id=proj_uuid,
        organization_id=org_id,
        user=current_user
    )

@router.post("/outcomes", status_code=status.HTTP_200_OK)
async def analyze_outcome_attribution(
    req: OutcomeAttributionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Captures Expected vs Actual outcomes with evidence attribution."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = OrganizationalExperienceLearningService(db)
    return await service.analyze_outcome_attribution(
        project_id=proj_uuid,
        expected_outcome=req.expected_outcome,
        actual_outcome=req.actual_outcome,
        organization_id=org_id,
        user=current_user
    )

@router.post("/lessons-patterns", status_code=status.HTTP_200_OK)
async def extract_lessons_and_patterns(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Extracts lessons and detects cross-project patterns."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalExperienceLearningService(db)
    return await service.extract_lessons_and_patterns(organization_id=org_id, user=current_user)

@router.post("/playbooks", status_code=status.HTTP_200_OK)
async def generate_playbook_and_retrospective(
    project_id: Optional[str] = None,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates draft Retrospectives separating facts from opinions and builds validated Playbooks."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(project_id) if project_id else None
    service = OrganizationalExperienceLearningService(db)
    return await service.generate_playbook_and_retrospective(project_id=proj_uuid, organization_id=org_id, user=current_user)

@router.post("/improvements", status_code=status.HTTP_200_OK)
async def manage_continuous_improvement(
    req: ImprovementRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Tracks ImprovementOpportunity items and measures baseline vs target vs actual benefit metrics."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalExperienceLearningService(db)
    return await service.manage_continuous_improvement(problem_description=req.problem_description, proposal=req.proposal, organization_id=org_id, user=current_user)
