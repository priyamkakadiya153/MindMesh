from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .os_service import OrganizationalMemoryOSService

router = APIRouter(prefix="/memory", tags=["Organizational Memory Operating System"])

class MemoryQueryRequest(BaseModel):
    query: str
    scope: Optional[str] = "CURRENT_PROJECT"

@router.get("/home", status_code=status.HTTP_200_OK)
async def get_memory_home(
    scope: str = Query("ORGANIZATION", description="Memory Scope (CURRENT_PROJECT, WORKSPACE, ORGANIZATION, PERSONAL)"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve unified Memory Home feed, highlights, and active project memory."""
    service = OrganizationalMemoryOSService(db)
    return await service.get_memory_home_feed(user=current_user, organization_id=org_id, scope=scope)

@router.get("/entity/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def get_entity_memory(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve unified memory context and side-panel info for any entity."""
    try:
        e_uuid = UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID format")

    service = OrganizationalMemoryOSService(db)
    return await service.get_entity_memory(user=current_user, organization_id=org_id, entity_type=entity_type, entity_id=e_uuid)

@router.post("/query", status_code=status.HTTP_200_OK)
async def query_memory(
    req: MemoryQueryRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute high-level Organizational Memory query."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    service = OrganizationalMemoryOSService(db)
    return await service.query_memory(
        user=current_user,
        organization_id=org_id,
        query=req.query,
        scope=req.scope or "CURRENT_PROJECT"
    )

@router.get("/health", status_code=status.HTTP_200_OK)
async def audit_memory_health(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Audit Memory OS operational health across all subsystems."""
    service = OrganizationalMemoryOSService(db)
    return await service.audit_memory_health(organization_id=org_id)

@router.post("/reindex", status_code=status.HTTP_200_OK)
async def reindex_memory_system(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger idempotent reindexing of Memory OS subsystems."""
    service = OrganizationalMemoryOSService(db)
    return await service.reindex_memory_system(organization_id=org_id)
