import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.user import User
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate
from app.settings.service import SettingsService
from app.settings.schemas import UserProfileUpdate, UserSettingsUpdate, NotificationPrefSchema

@pytest.mark.asyncio
async def test_get_and_update_user_profile(db_session: AsyncSession):
    user = User(
        email=f"profile_user_{uuid4().hex[:6]}@example.com",
        username=f"orig_name_{uuid4().hex[:4]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    service = SettingsService()
    updated = await service.update_user_profile(
        db_session, user, UserProfileUpdate(username="updated_name", mobile="+15550199", avatar_url="https://example.com/avatar.jpg")
    )

    assert updated.username == "updated_name"
    assert updated.mobile == "+15550199"
    assert updated.avatar_url == "https://example.com/avatar.jpg"

@pytest.mark.asyncio
async def test_user_settings_and_theme_persistence(db_session: AsyncSession):
    user = User(
        email=f"settings_user_{uuid4().hex[:6]}@example.com",
        username=f"sett_user_{uuid4().hex[:4]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    service = SettingsService()
    sett = await service.get_or_create_user_settings(db_session, user.id)
    assert sett.theme == "dark"

    updated_sett = await service.update_user_settings(
        db_session, user.id, UserSettingsUpdate(theme="light", language="es", timezone="America/New_York", email_notifications=False)
    )
    assert updated_sett.theme == "light"
    assert updated_sett.language == "es"
    assert updated_sett.timezone == "America/New_York"
    assert updated_sett.email_notifications is False

@pytest.mark.asyncio
async def test_audit_logging_and_retrieval(db_session: AsyncSession):
    user = User(
        email=f"audit_user_{uuid4().hex[:6]}@example.com",
        username=f"audit_user_{uuid4().hex[:4]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Audit Org", slug=f"aud-org-{uuid4().hex[:4]}")
    )

    service = SettingsService()
    await service.log_audit_event(
        db_session, user.id, org.id, "organization.update_branding", "Organization", str(org.id), {"color": "#3B82F6"}
    )

    logs = await service.list_audit_logs(db_session, org.id)
    assert len(logs) >= 1
    target = next(l for l in logs if l.action == "organization.update_branding")
    assert target.user_id == user.id
    assert target.details["color"] == "#3B82F6"
