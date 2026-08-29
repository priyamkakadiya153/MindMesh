from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .memory_orchestrator_service import OrganizationalMemoryOrchestrator

router = APIRouter(prefix="/memory-orchestration", tags=["Organizational Memory Orchestration & Knowledge Graph Intelligence"])

class ImpactAnalysisRequest(BaseModel):
    event_type: str
    source_entity_id: str

class SimulateImpactRequest(BaseModel):
    hypothetical_change: str
    source_entity_id: str

class MemoryDiffRequest(BaseModel):
    topic: str
    date_a: str
    date_b: str

@router.post("/impact-analysis", status_code=status.HTTP_200_OK)
async def analyze_event_impact(
    req: ImpactAnalysisRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluate event impact across graph dependencies."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.analyze_event_impact(
        event_type=req.event_type,
        source_entity_id=req.source_entity_id,
        organization_id=org_id,
        user=current_user
    )

@router.get("/dependencies", status_code=status.HTTP_200_OK)
async def get_dependency_map(
    entity_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace Upstream dependencies and Downstream impact."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.get_dependency_map(entity_id=entity_id, user=current_user)

@router.get("/knowledge-flow", status_code=status.HTTP_200_OK)
async def get_knowledge_flow(
    entity_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace real knowledge movement history."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.get_knowledge_flow(entity_id=entity_id, user=current_user)

@router.get("/clusters", status_code=status.HTTP_200_OK)
async def get_knowledge_clusters(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Consolidate multi-source entities into conceptual clusters."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.get_knowledge_clusters(organization_id=org_id, user=current_user)

@router.get("/patterns", status_code=status.HTTP_200_OK)
async def get_organizational_patterns(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Derive observed organizational patterns."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.get_organizational_patterns(organization_id=org_id, user=current_user)

@router.post("/simulate-impact", status_code=status.HTTP_200_OK)
async def simulate_impact(
    req: SimulateImpactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Simulate potential downstream impact of hypothetical changes."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.simulate_impact(
        hypothetical_change=req.hypothetical_change,
        source_entity_id=req.source_entity_id,
        user=current_user
    )

@router.get("/brief", status_code=status.HTTP_200_OK)
async def get_memory_brief(
    topic: str = Query(...),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate source-grounded Memory Brief for a topic."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.get_memory_brief(topic=topic, organization_id=org_id, user=current_user)

@router.post("/memory-diff", status_code=status.HTTP_200_OK)
async def compare_memory_state(
    req: MemoryDiffRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compute Then vs Now Memory Diff between two dates."""
    orchestrator = OrganizationalMemoryOrchestrator(db)
    return await orchestrator.compare_memory_state(topic=req.topic, date_a=req.date_a, date_b=req.date_b, user=current_user)
