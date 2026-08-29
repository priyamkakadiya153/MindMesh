from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from ..core.database import get_db_session
from ..api.dependencies import get_current_user
from ..authorization.organization_resolver import resolve_organization_id
from ..models.user import User
from .models import Folder
from .schemas import FolderResponse, FolderCreate, FolderUpdate

router = APIRouter(prefix="/folders", tags=["Folders"])

@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_in: FolderCreate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    folder = Folder(
        organization_id=org_id,
        workspace_id=folder_in.workspace_id,
        parent_id=folder_in.parent_id,
        name=folder_in.name,
        created_by=current_user.id
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder

@router.get("", response_model=List[FolderResponse])
@router.get("/", response_model=List[FolderResponse])
async def list_folders(
    workspace_id: UUID = Query(...),
    parent_id: Optional[UUID] = Query(None),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Folder).where(
        Folder.organization_id == org_id,
        Folder.workspace_id == workspace_id,
        Folder.deleted_at.is_(None)
    )
    if parent_id is not None:
        stmt = stmt.where(Folder.parent_id == parent_id)
    stmt = stmt.order_by(desc(Folder.created_at))
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.patch("/{id}", response_model=FolderResponse)
async def update_folder(
    id: UUID,
    folder_in: FolderUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Folder).where(Folder.id == id, Folder.organization_id == org_id, Folder.deleted_at.is_(None))
    res = await db.execute(stmt)
    folder = res.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if folder_in.name is not None:
        folder.name = folder_in.name
    if folder_in.parent_id is not None:
        folder.parent_id = folder_in.parent_id
    folder.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(folder)
    return folder

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Folder).where(Folder.id == id, Folder.organization_id == org_id)
    res = await db.execute(stmt)
    folder = res.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folder.deleted_at = datetime.utcnow()
    await db.commit()
