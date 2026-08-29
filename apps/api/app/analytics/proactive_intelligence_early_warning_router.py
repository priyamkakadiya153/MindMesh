from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .proactive_intelligence_early_warning_service import ProactiveIntelligenceEarlyWarningService

router = APIRouter(prefix="/proactive-intelligence", tags=["Proactive Intelligence, Predictive Understanding & Early-Warning System"])

class ManageSignalRequest(BaseModel):
    signal_id: str
    action: str
    reason: Optional[str] = None

class WhatIfRequest(BaseModel):
    scenario_name: str
    parameters: Dict[str, Any]

@router.get("/signals", status_code=status.HTTP_200_OK)
async def get_proactive_signals(
    project_id: Optional[str] = None,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Monitors authorized changes and surfaces correlated proactive signals."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(project_id) if project_id else None
    service = ProactiveIntelligenceEarlyWarningService(db)
    return await service.detect_and_correlate_proactive_signals(project_id=proj_uuid, organization_id=org_id, user=current_user)

@router.post("/manage-signal", status_code=status.HTTP_200_OK)
async def manage_signal_status(
    req: ManageSignalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Manages signal states (ACKNOWLEDGE, SNOOZE, DISMISS, RESOLVE)."""
    service = ProactiveIntelligenceEarlyWarningService(db)
    return await service.manage_signal_status(signal_id=req.signal_id, action=req.action, reason=req.reason, user=current_user)

@router.post("/what-if", status_code=status.HTTP_200_OK)
async def run_what_if_scenario(
    req: WhatIfRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulates hypothetical changes without mutating production state."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveIntelligenceEarlyWarningService(db)
    return await service.run_what_if_scenario(scenario_name=req.scenario_name, parameters=req.parameters, organization_id=org_id, user=current_user)

@router.get("/briefing", status_code=status.HTTP_200_OK)
async def generate_proactive_briefing(
    type: str = Query("MORNING"),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Produces personalized briefings with recommended next actions."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveIntelligenceEarlyWarningService(db)
    return await service.generate_proactive_briefing(briefing_type=type, organization_id=org_id, user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def generate_proactive_digest(
    frequency: str = Query("DAILY"),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates daily/weekly digests with trends and knowledge changes."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveIntelligenceEarlyWarningService(db)
    return await service.generate_proactive_digest(digest_frequency=frequency, organization_id=org_id, user=current_user)
