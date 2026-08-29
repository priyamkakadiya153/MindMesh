from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_learning_service import OrganizationalLearningService

router = APIRouter(prefix="/learning-feedback", tags=["Organizational Learning, Feedback & Adaptive Intelligence"])

class FeedbackRequest(BaseModel):
    entity_id: str
    entity_type: str
    feedback_type: str
    rating: str
    reason: Optional[str] = None

class ProposeCorrectionRequest(BaseModel):
    source_entity_id: str
    proposed_content: str
    reason: str

class CreatePlaybookRequest(BaseModel):
    title: str
    steps: List[str]

@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Capture explicit/implicit feedback."""
    service = OrganizationalLearningService(db)
    return await service.submit_feedback(
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        feedback_type=req.feedback_type,
        rating=req.rating,
        reason=req.reason,
        user=current_user
    )

@router.post("/corrections", status_code=status.HTTP_200_OK)
async def propose_correction(
    req: ProposeCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit proposed content correction."""
    service = OrganizationalLearningService(db)
    return await service.propose_correction(
        source_entity_id=req.source_entity_id,
        proposed_content=req.proposed_content,
        reason=req.reason,
        user=current_user
    )

@router.post("/corrections/{correction_id}/approve", status_code=status.HTTP_200_OK)
async def approve_correction(
    correction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve proposed correction into a published governed version."""
    service = OrganizationalLearningService(db)
    return await service.approve_correction(correction_id=correction_id, user=current_user)

@router.get("/knowledge-gaps", status_code=status.HTTP_200_OK)
async def get_knowledge_gaps(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detected knowledge gaps."""
    service = OrganizationalLearningService(db)
    return await service.get_knowledge_gaps(organization_id=org_id, user=current_user)

@router.get("/question-clusters", status_code=status.HTTP_200_OK)
async def get_question_clusters(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve question clusters."""
    service = OrganizationalLearningService(db)
    return await service.get_question_clusters(organization_id=org_id, user=current_user)

@router.get("/playbooks", status_code=status.HTTP_200_OK)
async def get_playbooks(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve governed playbooks."""
    service = OrganizationalLearningService(db)
    return await service.get_playbooks(organization_id=org_id, user=current_user)

@router.post("/create-playbook", status_code=status.HTTP_200_OK)
async def create_playbook(
    req: CreatePlaybookRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new governed playbook."""
    service = OrganizationalLearningService(db)
    return await service.create_playbook(title=req.title, steps=req.steps, user=current_user)

@router.get("/analytics", status_code=status.HTTP_200_OK)
async def get_learning_analytics(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve system-level learning metrics."""
    service = OrganizationalLearningService(db)
    return await service.get_learning_analytics(organization_id=org_id)
