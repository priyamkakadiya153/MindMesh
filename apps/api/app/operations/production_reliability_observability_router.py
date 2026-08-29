from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .production_reliability_observability_service import ProductionReliabilityObservabilityService

router = APIRouter(prefix="/production-operations", tags=["Reliability, Observability, Self-Healing & Production Operations"])

class CircuitBreakerExecRequest(BaseModel):
    operation_name: str
    simulate_failure: bool = False

class ManageJobRequest(BaseModel):
    job_type: str
    idempotency_key: str
    simulate_permanent_failure: bool = False

class ReplayJobRequest(BaseModel):
    job_id: str

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_liveness(
    db: AsyncSession = Depends(get_db_session)
):
    """Provides fast liveness check: Is this process alive?"""
    service = ProductionReliabilityObservabilityService(db)
    return await service.get_liveness()

@router.get("/readiness", status_code=status.HTTP_200_OK)
async def get_readiness(
    db: AsyncSession = Depends(get_db_session)
):
    """Provides readiness check: Can this service safely receive work?"""
    service = ProductionReliabilityObservabilityService(db)
    return await service.get_readiness()

@router.get("/deep-health", status_code=status.HTTP_200_OK)
async def evaluate_deep_health(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs deep diagnostic health evaluation across dependencies."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProductionReliabilityObservabilityService(db)
    return await service.evaluate_deep_health(organization_id=org_id, user=current_user)

@router.post("/execute-cb", status_code=status.HTTP_200_OK)
async def execute_with_circuit_breaker(
    req: CircuitBreakerExecRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Wraps AI calls in circuit breakers with graceful degradation fallback."""
    service = ProductionReliabilityObservabilityService(db)
    return await service.execute_with_circuit_breaker(operation_name=req.operation_name, simulate_failure=req.simulate_failure)

@router.post("/manage-job", status_code=status.HTTP_200_OK)
async def manage_background_job(
    req: ManageJobRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Handles background job execution, retries, idempotency, and dead-letter routing."""
    service = ProductionReliabilityObservabilityService(db)
    return await service.manage_background_job(job_type=req.job_type, idempotency_key=req.idempotency_key, simulate_permanent_failure=req.simulate_permanent_failure)

@router.post("/replay-dead-letter", status_code=status.HTTP_200_OK)
async def replay_dead_letter_job(
    req: ReplayJobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Safely replays dead-letter jobs respecting current permissions and policy."""
    service = ProductionReliabilityObservabilityService(db)
    return await service.replay_dead_letter_job(job_id=req.job_id, user=current_user)

@router.post("/rebuild-indexes", status_code=status.HTTP_200_OK)
async def reconcile_and_rebuild_indexes(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Rebuilds vector embeddings and search indexes from PostgreSQL source of truth."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProductionReliabilityObservabilityService(db)
    return await service.reconcile_and_rebuild_indexes(organization_id=org_id, user=current_user)

@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_operations_dashboard(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves overall operational metrics dashboard."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ProductionReliabilityObservabilityService(db)
    return await service.get_operations_dashboard(organization_id=org_id, user=current_user)
