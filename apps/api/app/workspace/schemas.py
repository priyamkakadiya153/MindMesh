from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Union

class WorkspaceSettingsSchema(BaseModel):
    theme: str = "dark"
    timezone: str = "UTC"
    language: str = "en"
    default_dashboard: str = "overview"
    allow_ai: bool = True
    visibility: str = "private"
    default_ai_model: str = "gemini-2.5-flash"
    auto_index_files: bool = True
    enable_semantic_search: bool = True
    enable_ai_chat: bool = True

    class Config:
        from_attributes = True

class WorkspaceSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    default_dashboard: Optional[str] = None
    allow_ai: Optional[bool] = None
    visibility: Optional[str] = None
    default_ai_model: Optional[str] = None
    auto_index_files: Optional[bool] = None
    enable_semantic_search: Optional[bool] = None
    enable_ai_chat: Optional[bool] = None

class WorkspaceBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)

class WorkspaceCreate(WorkspaceBase):
    slug: Optional[str] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)

class WorkspaceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    owner_id: Optional[Union[UUID, str]] = None
    status: Optional[str] = "active"
    is_default: Optional[bool] = False
    is_archived: Optional[bool] = False
    created_by: Optional[Union[UUID, str]] = None
    created_at: datetime
    updated_at: datetime
    settings: Optional[WorkspaceSettingsSchema] = None

    class Config:
        from_attributes = True

class WorkspaceMemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"

class WorkspaceMemberRoleUpdate(BaseModel):
    role: str

class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    status: str = "active"
    joined_at: datetime
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

