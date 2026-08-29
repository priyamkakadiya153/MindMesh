from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Union

class ProjectSettingsSchema(BaseModel):
    id: UUID
    project_id: UUID
    allow_external_sharing: bool
    default_view: str
    enable_ai: bool
    notification_level: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSettingsUpdate(BaseModel):
    allow_external_sharing: Optional[bool] = None
    default_view: Optional[str] = None
    enable_ai: Optional[bool] = None
    notification_level: Optional[str] = None


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field("#3B82F6", max_length=20)
    visibility: str = Field("private")
    status: str = Field("active")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    workspace_id: UUID


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    visibility: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    default_ai_model: Optional[str] = Field(None)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    organization_id: UUID
    owner_id: Optional[Union[UUID, str]] = None
    created_by: Optional[Union[UUID, str]] = None
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    visibility: Optional[str] = "private"
    status: Optional[str] = "active"
    default_ai_model: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_archived: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    settings: Optional[ProjectSettingsSchema] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    email: str
    role: str = "contributor"


class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: str
    status: str
    joined_at: datetime
    username: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectDashboardResponse(BaseModel):
    project: ProjectResponse
    member_count: int
    document_count: int
    chat_count: int
    task_count: int
    recent_activity: List[dict] = []


class ProjectStatsResponse(BaseModel):
    member_count: int
    document_count: int
    chat_count: int
    storage_used: int = 0

