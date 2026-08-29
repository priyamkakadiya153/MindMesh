from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class WorkspaceBase(BaseModel):
    name: str
    slug: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class WorkspaceResponse(WorkspaceBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: Optional[str] = "Active"
    projects_count: int = 0
    documents_count: int = 0
    members_count: int = 1
    storage_used: int = 0

    class Config:
        from_attributes = True

class WorkspaceMemberInvite(BaseModel):
    email: str
    role: str = "MEMBER"

class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    username: str
    email: str

    class Config:
        from_attributes = True
