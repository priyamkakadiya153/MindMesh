from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import GovernanceService

router = APIRouter(prefix="/governance", tags=["Knowledge Governance"])

class VerifyRequest(BaseModel):
    entity_type: str
    entity_id: str

class SupersedeRequest(BaseModel):
    old_entity_type: str
    old_entity_id: str
    new_entity_id: str

class LifecycleActionRequest(BaseModel):
    entity_type: str
    entity_id: str

@router.get("/review-queue", status_code=status.HTTP_200_OK)
async def get_review_queue(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve review queue items requiring human verification or attention."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = GovernanceService(db)
    return await service.get_review_queue(organization_id=org_id, workspace_id=ws_uuid)

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_knowledge(
    req: VerifyRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark a knowledge item human-verified."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID")

    service = GovernanceService(db)
    gov = await service.verify_knowledge(
        entity_type=req.entity_type,
        entity_id=e_uuid,
        user=current_user,
        organization_id=org_id
    )
    return {"message": "Knowledge item verified successfully", "verification_state": gov.verification_state}

@router.post("/supersede", status_code=status.HTTP_200_OK)
async def supersede_knowledge(
    req: SupersedeRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark an old knowledge item SUPERSEDED by a newer knowledge item."""
    try:
        old_uuid = UUID(req.old_entity_id)
        new_uuid = UUID(req.new_entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    service = GovernanceService(db)
    gov = await service.supersede_knowledge(
        old_entity_type=req.old_entity_type,
        old_entity_id=old_uuid,
        new_entity_id=new_uuid,
        user=current_user,
        organization_id=org_id
    )
    return {"message": "Knowledge marked superseded", "lifecycle_state": gov.lifecycle_state}

@router.post("/archive", status_code=status.HTTP_200_OK)
async def archive_knowledge(
    req: LifecycleActionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Archive a knowledge item."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID")

    service = GovernanceService(db)
    gov = await service.archive_knowledge(
        entity_type=req.entity_type,
        entity_id=e_uuid,
        user=current_user,
        organization_id=org_id
    )
    return {"message": "Knowledge item archived", "lifecycle_state": gov.lifecycle_state}

@router.post("/restore", status_code=status.HTTP_200_OK)
async def restore_knowledge(
    req: LifecycleActionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Restore an archived knowledge item to ACTIVE."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID")

    service = GovernanceService(db)
    gov = await service.restore_knowledge(
        entity_type=req.entity_type,
        entity_id=e_uuid,
        user=current_user,
        organization_id=org_id
    )
    return {"message": "Knowledge item restored", "lifecycle_state": gov.lifecycle_state}

@router.get("/audit-trail", status_code=status.HTTP_200_OK)
async def get_audit_trail(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve immutable governance audit records."""
    service = GovernanceService(db)
    return await service.get_audit_trail(organization_id=org_id)
