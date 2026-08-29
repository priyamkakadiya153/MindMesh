from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_simulation_service import OrganizationalSimulationService

router = APIRouter(prefix="/simulation", tags=["Organizational Simulation, Digital Twin & What-If Intelligence"])

class CreateScenarioRequest(BaseModel):
    name: str
    natural_language_request: Optional[str] = None
    changes: List[Dict[str, Any]] = []

class RunSimulationRequest(BaseModel):
    scenario_id: str

class CompareScenariosRequest(BaseModel):
    scenario_ids: List[str]

class HandoffScenarioRequest(BaseModel):
    scenario_id: str
    is_stale: bool = False

@router.get("/digital-twin", status_code=status.HTTP_200_OK)
async def get_digital_twin_snapshot(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Constructs TwinSnapshot representing current projects, tasks, dependencies, risks, controls, and workflows."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalSimulationService(db)
    return await service.get_digital_twin_snapshot(organization_id=org_id, user=current_user)

@router.post("/scenarios/create", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    req: CreateScenarioRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Parses natural language what-if request or structured changes into a Scenario object with explicit assumptions."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalSimulationService(db)
    return await service.create_scenario(
        name=req.name,
        natural_language_request=req.natural_language_request,
        changes=req.changes,
        organization_id=org_id,
        user=current_user
    )

@router.post("/scenarios/run", status_code=status.HTTP_200_OK)
async def run_simulation(
    req: RunSimulationRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Runs What-If Engine, propagates downstream impacts via Graph Intelligence, and calculates range-first deltas."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalSimulationService(db)
    return await service.run_simulation(
        scenario_id=req.scenario_id,
        organization_id=org_id,
        user=current_user
    )

@router.post("/scenarios/compare", status_code=status.HTTP_200_OK)
async def compare_scenarios(
    req: CompareScenariosRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs side-by-side multi-objective scenario comparison (Option A vs Option B)."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalSimulationService(db)
    return await service.compare_scenarios(
        scenario_ids=req.scenario_ids,
        organization_id=org_id,
        user=current_user
    )

@router.post("/scenarios/handoff", status_code=status.HTTP_200_OK)
async def handoff_scenario_to_workflow(
    req: HandoffScenarioRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Validates state freshness (detects STALE state if dependencies changed) and hands off approved scenario to Phase 6.27 workflow engine."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalSimulationService(db)
    return await service.handoff_scenario_to_workflow(
        scenario_id=req.scenario_id,
        is_stale=req.is_stale,
        organization_id=org_id,
        user=current_user
    )
