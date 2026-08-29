import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from app.models.user import User
from app.notifications.service import NotificationService
from app.activity.service import ActivityService
from app.settings.service import SettingsService
from app.main import app

@pytest.mark.asyncio
async def test_notification_framework_endpoints(db_session: AsyncSession):
    user = User(
        email=f"notif_user_{uuid4().hex[:6]}@example.com",
        username=f"notif_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    service = NotificationService(db_session)
    n1 = await service.create_notification(user.id, "Welcome", "Welcome to MindMesh")
    n2 = await service.create_notification(user.id, "Alert", "Security alert notice")

    notifs = await service.list_notifications(user.id)
    assert len(notifs) >= 2

    # Mark single read
    await service.mark_as_read(user.id, n1.id)
    unread = await service.list_notifications(user.id, only_unread=True)
    assert len(unread) == 1

    # Mark all read
    count = await service.mark_all_read(user.id)
    assert count >= 1

@pytest.mark.asyncio
async def test_activity_and_audit_logging_services(db_session: AsyncSession):
    user = User(
        email=f"audit_user_{uuid4().hex[:6]}@example.com",
        username=f"audit_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    act_service = ActivityService(db_session)
    await act_service.record_event(org_id, user.id, "user.login", metadata={"ip": "127.0.0.1"})

    settings_service = SettingsService()
    await settings_service.log_audit_event(
        db=db_session,
        user_id=user.id,
        org_id=org_id,
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address="127.0.0.1"
    )

    timeline = await act_service.list_timeline(org_id)
    assert len(timeline) >= 1

    audit_logs = await settings_service.list_audit_logs(db_session, org_id)
    assert len(audit_logs) >= 1

@pytest.mark.asyncio
async def test_secure_headers_middleware():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Strict-Transport-Security" in response.headers
