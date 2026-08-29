from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_graph_causal_reasoning_service import OrganizationalGraphCausalReasoningService

router = APIRouter(prefix="/graph-intelligence", tags=["Organizational Graph Intelligence, Causal Context & Systemic Reasoning"])

class GraphQueryRequest(BaseModel):
    center_node_id: Optional[str] = None
    max_depth: int = 2

class ImpactAnalysisRequest(BaseModel):
    node_id: str
    proposed_change: str

class RootCauseRequest(BaseModel):
    symptom_description: str

@router.post("/query", status_code=status.HTTP_200_OK)
async def query_organizational_graph(
    req: GraphQueryRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs authorized multi-hop graph traversal and subgraph filtering."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalGraphCausalReasoningService(db)
    return await service.query_organizational_graph(center_node_id=req.center_node_id, max_depth=req.max_depth, organization_id=org_id, user=current_user)

@router.get("/lineage", status_code=status.HTTP_200_OK)
async def trace_knowledge_and_decision_lineage(
    node_id: str = Query("dec-301"),
    direction: str = Query("BACKWARD"),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Traces forward/backward derivation chains with path explanations."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalGraphCausalReasoningService(db)
    return await service.trace_knowledge_and_decision_lineage(target_node_id=node_id, direction=direction, organization_id=org_id, user=current_user)

@router.post("/impact-analysis", status_code=status.HTTP_200_OK)
async def analyze_change_impact_and_blast_radius(
    req: ImpactAnalysisRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculates blast radius scores and previews affected objects before major changes."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalGraphCausalReasoningService(db)
    return await service.analyze_change_impact_and_blast_radius(node_id=req.node_id, proposed_change=req.proposed_change, organization_id=org_id, user=current_user)

@router.post("/root-cause", status_code=status.HTTP_200_OK)
async def perform_root_cause_analysis(
    req: RootCauseRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Formulates explainable causal hypotheses separating connection from causation."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalGraphCausalReasoningService(db)
    return await service.perform_root_cause_analysis(symptom_description=req.symptom_description, organization_id=org_id, user=current_user)

@router.get("/bottlenecks", status_code=status.HTTP_200_OK)
async def detect_systemic_bottlenecks_and_risks(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Identifies shared dependencies, knowledge concentration ("Bus Factor"), and cross-project systemic risks."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalGraphCausalReasoningService(db)
    return await service.detect_systemic_bottlenecks_and_risks(organization_id=org_id, user=current_user)
