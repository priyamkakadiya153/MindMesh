from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_automation_adaptive_learning_service import KnowledgeAutomationAdaptiveLearningService

router = APIRouter(prefix="/adaptive-learning", tags=["Knowledge Automation, Continuous Learning & Adaptive Intelligence"])

class RecordLearningEventRequest(BaseModel):
    event_type: str
    scope: str
    payload: Dict[str, Any]

class ReviewActionRequest(BaseModel):
    item_id: str
    action: str

class RevalidateRequest(BaseModel):
    document_id: str

class PromoteAutomationRequest(BaseModel):
    rule_name: str

@router.post("/events", status_code=status.HTTP_200_OK)
async def record_learning_event(
    req: RecordLearningEventRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Captures explicit/implicit feedback, human corrections, and outcome signals."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.record_learning_event(event_type=req.event_type, scope=req.scope, payload=req.payload, user=current_user, organization_id=org_id)

@router.get("/review-queue", status_code=status.HTTP_200_OK)
async def get_learning_review_queue(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves learning signals requiring human review before organization-wide promotion."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.get_learning_review_queue(organization_id=org_id, user=current_user)

@router.post("/review-action", status_code=status.HTTP_200_OK)
async def validate_learning_signal(
    req: ReviewActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approves, rejects, modifies, or expires learning signals."""
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.validate_learning_signal(item_id=req.item_id, action=req.action, user=current_user)

@router.post("/revalidate", status_code=status.HTTP_200_OK)
async def revalidate_knowledge_on_source_change(
    req: RevalidateRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Revalidates dependent knowledge when source documents change."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.revalidate_knowledge_on_source_change(document_id=req.document_id, organization_id=org_id)

@router.get("/impact-preview", status_code=status.HTTP_200_OK)
async def evaluate_downstream_impact(
    knowledge_id: str = Query(..., description="Knowledge UUID/ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Renders impact graph preview (Knowledge -> Decision -> Task -> Workflow)."""
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.evaluate_downstream_impact(knowledge_id=knowledge_id, user=current_user)

@router.get("/shadow-automation", status_code=status.HTTP_200_OK)
async def evaluate_shadow_automation(
    rule_name: str = Query(..., description="Shadow Rule Name"),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulates candidate automations in shadow mode without side effects."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.evaluate_shadow_automation(candidate_rule_name=rule_name, organization_id=org_id)

@router.post("/promote-automation", status_code=status.HTTP_200_OK)
async def promote_automation_rule(
    req: PromoteAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Promotes validated shadow automations to active execution with rollback metadata."""
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.promote_automation_rule(rule_name=req.rule_name, user=current_user)

@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_adaptive_intelligence_dashboard(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns telemetry on signal quality, active experiments, drift alerts, and learning audit history."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeAutomationAdaptiveLearningService(db)
    return await service.get_adaptive_intelligence_dashboard(organization_id=org_id, user=current_user)
