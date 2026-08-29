from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .organizational_memory_fabric_service import OrganizationalMemoryFabricService

router = APIRouter(prefix="/memory-fabric", tags=["Organizational Memory Fabric, Knowledge Synthesis & Continuous Context"])

class ContextPackRequest(BaseModel):
    scope_type: str = "TASK"
    scope_id: str = "task-deploy-101"

class KnowledgeBriefRequest(BaseModel):
    project_id: str

class HandoffRequest(BaseModel):
    project_id: str
    recipient_id: str

@router.get("/project-memory", status_code=status.HTTP_200_OK)
async def get_project_memory(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve comprehensive project memory context."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = OrganizationalMemoryFabricService(db)
    return await service.get_project_memory(project_id=p_uuid, user=current_user)

@router.post("/context-pack", status_code=status.HTTP_200_OK)
async def generate_context_pack(
    req: ContextPackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Assemble dynamic Context Pack for task, meeting, or decision."""
    service = OrganizationalMemoryFabricService(db)
    return await service.generate_context_pack(scope_type=req.scope_type, scope_id=req.scope_id, user=current_user)

@router.post("/knowledge-brief", status_code=status.HTTP_200_OK)
async def synthesize_knowledge_brief(
    req: KnowledgeBriefRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Synthesize evidence-grounded Knowledge Brief."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = OrganizationalMemoryFabricService(db)
    return await service.synthesize_knowledge_brief(project_id=p_uuid, user=current_user)

@router.post("/create-handoff", status_code=status.HTTP_200_OK)
async def create_knowledge_handoff(
    req: HandoffRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create context-rich Knowledge Handoff."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = OrganizationalMemoryFabricService(db)
    return await service.create_knowledge_handoff(project_id=p_uuid, recipient_id=req.recipient_id, user=current_user)

@router.get("/decision-memory", status_code=status.HTTP_200_OK)
async def get_decision_memory(
    decision_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve decision rationale and execution outcome memory."""
    service = OrganizationalMemoryFabricService(db)
    return await service.get_decision_memory(decision_id=decision_id, user=current_user)

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_memory_health(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Detect memory gaps and coverage health."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalMemoryFabricService(db)
    return await service.get_memory_health(organization_id=org_id, user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_memory_digest(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve memory fabric summary digest metrics."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = OrganizationalMemoryFabricService(db)
    return await service.get_memory_digest(organization_id=org_id, user=current_user)
