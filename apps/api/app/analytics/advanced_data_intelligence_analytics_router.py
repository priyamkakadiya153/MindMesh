from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .advanced_data_intelligence_analytics_service import AdvancedDataIntelligenceAnalyticsService

router = APIRouter(prefix="/data-intelligence", tags=["Advanced Data Intelligence, Analytics & Organizational Insight"])

@router.get("/project-health/{project_id}", status_code=status.HTTP_200_OK)
async def get_project_intelligence(
    project_id: UUID,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluates project health signals, trend direction, and change explanations."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.get_project_intelligence(project_id=project_id, organization_id=org_id, user=current_user)

@router.get("/knowledge-health", status_code=status.HTTP_200_OK)
async def get_knowledge_health_analytics(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Analyzes freshness, coverage, verification state, zero-result searches, and unresolved conflicts."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.get_knowledge_health_analytics(organization_id=org_id, user=current_user)

@router.get("/bottlenecks", status_code=status.HTTP_200_OK)
async def detect_bottlenecks_and_dependencies(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Identifies work accumulation points, task blockers, decision bottlenecks, and shared dependency risks."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.detect_bottlenecks_and_dependencies(organization_id=org_id, user=current_user)

@router.get("/trends-anomalies", status_code=status.HTTP_200_OK)
async def detect_trends_anomalies_patterns(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Detects statistical trends, activity anomalies, and recurring organizational patterns."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.detect_trends_anomalies_patterns(organization_id=org_id, user=current_user)

@router.get("/portfolio", status_code=status.HTTP_200_OK)
async def get_portfolio_analytics(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates executive portfolio view showing health, risks, progress, and dependencies."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.get_portfolio_analytics(organization_id=org_id, user=current_user)

@router.get("/drilldown/{insight_id}", status_code=status.HTTP_200_OK)
async def get_drilldown_evidence(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Provides security-enforced drill-down evidence for any analytical insight."""
    service = AdvancedDataIntelligenceAnalyticsService(db)
    return await service.get_drilldown_evidence(insight_id=insight_id, user=current_user)
