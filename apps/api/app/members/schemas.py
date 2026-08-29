from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class InvitationCreate(BaseModel):
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    email: str
    mobile: Optional[str] = None
    role: str = Field("member", description="owner, admin, manager, contributor, member, guest, viewer")


class InvitationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    email: str
    mobile: Optional[str] = None
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime
    org_name: Optional[str] = None
    workspace_name: Optional[str] = None
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MemberDirectoryItem(BaseModel):
    user_id: UUID
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    last_login_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    org_role: Optional[str] = None
    workspace_role: Optional[str] = None
    project_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MemberActionPayload(BaseModel):
    action: Optional[str] = Field(None, description="promote, demote, suspend, activate, transfer_ownership")
    role: Optional[str] = None
    status: Optional[str] = None
    level: str = Field("organization", description="organization, workspace, project")
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class JoinRequestCreate(BaseModel):
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    message: Optional[str] = None


class JoinRequestResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    user_id: UUID
    username: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionMatrixItem(BaseModel):
    role_name: str
    permission_key: str
    is_granted: bool
