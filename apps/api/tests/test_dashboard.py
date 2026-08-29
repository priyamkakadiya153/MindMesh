import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.workspace.models import Workspace
from app.projects.models import Project
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.core.security import create_access_token
from passlib.hash import bcrypt

from app.models.session import UserSession
from datetime import datetime, timedelta

@pytest_asyncio.fixture
async def seeded_dashboard_data(db_session: AsyncSession):
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = bcrypt.hash("password123")
    user = User(username="dashuser", email="dash@example.com", hashed_password=hashed_pwd)
    db_session.add(user)
    await db_session.flush()

    org = Organization(name="Dash Org", slug="dash-org", owner_id=user.id)
    db_session.add(org)
    await db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(member)
    await db_session.flush()

    ws = Workspace(name="Dash WS", slug="dash-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()

    user_session = UserSession(
        user_id=user.id,
        refresh_token_hash="test_refresh_token_hash",
        device_name="pytest",
        ip_address="127.0.0.1",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(user_session)
    await db_session.commit()

    return {
        "user": user,
        "org": org,
        "workspace": ws,
        "session": user_session
    }

@pytest.mark.asyncio
async def test_activity_log(client: AsyncClient, seeded_dashboard_data: dict, db_session: AsyncSession):
    user = seeded_dashboard_data["user"]
    org = seeded_dashboard_data["org"]
    ws = seeded_dashboard_data["workspace"]
    sess = seeded_dashboard_data["session"]
    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    response = await client.get("/api/v1/activity/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

    from app.activity.service import ActivityService
    service = ActivityService(db_session)
    await service.record_event(
        org_id=org.id,
        user_id=user.id,
        event_type="Workspace Created",
        workspace_id=ws.id,
        metadata={"name": ws.name}
    )
    await db_session.commit()

    response2 = await client.get("/api/v1/activity/", headers=headers)
    assert response2.status_code == 200
    data = response2.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "Workspace Created"
    assert data[0]["metadata"]["name"] == "Dash WS"

@pytest.mark.asyncio
async def test_notifications(client: AsyncClient, seeded_dashboard_data: dict, db_session: AsyncSession):
    user = seeded_dashboard_data["user"]
    org = seeded_dashboard_data["org"]
    sess = seeded_dashboard_data["session"]
    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    from app.notifications.service import NotificationService
    service = NotificationService(db_session)
    notif = await service.create_notification(
        user_id=user.id,
        title="Alert",
        message="System shutdown incoming",
        type="alert",
        priority="high"
    )
    await db_session.commit()

    response = await client.get("/api/v1/notifications/", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    notif_list = res_data if isinstance(res_data, list) else res_data.get("notifications", [])
    assert len(notif_list) == 1
    assert notif_list[0]["title"] == "Alert"

    res_read = await client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    res_del = await client.delete(f"/api/v1/notifications/{notif.id}", headers=headers)
    assert res_del.status_code in (200, 204)

@pytest.mark.asyncio
async def test_recent_items(client: AsyncClient, seeded_dashboard_data: dict, db_session: AsyncSession):
    user = seeded_dashboard_data["user"]
    org = seeded_dashboard_data["org"]
    ws = seeded_dashboard_data["workspace"]
    sess = seeded_dashboard_data["session"]
    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    from app.recent.service import RecentItemService
    service = RecentItemService(db_session)
    await service.record_recent(
        user_id=user.id,
        entity_type="workspace",
        entity_id=ws.id,
        name=ws.name,
        slug=ws.slug
    )
    await db_session.commit()

    response = await client.get("/api/v1/recent/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Dash WS"

@pytest.mark.asyncio
async def test_favorites(client: AsyncClient, seeded_dashboard_data: dict, db_session: AsyncSession):
    user = seeded_dashboard_data["user"]
    org = seeded_dashboard_data["org"]
    ws = seeded_dashboard_data["workspace"]
    sess = seeded_dashboard_data["session"]
    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "item_type": "workspace",
        "item_id": str(ws.id),
        "name": ws.name,
        "slug": ws.slug
    }
    response = await client.post("/api/v1/favorites/", json=payload, headers=headers)
    assert response.status_code == 201
    fav_id = response.json()["id"]

    response_list = await client.get("/api/v1/favorites/", headers=headers)
    assert response_list.status_code == 200
    assert len(response_list.json()) == 1

    res_del = await client.delete(f"/api/v1/favorites/{fav_id}", headers=headers)
    assert res_del.status_code == 204

@pytest.mark.asyncio
async def test_dashboard_aggregation(client: AsyncClient, seeded_dashboard_data: dict):
    user = seeded_dashboard_data["user"]
    org = seeded_dashboard_data["org"]
    ws = seeded_dashboard_data["workspace"]
    sess = seeded_dashboard_data["session"]
    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    response = await client.get(f"/api/v1/dashboard/?workspace_id={ws.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    assert "recent_projects" in data
    assert "notifications" in data

    response2 = await client.get("/api/v1/dashboard/widgets", headers=headers)
    assert response2.status_code == 200
    assert "widgets" in response2.json()

    response3 = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert response3.status_code == 200
    assert "statistics" in response3.json()

