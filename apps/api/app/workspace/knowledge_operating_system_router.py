from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_operating_system_service import KnowledgeOperatingSystemService

router = APIRouter(prefix="/knowledge-os", tags=["Knowledge Operating System, Universal Workspace & Intelligent Information Experience"])

class ContextPackCreateRequest(BaseModel):
    title: str
    chips: List[Dict[str, str]]

class CommandExecuteRequest(BaseModel):
    command_text: str
    context_entity_id: Optional[str] = None

@router.get("/universal-search", status_code=status.HTTP_200_OK)
async def execute_universal_search(
    q: str = Query(..., description="Search query string"),
    types: Optional[List[str]] = Query(None, description="Entity type filters"),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes cross-entity search over Documents, Messages, Projects, Tasks, Decisions, Risks, Knowledge, Workflows, and Insights."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeOperatingSystemService(db)
    return await service.execute_universal_search(query=q, organization_id=org_id, user=current_user, entity_types=types)

@router.get("/entity/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def get_entity_detail(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves universal entity payload across 13 core MindMesh entity types."""
    service = KnowledgeOperatingSystemService(db)
    return await service.get_entity_detail(entity_type=entity_type, entity_id=entity_id, user=current_user)

@router.post("/context-pack", status_code=status.HTTP_200_OK)
async def create_context_pack(
    req: ContextPackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Bundles selected entities into reusable context packs."""
    service = KnowledgeOperatingSystemService(db)
    return await service.create_context_pack(title=req.title, chips=req.chips, user=current_user)

@router.get("/activity", status_code=status.HTTP_200_OK)
async def get_activity_feed(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Aggregates unified activity events across projects."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeOperatingSystemService(db)
    return await service.get_activity_feed(organization_id=org_id, user=current_user)

@router.post("/command", status_code=status.HTTP_200_OK)
async def execute_universal_command(
    req: CommandExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes keyboard command bar shortcuts."""
    service = KnowledgeOperatingSystemService(db)
    return await service.execute_universal_command(command_text=req.command_text, context_entity_id=req.context_entity_id, user=current_user)

@router.get("/personal-workspace", status_code=status.HTTP_200_OK)
async def get_personal_workspace(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compiles personal home workspace."""
    service = KnowledgeOperatingSystemService(db)
    return await service.get_personal_workspace(user=current_user)

@router.get("/project-workspace/{project_id}", status_code=status.HTTP_200_OK)
async def get_project_workspace(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compiles unified project workspace view."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        p_uuid = UUID("bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4")

    service = KnowledgeOperatingSystemService(db)
    return await service.get_project_workspace(project_id=p_uuid, user=current_user)
