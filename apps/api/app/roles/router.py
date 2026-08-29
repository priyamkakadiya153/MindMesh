from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID, uuid4
from typing import List, Optional
from pydantic import BaseModel, Field

from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from ..permissions.service import PermissionService, ROLE_PERMISSION_MAP
from ..models.permission import Permission, PermissionRole

router = APIRouter()
perm_service = PermissionService()

class RoleCreatePayload(BaseModel):
    name: str
    level: str = Field("organization", description="organization, workspace, project")
    description: Optional[str] = None
    permissions: List[str] = []

class PermissionCreatePayload(BaseModel):
    name: str
    category: str = Field("general", description="organization, workspace, project, member, messages, files, knowledge, ai, settings, analytics")
    description: Optional[str] = None

SYSTEM_PERMISSIONS = [
    {"name": "organization.create", "category": "organizations", "description": "Create new organizations"},
    {"name": "organization.edit", "category": "organizations", "description": "Edit organization details"},
    {"name": "organization.delete", "category": "organizations", "description": "Delete organization"},
    {"name": "workspace.create", "category": "workspaces", "description": "Create workspaces"},
    {"name": "workspace.edit", "category": "workspaces", "description": "Edit workspace settings"},
    {"name": "workspace.delete", "category": "workspaces", "description": "Delete workspace"},
    {"name": "project.create", "category": "projects", "description": "Create projects"},
    {"name": "project.edit", "category": "projects", "description": "Edit project details"},
    {"name": "project.delete", "category": "projects", "description": "Delete project"},
    {"name": "member.invite", "category": "members", "description": "Invite new members"},
    {"name": "member.remove", "category": "members", "description": "Remove members"},
    {"name": "member.promote", "category": "members", "description": "Promote/demote member roles"},
    {"name": "settings.update", "category": "settings", "description": "Update system settings"},
    {"name": "analytics.view", "category": "analytics", "description": "View analytics overview"},
]

@router.get("/roles")
async def list_roles(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Standard System Roles
    system_roles = []
    for r_name, p_set in ROLE_PERMISSION_MAP.items():
        system_roles.append({
            "id": r_name,
            "name": r_name,
            "level": "organization" if r_name in ["owner", "admin", "manager", "member", "guest"] else "project",
            "is_system_role": True,
            "description": f"Standard system role: {r_name}",
            "permissions": list(p_set)
        })

    # Custom DB Roles
    stmt = select(PermissionRole)
    res = await db.execute(stmt)
    custom_roles = res.scalars().all()

    for cr in custom_roles:
        system_roles.append({
            "id": str(cr.id),
            "name": cr.name,
            "level": cr.level,
            "is_system_role": False,
            "description": cr.description,
            "permissions": []
        })

    return system_roles

@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_custom_role(
    payload: RoleCreatePayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    new_role = PermissionRole(
        id=uuid4(),
        name=payload.name.lower().strip(),
        level=payload.level,
        description=payload.description
    )
    db.add(new_role)
    await db.commit()
    return {"id": str(new_role.id), "name": new_role.name, "level": new_role.level}

@router.patch("/roles/{role_id}")
async def update_custom_role(
    role_id: str,
    payload: RoleCreatePayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if role_id in ROLE_PERMISSION_MAP:
        raise HTTPException(status_code=400, detail="Cannot modify built-in system role")

    try:
        r_uuid = UUID(role_id)
        role = await db.get(PermissionRole, r_uuid)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        role.name = payload.name.lower().strip()
        role.level = payload.level
        role.description = payload.description
        await db.commit()
        return {"status": "ok", "message": "Role updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID")

@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def delete_custom_role(
    role_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if role_id in ROLE_PERMISSION_MAP:
        raise HTTPException(status_code=400, detail="Cannot delete built-in system role")

    try:
        r_uuid = UUID(role_id)
        await db.execute(delete(PermissionRole).where(PermissionRole.id == r_uuid))
        await db.commit()
        return {"status": "ok", "message": "Role deleted"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID")

@router.get("/permissions")
async def list_permissions(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Permission)
    res = await db.execute(stmt)
    db_perms = res.scalars().all()

    combined = SYSTEM_PERMISSIONS + [
        {"name": p.name, "category": "custom", "description": p.description} for p in db_perms
    ]
    return combined

@router.post("/permissions", status_code=status.HTTP_201_CREATED)
async def register_permission(
    payload: PermissionCreatePayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    new_p = Permission(
        id=uuid4(),
        name=payload.name.lower().strip(),
        description=payload.description
    )
    db.add(new_p)
    await db.commit()
    return {"id": str(new_p.id), "name": new_p.name}

@router.get("/roles/me/permissions")
async def get_my_effective_permissions(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    perms = await perm_service.get_user_effective_permissions(
        db, current_user.id, org_id, workspace_id, project_id
    )
    return {"user_id": str(current_user.id), "organization_id": str(org_id), "permissions": list(perms)}
