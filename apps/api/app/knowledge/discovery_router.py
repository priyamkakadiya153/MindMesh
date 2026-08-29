from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .discovery_service import KnowledgeDiscoveryNavigationService

router = APIRouter(prefix="/knowledge/discovery", tags=["Knowledge Discovery & Intelligent Navigation"])

class BookmarkRequest(BaseModel):
    entity_id: str
    entity_type: str
    title: str
    governance_status: Optional[str] = "CURRENT"

class FollowRequest(BaseModel):
    entity_id: str

@router.get("/related", status_code=status.HTTP_200_OK)
async def get_related_knowledge(
    entity_id: str = Query(..., description="Entity UUID to retrieve related knowledge"),
    entity_type: str = Query("DOCUMENT", description="Entity type (DOCUMENT, DECISION, TASK, PROJECT)"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve multi-category related knowledge (Directly Related, Supporting, Affected, Historical, Suggested)."""
    try:
        e_uuid = UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID format")

    service = KnowledgeDiscoveryNavigationService(db)
    return await service.get_related_knowledge(user=current_user, organization_id=org_id, entity_type=entity_type, entity_id=e_uuid)

@router.get("/path", status_code=status.HTTP_200_OK)
async def get_knowledge_path(
    project_id: str = Query(..., description="Project UUID"),
    current_entity_id: str = Query(..., description="Current Entity UUID"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve guided knowledge path and navigation breadcrumbs."""
    try:
        p_uuid = UUID(project_id)
        e_uuid = UUID(current_entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    service = KnowledgeDiscoveryNavigationService(db)
    return await service.get_knowledge_path(user=current_user, organization_id=org_id, project_id=p_uuid, current_entity_id=e_uuid)

@router.post("/bookmark", status_code=status.HTTP_200_OK)
async def bookmark_knowledge(
    req: BookmarkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Bookmark an entity to user's saved knowledge collection."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID format")

    service = KnowledgeDiscoveryNavigationService(db)
    return await service.bookmark_knowledge(
        user_id=current_user.id,
        entity_id=e_uuid,
        entity_type=req.entity_type,
        title=req.title,
        governance_status=req.governance_status or "CURRENT"
    )

@router.post("/follow", status_code=status.HTTP_200_OK)
async def follow_entity(
    req: FollowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Subscribe to proactive updates on a decision/project."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID format")

    service = KnowledgeDiscoveryNavigationService(db)
    return await service.follow_entity(user_id=current_user.id, entity_id=e_uuid)

@router.get("/saved", status_code=status.HTTP_200_OK)
async def get_saved_knowledge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve user's saved knowledge collection."""
    service = KnowledgeDiscoveryNavigationService(db)
    return await service.get_saved_knowledge(user_id=current_user.id)
