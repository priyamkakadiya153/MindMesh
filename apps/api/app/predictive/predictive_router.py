from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .predictive_service import PredictiveIntelligenceService

router = APIRouter(prefix="/predictive", tags=["Predictive Project Intelligence & Decision Support"])

class WhatIfRequest(BaseModel):
    scenario: str
    project_id: Optional[str] = None

class DecisionBriefRequest(BaseModel):
    topic: str

@router.get("/early-warnings", status_code=status.HTTP_200_OK)
async def get_early_warnings(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active early warning prediction alerts."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = PredictiveIntelligenceService(db)
    return await service.get_early_warnings(user=current_user, organization_id=org_id, project_id=p_uuid)

@router.get("/decision-impact/{decision_id}", status_code=status.HTTP_200_OK)
async def get_decision_impact(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace downstream impact path (Decision -> Document -> Task -> Deployment)."""
    service = PredictiveIntelligenceService(db)
    return await service.get_decision_impact(decision_id=decision_id)

@router.post("/what-if", status_code=status.HTTP_200_OK)
async def perform_what_if_analysis(
    req: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulate scenario consequences and identify known vs unknown impacts."""
    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = PredictiveIntelligenceService(db)
    return await service.perform_what_if_analysis(scenario=req.scenario, project_id=p_uuid)

@router.get("/project-readiness/{project_id}", status_code=status.HTTP_200_OK)
async def get_project_readiness(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve project release readiness assessment."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = PredictiveIntelligenceService(db)
    return await service.get_project_readiness(project_id=p_uuid)

@router.post("/decision-brief", status_code=status.HTTP_200_OK)
async def generate_decision_brief(
    req: DecisionBriefRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Produce source-backed Decision Brief with trade-off option matrix."""
    service = PredictiveIntelligenceService(db)
    return await service.generate_decision_brief(topic=req.topic)

@router.post("/rebuild-predictions", status_code=status.HTTP_200_OK)
async def rebuild_predictions(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently reconstruct predictive insights from primary database records."""
    service = PredictiveIntelligenceService(db)
    return await service.rebuild_predictions(organization_id=org_id)
