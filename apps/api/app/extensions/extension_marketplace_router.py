from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .extension_platform_service import ExtensionPlatformService

router = APIRouter(prefix="/extensions", tags=["Extension Platform, Marketplace & Plugin Ecosystem"])

class InstallExtensionRequest(BaseModel):
    extension_id: str

class SyncConnectorRequest(BaseModel):
    connector_id: str
    sync_mode: str = "INCREMENTAL" # INITIAL, INCREMENTAL, ON_DEMAND

class BuildAgentRequest(BaseModel):
    name: str
    role: str
    capabilities: List[str]
    instructions: str
    visibility: str = "WORKSPACE" # PRIVATE, WORKSPACE, ORGANIZATION, MARKETPLACE

class RevokePermissionRequest(BaseModel):
    extension_id: str
    reason: str

@router.get("/marketplace", status_code=status.HTTP_200_OK)
async def list_marketplace_extensions(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Searches & filters marketplace catalog for ExtensionDefinition objects."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ExtensionPlatformService(db)
    return await service.list_marketplace_extensions(query=query, category=category, organization_id=org_id, user=current_user)

@router.post("/install", status_code=status.HTTP_200_OK)
async def install_extension(
    req: InstallExtensionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Validates package manifest, requests permissions, performs admin review, and sets activation state."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ExtensionPlatformService(db)
    return await service.install_extension(extension_id=req.extension_id, organization_id=org_id, user=current_user)

@router.post("/connectors/sync", status_code=status.HTTP_200_OK)
async def sync_knowledge_connector(
    req: SyncConnectorRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes connector sync, preserves data lineage, handles duplicate syncs idempotently, and resolves conflicts."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ExtensionPlatformService(db)
    return await service.sync_knowledge_connector(connector_id=req.connector_id, sync_mode=req.sync_mode, organization_id=org_id, user=current_user)

@router.post("/agents/builder", status_code=status.HTTP_200_OK)
async def build_custom_agent(
    req: BuildAgentRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Provides Custom Agent Builder pipeline (Define Role -> Capabilities -> Instructions -> Permissions -> Publish)."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ExtensionPlatformService(db)
    return await service.build_custom_agent(
        name=req.name,
        role=req.role,
        capabilities=req.capabilities,
        instructions=req.instructions,
        visibility=req.visibility,
        organization_id=org_id,
        user=current_user
    )

@router.post("/permissions/revoke", status_code=status.HTTP_200_OK)
async def revoke_extension_permissions(
    req: RevokePermissionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs immediate permission revocation or emergency disablement (circuit breaker)."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ExtensionPlatformService(db)
    return await service.revoke_extension_permissions(extension_id=req.extension_id, reason=req.reason, organization_id=org_id, user=current_user)
