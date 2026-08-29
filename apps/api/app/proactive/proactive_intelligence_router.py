from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .proactive_intelligence_service import ProactiveIntelligenceService

router = APIRouter(prefix="/proactive-intelligence", tags=["Proactive Intelligence, Early Warning & Organizational Awareness"])

class ReportMissedInsightRequest(BaseModel):
    description: str
    project_id: str

class DismissInsightRequest(BaseModel):
    reason: Optional[str] = None

@router.get("/insights", status_code=status.HTTP_200_OK)
async def get_proactive_insights(
    scope: str = Query("PROJECT"),
    project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve scoped proactive insights feed."""
    service = ProactiveIntelligenceService(db)
    return await service.get_proactive_insights(scope=scope, project_id=project_id, user=current_user)

@router.post("/insights/scan-drift", status_code=status.HTTP_200_OK)
async def scan_knowledge_drift(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Scan documents and tasks for Knowledge & Decision Drift."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ProactiveIntelligenceService(db)
    return await service.scan_knowledge_drift(project_id=p_uuid, user=current_user)

@router.post("/insights/{insight_id}/acknowledge", status_code=status.HTTP_200_OK)
async def acknowledge_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Acknowledge a proactive insight."""
    service = ProactiveIntelligenceService(db)
    return await service.acknowledge_insight(insight_id=insight_id, user=current_user)

@router.post("/insights/{insight_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_insight(
    insight_id: str,
    req: Optional[DismissInsightRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss a proactive insight."""
    service = ProactiveIntelligenceService(db)
    return await service.dismiss_insight(insight_id=insight_id, reason=req.reason if req else None, user=current_user)

@router.get("/emerging-patterns", status_code=status.HTTP_200_OK)
async def detect_emerging_patterns(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Detect emerging organizational patterns across projects."""
    if not org_id:
        org_id = UUID("7bd93237-c297-4007-a84b-04df57601a44")
    service = ProactiveIntelligenceService(db)
    return await service.detect_emerging_patterns(organization_id=org_id, user=current_user)

@router.post("/report-missed-insight", status_code=status.HTTP_200_OK)
async def report_missed_insight(
    req: ReportMissedInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Report a missed insight for organizational learning feedback."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ProactiveIntelligenceService(db)
    return await service.report_missed_insight(description=req.description, project_id=p_uuid, user=current_user)

@router.get("/project-health", status_code=status.HTTP_200_OK)
async def get_project_health(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve proactive project health indicators."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ProactiveIntelligenceService(db)
    return await service.get_project_health(project_id=p_uuid, user=current_user)
