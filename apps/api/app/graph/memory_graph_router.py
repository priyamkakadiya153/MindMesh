from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .memory_graph_service import OrganizationalMemoryGraphService

router = APIRouter(prefix="/graph", tags=["Organizational Memory Graph & Knowledge Navigation"])

@router.get("/explore", status_code=status.HTTP_200_OK)
async def explore_graph(
    focus_entity_id: Optional[str] = None,
    focus_entity_type: Optional[str] = None,
    hops: int = Query(2, ge=1, le=3),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Explore connected nodes around a focus entity up to specified hop depth."""
    service = OrganizationalMemoryGraphService(db)
    return await service.explore_graph(
        focus_entity_id=focus_entity_id,
        focus_entity_type=focus_entity_type,
        hops=hops,
        user=current_user,
        organization_id=org_id
    )

@router.get("/lineage/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def trace_lineage(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace backward source provenance."""
    service = OrganizationalMemoryGraphService(db)
    return await service.trace_lineage(entity_type=entity_type, entity_id=entity_id)

@router.get("/impact/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def trace_impact(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace forward downstream impact path."""
    service = OrganizationalMemoryGraphService(db)
    return await service.trace_impact(entity_type=entity_type, entity_id=entity_id)

@router.get("/conflicts", status_code=status.HTTP_200_OK)
async def get_governance_conflicts(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Identify conflicting entity nodes and source trace paths."""
    service = OrganizationalMemoryGraphService(db)
    return await service.get_governance_conflicts(organization_id=org_id)

@router.get("/history/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve entity version timeline and historical graph snapshots."""
    service = OrganizationalMemoryGraphService(db)
    return await service.get_entity_history(entity_type=entity_type, entity_id=entity_id)

@router.post("/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_graph(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently reconstruct graph nodes and relationships from primary database records."""
    service = OrganizationalMemoryGraphService(db)
    return await service.rebuild_graph(organization_id=org_id)
