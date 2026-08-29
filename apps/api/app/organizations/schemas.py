from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class OrgSettingsSchema(BaseModel):
    default_language: str = "en"
    timezone: str = "UTC"
    theme: str = "dark"
    branding_color: str = "#3B82F6"
    allow_public_invites: bool = False
    allow_guest_access: bool = True

    class Config:
        from_attributes = True

class OrgSettingsUpdate(BaseModel):
    default_language: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    branding_color: Optional[str] = None
    allow_public_invites: Optional[bool] = None
    allow_guest_access: Optional[bool] = None

class OrgCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"

class OrgUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    visibility: Optional[str] = None
    status: Optional[str] = None

class OrgResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    owner_id: Optional[UUID] = None
    status: str = "active"
    visibility: str = "private"
    is_personal: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    settings: Optional[OrgSettingsSchema] = None

    class Config:
        from_attributes = True

class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"

class MemberRoleUpdate(BaseModel):
    role: str

class MemberResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    status: str = "active"
    joined_at: datetime

class InvitationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    org_name: Optional[str] = None
    email: str
    role: str
    token: str
    invited_by: Optional[UUID] = None
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

