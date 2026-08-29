from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .universal_search_service import UniversalSearchService

router = APIRouter(prefix="/search", tags=["Universal Knowledge Discovery & Intelligent Search"])

class SearchQueryRequest(BaseModel):
    query: str
    mode: str = "HYBRID"
    project_id: Optional[str] = None
    entity_types: Optional[List[str]] = None

class CompareResultsRequest(BaseModel):
    item_id_a: str
    item_id_b: str

@router.post("/query", status_code=status.HTTP_200_OK)
async def execute_search(
    req: SearchQueryRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Orchestrate hybrid lexical + semantic search across authorized entities."""
    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = UniversalSearchService(db)
    return await service.search(
        query=req.query,
        mode=req.mode,
        project_id=p_uuid,
        entity_types=req.entity_types,
        user=current_user,
        organization_id=org_id
    )

@router.get("/autocomplete", status_code=status.HTTP_200_OK)
async def autocomplete(
    prefix: str = Query("auth"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate fast entity and topic suggestions."""
    service = UniversalSearchService(db)
    return await service.autocomplete(prefix=prefix, user=current_user, organization_id=org_id)

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_results(
    req: CompareResultsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compare selected search result items."""
    service = UniversalSearchService(db)
    return await service.compare_results(item_id_a=req.item_id_a, item_id_b=req.item_id_b)

@router.get("/facets", status_code=status.HTTP_200_OK)
async def get_facets(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate category counts across authorized entity types."""
    service = UniversalSearchService(db)
    return await service.get_facets(user=current_user, organization_id=org_id)

@router.post("/rebuild-index", status_code=status.HTTP_200_OK)
async def rebuild_search_index(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently reconstruct search indexes from primary database records."""
    service = UniversalSearchService(db)
    return await service.rebuild_search_index(organization_id=org_id)
