from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from ..models.user import User
from ..models.user_settings import UserSettings
from ..models.notification_preference import NotificationPreference
from ..models.audit import AuditLog
from ..auth.security import get_password_hash, verify_password
from .schemas import UserProfileUpdate, UserSettingsUpdate, NotificationPrefSchema

class SettingsService:
    async def get_or_create_user_settings(self, db: AsyncSession, user_id: UUID) -> UserSettings:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        res = await db.execute(stmt)
        sett = res.scalar_one_or_none()
        if not sett:
            u_stmt = select(User).where(User.id == user_id)
            u_res = await db.execute(u_stmt)
            user = u_res.scalar_one_or_none()

            sett = UserSettings(
                user_id=user_id,
                theme=user.theme if user and user.theme else "dark",
                language=user.language if user and user.language else "en",
                timezone=user.timezone if user and user.timezone else "UTC",
                email_notifications=True,
                in_app_notifications=True,
                privacy_level="standard",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(sett)
            await db.commit()
            await db.refresh(sett)
        return sett

    async def get_or_create_notification_preferences(self, db: AsyncSession, user_id: UUID) -> NotificationPreference:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        res = await db.execute(stmt)
        np = res.scalar_one_or_none()
        if not np:
            np = NotificationPreference(
                id=uuid4(),
                user_id=user_id,
                mentions=True,
                project_updates=True,
                workspace_updates=True,
                marketing=False
            )
            db.add(np)
            await db.commit()
            await db.refresh(np)
        return np

    async def update_user_profile(self, db: AsyncSession, user: User, payload: UserProfileUpdate) -> User:
        if payload.username and payload.username != user.username:
            chk_stmt = select(User).where(User.username == payload.username, User.id != user.id)
            chk_res = await db.execute(chk_stmt)
            if chk_res.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Username is already taken by another account.")
            user.username = payload.username

        if payload.email and payload.email != user.email:
            chk_stmt = select(User).where(User.email == payload.email, User.id != user.id)
            chk_res = await db.execute(chk_stmt)
            if chk_res.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email address is already in use.")
            user.email = payload.email

        norm_phone = payload.mobile if payload.mobile is not None else payload.phone_number
        if norm_phone is not None:
            user.phone_number = norm_phone

        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url

        if payload.new_password:
            if not payload.current_password:
                raise HTTPException(status_code=400, detail="Current password is required to set a new password.")
            if not verify_password(payload.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect.")
            user.hashed_password = get_password_hash(payload.new_password)

        user.updated_at = datetime.utcnow()
        db.add(user)
        await db.commit()
        await db.refresh(user)

        await self.log_audit_event(
            db, user.id, user.current_organization_id, "user.profile_update", "User", str(user.id),
            {"updated_fields": [k for k, v in payload.model_dump().items() if v is not None]}
        )
        return user

    async def update_user_settings(self, db: AsyncSession, user_id: UUID, payload: UserSettingsUpdate) -> UserSettings:
        sett = await self.get_or_create_user_settings(db, user_id)
        if payload.theme:
            sett.theme = payload.theme
        if payload.language:
            sett.language = payload.language
        if payload.timezone:
            sett.timezone = payload.timezone
        if payload.email_notifications is not None:
            sett.email_notifications = payload.email_notifications
        if payload.in_app_notifications is not None:
            sett.in_app_notifications = payload.in_app_notifications
        if payload.mentions is not None:
            sett.mentions = payload.mentions
        if payload.project_updates is not None:
            sett.project_updates = payload.project_updates
        if payload.privacy_level:
            sett.privacy_level = payload.privacy_level

        sett.updated_at = datetime.utcnow()
        db.add(sett)

        # Sync theme, language, timezone to User model as well
        u_stmt = select(User).where(User.id == user_id)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if user:
            if payload.theme:
                user.theme = payload.theme
            if payload.language:
                user.language = payload.language
            if payload.timezone:
                user.timezone = payload.timezone
            db.add(user)

        await db.commit()
        await db.refresh(sett)
        return sett


    async def update_notification_preferences(self, db: AsyncSession, user_id: UUID, payload: NotificationPrefSchema) -> NotificationPreference:
        np = await self.get_or_create_notification_preferences(db, user_id)
        if payload.mentions is not None:
            np.mentions = payload.mentions
        if payload.project_updates is not None:
            np.project_updates = payload.project_updates
        if payload.workspace_updates is not None:
            np.workspace_updates = payload.workspace_updates
        if payload.marketing is not None:
            np.marketing = payload.marketing

        np.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(np)
        return np

    async def log_audit_event(
        self, db: AsyncSession, user_id: UUID, org_id: Optional[UUID], action: str,
        resource_type: Optional[str] = None, resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None
    ) -> AuditLog:
        audit = AuditLog(
            id=uuid4(),
            action=action,
            user_id=user_id,
            organization_id=org_id,
            details=details or {},
            created_at=datetime.utcnow()
        )
        setattr(audit, "resource_type", resource_type)
        setattr(audit, "resource_id", resource_id)
        setattr(audit, "ip_address", ip_address)
        db.add(audit)
        await db.commit()
        return audit

    async def list_audit_logs(self, db: AsyncSession, org_id: UUID, limit: int = 50) -> List[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.organization_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
