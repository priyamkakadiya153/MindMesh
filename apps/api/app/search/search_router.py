from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..authorization.organization_resolver import resolve_organization_id
from ..models.user import User
from ..models.search_models import SavedSearch, RecentSearch
from .base import SearchResponse
from .postgres_provider import PostgresSearchProvider

router = APIRouter()

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    query_text: str = Field(..., min_length=1)
    filters_json: Optional[Dict[str, Any]] = None

class SavedSearchResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    query_text: str
    filters_json: Optional[Dict[str, Any]] = None
    created_at: datetime

@router.get("", response_model=SearchResponse)
async def global_search(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = q or query or ""
    search_q = search_q.strip()

    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])

    resolved_org_id = organization_id
    if not resolved_org_id:
        resolved_org_id = await resolve_organization_id(request, current_user, db)

    provider = PostgresSearchProvider(db)
    
    # Save to recent searches
    rec = RecentSearch(
        id=uuid4(),
        user_id=current_user.id,
        organization_id=resolved_org_id,
        query_text=search_q,
        searched_at=datetime.utcnow()
    )
    db.add(rec)
    await db.commit()

    return await provider.search_global(search_q, resolved_org_id, current_user.id, workspace_id, limit, offset)

@router.get("/messages", response_model=SearchResponse)
async def search_messages(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    conversation_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = (q or query or "").strip()
    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    provider = PostgresSearchProvider(db)
    return await provider.search_messages(search_q, resolved_org_id, current_user.id, conversation_id, limit, offset)

@router.get("/files", response_model=SearchResponse)
async def search_files(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    mime_category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = (q or query or "").strip()
    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    provider = PostgresSearchProvider(db)
    return await provider.search_files(search_q, resolved_org_id, current_user.id, mime_category, limit, offset)

@router.get("/projects", response_model=SearchResponse)
async def search_projects(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = (q or query or "").strip()
    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    provider = PostgresSearchProvider(db)
    return await provider.search_projects(search_q, resolved_org_id, current_user.id, workspace_id, limit, offset)

@router.get("/members", response_model=SearchResponse)
async def search_members(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = (q or query or "").strip()
    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    provider = PostgresSearchProvider(db)
    return await provider.search_members(search_q, resolved_org_id, current_user.id, limit, offset)

@router.get("/conversations", response_model=SearchResponse)
async def search_conversations(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    search_q = (q or query or "").strip()
    if not search_q:
        return SearchResponse(query="", total_results=0, items=[])
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    provider = PostgresSearchProvider(db)
    return await provider.search_conversations(search_q, resolved_org_id, current_user.id, limit, offset)

@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    request: Request,
    organization_id: Optional[UUID] = None,
    payload: SavedSearchCreate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    saved = SavedSearch(
        id=uuid4(),
        user_id=current_user.id,
        organization_id=resolved_org_id,
        name=payload.name,
        query_text=payload.query_text,
        filters_json=payload.filters_json
    )
    db.add(saved)
    await db.commit()
    return saved

@router.get("/saved", response_model=List[SavedSearchResponse])
async def list_saved_searches(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    stmt = select(SavedSearch).where(
        SavedSearch.user_id == current_user.id,
        SavedSearch.organization_id == resolved_org_id
    ).order_by(desc(SavedSearch.created_at))

    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/recent", response_model=List[str])
async def get_recent_searches(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    resolved_org_id = organization_id or await resolve_organization_id(request, current_user, db)
    stmt = select(RecentSearch.query_text).where(
        RecentSearch.user_id == current_user.id,
        RecentSearch.organization_id == resolved_org_id
    ).order_by(desc(RecentSearch.searched_at)).limit(10)

    res = await db.execute(stmt)
    return list(dict.fromkeys(res.scalars().all()))
