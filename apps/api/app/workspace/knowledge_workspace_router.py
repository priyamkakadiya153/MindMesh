from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_workspace_service import KnowledgeWorkspaceService

router = APIRouter(prefix="/workspace-experience", tags=["Knowledge Operations, Discovery & Intelligent Workspace Experience"])

class CreateCollectionRequest(BaseModel):
    name: str
    collection_type: str = "PERSONAL"
    description: Optional[str] = None
    smart_rule: Optional[str] = None

class AddCollectionItemRequest(BaseModel):
    entity_id: str
    entity_type: str
    title: str

class SaveItemRequest(BaseModel):
    entity_id: str
    entity_type: str
    title: str

class AttachItemRequest(BaseModel):
    target_type: str
    target_id: str
    referenced_entity_id: str
    referenced_entity_type: str
    relationship_type: str = "SUPPORTS"

@router.get("/home", status_code=status.HTTP_200_OK)
async def get_knowledge_home(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Assemble personalized Knowledge Home context."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = KnowledgeWorkspaceService(db)
    return await service.get_knowledge_home(user=current_user, organization_id=org_id, project_id=p_uuid)

@router.get("/my-knowledge", status_code=status.HTTP_200_OK)
async def get_my_knowledge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve user's personal knowledge space."""
    service = KnowledgeWorkspaceService(db)
    return await service.get_my_knowledge(user=current_user)

@router.post("/collections", status_code=status.HTTP_200_OK)
async def create_collection(
    req: CreateCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a Personal, Shared, or Project Collection (or Smart Rule Collection)."""
    service = KnowledgeWorkspaceService(db)
    return await service.create_collection(
        name=req.name,
        collection_type=req.collection_type,
        description=req.description,
        smart_rule=req.smart_rule,
        user=current_user
    )

@router.get("/collections/{collection_id}", status_code=status.HTTP_200_OK)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve collection details and authorized item references."""
    service = KnowledgeWorkspaceService(db)
    return await service.get_collection(collection_id=collection_id, user=current_user)

@router.post("/collections/{collection_id}/items", status_code=status.HTTP_200_OK)
async def add_item_to_collection(
    collection_id: str,
    req: AddCollectionItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Add an entity reference to a collection without content duplication."""
    service = KnowledgeWorkspaceService(db)
    return await service.add_item_to_collection(
        collection_id=collection_id,
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        title=req.title,
        user=current_user
    )

@router.get("/project-hub/{project_id}", status_code=status.HTTP_200_OK)
async def get_project_knowledge_hub(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Aggregate project overview, architecture documents, current decisions, open tasks, research briefs, risks, and graph map nodes."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = KnowledgeWorkspaceService(db)
    return await service.get_project_knowledge_hub(project_id=p_uuid, user=current_user)

@router.post("/save-item", status_code=status.HTTP_200_OK)
async def save_knowledge_item(
    req: SaveItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Save/bookmark a knowledge item to user's personal saved space."""
    service = KnowledgeWorkspaceService(db)
    return await service.save_knowledge_item(entity_id=req.entity_id, entity_type=req.entity_type, title=req.title, user=current_user)

@router.post("/attach-item", status_code=status.HTTP_200_OK)
async def attach_knowledge_reference(
    req: AttachItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Attach a governed knowledge reference to a task, decision, or research brief."""
    service = KnowledgeWorkspaceService(db)
    return await service.attach_knowledge_reference(
        target_type=req.target_type,
        target_id=req.target_id,
        referenced_entity_id=req.referenced_entity_id,
        referenced_entity_type=req.referenced_entity_type,
        relationship_type=req.relationship_type,
        user=current_user
    )
