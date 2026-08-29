from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .universal_service import UniversalSearchIntelligenceService

router = APIRouter(prefix="/search", tags=["Universal Knowledge Search & Retrieval"])

@router.get("/universal", status_code=status.HTTP_200_OK)
async def execute_universal_search(
    q: str = Query(..., min_length=1, description="Universal search query string"),
    workspace_id: Optional[str] = Query(None, description="Workspace UUID filter"),
    project_id: Optional[str] = Query(None, description="Project UUID filter"),
    entity_filter: str = Query("ALL", description="Entity filter (ALL, DOCUMENT, MESSAGE, DECISION, TASK, FILE)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute hybrid universal search across all authorized workspace & project entities."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    p_uuid = UUID(project_id) if project_id else None

    service = UniversalSearchIntelligenceService(db)
    return await service.execute_hybrid_search(
        query=q,
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=p_uuid,
        entity_filter=entity_filter,
        limit=limit
    )

@router.get("/suggestions", status_code=status.HTTP_200_OK)
async def get_typeahead_suggestions(
    q: str = Query(..., min_length=1, description="Search query prefix"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve real-data typeahead search suggestions."""
    service = UniversalSearchIntelligenceService(db)
    return await service.get_typeahead_suggestions(query=q, user=current_user, organization_id=org_id)
