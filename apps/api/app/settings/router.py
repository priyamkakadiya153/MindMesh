from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from .schemas import (
    UserProfileResponse, UserProfileUpdate, UserSettingsResponse,
    UserSettingsUpdate, NotificationPrefSchema, AuditLogResponse
)
from .service import SettingsService

router = APIRouter()
settings_service = SettingsService()

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await settings_service.update_user_profile(db, current_user, payload)

@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await settings_service.get_or_create_user_settings(db, current_user.id)

@router.patch("/settings", response_model=UserSettingsResponse)
async def update_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await settings_service.update_user_settings(db, current_user.id, payload)

@router.get("/audit", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    logs = await settings_service.list_audit_logs(db, org_id, limit)
    res = []
    for l in logs:
        item = AuditLogResponse.model_validate(l)
        res.append(item)
    return res
