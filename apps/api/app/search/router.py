import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..api.dependencies import get_current_user
from ..authorization.organization_resolver import resolve_organization_id
from ..models.user import User
from .schemas import (
    SearchRequest,
    MetadataSearchRequest,
    SearchResponse,
    UniversalSearchResponse,
    AutocompleteSuggestion,
    SearchHistoryResponseItem,
    ClearHistoryResponse,
)
from .service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search Platform"])

@router.get("", response_model=UniversalSearchResponse, status_code=status.HTTP_200_OK)
@router.get("/", response_model=UniversalSearchResponse, status_code=status.HTTP_200_OK)
async def universal_search(
    q: Optional[str] = Query(None, description="Search query string"),
    query: Optional[str] = Query(None, description="Search query string"),
    type: str = Query("all", description="Entity type: all, documents, projects, tasks, chat, knowledge, users, workflows, etc."),
    workspace: Optional[str] = Query(None, description="Workspace UUID filter"),
    organization: Optional[str] = Query(None, description="Organization UUID filter"),
    owner: Optional[str] = Query(None, description="Owner/Creator UUID filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("most_relevant", description="Sort order: most_relevant, newest, oldest, alphabetical"),
    status: Optional[str] = Query(None, description="Entity status filter"),
    file_type: Optional[str] = Query(None, description="File extension/type filter"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Universal search endpoint across all MindMesh entities with full RBAC, filtering, and facets."""
    search_query = q if q is not None else (query or "")
    ws_uuid = UUID(workspace) if workspace and workspace != "all" and workspace != "null" else None
    org_uuid = UUID(organization) if organization and organization != "all" else org_id
    owner_uuid = UUID(owner) if owner and owner != "all" else None

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    service = SearchService(db)
    res = await service.universal_search(
        user=current_user,
        query=search_query,
        entity_type=type,
        workspace_id=ws_uuid,
        organization_id=org_uuid,
        owner_id=owner_uuid,
        page=page,
        limit=limit,
        sort=sort,
        status=status,
        file_type=file_type,
        tags=tag_list,
        date_from=date_from,
        date_to=date_to,
    )
    return res

@router.get("/suggestions", response_model=List[AutocompleteSuggestion], status_code=status.HTTP_200_OK)
async def get_search_suggestions(
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Real-time autocomplete query recommendations matching input text prefix."""
    search_term = q if q is not None else (query or "")
    service = SearchService(db)
    return await service.get_suggestions(
        user=current_user,
        query_prefix=search_term,
        organization_id=org_id
    )

@router.get("/history", response_model=List[SearchHistoryResponseItem], status_code=status.HTTP_200_OK)
async def get_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves recent unique search queries for current authenticated user."""
    service = SearchService(db)
    return await service.get_user_search_history(user_id=current_user.id, limit=10)

@router.delete("/history", response_model=ClearHistoryResponse, status_code=status.HTTP_200_OK)
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Clears search query history for current authenticated user."""
    service = SearchService(db)
    await service.clear_user_search_history(user_id=current_user.id)
    return {"success": True, "message": "Search history cleared successfully."}

# Backward Compatibility Endpoints

@router.post("/semantic", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = SearchService(db)
    return await service.execute_semantic_search(
        org_id=org_id,
        query=request.query,
        limit=request.limit or 10,
        filters=request.filters,
        user_id=current_user.id
    )

@router.post("/hybrid", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = SearchService(db)
    return await service.execute_hybrid_search(
        org_id=org_id,
        query=request.query,
        limit=request.limit or 10,
        filters=request.filters,
        user_id=current_user.id
    )

@router.post("/metadata", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def metadata_search(
    request: MetadataSearchRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = SearchService(db)
    return await service.execute_semantic_search(
        org_id=org_id,
        query="",
        limit=request.limit or 10,
        filters=request.filters,
        user_id=current_user.id
    )
