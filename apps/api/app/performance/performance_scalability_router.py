from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .performance_scalability_service import PerformanceScalabilityService

router = APIRouter(prefix="/performance-scale", tags=["Performance, Scalability & High-Scale Architecture"])

class OptimizeQueryRequest(BaseModel):
    query_type: str
    cursor: Optional[str] = None
    limit: int = 50

class RouteAIRequest(BaseModel):
    task_complexity: str
    raw_prompt: str

class BatchEmbeddingsRequest(BaseModel):
    document_ids: List[str]
    workspace_id: str

@router.get("/baselines", status_code=status.HTTP_200_OK)
async def get_performance_baselines(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Measures P50, P95, P99 metrics across critical user journeys."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = PerformanceScalabilityService(db)
    return await service.get_performance_baselines(organization_id=org_id, user=current_user)

@router.post("/optimize-query", status_code=status.HTTP_200_OK)
async def optimize_query_execution(
    req: OptimizeQueryRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Executes cursor pagination and N+1 query elimination."""
    service = PerformanceScalabilityService(db)
    return await service.optimize_query_execution(query_type=req.query_type, cursor=req.cursor, limit=req.limit)

@router.post("/route-ai", status_code=status.HTTP_200_OK)
async def route_ai_request(
    req: RouteAIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Directs simple tasks to small fast models and complex tasks to deep reasoning paths."""
    service = PerformanceScalabilityService(db)
    return await service.route_ai_request(task_complexity=req.task_complexity, raw_prompt=req.raw_prompt, user=current_user)

@router.post("/batch-embeddings", status_code=status.HTTP_200_OK)
async def partition_and_batch_embeddings(
    req: BatchEmbeddingsRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Batches embedding requests into optimal chunk sizes with scope partitioning."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    try:
        ws_uuid = UUID(req.workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace UUID format")

    service = PerformanceScalabilityService(db)
    return await service.partition_and_batch_embeddings(document_ids=req.document_ids, organization_id=org_id, workspace_id=ws_uuid)

@router.get("/capacity-metrics", status_code=status.HTTP_200_OK)
async def get_capacity_planning_metrics(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluates system capacity limits and cost efficiency."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = PerformanceScalabilityService(db)
    return await service.get_capacity_planning_metrics(organization_id=org_id)
