from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_knowledge_graph_service import OrganizationalKnowledgeGraphService

router = APIRouter(prefix="/org-knowledge-graph", tags=["Organizational Knowledge Graph, Causal Intelligence & System-Wide Reasoning"])

class PathFindingRequest(BaseModel):
    source_id: str
    target_id: str

class ImpactSimulationRequest(BaseModel):
    entity_id: str

class RootCauseRequest(BaseModel):
    incident_id: str

@router.get("/explorer", status_code=status.HTTP_200_OK)
async def get_graph_subgraph(
    project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve focused graph subgraph."""
    p_uuid = None
    if project_id and project_id.strip():
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            p_uuid = None

    service = OrganizationalKnowledgeGraphService(db)
    return await service.get_graph_subgraph(project_id=p_uuid, user=current_user)

@router.post("/path-finding", status_code=status.HTTP_200_OK)
async def find_explainable_path(
    req: PathFindingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Find explainable relationship path."""
    service = OrganizationalKnowledgeGraphService(db)
    return await service.find_explainable_path(source_id=req.source_id, target_id=req.target_id, user=current_user)

@router.post("/simulate-impact", status_code=status.HTTP_200_OK)
async def simulate_change_impact(
    req: ImpactSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate non-destructive change impact blast radius."""
    service = OrganizationalKnowledgeGraphService(db)
    return await service.simulate_change_impact(entity_id=req.entity_id, user=current_user)

@router.post("/root-cause-analysis", status_code=status.HTTP_200_OK)
async def perform_root_cause_analysis(
    req: RootCauseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Perform systemic root cause tree analysis."""
    service = OrganizationalKnowledgeGraphService(db)
    return await service.perform_root_cause_analysis(incident_id=req.incident_id, user=current_user)

@router.get("/bottlenecks", status_code=status.HTTP_200_OK)
async def detect_system_bottlenecks(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Detect bottlenecks and knowledge fragility points."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalKnowledgeGraphService(db)
    return await service.detect_system_bottlenecks(organization_id=org_id, user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_graph_digest(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve organizational graph summary digest."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalKnowledgeGraphService(db)
    return await service.get_graph_digest(organization_id=org_id, user=current_user)
