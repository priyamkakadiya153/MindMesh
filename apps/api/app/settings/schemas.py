from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Dict

class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    email: str
    mobile: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class UserSettingsResponse(BaseModel):
    user_id: UUID
    theme: str
    language: str
    timezone: str
    email_notifications: bool
    in_app_notifications: bool
    mentions: bool = True
    project_updates: bool = True
    privacy_level: str

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None
    mentions: Optional[bool] = None
    project_updates: Optional[bool] = None
    privacy_level: Optional[str] = None


class NotificationPrefSchema(BaseModel):
    mentions: Optional[bool] = None
    project_updates: Optional[bool] = None
    workspace_updates: Optional[bool] = None
    marketing: Optional[bool] = None


class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    user_id: UUID
    username: Optional[str] = None
    organization_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
