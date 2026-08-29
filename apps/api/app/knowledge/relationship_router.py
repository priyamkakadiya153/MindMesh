from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .relationship_service import KnowledgeGraphRelationshipIntelligenceService

router = APIRouter(prefix="/knowledge/relationship", tags=["Knowledge Graph & Relationship Intelligence"])

@router.get("/explorer", status_code=status.HTTP_200_OK)
async def get_graph_explorer(
    entity_id: str = Query(..., description="Entity UUID to explore neighborhood"),
    depth: int = Query(1, ge=1, le=3),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve graph neighborhood (1-hop / 2-hop) for an entity."""
    try:
        e_uuid = UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID format")

    service = KnowledgeGraphRelationshipIntelligenceService(db)
    return await service.get_graph_neighborhood(organization_id=org_id, entity_id=e_uuid, depth=depth)

@router.get("/impact-analysis", status_code=status.HTTP_200_OK)
async def analyze_decision_impact(
    decision_id: str = Query(..., description="Decision UUID to analyze forward impact"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute multi-hop forward impact analysis for a decision."""
    try:
        d_uuid = UUID(decision_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision UUID format")

    service = KnowledgeGraphRelationshipIntelligenceService(db)
    return await service.analyze_decision_impact(organization_id=org_id, decision_id=d_uuid)

@router.get("/origin-trace", status_code=status.HTTP_200_OK)
async def trace_decision_origin(
    decision_id: str = Query(..., description="Decision UUID to trace origin source"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace decision origin back to conversation/meeting source."""
    try:
        d_uuid = UUID(decision_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision UUID format")

    service = KnowledgeGraphRelationshipIntelligenceService(db)
    return await service.trace_decision_origin(organization_id=org_id, decision_id=d_uuid)

@router.get("/health", status_code=status.HTTP_200_OK)
async def audit_graph_health(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Audit Knowledge Graph health and broken links."""
    service = KnowledgeGraphRelationshipIntelligenceService(db)
    return await service.audit_graph_health(organization_id=org_id)

@router.post("/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_graph_relationships(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Rebuild graph relationships idempotently from application data."""
    service = KnowledgeGraphRelationshipIntelligenceService(db)
    return await service.rebuild_graph_relationships(organization_id=org_id)
