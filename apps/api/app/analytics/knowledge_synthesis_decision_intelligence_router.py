from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_synthesis_decision_intelligence_service import KnowledgeSynthesisDecisionIntelligenceService

router = APIRouter(prefix="/decision-intelligence", tags=["Knowledge Synthesis, Organizational Reasoning & Decision Intelligence"])

class SynthesizeRequest(BaseModel):
    project_id: Optional[str] = None

class CandidateRequest(BaseModel):
    project_id: Optional[str] = None
    topic_description: str

class CompareOptionsRequest(BaseModel):
    candidate_id: str
    options: List[Dict[str, Any]]

class RecordDecisionRequest(BaseModel):
    decision_question: str
    chosen_option_id: str
    rationale: str
    supersedes_decision_id: Optional[str] = None

class EvaluateOutcomeRequest(BaseModel):
    decision_id: str
    actual_outcome: str

@router.post("/synthesize", status_code=status.HTTP_200_OK)
async def synthesize_knowledge_and_evidence(
    req: SynthesizeRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Combines authorized sources into evidence bundles with claim provenance and surfaces conflicts."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = KnowledgeSynthesisDecisionIntelligenceService(db)
    return await service.synthesize_knowledge_and_evidence(scope_project_id=proj_uuid, organization_id=org_id, user=current_user)

@router.post("/candidates", status_code=status.HTTP_200_OK)
async def evaluate_decision_candidate(
    req: CandidateRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Formulates decision questions, readiness statuses, constraints, and missing evidence gaps."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = KnowledgeSynthesisDecisionIntelligenceService(db)
    return await service.evaluate_decision_candidate(project_id=proj_uuid, topic_description=req.topic_description, organization_id=org_id, user=current_user)

@router.post("/compare-options", status_code=status.HTTP_200_OK)
async def compare_decision_options_and_tradeoffs(
    req: CompareOptionsRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluates options across criteria, calculates weighted decision matrices, checks constraint feasibility, and runs sensitivity analysis."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeSynthesisDecisionIntelligenceService(db)
    return await service.compare_decision_options_and_tradeoffs(candidate_id=req.candidate_id, options=req.options, organization_id=org_id, user=current_user)

@router.post("/record", status_code=status.HTTP_200_OK)
async def record_and_version_decision(
    req: RecordDecisionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Records decisions with immutable rationale, tracks decision versions and supersession, and generates draft Decision Briefs."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeSynthesisDecisionIntelligenceService(db)
    return await service.record_and_version_decision(
        decision_question=req.decision_question,
        chosen_option_id=req.chosen_option_id,
        rationale=req.rationale,
        supersedes_decision_id=req.supersedes_decision_id,
        organization_id=org_id,
        user=current_user
    )

@router.post("/evaluate-outcome", status_code=status.HTTP_200_OK)
async def evaluate_decision_outcome_and_effectiveness(
    req: EvaluateOutcomeRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compares Expected vs Actual outcomes, evaluates decision effectiveness, and feeds outcome signals to Phase 6.20."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeSynthesisDecisionIntelligenceService(db)
    return await service.evaluate_decision_outcome_and_effectiveness(decision_id=req.decision_id, actual_outcome=req.actual_outcome, organization_id=org_id, user=current_user)
