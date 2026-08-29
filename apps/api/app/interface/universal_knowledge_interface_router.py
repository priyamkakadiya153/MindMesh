from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .universal_knowledge_interface_service import UniversalKnowledgeInterfaceService

router = APIRouter(prefix="/universal-interface", tags=["Universal Knowledge Interface & Natural Language Operating Layer"])

class UniversalQueryRequest(BaseModel):
    raw_prompt: str
    active_resource_id: Optional[str] = None

class FileIntelligenceRequest(BaseModel):
    file_name: str
    file_mime: str

class ConvertActionRequest(BaseModel):
    action_type: str
    payload: Dict[str, Any]

@router.post("/query", status_code=status.HTTP_200_OK)
async def query_universal_interface(
    req: UniversalQueryRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Processes natural language query across all authorized knowledge sources."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    res_uuid = UUID(req.active_resource_id) if req.active_resource_id else None
    service = UniversalKnowledgeInterfaceService(db)
    return await service.generate_universal_answer(raw_prompt=req.raw_prompt, active_resource_id=res_uuid, organization_id=org_id, user=current_user)

@router.post("/file-intelligence", status_code=status.HTTP_200_OK)
async def analyze_file_intelligence(
    req: FileIntelligenceRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs multi-source file analysis (including DST unsupported preview handling)."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = UniversalKnowledgeInterfaceService(db)
    return await service.analyze_file_intelligence(file_name=req.file_name, file_mime=req.file_mime, organization_id=org_id, user=current_user)

@router.post("/convert-action", status_code=status.HTTP_200_OK)
async def convert_answer_to_action(
    req: ConvertActionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Converts natural language recommendation into Phase 6.21 execution plan with human approval gate."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = UniversalKnowledgeInterfaceService(db)
    return await service.convert_answer_to_action(action_type=req.action_type, payload=req.payload, organization_id=org_id, user=current_user)

@router.get("/context-sources", status_code=status.HTTP_200_OK)
async def get_available_context_sources(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns authorized active context sources for the universal intelligence bar."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = UniversalKnowledgeInterfaceService(db)
    return await service.get_available_context_sources(organization_id=org_id, user=current_user)
