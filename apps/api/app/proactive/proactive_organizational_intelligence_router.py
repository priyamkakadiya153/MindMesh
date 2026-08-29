from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .proactive_organizational_intelligence_service import ProactiveOrganizationalIntelligenceService

router = APIRouter(prefix="/proactive-intelligence", tags=["Proactive Organizational Intelligence & Anticipatory Decision Support"])

class ScanRequest(BaseModel):
    project_id: str

class ActionRequest(BaseModel):
    insight_id: str
    action_type: str

class DismissRequest(BaseModel):
    insight_id: str
    reason: Optional[str] = None

@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_proactive_dashboard(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active proactive insights categorized by severity."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.get_proactive_dashboard(organization_id=org_id, user=current_user)

@router.get("/brief", status_code=status.HTTP_200_OK)
async def generate_daily_brief(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compile role-aware daily intelligence brief."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.generate_daily_brief(organization_id=org_id, user=current_user)

@router.post("/scan", status_code=status.HTTP_200_OK)
async def scan_system_signals(
    req: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Monitor system events and generate prioritized insight candidates."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.scan_system_signals(project_id=p_uuid, user=current_user)

@router.post("/action", status_code=status.HTTP_200_OK)
async def handle_insight_action(
    req: ActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Process user action on proactive insight."""
    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.handle_insight_action(insight_id=req.insight_id, action_type=req.action_type, user=current_user)

@router.post("/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_insight(
    req: DismissRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss proactive insight cleanly with feedback."""
    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.handle_insight_action(insight_id=req.insight_id, action_type="DISMISS", user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_proactive_digest(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve proactive intelligence digest metrics."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProactiveOrganizationalIntelligenceService(db)
    return await service.get_proactive_digest(organization_id=org_id, user=current_user)
