from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from .schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectSettingsSchema, ProjectSettingsUpdate,
    ProjectMemberAdd, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectDashboardResponse, ProjectStatsResponse
)
from .service import ProjectService
from .dependencies import get_current_project
from .models import Project

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    proj_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.create_project(
        name=proj_in.name,
        workspace_id=proj_in.workspace_id,
        org_id=org_id,
        user_id=current_user.id,
        slug=proj_in.slug,
        description=proj_in.description,
        icon=proj_in.icon,
        color=proj_in.color,
        visibility=proj_in.visibility,
        status_val=proj_in.status,
        start_date=proj_in.start_date,
        end_date=proj_in.end_date
    )

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    workspace_id: Optional[UUID] = Query(None),
    status_val: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    include_archived: bool = Query(True),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.list_projects(org_id, workspace_id, status_val=status_val, search=search, include_archived=include_archived)

@router.get("/{id}", response_model=ProjectResponse)
async def get_project(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.get_project(id, org_id)

@router.patch("/{id}", response_model=ProjectResponse)
async def update_project(
    id: UUID,
    proj_in: ProjectUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.update_project(
        id=id,
        org_id=org_id,
        name=proj_in.name,
        slug=proj_in.slug,
        description=proj_in.description,
        icon=proj_in.icon,
        color=proj_in.color,
        visibility=proj_in.visibility,
        status_val=proj_in.status,
        default_ai_model=proj_in.default_ai_model,
        start_date=proj_in.start_date,
        end_date=proj_in.end_date
    )

@router.post("/{id}/archive", response_model=ProjectResponse)
async def archive_project(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.archive_project(id, org_id)

@router.post("/{id}/restore", response_model=ProjectResponse)
async def restore_project(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.restore_project(id, org_id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    await service.delete_project(id, org_id, soft=True)

# Settings Router Endpoints
@router.get("/{id}/settings", response_model=ProjectSettingsSchema)
async def get_project_settings(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.get_settings(id, org_id)

@router.patch("/{id}/settings", response_model=ProjectSettingsSchema)
async def update_project_settings(
    id: UUID,
    settings_in: ProjectSettingsUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.update_settings(id, org_id, **settings_in.model_dump(exclude_unset=True))

# Dashboard Router Endpoint
@router.get("/{id}/dashboard", response_model=ProjectDashboardResponse)
async def get_project_dashboard(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.get_dashboard(id, org_id)

# Roster Router Endpoints
@router.get("/{id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.get_project_members(id, org_id)

@router.post("/{id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    id: UUID,
    member_in: ProjectMemberAdd,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.add_project_member(id, org_id, member_in.email, member_in.role)

@router.patch("/{id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    id: UUID,
    user_id: UUID,
    member_in: ProjectMemberUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.update_project_member(id, org_id, user_id, role=member_in.role, status_val=member_in.status)

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    id: UUID,
    user_id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    await service.remove_project_member(id, org_id, user_id)

@router.get("/{id}/statistics", response_model=ProjectStatsResponse)
async def get_project_statistics(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ProjectService(db)
    return await service.get_project_statistics(id, org_id)
